import contextlib
import io
import json
import os
import shutil
import threading
import time
import unittest
import urllib.error

from helpers import FakeRegistry, ModelsTree, base_cfg, make_self_signed, ollama_node, tmpdir, wait_for

TOKEN = "s3cr3t-token"


class PayloadTest(unittest.TestCase):
    def test_claves_y_tipos(self):
        cfg = base_cfg()
        models = [{"name": "m:latest"}]
        p = ollama_node.build_payload(cfg, models=models, version="1.2.3")
        self.assertEqual(sorted(p), sorted(["name", "url", "os", "arch", "ram_gb", "priority", "tags",
                                            "ollama_version", "ts", "models"]))
        self.assertEqual(p["name"], "mac-test")
        self.assertEqual(p["tags"], ["mac"])
        self.assertEqual(p["priority"], 10)
        self.assertEqual(p["ollama_version"], "1.2.3")
        self.assertEqual(p["models"], models)
        self.assertRegex(p["ts"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertIn(p["arch"], ("amd64", "arm64"))
        json.dumps(p)

    def test_version_del_binario_falso(self):
        from helpers import make_fake_ollama
        d = tmpdir()
        try:
            cfg = base_cfg(ollama_bin=make_fake_ollama(d))
            self.assertEqual(ollama_node.ollama_version(cfg), "9.9.9-fake")
        finally:
            shutil.rmtree(d, ignore_errors=True)


class RegistryClientTest(unittest.TestCase):
    def setUp(self):
        self.dir = tmpdir()
        self.tokfile = os.path.join(self.dir, "token")
        with open(self.tokfile, "w") as fh:
            fh.write(TOKEN + "\n")
        os.chmod(self.tokfile, 0o600)
        self.tree = ModelsTree(os.path.join(self.dir, "models"))
        self.tree.put("manifests", "registry.ollama.ai/library/m/latest", self.tree.model_manifest())
        self.reg = FakeRegistry(token=TOKEN)

    def tearDown(self):
        self.reg.close()
        shutil.rmtree(self.dir, ignore_errors=True)

    def cfg(self, **over):
        kw = dict(registry_url=self.reg.url, token_file=self.tokfile, models_dir=self.tree.root,
                  ollama_bin="/bin/echo")
        kw.update(over)
        return base_cfg(**kw)

    def test_put_y_delete(self):
        body = ollama_node.register_once(self.cfg(), sleep=lambda s: None)
        self.assertEqual(self.reg.alive(), ["mac-test"])
        sent = self.reg.nodes["mac-test"][0]
        self.assertEqual([m["name"] for m in sent["models"]], ["m:latest"])
        self.assertEqual(body["name"], "mac-test")
        method, path, auth, _ = self.reg.requests[0]
        self.assertEqual((method, path, auth), ("PUT", "/_registry/nodes/mac-test", "Bearer " + TOKEN))
        ollama_node.deregister(self.cfg(), sleep=lambda s: None)
        self.assertEqual(self.reg.alive(), [])
        self.assertEqual(self.reg.requests[-1][:2], ("DELETE", "/_registry/nodes/mac-test"))

    def test_delete_de_nodo_inexistente_no_falla(self):
        ollama_node.deregister(self.cfg(), sleep=lambda s: None)

    def test_ttl_expira_y_el_latido_lo_renueva(self):
        self.reg.ttl = 0.6
        stop = threading.Event()
        cfg = self.cfg(interval=1)
        ollama_node.register_once(cfg, sleep=lambda s: None)
        self.assertEqual(self.reg.alive(), ["mac-test"])
        self.assertTrue(wait_for(lambda: self.reg.alive() == [], 3))
        t = threading.Thread(target=ollama_node.register_loop, args=(cfg, stop), kwargs={"deregister_on_exit": False})
        cfg["interval"] = 0.2
        t.start()
        try:
            self.assertTrue(wait_for(lambda: self.reg.alive() == ["mac-test"], 3))
            self.assertTrue(wait_for(lambda: self.reg.count("PUT") >= 4, 5))
        finally:
            stop.set()
            t.join(5)

    def test_loop_hace_delete_al_salir(self):
        cfg = self.cfg(interval=0.2)
        stop = threading.Event()
        t = threading.Thread(target=ollama_node.register_loop, args=(cfg, stop))
        t.start()
        self.assertTrue(wait_for(lambda: self.reg.count("PUT") >= 2, 5))
        stop.set()
        t.join(5)
        self.assertEqual(self.reg.count("DELETE"), 1)
        self.assertEqual(self.reg.alive(), [])

    def test_reintenta_5xx_con_backoff(self):
        self.reg.fail_next = [503, 503]
        sleeps = []
        ollama_node.register_once(self.cfg(), retries=5, sleep=sleeps.append)
        self.assertEqual(self.reg.count("PUT"), 3)
        self.assertEqual(len(sleeps), 2)
        self.assertGreater(sleeps[1], sleeps[0] * 0.9)  # crece (con jitter 0.5x..1x)
        self.assertEqual(self.reg.alive(), ["mac-test"])

    def test_agota_reintentos(self):
        self.reg.fail_next = [503] * 10
        with self.assertRaises(RuntimeError):
            ollama_node.register_once(self.cfg(), retries=3, sleep=lambda s: None)
        self.assertEqual(self.reg.count("PUT"), 3)

    def test_token_incorrecto_no_reintenta_y_no_se_imprime(self):
        self.reg.token = "otro"
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            with self.assertRaises(RuntimeError) as ctx:
                ollama_node.register_once(self.cfg(), retries=5, sleep=lambda s: None)
            rc = ollama_node.main(["--config", self._write_cfg(), "register", "--retries", "1"])
        self.assertEqual(self.reg.count("PUT"), 2)  # 1 directo + 1 por main
        self.assertEqual(rc, 1)
        self.assertNotIn(TOKEN, err.getvalue())
        self.assertNotIn(TOKEN, str(ctx.exception))
        self.assertNotIn("otro", err.getvalue())

    def _write_cfg(self, **over):
        cfg = self.cfg(**over)
        cfg.pop("_path", None)
        path = os.path.join(self.dir, "config.json")
        with open(path, "w") as fh:
            json.dump(cfg, fh)
        return path

    def test_main_register_once_y_deregister(self):
        path = self._write_cfg()
        self.assertEqual(ollama_node.main(["--config", path, "register", "--once"]), 0)
        self.assertEqual(self.reg.alive(), ["mac-test"])
        self.assertEqual(ollama_node.main(["--config", path, "status"]), 0)
        self.assertEqual(ollama_node.main(["--config", path, "deregister"]), 0)
        self.assertEqual(self.reg.alive(), [])

    def test_http_fuera_de_loopback_se_rechaza(self):
        cfg = self.cfg()
        cfg["registry_url"] = "http://192.0.2.1"
        with self.assertRaises(RuntimeError):
            ollama_node.register_once(cfg, retries=1, sleep=lambda s: None)
        self.assertEqual(self.reg.count("PUT"), 0)

    def test_token_desde_variable_de_entorno(self):
        cfg = self.cfg(token_file="")
        os.environ["OLLAMA_NODE_TOKEN"] = TOKEN
        try:
            ollama_node.register_once(cfg, sleep=lambda s: None)
        finally:
            del os.environ["OLLAMA_NODE_TOKEN"]
        self.assertEqual(self.reg.alive(), ["mac-test"])


class RegistryTlsTest(unittest.TestCase):
    def setUp(self):
        self.dir = tmpdir()
        self.pair = make_self_signed(self.dir)
        if not self.pair:
            self.skipTest("openssl no disponible")
        self.tokfile = os.path.join(self.dir, "token")
        with open(self.tokfile, "w") as fh:
            fh.write(TOKEN)
        self.reg = FakeRegistry(token=TOKEN, tls=self.pair)

    def tearDown(self):
        self.reg.close()
        shutil.rmtree(self.dir, ignore_errors=True)

    def cfg(self, **over):
        kw = dict(registry_url=self.reg.url, token_file=self.tokfile, models_dir=self.dir, ollama_bin="/bin/echo")
        kw.update(over)
        return base_cfg(**kw)

    def test_con_ca_valida(self):
        ollama_node.register_once(self.cfg(ca_file=self.pair["cert"]), retries=1, sleep=lambda s: None)
        self.assertEqual(self.reg.alive(), ["mac-test"])

    def test_sin_ca_falla_la_validacion(self):
        with self.assertRaises(RuntimeError):
            ollama_node.register_once(self.cfg(), retries=1, sleep=lambda s: None)
        self.assertEqual(self.reg.count("PUT"), 0)


if __name__ == "__main__":
    unittest.main()
