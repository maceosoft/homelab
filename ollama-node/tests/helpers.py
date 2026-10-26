"""Utilidades compartidas por las pruebas: ollama falso, registro falso, árboles de manifests."""
import hashlib
import json
import os
import socket
import ssl
import stat
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import ollama_node  # noqa: E402


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def wait_for(cond, timeout=10.0, step=0.05):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(step)
    return cond()


def write_exe(path, text):
    with open(path, "w") as fh:
        fh.write(text)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
    return path


def make_fake_ollama(directory):
    """Crea un `ollama` falso: `serve` escucha en OLLAMA_HOST y responde /api/version y /api/chat (NDJSON)."""
    code = textwrap.dedent('''\
        #!%(py)s
        import json, os, signal, sys, time
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        class HTTPServer(ThreadingHTTPServer):
            request_queue_size = 128

        log = os.environ.get("FAKE_OLLAMA_LOG")
        def note(obj):
            if log:
                with open(log, "a") as fh:
                    fh.write(json.dumps(obj) + "\\n")

        if sys.argv[1:] == ["--version"]:
            print("ollama version is 9.9.9-fake")
            sys.exit(0)
        if sys.argv[1:2] != ["serve"]:
            sys.exit(2)
        host, _, port = os.environ["OLLAMA_HOST"].rpartition(":")
        note({"event": "start", "host": os.environ["OLLAMA_HOST"],
              "keep_alive": os.environ.get("OLLAMA_KEEP_ALIVE"),
              "max_loaded": os.environ.get("OLLAMA_MAX_LOADED_MODELS")})
        time.sleep(float(os.environ.get("FAKE_OLLAMA_DELAY", "0")))

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a): pass
            def do_GET(self):
                body = json.dumps({"version": "9.9.9-fake"}).encode()
                self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers()
                self.wfile.write(body)
            def do_POST(self):
                n = int(self.headers.get("Content-Length", 0)); self.rfile.read(n)
                self.send_response(200); self.send_header("Content-Type", "application/x-ndjson"); self.end_headers()
                for i in range(3):
                    self.wfile.write(json.dumps({"i": i, "done": i == 2}).encode() + b"\\n"); self.wfile.flush()
                    time.sleep(float(os.environ.get("FAKE_OLLAMA_CHUNK_DELAY", "0.3")))

        srv = HTTPServer((host, int(port)), H)
        def stop(*_):
            note({"event": "stop"}); os._exit(0)
        signal.signal(signal.SIGTERM, stop)
        srv.serve_forever()
        ''' % {"py": sys.executable})
    return write_exe(os.path.join(directory, "ollama"), code)


def make_fake_caffeinate(directory, marker):
    code = "#!/bin/sh\necho \"$@\" > '%s'\nexec sleep 600\n" % marker
    return write_exe(os.path.join(directory, "caffeinate"), code)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


class ModelsTree(object):
    """Construye un OLLAMA_MODELS de ejemplo (blobs + manifests / manifests-v2)."""

    def __init__(self, root):
        self.root = root
        os.makedirs(os.path.join(root, "blobs"), exist_ok=True)

    def blob(self, data):
        raw = data if isinstance(data, bytes) else json.dumps(data).encode()
        digest = "sha256:" + sha256_bytes(raw)
        with open(os.path.join(self.root, "blobs", digest.replace(":", "-")), "wb") as fh:
            fh.write(raw)
        return digest, len(raw)

    def model_manifest(self, family="llama", ptype="8.0B", quant="Q4_K_M", layer_sizes=(1000, 20, 3), fmt="gguf"):
        cdigest, csize = self.blob({"model_format": fmt, "model_family": family, "model_families": [family],
                                    "model_type": ptype, "file_type": quant, "architecture": "arm64", "os": "darwin"})
        layers = [{"mediaType": "application/vnd.ollama.image.model", "digest": "sha256:" + "ab" * 32, "size": s}
                  for s in layer_sizes]
        return {"schemaVersion": 2, "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                "config": {"mediaType": "application/vnd.docker.container.image.v1+json",
                           "digest": cdigest, "size": csize}, "layers": layers}

    def put(self, sub, relpath, manifest, mtime=None):
        path = os.path.join(self.root, sub, *relpath.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        raw = json.dumps(manifest).encode()
        with open(path, "wb") as fh:
            fh.write(raw)
        if mtime:
            os.utime(path, (mtime, mtime))
        return path, sha256_bytes(raw)


class FakeRegistry(object):
    """Registro falso: PUT/DELETE/GET /_registry/nodes, token Bearer, TTL, fallos programables."""

    def __init__(self, token="s3cr3t-token", ttl=180.0, tls=None):
        self.token = token
        self.ttl = ttl
        self.nodes = {}
        self.requests = []
        self.fail_next = []  # códigos HTTP a devolver antes de aceptar
        self.lock = threading.Lock()
        reg = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _auth(self):
                if self.headers.get("Authorization") != "Bearer " + reg.token:
                    self._send(401, {"error": "unauthorized"})
                    return False
                return True

            def _send(self, code, obj=None):
                body = json.dumps(obj if obj is not None else {}).encode()
                self.send_response(code)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _alive(self):
                now = time.time()
                return {k: v for k, v in reg.nodes.items() if v[1] > now}

            def do_PUT(self):
                n = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(n)
                with reg.lock:
                    reg.requests.append(("PUT", self.path, self.headers.get("Authorization"), raw))
                    if reg.fail_next:
                        return self._send(reg.fail_next.pop(0))
                    if not self._auth():
                        return
                    name = self.path.rsplit("/", 1)[-1]
                    reg.nodes[name] = (json.loads(raw), time.time() + reg.ttl)
                    self._send(204 if False else 200, {"ok": True})

            def do_DELETE(self):
                with reg.lock:
                    reg.requests.append(("DELETE", self.path, self.headers.get("Authorization"), b""))
                    if not self._auth():
                        return
                    name = self.path.rsplit("/", 1)[-1]
                    if reg.nodes.pop(name, None) is None:
                        return self._send(404)
                    self._send(200)

            def do_GET(self):
                with reg.lock:
                    reg.requests.append(("GET", self.path, self.headers.get("Authorization"), b""))
                    if not self._auth():
                        return
                    self._send(200, {"nodes": [v[0] for v in self._alive().values()]})

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.port = self.httpd.server_address[1]
        self.scheme = "http"
        if tls:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(tls["cert"], tls["key"])
            self.httpd.socket = ctx.wrap_socket(self.httpd.socket, server_side=True)
            self.scheme = "https"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    @property
    def url(self):
        return "%s://127.0.0.1:%d" % (self.scheme, self.port)

    def alive(self):
        now = time.time()
        with self.lock:
            return sorted(k for k, v in self.nodes.items() if v[1] > now)

    def count(self, method):
        with self.lock:
            return len([r for r in self.requests if r[0] == method])

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def make_self_signed(directory):
    """Certificado autofirmado para 127.0.0.1 con openssl; devuelve None si no se puede."""
    cnf = os.path.join(directory, "openssl.cnf")
    with open(cnf, "w") as fh:
        fh.write("[req]\ndistinguished_name=dn\nx509_extensions=v3\nprompt=no\n[dn]\nCN=127.0.0.1\n"
                 "[v3]\nsubjectAltName=IP:127.0.0.1\nbasicConstraints=CA:TRUE\n")
    cert, key = os.path.join(directory, "cert.pem"), os.path.join(directory, "key.pem")
    try:
        res = subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "2",
                              "-keyout", key, "-out", cert, "-config", cnf],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return None
    return {"cert": cert, "key": key} if res.returncode == 0 else None


def tmpdir():
    return tempfile.mkdtemp(prefix="ollama-node-test-")


def base_cfg(**over):
    cfg = dict(ollama_node.DEFAULTS)
    cfg.update({"name": "mac-test", "url": "http://192.0.2.10:11434", "priority": 10, "tags": ["mac"]})
    cfg.update(over)
    return cfg
