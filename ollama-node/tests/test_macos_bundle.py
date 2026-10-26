"""Instalador y CLI de macOS con directorios temporales y un `launchctl` falso (no toca launchd real)."""
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import unittest

from helpers import FakeRegistry, ROOT, make_fake_ollama, tmpdir, write_exe

MACOS = os.path.join(ROOT, "macos")
TOKEN = "s3cr3t-token"


@unittest.skipUnless(sys.platform == "darwin", "solo macOS")
class BundleTest(unittest.TestCase):
    def setUp(self):
        self.d = tmpdir()
        self.state = os.path.join(self.d, "loaded")
        os.makedirs(self.state)
        self.calls = os.path.join(self.d, "launchctl.calls")
        self.fake = write_exe(os.path.join(self.d, "launchctl"), """#!/bin/sh
echo "$@" >> '%s'
case "$1" in
  bootstrap) b=$(basename "$3" .plist); touch '%s'/"$b" ;;
  bootout) b=$(basename "$2"); [ -f '%s'/"$b" ] && rm '%s'/"$b" ;;
  print) b=$(basename "$2"); [ -f '%s'/"$b" ] ;;
esac
""" % (self.calls, self.state, self.state, self.state, self.state))
        self.reg = FakeRegistry(token=TOKEN)
        self.env = dict(os.environ, OLLAMA_NODE_HOME=os.path.join(self.d, "app"),
                        OLLAMA_NODE_AGENTS_DIR=os.path.join(self.d, "agents"),
                        OLLAMA_NODE_LOG_DIR=os.path.join(self.d, "logs"),
                        OLLAMA_NODE_BIN_DIR=os.path.join(self.d, "bin"),
                        OLLAMA_NODE_LAUNCHCTL=self.fake, OLLAMA_NODE_PYTHON=sys.executable)
        tok = os.path.join(self.d, "tok.txt")
        with open(tok, "w") as fh:
            fh.write(TOKEN + "\n")
        self.install = subprocess.run(
            [os.path.join(MACOS, "install.sh"), "--yes", "--name", "mac-test", "--url", "http://192.0.2.10:11434",
             "--registry-url", self.reg.url, "--allowed-cidrs", "192.0.2.0/24,127.0.0.1/32",
             "--token-file", tok, "--python", sys.executable, "--ollama-bin", make_fake_ollama(self.d),
             "--listen-port", "18434", "--tags", "mac,gpu"],
            env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.app = self.env["OLLAMA_NODE_HOME"]
        self.cli = os.path.join(self.env["OLLAMA_NODE_BIN_DIR"], "ollama-node")

    def tearDown(self):
        self.reg.close()
        shutil.rmtree(self.d, ignore_errors=True)

    def run_cli(self, *args):
        return subprocess.run([self.cli] + list(args), env=self.env, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, universal_newlines=True)

    def launch_calls(self):
        if not os.path.exists(self.calls):
            return []
        with open(self.calls) as fh:
            return [l.strip() for l in fh if l.strip()]

    def test_instalacion_deja_todo_sin_cargar(self):
        self.assertEqual(self.install.returncode, 0, self.install.stderr)
        self.assertIn("OFF", self.install.stdout)
        self.assertEqual(self.launch_calls(), [])  # el instalador no llama a launchctl
        for name in ("socket", "register"):
            p = os.path.join(self.env["OLLAMA_NODE_AGENTS_DIR"], "local.homelab.ollama-node.%s.plist" % name)
            self.assertEqual(subprocess.run(["plutil", "-lint", p], stdout=subprocess.DEVNULL).returncode, 0)
            with open(p) as fh:
                self.assertIsNone(re.search(r"@[A-Z_]+@", fh.read()))
        sock = open(os.path.join(self.env["OLLAMA_NODE_AGENTS_DIR"], "local.homelab.ollama-node.socket.plist")).read()
        self.assertIn("<string>18434</string>", sock)
        self.assertIn("<key>Sockets</key>", sock)
        self.assertIn("<string>proxy</string>", sock)
        reg = open(os.path.join(self.env["OLLAMA_NODE_AGENTS_DIR"], "local.homelab.ollama-node.register.plist")).read()
        self.assertIn("<string>--loop</string>", reg)

    def test_permisos_y_secretos(self):
        mode = lambda p: stat.S_IMODE(os.stat(p).st_mode)
        self.assertEqual(mode(os.path.join(self.app, "token")), 0o600)
        self.assertEqual(mode(os.path.join(self.app, "config.json")), 0o600)
        cfg = json.load(open(os.path.join(self.app, "config.json")))
        self.assertNotIn(TOKEN, json.dumps(cfg))
        self.assertEqual(cfg["token_file"], os.path.join(self.app, "token"))
        self.assertEqual(cfg["allowed_cidrs"], ["192.0.2.0/24", "127.0.0.1/32"])
        self.assertEqual(cfg["tags"], ["mac", "gpu"])
        self.assertEqual(cfg["listen_port"], 18434)
        self.assertNotIn(TOKEN, self.install.stdout + self.install.stderr)

    def test_on_status_off(self):
        r = self.run_cli("on")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([c.split()[0] for c in self.launch_calls() if not c.startswith("print")],
                         ["bootstrap", "bootstrap"])
        self.assertIn("estado: ON", self.run_cli("status").stdout)
        self.assertEqual(self.run_cli("on").returncode, 0)  # idempotente: no vuelve a cargar
        self.assertEqual(len([c for c in self.launch_calls() if c.startswith("bootstrap")]), 2)
        # el latido real no corre (launchctl es falso): registramos a mano y comprobamos que off hace DELETE
        subprocess.run([sys.executable, os.path.join(self.app, "ollama_node.py"), "--config",
                        os.path.join(self.app, "config.json"), "register", "--once"], env=self.env,
                       stderr=subprocess.DEVNULL)
        self.assertEqual(self.reg.alive(), ["mac-test"])
        r = self.run_cli("off")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.reg.alive(), [])
        self.assertEqual(len([c for c in self.launch_calls() if c.startswith("bootout")]), 2)
        self.assertIn("estado: OFF", self.run_cli("status").stdout)

    def test_off_quita_el_latido_antes_de_dar_de_baja(self):
        self.run_cli("on")
        self.run_cli("off")
        outs = [c for c in self.launch_calls() if c.startswith("bootout")]
        self.assertTrue(outs[0].endswith("register"))
        self.assertTrue(outs[1].endswith("socket"))

    def test_config_muestra_sin_token(self):
        r = self.run_cli("config")
        self.assertIn('"name": "mac-test"', r.stdout)
        self.assertNotIn(TOKEN, r.stdout)

    def test_uninstall(self):
        r = subprocess.run([os.path.join(MACOS, "install.sh"), "--uninstall"], env=self.env,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(r.returncode, 0)
        self.assertFalse(os.path.exists(self.cli))
        self.assertEqual(os.listdir(self.env["OLLAMA_NODE_AGENTS_DIR"]), [])


if __name__ == "__main__":
    unittest.main()
