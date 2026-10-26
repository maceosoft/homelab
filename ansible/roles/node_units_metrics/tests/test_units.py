"""Prueba files/node-units-metrics.sh con systemctl, ps, /proc y cgroups simulados (no toca el sistema).

    python3 -m unittest discover -s ansible/roles/node_units_metrics/tests
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "files" / "node-units-metrics.sh"

# ollama.service activa con 5 GiB; k3s-agent no existe en este nodo; incus detenida.
SYSTEMCTL = """#!/bin/sh
unit="$2"; prop="$4"
case "$unit:$prop" in
  ollama.service:LoadState|incus.service:LoadState) echo loaded ;;
  *:LoadState) echo not-found ;;
  ollama.service:ActiveState) echo active ;;
  ollama.service:MemoryCurrent) echo 5368709120 ;;
  ollama.service:CPUUsageNSec) echo 1500000000 ;;
  incus.service:ActiveState) echo inactive ;;
  incus.service:MemoryCurrent|incus.service:CPUUsageNSec) echo "[not set]" ;;
esac
"""
# pid rss(KiB) comm, del mayor al menor: el 100 es un pod (se excluye).
PS = """#!/bin/sh
printf '100 9000000 java\\n200 5000000 ollama\\n300 800000 incusd\\n400 200000 k3s-server\\n'
"""


class UnitsMetricsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        (d / "bin").mkdir()
        for name, body in (("systemctl", SYSTEMCTL), ("ps", PS)):
            (d / "bin" / name).write_text(body)
            (d / "bin" / name).chmod(0o755)
        for pid, cg in (("100", "0::/kubepods/burstable/pod1/abc"), ("200", "0::/system.slice/ollama.service"),
                        ("300", "0::/system.slice/incus.service"), ("400", "0::/system.slice/k3s.service")):
            (d / "proc" / pid).mkdir(parents=True)
            (d / "proc" / pid / "cgroup").write_text(cg + "\n")
        (d / "cg" / "kubepods").mkdir(parents=True)
        (d / "cg" / "kubepods" / "memory.current").write_text("3221225472\n")
        env = dict(os.environ, PATH=f"{d / 'bin'}:{os.environ['PATH']}",
                   NODE_UNITS_CGROUP_ROOT=str(d / "cg"), NODE_UNITS_PROC_ROOT=str(d / "proc"))
        subprocess.run(["bash", str(SCRIPT), str(d / "out"), "ollama.service,k3s-agent.service,incus.service", "2"],
                       env=env, check=True)
        self.metrics = {line.rsplit(" ", 1)[0]: line.rsplit(" ", 1)[1]
                        for line in (d / "out" / "units.prom").read_text().splitlines() if not line.startswith("#")}

    def tearDown(self):
        self.tmp.cleanup()

    def test_unidades(self):
        self.assertEqual(self.metrics['node_systemd_unit_active{unit="ollama.service"}'], "1")
        self.assertEqual(self.metrics['node_systemd_unit_memory_bytes{unit="ollama.service"}'], "5368709120")
        self.assertEqual(self.metrics['node_systemd_unit_cpu_seconds_total{unit="ollama.service"}'], "1.500")
        self.assertEqual(self.metrics['node_systemd_unit_active{unit="incus.service"}'], "0")
        self.assertEqual(self.metrics['node_systemd_unit_memory_bytes{unit="incus.service"}'], "0")
        self.assertNotIn('node_systemd_unit_active{unit="k3s-agent.service"}', self.metrics)

    def test_pods_y_top_de_procesos(self):
        self.assertEqual(self.metrics["node_memory_kubepods_bytes"], "3221225472")
        # el proceso del pod (java) no cuenta; el top 2 es ollama e incusd
        self.assertEqual(self.metrics['node_top_process_rss_bytes{rank="1",comm="ollama"}'], str(5000000 * 1024))
        self.assertEqual(self.metrics['node_top_process_rss_bytes{rank="2",comm="incusd"}'], str(800000 * 1024))
        self.assertFalse(any("java" in k for k in self.metrics))
        self.assertFalse(any('rank="3"' in k for k in self.metrics))


if __name__ == "__main__":
    unittest.main()
