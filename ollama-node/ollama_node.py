#!/usr/bin/env python3
"""Agente de nodo Ollama para el HomeLab (solo biblioteca estándar, Python >= 3.9).

Subcomandos:
  register [--loop|--once]   registra el nodo (PUT /_registry/nodes/<name>) y manda latidos
  deregister                 saca el nodo del registro (DELETE)
  list-models                imprime el JSON de modelos leído de los manifests
  payload                    imprime el cuerpo JSON que se enviaría al registro
  status                     consulta el registro y dice si este nodo figura
  proxy                      modo macOS: proxy bajo demanda detrás de un socket de launchd

El agente nunca imprime el token del registro. La lectura de modelos no despierta
a Ollama: recorre OLLAMA_MODELS/manifests y manifests-v2 directamente.
"""
import argparse
import hashlib
import ipaddress
import json
import os
import platform
import random
import re
import shutil
import signal
import socket
import ssl
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

DEFAULT_REGISTRY_HOST = "registry.ollama.ai"
# En manifests-v2 el host público se guarda como ollama.com.
_PUBLIC_HOSTS = ("registry.ollama.ai", "ollama.com")

DEFAULTS = {
    "name": "",
    "url": "",
    "registry_url": "",
    "token_file": "",
    "token_keychain": "",
    "ca_file": "",
    "priority": 50,
    "tags": [],
    "models_dir": "",
    "interval": 60,
    "allowed_cidrs": [],
    "idle_timeout": 300,
    "ollama_bin": "",
    "internal_port": 11435,
    "listen_port": 11434,
    "keep_alive": "5m",
    "max_loaded_models": 1,
    "start_timeout": 120,
    "start_cooldown": 20,
    "first_byte_timeout": 10,
    "conn_idle_timeout": 300,
    "pid_file": "",
    "caffeinate_bin": "",
    "allow_insecure_registry": False,
}


def log(msg):
    sys.stderr.write("%s ollama-node: %s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg))
    sys.stderr.flush()


# ---------------------------------------------------------------- configuración

def default_config_path():
    env = os.environ.get("OLLAMA_NODE_CONFIG")
    if env:
        return env
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/ollama-node/config.json")
    return "/etc/ollama-node/config.json"


def load_config(path=None):
    path = path or default_config_path()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise SystemExit("no existe el config: %s" % path)
    except ValueError as exc:
        raise SystemExit("config inválido (%s): %s" % (path, exc))
    if not isinstance(data, dict):
        raise SystemExit("config inválido (%s): se esperaba un objeto JSON" % path)
    cfg = dict(DEFAULTS)
    cfg.update(data)
    cfg["_path"] = path
    if not cfg["name"]:
        cfg["name"] = socket.gethostname().split(".")[0]
    return cfg


def read_token(cfg):
    """Devuelve el token del registro: archivo, Keychain (macOS) o variable de entorno."""
    tf = cfg.get("token_file")
    if tf:
        try:
            with open(os.path.expanduser(tf), "r", encoding="utf-8") as fh:
                tok = fh.read().strip()
        except OSError as exc:
            raise RuntimeError("no se pudo leer token_file (%s)" % exc.strerror)
        if tok:
            return tok
    svc = cfg.get("token_keychain")
    if svc and sys.platform == "darwin":
        res = subprocess.run(["security", "find-generic-password", "-s", svc, "-a", cfg["name"], "-w"],
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
        raise RuntimeError("no se encontró el token en el Keychain (servicio %s)" % svc)
    env = os.environ.get("OLLAMA_NODE_TOKEN", "").strip()
    if env:
        return env
    raise RuntimeError("sin token: define token_file, token_keychain u OLLAMA_NODE_TOKEN")


# ---------------------------------------------------------------- lector de manifests

def default_models_dir(cfg=None):
    if cfg and cfg.get("models_dir"):
        return os.path.expanduser(cfg["models_dir"])
    env = os.environ.get("OLLAMA_MODELS")
    if env:
        return os.path.expanduser(env)
    if sys.platform == "darwin":
        return os.path.expanduser("~/.ollama/models")
    if sys.platform.startswith("linux"):
        # Ruta del instalador oficial; el rol de Ansible usa /var/lib/ollama (se detecta si existe).
        for cand in ("/usr/share/ollama/.ollama/models", "/var/lib/ollama/.ollama/models"):
            if os.path.isdir(cand):
                return cand
        return "/usr/share/ollama/.ollama/models"
    raise SystemExit("sistema no soportado: %s (Windows no se implementa)" % sys.platform)


def _canon_host(host):
    host = urllib.parse.unquote(host).lower()
    return DEFAULT_REGISTRY_HOST if host in _PUBLIC_HOSTS else host


def display_name(host, namespace, model, tag):
    """Equivale a DisplayShortest de Ollama (types/model/name.go)."""
    if _canon_host(host) != DEFAULT_REGISTRY_HOST:
        prefix = "%s/%s/" % (urllib.parse.unquote(host), namespace)
    elif namespace != "library":
        prefix = namespace + "/"
    else:
        prefix = ""
    return "%s%s:%s" % (prefix, model, tag)


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _blob_path(models_dir, digest):
    return os.path.join(models_dir, "blobs", digest.replace(":", "-"))


def _read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _resolve_child(models_dir, child):
    """Un hijo de una manifest list puede venir en línea o como referencia a un blob."""
    if not isinstance(child, dict):
        return None
    if child.get("config") or child.get("layers"):
        return child
    digest = child.get("digest")
    if isinstance(digest, str) and digest:
        try:
            res = _read_json(_blob_path(models_dir, digest))
        except (OSError, ValueError):
            return None
        return res if isinstance(res, dict) else None
    return None


def _select_manifest(models_dir, data):
    """Devuelve el manifest 'plano' (con config y layers); en una lista elige el primer hijo resoluble."""
    if not isinstance(data, dict):
        return None
    if data.get("manifests") and not data.get("config"):
        children = data["manifests"]
        if not isinstance(children, list):
            return None
        for child in children:
            res = _resolve_child(models_dir, child)
            if res is not None:
                return res
        return None
    return data


def _manifest_size(m):
    total = 0
    cfg = m.get("config") or {}
    total += int(cfg.get("size") or 0)
    for layer in m.get("layers") or []:
        total += int(layer.get("size") or 0)
    return total


def _model_entry(models_dir, path, host, namespace, model, tag):
    """Entrada de un modelo; ante cualquier forma inesperada devuelve None (el modelo se omite con un log)."""
    try:
        digest = _sha256_file(path)
        st = os.stat(path)
        data = _read_json(path)
        flat = _select_manifest(models_dir, data)
        if flat is None:
            log("manifest sin forma válida o sin hijo resoluble: %s" % path)
            return None
        conf = {}
        cdigest = (flat.get("config") or {}).get("digest")
        if cdigest:
            try:
                conf = _read_json(_blob_path(models_dir, cdigest))
            except (OSError, ValueError):
                conf = {}
            if not isinstance(conf, dict):
                conf = {}
        name = display_name(host, namespace, model, tag)
        return {
            "name": name,
            "model": name,
            "modified_at": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
            "size": _manifest_size(flat),
            "digest": digest,
            "details": {
                "format": conf.get("model_format", ""),
                "family": conf.get("model_family", ""),
                "families": conf.get("model_families"),
                "parameter_size": conf.get("model_type", ""),
                "quantization_level": conf.get("file_type", ""),
            },
        }
    except Exception as exc:  # noqa: BLE001 - un manifest raro no debe tumbar al agente
        log("manifest inválido %s: %s: %s" % (path, type(exc).__name__, exc))
        return None


def _scan_tree(root):
    """Itera (ruta, host, namespace, modelo, tag) del árbol host/namespace/model/tag; ignora ocultos."""
    if not os.path.isdir(root):
        return
    for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for fn in sorted(filenames):
            if fn.startswith("."):
                continue
            full = os.path.join(dirpath, fn)
            parts = os.path.relpath(full, root).split(os.sep)
            if len(parts) != 4:
                continue
            yield (full,) + tuple(parts)


def read_models(models_dir):
    """Lee los modelos instalados sin tocar a Ollama. manifests-v2 gana sobre manifests."""
    found = {}
    # v2 primero: la primera entrada de cada nombre se conserva (igual que namedManifestRefs).
    for sub in ("manifests-v2", "manifests"):
        for full, host, ns, model, tag in _scan_tree(os.path.join(models_dir, sub)):
            key = (_canon_host(host), ns.lower(), model.lower(), tag.lower())
            if key in found:
                continue
            entry = _model_entry(models_dir, full, host, ns, model, tag)
            if entry is not None:
                found[key] = entry
    return sorted(found.values(), key=lambda e: e["name"])


# ---------------------------------------------------------------- datos del nodo

def go_arch():
    m = platform.machine().lower()
    return {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}.get(m, m)


def ram_gb():
    try:
        if sys.platform == "darwin":
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], universal_newlines=True)
            return round(int(out.strip()) / 1024 ** 3, 1)
        with open("/proc/meminfo", "r") as fh:
            for line in fh:
                if line.startswith("MemTotal:"):
                    return round(int(line.split()[1]) / 1024 ** 2, 1)
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return 0


def find_ollama(cfg):
    if cfg.get("ollama_bin"):
        return cfg["ollama_bin"]
    found = shutil.which("ollama")
    if found:
        return found
    for cand in ("/opt/homebrew/bin/ollama", "/usr/local/bin/ollama", "/usr/bin/ollama"):
        if os.path.exists(cand):
            return cand
    return "ollama"


def ollama_version(cfg):
    """Versión del binario (ollama --version no arranca el servidor)."""
    try:
        res = subprocess.run([find_ollama(cfg), "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             universal_newlines=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return ""
    m = re.search(r"(?:ollama|client) version is\s+(\S+)", res.stdout)
    return m.group(1) if m else ""


def build_payload(cfg, models=None, version=None):
    if models is None:
        models = read_models(default_models_dir(cfg))
    return {
        "name": cfg["name"],
        "url": cfg["url"],
        "os": {"darwin": "darwin"}.get(sys.platform, "linux" if sys.platform.startswith("linux") else sys.platform),
        "arch": go_arch(),
        "ram_gb": ram_gb(),
        "priority": int(cfg["priority"]),
        "tags": list(cfg.get("tags") or []),
        "ollama_version": version if version is not None else ollama_version(cfg),
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "models": models,
    }


# ---------------------------------------------------------------- cliente del registro

def _is_loopback(host):
    return host in ("localhost", "127.0.0.1", "::1")


def _registry_target(cfg):
    base = (cfg.get("registry_url") or "").rstrip("/")
    if not base:
        raise RuntimeError("falta registry_url en el config")
    parsed = urllib.parse.urlparse(base)
    if parsed.scheme not in ("http", "https"):
        raise RuntimeError("registry_url debe ser http(s)")
    if parsed.scheme == "http" and not _is_loopback(parsed.hostname or "") and not cfg.get("allow_insecure_registry"):
        raise RuntimeError("registry_url usa http fuera de loopback: el token viajaría en claro (usa https)")
    return base


def _ssl_context(cfg):
    ca = cfg.get("ca_file")
    if ca:
        return ssl.create_default_context(cafile=os.path.expanduser(ca))
    return ssl.create_default_context()


def _request(cfg, method, body=None, timeout=15):
    base = _registry_target(cfg)
    url = "%s/_registry/nodes/%s" % (base, urllib.parse.quote(cfg["name"], safe=""))
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + read_token(cfg))
    if data is not None:
        req.add_header("Content-Type", "application/json")
    ctx = _ssl_context(cfg) if base.startswith("https") else None
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        resp.read()
        return resp.status


def _with_retries(fn, retries, sleep, base_delay=1.0, max_delay=30.0):
    """Reintenta con backoff exponencial y jitter. No reintenta 4xx (salvo 408/429)."""
    last = None
    for attempt in range(retries):
        try:
            return fn()
        except urllib.error.HTTPError as exc:
            last = "HTTP %d" % exc.code
            exc.close()
            if 400 <= exc.code < 500 and exc.code not in (408, 429):
                raise RuntimeError("el registro rechazó la petición: " + last)
        except (urllib.error.URLError, OSError, ssl.SSLError) as exc:
            reason = getattr(exc, "reason", exc)
            last = type(reason).__name__ + ": " + str(reason)
        if attempt + 1 < retries:
            delay = min(max_delay, base_delay * (2 ** attempt))
            sleep(delay * (0.5 + random.random() / 2))
    raise RuntimeError("registro inalcanzable tras %d intentos (%s)" % (retries, last))


def register_once(cfg, retries=5, sleep=time.sleep):
    body = build_payload(cfg)
    _with_retries(lambda: _request(cfg, "PUT", body), retries, sleep)
    return body


def deregister(cfg, retries=3, sleep=time.sleep):
    def call():
        try:
            return _request(cfg, "DELETE")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:  # ya no estaba registrado
                exc.close()
                return 404
            raise
    return _with_retries(call, retries, sleep)


def register_loop(cfg, stop_event, retries=3, sleep=time.sleep, deregister_on_exit=True):
    interval = max(0.05, float(cfg["interval"]))
    while not stop_event.is_set():
        try:
            body = register_once(cfg, retries=retries, sleep=sleep)
            log("registrado: %s (%d modelos)" % (cfg["name"], len(body["models"])))
        except Exception as exc:  # noqa: BLE001 - el latido debe seguir pase lo que pase
            log("error de registro: %s: %s" % (type(exc).__name__, exc))
        stop_event.wait(interval)
    if deregister_on_exit:
        try:
            deregister(cfg, retries=1, sleep=sleep)
            log("retirado del registro")
        except RuntimeError as exc:
            log("no se pudo retirar del registro: %s" % exc)


# ---------------------------------------------------------------- proxy bajo demanda

def launchd_sockets(name="Listeners"):
    """Recoge los sockets que launchd abrió para la clave Sockets del plist (libSystem)."""
    import ctypes
    lib = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    fn = lib.launch_activate_socket
    fn.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.POINTER(ctypes.c_int)), ctypes.POINTER(ctypes.c_size_t)]
    fn.restype = ctypes.c_int
    lib.free.argtypes = [ctypes.c_void_p]
    fds = ctypes.POINTER(ctypes.c_int)()
    cnt = ctypes.c_size_t()
    rc = fn(name.encode("utf-8"), ctypes.byref(fds), ctypes.byref(cnt))
    if rc != 0:
        raise OSError(rc, "launch_activate_socket: " + os.strerror(rc))
    result = [fds[i] for i in range(cnt.value)]
    lib.free(ctypes.cast(fds, ctypes.c_void_p))
    return [socket.socket(fileno=fd) for fd in result]


def parse_cidrs(items):
    nets = []
    for item in items or []:
        nets.append(ipaddress.ip_network(str(item).strip(), strict=False))
    return nets


def ip_allowed(ip, nets):
    """Lista vacía = nadie (cierra por defecto)."""
    try:
        addr = ipaddress.ip_address(ip.split("%")[0])
    except ValueError:
        return False
    if getattr(addr, "ipv4_mapped", None):
        addr = addr.ipv4_mapped
    return any(addr in n for n in nets if n.version == addr.version)


def _pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except OSError:
        return True


def _pid_is_ollama(pid):
    """Comprueba que el pid sea un `ollama serve` (evita matar un pid reutilizado por otro programa)."""
    try:
        out = subprocess.run(["ps", "-p", str(pid), "-o", "command="], stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, universal_newlines=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    return "ollama" in out.lower() and "serve" in out


def _kill_group(pid, grace=10.0):
    """SIGTERM al grupo de Ollama (lo lanzamos con sesión propia) y SIGKILL si no sale."""
    def send(sig):
        try:
            if os.getpgid(pid) == pid:
                os.killpg(pid, sig)
            else:
                os.kill(pid, sig)
        except OSError:
            pass
    send(signal.SIGTERM)
    end = time.time() + grace
    while time.time() < end and _pid_alive(pid):
        time.sleep(0.1)
    if _pid_alive(pid):
        send(signal.SIGKILL)


class OnDemandProxy(object):
    def __init__(self, cfg, listeners):
        self.cfg = cfg
        self.listeners = listeners
        self.nets = parse_cidrs(cfg.get("allowed_cidrs"))
        self.port = int(cfg["internal_port"])
        self.idle_timeout = float(cfg["idle_timeout"])
        self.first_byte_timeout = float(cfg["first_byte_timeout"])
        self.conn_idle_timeout = float(cfg["conn_idle_timeout"])
        self.start_cooldown = float(cfg["start_cooldown"])
        self.lock = threading.Lock()
        self.start_lock = threading.Lock()
        self.active = 0   # conexiones aceptadas y aún no cerradas (se suma en el hilo de accept)
        self.busy = 0     # conexiones que ya enviaron datos (mantienen caffeinate)
        self.last_activity = time.time()
        self.proc = None
        self.ready = False
        self.fail_until = 0.0
        self.caff = None
        self.stopping = threading.Event()
        self.started_at = []  # marcas de tiempo de cada arranque de Ollama (para pruebas)
        self._sel = None

    # -- pidfile (junto al config, modo 0600)
    def _pid_path(self):
        if self.cfg.get("pid_file"):
            return os.path.expanduser(self.cfg["pid_file"])
        if self.cfg.get("_path"):
            return os.path.join(os.path.dirname(os.path.abspath(self.cfg["_path"])), "ollama.pid")
        return ""

    def _write_pid(self, pid):
        path = self._pid_path()
        if not path:
            return
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as fh:
                fh.write("%d\n" % pid)
        except OSError as exc:
            log("no se pudo escribir el pidfile %s: %s" % (path, exc.strerror))

    def _clear_pid(self):
        path = self._pid_path()
        if path:
            try:
                os.unlink(path)
            except OSError:
                pass

    def reap_orphan(self):
        """Si un proxy anterior murió (kill -9) dejando su Ollama vivo, lo detiene antes de empezar."""
        path = self._pid_path()
        if not path or not os.path.exists(path):
            return
        try:
            with open(path) as fh:
                pid = int(fh.read().strip())
        except (OSError, ValueError):
            self._clear_pid()
            return
        if pid != os.getpid() and _pid_alive(pid) and _pid_is_ollama(pid):
            log("deteniendo Ollama huérfano (pid %d) de un proxy anterior" % pid)
            _kill_group(pid)
        self._clear_pid()

    # -- Ollama
    def _probe(self):
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/api/version" % self.port, timeout=2) as r:
                return r.status == 200
        except (OSError, urllib.error.URLError):
            return False

    def _launch(self):
        """Lanza ollama serve y espera a que responda. Lanza RuntimeError si falla (y lo mata)."""
        env = dict(os.environ)
        env["OLLAMA_HOST"] = "127.0.0.1:%d" % self.port
        env["OLLAMA_KEEP_ALIVE"] = str(self.cfg["keep_alive"])
        env["OLLAMA_MAX_LOADED_MODELS"] = str(self.cfg["max_loaded_models"])
        if self.cfg.get("models_dir"):
            env["OLLAMA_MODELS"] = os.path.expanduser(self.cfg["models_dir"])
        log("arrancando ollama serve en 127.0.0.1:%d" % self.port)
        try:
            proc = subprocess.Popen([find_ollama(self.cfg), "serve"], env=env,
                                    stdin=subprocess.DEVNULL, start_new_session=True)
        except OSError as exc:
            raise RuntimeError("no se pudo lanzar ollama: %s" % exc.strerror)
        self.proc = proc
        self._write_pid(proc.pid)
        self.started_at.append(time.time())
        deadline = time.time() + float(self.cfg["start_timeout"])
        while time.time() < deadline and not self.stopping.is_set():
            if proc.poll() is not None:
                raise RuntimeError("ollama serve terminó con código %s" % proc.returncode)
            if self._probe():
                self.ready = True
                return
            time.sleep(0.2)
        self._stop_ollama()  # nunca escuchó (o nos están apagando): no dejarlo vivo
        raise RuntimeError("ollama no respondió en %ss" % self.cfg["start_timeout"])

    def _ensure_ollama(self):
        """Todas las conexiones que esperan comparten el mismo intento de arranque."""
        with self.start_lock:
            proc = self.proc
            if self.ready and (proc is None or proc.poll() is None):
                return
            self.ready = False
            if time.time() < self.fail_until:
                raise RuntimeError("arranque de ollama en cooldown tras un fallo reciente")
            if proc is not None and proc.poll() is None:
                self._stop_ollama()
            if self._probe():  # ya hay algo sirviendo en el puerto interno: no es nuestro
                self.proc = None
                self.ready = True
                return
            try:
                self._launch()
            except RuntimeError:
                self.fail_until = time.time() + self.start_cooldown
                raise

    def _stop_ollama(self):
        proc, self.proc, self.ready = self.proc, None, False
        if proc is None:
            return
        if proc.poll() is None:
            log("deteniendo ollama")
            try:
                proc.terminate()
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except OSError:
                    proc.kill()
                proc.wait()
            except OSError:
                pass
        self._clear_pid()

    # -- caffeinate
    def _caff_start(self):
        binary = self.cfg.get("caffeinate_bin") or (shutil.which("caffeinate") if sys.platform == "darwin" else "")
        if not binary or self.caff is not None:
            return
        try:
            self.caff = subprocess.Popen([binary, "-i", "-w", str(os.getpid())], stdin=subprocess.DEVNULL)
        except OSError as exc:
            log("no se pudo lanzar caffeinate: %s" % exc)

    def _caff_stop(self):
        caff, self.caff = self.caff, None
        if caff is not None:
            caff.terminate()
            try:
                caff.wait(timeout=5)
            except subprocess.TimeoutExpired:
                caff.kill()

    # -- conexiones
    @staticmethod
    def _keepalive(sock):
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            opt = getattr(socket, "TCP_KEEPALIVE", None) or getattr(socket, "TCP_KEEPIDLE", None)
            if opt is None and sys.platform == "darwin":
                opt = 0x10  # TCP_KEEPALIVE en macOS
            if opt is not None:
                sock.setsockopt(socket.IPPROTO_TCP, opt, 60)
        except OSError:
            pass

    def _relay(self, a, b):
        """Reenvía en ambos sentidos con tope de inactividad por conexión (sin bytes -> se cierra)."""
        import select
        peers = {a: b, b: a}
        while peers:
            ready, _, _ = select.select(list(peers), [], [], self.conn_idle_timeout)
            if not ready:
                log("conexión inactiva %.0fs: cerrando" % self.conn_idle_timeout)
                return
            for src in ready:
                dst = peers[src]
                try:
                    data = src.recv(65536)
                except OSError:
                    return
                if not data:
                    del peers[src]
                    try:
                        dst.shutdown(socket.SHUT_WR)
                    except OSError:
                        pass
                    continue
                try:
                    dst.sendall(data)
                except OSError:
                    return

    def handle(self, conn, ip):
        """Hilo de la conexión. `active` ya se sumó en el hilo de accept; aquí solo se resta."""
        up = None
        counted_busy = False
        try:
            self._keepalive(conn)
            # No se despierta a Ollama hasta recibir el primer byte del cliente.
            conn.settimeout(self.first_byte_timeout)
            try:
                first = conn.recv(65536)
            except (socket.timeout, OSError):
                first = b""
            if not first:
                return
            with self.lock:
                self.busy += 1
                counted_busy = True
                if self.busy == 1:
                    self._caff_start()
            self._ensure_ollama()
            up = socket.create_connection(("127.0.0.1", self.port), timeout=10)
            self._keepalive(up)
            up.settimeout(self.conn_idle_timeout)
            conn.settimeout(self.conn_idle_timeout)
            up.sendall(first)
            self._relay(conn, up)
        except (RuntimeError, OSError) as exc:
            log("error atendiendo a %s: %s" % (ip, exc))
        finally:
            for sk in (up, conn):
                if sk is not None:
                    try:
                        sk.close()
                    except OSError:
                        pass
            with self.lock:
                if counted_busy:
                    self.busy -= 1
                    if self.busy == 0:
                        self._caff_stop()
                self.active -= 1
                self.last_activity = time.time()

    def _accept_ready(self, key):
        try:
            conn, addr = key.fileobj.accept()
        except (BlockingIOError, InterruptedError):
            return
        except OSError as exc:  # ECONNABORTED, EMFILE...: se registra y se sigue
            log("accept falló: %s" % exc)
            time.sleep(0.1)
            return
        ip = addr[0]
        if not ip_allowed(ip, self.nets):
            log("conexión rechazada de %s (fuera de allowed_cidrs)" % ip)
            conn.close()
            return
        conn.setblocking(True)
        # La conexión se cuenta aquí, en el hilo de accept, ANTES de que exista su hilo: así la
        # decisión de inactividad nunca ve "0 activas" con una conexión ya aceptada.
        with self.lock:
            self.active += 1
            self.last_activity = time.time()
        try:
            threading.Thread(target=self.handle, args=(conn, ip), daemon=True).start()
        except Exception:  # noqa: BLE001
            with self.lock:
                self.active -= 1
            conn.close()
            raise

    def poll_once(self, timeout=0.5):
        """Un ciclo del bucle principal. Devuelve True si el proxy debe salir por inactividad."""
        import selectors
        if self._sel is None:
            self._sel = selectors.DefaultSelector()
            for lst in self.listeners:
                lst.setblocking(False)
                self._sel.register(lst, selectors.EVENT_READ)
        try:
            events = self._sel.select(timeout=timeout)
        except OSError as exc:
            log("select falló: %s" % exc)
            time.sleep(0.1)
            return False
        for key, _ in events:
            self._accept_ready(key)
        with self.lock:
            idle = self.active == 0 and (time.time() - self.last_activity) >= self.idle_timeout
        if idle and self._sel.select(timeout=0):
            return False  # hay una conexión esperando en el backlog: se atiende en el siguiente ciclo
        return idle

    def serve_forever(self):
        self.reap_orphan()
        try:
            while not self.stopping.is_set():
                if self.poll_once():
                    log("inactivo %.0fs: saliendo" % self.idle_timeout)
                    break
        finally:
            if self._sel is not None:
                self._sel.close()
            self.shutdown()

    def shutdown(self):
        self.stopping.set()  # aborta un arranque en curso
        with self.start_lock:
            self._stop_ollama()
        with self.lock:
            self._caff_stop()


def make_listener(spec):
    host, _, port = spec.rpartition(":")
    sock = socket.socket(socket.AF_INET6 if ":" in host else socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host or "0.0.0.0", int(port)))
    sock.listen(64)
    return sock


# ---------------------------------------------------------------- comandos

def cmd_register(args):
    cfg = load_config(args.config)
    if args.loop:
        stop = threading.Event()
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda *_: stop.set())
        register_loop(cfg, stop, deregister_on_exit=not args.keep_on_exit)
        return 0
    try:
        body = register_once(cfg, retries=args.retries)
    except Exception as exc:  # noqa: BLE001
        log("error: %s: %s" % (type(exc).__name__, exc))
        return 1
    log("registrado: %s (%d modelos)" % (cfg["name"], len(body["models"])))
    return 0


def cmd_deregister(args):
    cfg = load_config(args.config)
    try:
        deregister(cfg)
    except RuntimeError as exc:
        log("error: %s" % exc)
        return 1
    log("retirado del registro: %s" % cfg["name"])
    return 0


def cmd_list_models(args):
    cfg = load_config(args.config) if (args.config or os.path.exists(default_config_path())) else dict(DEFAULTS)
    models_dir = args.models_dir or default_models_dir(cfg)
    print(json.dumps(read_models(models_dir), indent=2, ensure_ascii=False))
    return 0


def cmd_payload(args):
    cfg = load_config(args.config)
    print(json.dumps(build_payload(cfg), indent=2, ensure_ascii=False))
    return 0


def cmd_status(args):
    cfg = load_config(args.config)
    try:
        base = _registry_target(cfg)
        req = urllib.request.Request(base + "/_registry/nodes")
        req.add_header("Authorization", "Bearer " + read_token(cfg))
        ctx = _ssl_context(cfg) if base.startswith("https") else None
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (RuntimeError, OSError, ValueError, urllib.error.URLError) as exc:
        print("registro: inalcanzable (%s)" % exc)
        return 1
    nodes = data.get("nodes", data) if isinstance(data, dict) else data
    names = [n.get("name") for n in nodes if isinstance(n, dict)]
    print("registro: %s" % ("este nodo FIGURA" if cfg["name"] in names else "este nodo NO figura"))
    print("nodos vivos: %s" % ", ".join(sorted(str(n) for n in names)))
    return 0 if cfg["name"] in names else 2


def cmd_proxy(args):
    cfg = load_config(args.config)
    if args.listen:
        listeners = [make_listener(args.listen)]
    else:
        if sys.platform != "darwin":
            raise SystemExit("proxy sin --listen solo funciona bajo launchd (macOS)")
        listeners = launchd_sockets(args.socket_name)
    proxy = OnDemandProxy(cfg, listeners)
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: proxy.stopping.set())
    log("proxy listo (allowed_cidrs=%s, idle_timeout=%ss)" % (cfg["allowed_cidrs"], cfg["idle_timeout"]))
    proxy.serve_forever()
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="ollama_node.py", description=__doc__.split("\n")[0])
    p.add_argument("--config", help="ruta del config JSON (por defecto: %s)" % default_config_path())
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("register", help="registra el nodo")
    g = r.add_mutually_exclusive_group()
    g.add_argument("--loop", action="store_true", help="latido continuo cada `interval` segundos")
    g.add_argument("--once", action="store_true", help="un solo registro y salir (por defecto)")
    r.add_argument("--retries", type=int, default=5)
    r.add_argument("--keep-on-exit", action="store_true", help="con --loop, no hacer DELETE al recibir SIGTERM")
    r.set_defaults(fn=cmd_register)
    sub.add_parser("deregister", help="saca el nodo del registro").set_defaults(fn=cmd_deregister)
    lm = sub.add_parser("list-models", help="imprime los modelos instalados (JSON)")
    lm.add_argument("--models-dir")
    lm.set_defaults(fn=cmd_list_models)
    sub.add_parser("payload", help="imprime el cuerpo del registro").set_defaults(fn=cmd_payload)
    sub.add_parser("status", help="consulta si el nodo figura en el registro").set_defaults(fn=cmd_status)
    px = sub.add_parser("proxy", help="proxy bajo demanda (launchd en macOS)")
    px.add_argument("--listen", help="HOST:PUERTO propio en vez del socket de launchd (pruebas)")
    px.add_argument("--socket-name", default="Listeners", help="clave de Sockets en el plist")
    px.set_defaults(fn=cmd_proxy)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
