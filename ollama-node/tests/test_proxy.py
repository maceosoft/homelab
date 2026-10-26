import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import unittest

from helpers import (ROOT, base_cfg, free_port, make_fake_caffeinate, make_fake_ollama, ollama_node, tmpdir,
                     wait_for)


def http_post(port, path="/api/chat", body=b"{}"):
    """Devuelve (lista de (t, línea), socket cerrado) leyendo la respuesta en streaming."""
    s = socket.create_connection(("127.0.0.1", port), timeout=15)
    s.sendall(("POST %s HTTP/1.0\r\nHost: x\r\nContent-Length: %d\r\n\r\n" % (path, len(body))).encode() + body)
    t0 = time.time()
    buf, stamps = b"", []
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            if line.startswith(b"{"):
                stamps.append((time.time() - t0, json.loads(line)))
    s.close()
    return stamps


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


class ProxyTest(unittest.TestCase):
    def setUp(self):
        self.dir = tmpdir()
        self.log = os.path.join(self.dir, "ollama.log")
        self.caff_marker = os.path.join(self.dir, "caff.txt")
        os.environ["FAKE_OLLAMA_LOG"] = self.log
        os.environ["FAKE_OLLAMA_DELAY"] = "0.8"
        self.internal = free_port()
        self.proxy = None
        self.thread = None

    def tearDown(self):
        if self.proxy:
            self.proxy.stopping.set()
        if self.thread:
            self.thread.join(15)
        for k in ("FAKE_OLLAMA_LOG", "FAKE_OLLAMA_DELAY", "FAKE_OLLAMA_CHUNK_DELAY"):
            os.environ.pop(k, None)
        shutil.rmtree(self.dir, ignore_errors=True)

    def start(self, **over):
        kw = dict(ollama_bin=make_fake_ollama(self.dir), internal_port=self.internal, idle_timeout=30,
                  allowed_cidrs=["127.0.0.0/8"], keep_alive="7m", max_loaded_models=2, start_timeout=20,
                  caffeinate_bin=make_fake_caffeinate(self.dir, self.caff_marker))
        kw.update(over)
        cfg = base_cfg(**kw)
        lst = ollama_node.make_listener("127.0.0.1:0")
        self.port = lst.getsockname()[1]
        self.proxy = ollama_node.OnDemandProxy(cfg, [lst])
        self.thread = threading.Thread(target=self.proxy.serve_forever)
        self.thread.start()
        return self.proxy

    def events(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log) as fh:
            return [json.loads(l) for l in fh if l.strip()]

    def test_arranque_bajo_demanda_y_streaming(self):
        p = self.start()
        time.sleep(0.5)
        self.assertEqual(self.events(), [])  # nada arranca sin tráfico
        stamps = http_post(self.port)
        starts = [e for e in self.events() if e["event"] == "start"]
        self.assertEqual(len(starts), 1)
        self.assertEqual(starts[0]["host"], "127.0.0.1:%d" % self.internal)
        self.assertEqual(starts[0]["keep_alive"], "7m")
        self.assertEqual(starts[0]["max_loaded"], "2")
        self.assertEqual([s[1]["i"] for s in stamps], [0, 1, 2])
        # streaming real: el primer trozo llega bastante antes que el último (0.3 s entre trozos)
        self.assertGreater(stamps[2][0] - stamps[0][0], 0.45)
        # segunda petición reutiliza el mismo Ollama
        http_post(self.port)
        self.assertEqual(len([e for e in self.events() if e["event"] == "start"]), 1)
        self.assertEqual(len(p.started_at), 1)

    def test_caffeinate_mientras_hay_conexiones(self):
        p = self.start()
        os.environ["FAKE_OLLAMA_CHUNK_DELAY"] = "0.4"
        t = threading.Thread(target=http_post, args=(self.port,))
        t.start()
        self.assertTrue(wait_for(lambda: p.caff is not None and os.path.exists(self.caff_marker), 8))
        with open(self.caff_marker) as fh:
            args = fh.read().split()
        self.assertEqual(args[0], "-i")
        self.assertEqual(args[1:], ["-w", str(os.getpid())])
        caff = p.caff
        t.join(10)
        self.assertTrue(wait_for(lambda: p.caff is None and caff.poll() is not None, 5))

    def test_allowed_cidrs_rechaza_origen(self):
        p = self.start(allowed_cidrs=["10.0.0.0/8"])
        s = socket.create_connection(("127.0.0.1", self.port), timeout=5)
        try:
            s.sendall(b"GET /api/version HTTP/1.0\r\n\r\n")
            self.assertEqual(s.recv(100), b"")
        except (ConnectionResetError, BrokenPipeError):
            pass  # cerrado por el proxy
        s.close()
        time.sleep(0.5)
        self.assertEqual(self.events(), [])  # ni siquiera despierta a Ollama
        self.assertEqual(p.started_at, [])
        self.assertIsNone(p.caff)

    def test_lista_vacia_cierra_por_defecto(self):
        self.start(allowed_cidrs=[])
        s = socket.create_connection(("127.0.0.1", self.port), timeout=5)
        self.assertEqual(s.recv(10), b"")
        s.close()
        self.assertEqual(self.events(), [])

    def test_apagado_por_inactividad(self):
        p = self.start(idle_timeout=2)
        http_post(self.port)
        self.assertTrue(p.proc is not None)
        pid = p.proc.pid
        self.assertTrue(pid_alive(pid))
        self.thread.join(15)
        self.assertFalse(self.thread.is_alive())  # el proxy salió solo
        self.assertTrue(wait_for(lambda: not pid_alive(pid), 5))
        self.assertIn("stop", [e["event"] for e in self.events()])

    def test_ollama_muerto_se_reinicia(self):
        p = self.start()
        http_post(self.port)
        p.proc.terminate()
        p.proc.wait(5)
        http_post(self.port)
        self.assertEqual(len(p.started_at), 2)

    def test_ollama_que_no_arranca_cierra_la_conexion(self):
        cfg_over = dict(ollama_bin="/bin/false")
        cfg = base_cfg(internal_port=self.internal, idle_timeout=30, allowed_cidrs=["127.0.0.0/8"],
                       start_timeout=5, caffeinate_bin="", **cfg_over)
        lst = ollama_node.make_listener("127.0.0.1:0")
        self.proxy = ollama_node.OnDemandProxy(cfg, [lst])
        self.thread = threading.Thread(target=self.proxy.serve_forever)
        self.thread.start()
        s = socket.create_connection(("127.0.0.1", lst.getsockname()[1]), timeout=10)
        s.sendall(b"GET / HTTP/1.0\r\n\r\n")
        try:
            self.assertEqual(s.recv(10), b"")
        except ConnectionResetError:
            pass  # el proxy cerró con datos sin leer: también vale
        s.close()


class IpAllowedTest(unittest.TestCase):
    def test_casos(self):
        nets = ollama_node.parse_cidrs(["192.168.20.0/24", "fd00::/8"])
        self.assertTrue(ollama_node.ip_allowed("192.168.20.5", nets))
        self.assertFalse(ollama_node.ip_allowed("192.168.21.5", nets))
        self.assertTrue(ollama_node.ip_allowed("::ffff:192.168.20.9", nets))
        self.assertTrue(ollama_node.ip_allowed("fd12::1", nets))
        self.assertFalse(ollama_node.ip_allowed("basura", nets))
        self.assertFalse(ollama_node.ip_allowed("1.2.3.4", []))


class ProxyCliTest(unittest.TestCase):
    """Entrada real `ollama_node.py proxy --listen` como proceso (sin launchd)."""

    def test_proceso_completo_con_sigterm(self):
        d = tmpdir()
        try:
            internal = free_port()
            cfg = base_cfg(ollama_bin=make_fake_ollama(d), internal_port=internal, idle_timeout=60,
                           allowed_cidrs=["127.0.0.1/32"], start_timeout=20, caffeinate_bin="")
            path = os.path.join(d, "config.json")
            with open(path, "w") as fh:
                json.dump(cfg, fh)
            listen = free_port()
            env = dict(os.environ, FAKE_OLLAMA_LOG=os.path.join(d, "o.log"))
            proc = subprocess.Popen([sys.executable, os.path.join(ROOT, "ollama_node.py"), "--config", path,
                                     "proxy", "--listen", "127.0.0.1:%d" % listen], env=env,
                                    stderr=subprocess.DEVNULL)
            self.assertTrue(wait_for(lambda: _can_connect(listen), 5))
            self.assertEqual(len(http_post(listen)), 3)
            proc.terminate()
            self.assertEqual(proc.wait(20), 0)
            with open(os.path.join(d, "o.log")) as fh:
                self.assertIn('"stop"', fh.read())
        finally:
            shutil.rmtree(d, ignore_errors=True)


def _can_connect(port):
    try:
        socket.create_connection(("127.0.0.1", port), timeout=1).close()
        return True
    except OSError:
        return False


if __name__ == "__main__":
    unittest.main()
