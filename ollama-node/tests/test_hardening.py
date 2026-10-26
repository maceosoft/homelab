"""Endurecimiento del proxy y del lector de manifests (carreras, huérfanos, silencios, backoff)."""
import errno
import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import threading
import time
import unittest

from helpers import (ROOT, ModelsTree, base_cfg, free_port, make_fake_caffeinate, make_fake_ollama, ollama_node,
                     tmpdir, wait_for, write_exe)
from test_proxy import http_post, pid_alive


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tmpdir()
        self.olog = os.path.join(self.dir, "ollama.log")
        os.environ["FAKE_OLLAMA_LOG"] = self.olog
        self.internal = free_port()
        self.proxies = []
        self.threads = []

    def tearDown(self):
        for px in self.proxies:
            px.stopping.set()
        for t in self.threads:
            t.join(20)
        for px in self.proxies:
            px.shutdown()  # idempotente: no deja ningún ollama falso vivo
        for k in ("FAKE_OLLAMA_LOG", "FAKE_OLLAMA_DELAY", "FAKE_OLLAMA_CHUNK_DELAY"):
            os.environ.pop(k, None)
        shutil.rmtree(self.dir, ignore_errors=True)

    def cfg(self, **over):
        kw = dict(ollama_bin=make_fake_ollama(self.dir), internal_port=self.internal, idle_timeout=30,
                  allowed_cidrs=["127.0.0.0/8"], start_timeout=20, caffeinate_bin="",
                  pid_file=os.path.join(self.dir, "ollama.pid"))
        kw.update(over)
        return base_cfg(**kw)

    def make(self, run=True, **over):
        lst = ollama_node.make_listener("127.0.0.1:0")
        px = ollama_node.OnDemandProxy(self.cfg(**over), [lst])
        self.proxies.append(px)
        self.port = lst.getsockname()[1]
        if run:
            t = threading.Thread(target=px.serve_forever)
            t.start()
            self.threads.append(t)
        return px

    def events(self):
        if not os.path.exists(self.olog):
            return []
        with open(self.olog) as fh:
            return [json.loads(l) for l in fh if l.strip()]


class ShutdownRaceTest(Base):
    def test_conexion_aceptada_cuenta_antes_de_decidir_inactividad(self):
        px = self.make(run=False, idle_timeout=0.7)
        px.last_activity = time.time() - 10  # la inactividad ya venció
        c = socket.create_connection(("127.0.0.1", self.port))
        time.sleep(0.1)
        # Antes: accept + hilo aún sin sumar `active` + chequeo => salía perdiendo la conexión.
        self.assertFalse(px.poll_once(timeout=1.0))
        self.assertEqual(px.active, 1)
        c.close()
        self.assertTrue(wait_for(lambda: px.active == 0, 5))
        time.sleep(0.8)
        self.assertTrue(px.poll_once(timeout=0.1))  # sin conexiones y vencido: ahora sí sale
        px.shutdown()

    def test_rafaga_cerca_del_vencimiento(self):
        """Ráfagas de conexiones justo cuando vence idle_timeout: ninguna se pierde."""
        px = self.make(run=False, idle_timeout=0.7)
        px.last_activity = time.time() - 0.69
        done = []

        def client():
            try:
                done.append(len(http_post(self.port)))
            except OSError:
                done.append(-1)
        ts = []
        for _ in range(8):
            t = threading.Thread(target=client)
            ts.append(t)
            t.start()
            time.sleep(0.02)
        end = time.time() + 20
        while len(done) < 8 and time.time() < end:
            px.poll_once(timeout=0.05)
        for t in ts:
            t.join(5)
        self.assertEqual(done, [3] * 8)
        px.shutdown()


class OrphanTest(Base):
    def spawn_proxy(self, cfgpath, listen):
        p = subprocess.Popen([sys.executable, os.path.join(ROOT, "ollama_node.py"), "--config", cfgpath,
                              "proxy", "--listen", "127.0.0.1:%d" % listen], stderr=subprocess.DEVNULL,
                             env=dict(os.environ))
        self.assertTrue(wait_for(lambda: _connectable(listen), 5))
        return p

    def test_kill9_del_proxy_no_deja_ollama_huerfano(self):
        cfg = self.cfg(pid_file="")  # por defecto: ollama.pid junto al config
        path = os.path.join(self.dir, "config.json")
        json.dump(cfg, open(path, "w"))
        pidfile = os.path.join(self.dir, "ollama.pid")
        l1 = free_port()
        a = self.spawn_proxy(path, l1)
        http_post(l1)
        pid1 = int(open(pidfile).read())
        self.assertEqual(stat.S_IMODE(os.stat(pidfile).st_mode), 0o600)
        a.kill()
        a.wait()
        self.assertTrue(pid_alive(pid1))  # huérfano real
        l2 = free_port()
        b = self.spawn_proxy(path, l2)
        try:
            self.assertTrue(wait_for(lambda: not pid_alive(pid1), 15))  # el nuevo proxy lo mató
            self.assertEqual(len(http_post(l2)), 3)
            pid2 = int(open(pidfile).read())
            self.assertNotEqual(pid1, pid2)
        finally:
            b.terminate()
            b.wait(25)
        self.assertFalse(pid_alive(pid2))
        self.assertFalse(os.path.exists(pidfile))

    def test_no_mata_un_pid_que_no_es_ollama(self):
        sleeper = subprocess.Popen(["sleep", "30"])
        try:
            px = self.make(run=False)
            with open(px._pid_path(), "w") as fh:
                fh.write("%d\n" % sleeper.pid)
            px.reap_orphan()
            self.assertIsNone(sleeper.poll())
            self.assertFalse(os.path.exists(px._pid_path()))
            px.shutdown()
        finally:
            sleeper.kill()
            sleeper.wait()


def _connectable(port):
    try:
        socket.create_connection(("127.0.0.1", port), timeout=1).close()
        return True
    except OSError:
        return False


class SilentConnectionTest(Base):
    def test_sin_primer_byte_no_despierta_ollama(self):
        px = self.make(first_byte_timeout=1)
        c = socket.create_connection(("127.0.0.1", self.port))
        c.settimeout(5)
        self.assertEqual(c.recv(10), b"")  # cerrada por el proxy
        c.close()
        self.assertEqual(self.events(), [])
        self.assertEqual(px.started_at, [])
        self.assertTrue(wait_for(lambda: px.active == 0, 3))

    def test_tope_de_inactividad_libera_ollama_y_caffeinate(self):
        marker = os.path.join(self.dir, "caff")
        px = self.make(conn_idle_timeout=1, idle_timeout=2,
                       caffeinate_bin=make_fake_caffeinate(self.dir, marker))
        c = socket.create_connection(("127.0.0.1", self.port))
        c.settimeout(10)
        # Cabecera que promete un cuerpo que nunca llega: la conexión queda colgada.
        c.sendall(b"POST /api/chat HTTP/1.0\r\nContent-Length: 100\r\n\r\n")
        self.assertTrue(wait_for(lambda: px.caff is not None, 10))
        t0 = time.time()
        self.assertEqual(c.recv(10), b"")
        self.assertLess(time.time() - t0, 5)
        self.assertTrue(wait_for(lambda: px.caff is None and px.busy == 0, 3))
        self.threads[0].join(15)
        self.assertFalse(self.threads[0].is_alive())  # el proxy pudo apagarse solo
        c.close()

    def test_keepalive_activado(self):
        s = socket.socket()
        ollama_node.OnDemandProxy._keepalive(s)
        self.assertNotEqual(s.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE), 0)
        s.close()


class StartFailureTest(Base):
    def test_cooldown_tras_fallo_de_arranque(self):
        count = os.path.join(self.dir, "count")
        crash = write_exe(os.path.join(self.dir, "crash"), "#!/bin/sh\necho x >> '%s'\nexit 3\n" % count)
        px = self.make(ollama_bin=crash, start_cooldown=1.5)
        for _ in range(5):
            try:
                http_post(self.port)
            except OSError:
                pass
        self.assertEqual(len(open(count).read().split()), 1)  # un solo intento, no uno por conexión
        time.sleep(1.7)
        try:
            http_post(self.port)
        except OSError:
            pass
        self.assertEqual(len(open(count).read().split()), 2)  # pasado el cooldown se reintenta
        self.assertEqual(len(px.started_at), 2)

    def test_arranque_que_nunca_escucha_se_mata_y_se_comparte(self):
        hang = write_exe(os.path.join(self.dir, "hang"), "#!/bin/sh\nexec sleep 60\n")
        px = self.make(ollama_bin=hang, start_timeout=1.5, start_cooldown=30)
        t0 = time.time()
        results = []

        def go():
            try:
                results.append(http_post(self.port))
            except OSError:
                results.append("err")
        ts = [threading.Thread(target=go) for _ in range(5)]
        [t.start() for t in ts]
        [t.join(20) for t in ts]
        self.assertLess(time.time() - t0, 4.5)  # N conexiones no esperan N x start_timeout
        self.assertEqual(len(px.started_at), 1)
        pid = int(open(px._pid_path()).read()) if os.path.exists(px._pid_path()) else None
        self.assertIsNone(pid)  # pidfile retirado
        self.assertIsNone(px.proc)

    def test_sigterm_durante_el_arranque_no_lanza_excepcion(self):
        os.environ["FAKE_OLLAMA_DELAY"] = "6"
        errors = []
        old = threading.excepthook
        threading.excepthook = lambda a: errors.append(a)
        try:
            px = self.make()
            threading.Thread(target=lambda: _try(http_post, self.port), daemon=True).start()
            self.assertTrue(wait_for(lambda: len(px.started_at) == 1, 10))
            t0 = time.time()
            px.stopping.set()
            self.threads[0].join(15)
            self.assertFalse(self.threads[0].is_alive())
            self.assertLess(time.time() - t0, 6)
            time.sleep(0.5)
        finally:
            threading.excepthook = old
        self.assertEqual([e.exc_type.__name__ for e in errors], [])
        self.assertIsNone(px.proc)

    def test_accept_con_oserror_no_termina_el_proxy(self):
        px = self.make(run=False)

        class Boom(object):
            def accept(self):
                raise OSError(errno.ECONNABORTED, "abortada")

        class Key(object):
            fileobj = Boom()
        px._accept_ready(Key())  # no debe lanzar
        px.shutdown()


def _try(fn, *a):
    try:
        fn(*a)
    except Exception:  # noqa: BLE001
        pass


class MalformedManifestTest(unittest.TestCase):
    def setUp(self):
        self.root = tmpdir()
        self.t = ModelsTree(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def raw(self, rel, obj, sub="manifests"):
        path = os.path.join(self.root, sub, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(obj if isinstance(obj, str) else json.dumps(obj))

    def test_formas_raras_se_omiten_sin_excepcion(self):
        good = self.t.model_manifest()
        self.raw("registry.ollama.ai/library/size-str/latest", dict(good, layers=[{"size": "grande"}]))
        self.raw("registry.ollama.ai/library/lista/latest", [1, 2, 3])
        self.raw("registry.ollama.ai/library/nulo/latest", "null")
        self.raw("registry.ollama.ai/library/layers-int/latest", dict(good, layers=5))
        self.raw("registry.ollama.ai/library/layers-str/latest", dict(good, layers=["a"]))
        self.raw("registry.ollama.ai/library/config-str/latest", dict(good, config="x"))
        self.raw("registry.ollama.ai/library/mlist-dict/latest", {"manifests": {"a": 1}})
        self.raw("registry.ollama.ai/library/mlist-basura/latest", {"manifests": [1, None, "x"]})
        self.raw("registry.ollama.ai/library/vacio/latest", "")
        self.raw("registry.ollama.ai/library/ok/latest", good)
        # el blob de config con forma rara tampoco tumba nada
        d, _ = self.t.blob([1, 2])
        self.raw("registry.ollama.ai/library/conf-lista/latest", dict(good, config={"digest": d, "size": 2}))
        names = [m["name"] for m in ollama_node.read_models(self.root)]
        self.assertIn("ok:latest", names)
        self.assertIn("conf-lista:latest", names)
        for bad in ("size-str:latest", "lista:latest", "nulo:latest", "layers-int:latest", "config-str:latest",
                    "mlist-dict:latest", "mlist-basura:latest", "vacio:latest"):
            self.assertNotIn(bad, names)

    def test_list_models_cli_no_falla(self):
        self.raw("registry.ollama.ai/library/lista/latest", [1])
        self.raw("registry.ollama.ai/library/ok/latest", self.t.model_manifest())
        out = subprocess.run([sys.executable, os.path.join(ROOT, "ollama_node.py"), "list-models",
                              "--models-dir", self.root], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             universal_newlines=True)
        self.assertEqual(out.returncode, 0)
        self.assertEqual([m["name"] for m in json.loads(out.stdout)], ["ok:latest"])

    def test_el_bucle_de_registro_sobrevive_a_cualquier_excepcion(self):
        calls = []
        orig = ollama_node.register_once

        def boom(cfg, **kw):
            calls.append(1)
            raise ValueError("forma inesperada")
        ollama_node.register_once = boom
        try:
            stop = threading.Event()
            t = threading.Thread(target=ollama_node.register_loop,
                                 args=(base_cfg(interval=0.05), stop), kwargs={"deregister_on_exit": False})
            t.start()
            self.assertTrue(wait_for(lambda: len(calls) >= 3, 5))
            self.assertTrue(t.is_alive())
            stop.set()
            t.join(5)
        finally:
            ollama_node.register_once = orig


if __name__ == "__main__":
    unittest.main()
