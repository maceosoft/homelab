"""Prueba files/ollama-cpu-guard.sh con systemctl, date, nproc y logger simulados (no toca el sistema).

    python3 -m unittest discover -s ansible/roles/ollama_ondemand/tests
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "files" / "ollama-cpu-guard.sh"
STEP_NS = 300 * 10**9  # el temporizador corre cada 5 minutos
CPUS = 8

STUBS = {
    "date": 'cat "$FAKE/now"\n',
    "nproc": f"echo {CPUS}\n",
    "logger": 'echo "LOGGER: $*" >> "$FAKE/log"\n',
    "systemctl": """case "$*" in
  "is-active ollama.service") cat "$FAKE/active"; [ "$(cat "$FAKE/active")" = active ] ;;
  "show ollama.service -p CPUUsageNSec --value") cat "$FAKE/usage" ;;
  "is-active --quiet ollama-proxy.socket") [ "$(cat "$FAKE/socket")" = 1 ] ;;
  stop*) echo "STOP: $*" >> "$FAKE/log"; echo inactive > "$FAKE/active"; echo 0 > "$FAKE/socket" ;;
esac
""",
}


class CpuGuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "bin").mkdir()
        for name, body in STUBS.items():
            stub = self.dir / "bin" / name
            stub.write_text("#!/bin/sh\n" + body)
            stub.chmod(0o755)
        self.env = dict(
            os.environ,
            PATH=f"{self.dir / 'bin'}:{os.environ['PATH']}",
            FAKE=str(self.dir),
            OLLAMA_CPU_GUARD_STATE_DIR=str(self.dir / "state"),
        )
        self.now, self.usage = 10**18, 0
        self.write("active", "active")
        self.write("socket", 1)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, value):
        (self.dir / name).write_text(f"{value}\n")

    def tick(self, load):
        """Una corrida del temporizador después de 5 minutos con Ollama al `load` (0-1) de los núcleos."""
        self.write("now", self.now)
        self.write("usage", self.usage)
        subprocess.run(["bash", str(SCRIPT), str(self.dir / "out"), "60", "2"], env=self.env, check=True)
        self.now += STEP_NS
        self.usage += int(STEP_NS * CPUS * load)
        lines = (self.dir / "out" / "ollama_cpu_guard.prom").read_text().splitlines()
        return dict(line.split() for line in lines if not line.startswith("#"))

    def log(self):
        path = self.dir / "log"
        return path.read_text() if path.exists() else ""

    def test_detiene_ollama_tras_dos_horas_saturado(self):
        for _ in range(25):
            metrics = self.tick(0.70)
        self.assertEqual(metrics["ollama_cpu_guard_stops_total"], "0")
        metrics = self.tick(0.70)
        self.assertEqual(metrics["ollama_cpu_guard_stops_total"], "1")
        self.assertEqual(metrics["ollama_cpu_guard_socket_up"], "0")
        self.assertIn("STOP: stop ollama-proxy.socket ollama-proxy.service ollama.service", self.log())
        self.assertIn("daemon.crit", self.log())

    def test_picos_intermitentes_no_lo_detienen(self):
        for i in range(60):
            metrics = self.tick(0.10 if i % 6 == 0 else 0.70)
        self.assertEqual(metrics["ollama_cpu_guard_stops_total"], "0")
        self.assertEqual(self.log(), "")

    def test_ollama_apagado_reinicia_la_cuenta(self):
        for _ in range(20):
            self.tick(0.70)
        self.write("active", "inactive")
        metrics = self.tick(0)
        self.assertEqual(metrics["ollama_cpu_guard_saturated_seconds"], "0")
        self.write("active", "active")
        for _ in range(20):
            metrics = self.tick(0.70)
        self.assertEqual(metrics["ollama_cpu_guard_stops_total"], "0")


if __name__ == "__main__":
    unittest.main()
