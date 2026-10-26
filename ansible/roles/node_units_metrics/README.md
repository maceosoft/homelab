# node_units_metrics

Publica para node-exporter (textfile collector) cuánta memoria y CPU usa cada servicio importante del **host** y qué
procesos fuera de Kubernetes ocupan más memoria. El monitoreo de contenedores no ve el host: el 26-10, `invincible` se
quedó sin memoria por algo fuera de los pods (probablemente Ollama cargando un modelo) y no había cómo confirmarlo.

| Métrica | Qué es |
|---|---|
| `node_systemd_unit_active{unit}` | 1 si la unidad está activa |
| `node_systemd_unit_memory_bytes{unit}` | Memoria del cgroup de la unidad (`MemoryCurrent`) |
| `node_systemd_unit_cpu_seconds_total{unit}` | CPU acumulada de la unidad (`CPUUsageNSec`) |
| `node_memory_kubepods_bytes` | Memoria de todos los pods del nodo |
| `node_top_process_rss_bytes{rank,comm}` | Los `node_units_metrics_top` procesos con más memoria residente fuera de Kubernetes |

Son unas 30 series por nodo. Las usan la alerta `MemoriaDelHostFueraDeKubernetes` y el panel «Servicios del host» de
«HomeLab / Estado general» (repo `gitops`).

## Variables

| Variable | Por defecto | Para qué |
|---|---|---|
| `node_units_metrics_dir` | `/var/lib/node_exporter/textfile` | Carpeta del textfile collector |
| `node_units_metrics_units` | ollama, ollama-proxy, k3s, k3s-agent, incus, named, journald | Unidades a medir; las que no existen se omiten |
| `node_units_metrics_top` | `5` | Procesos en el top de memoria |
| `node_units_metrics_interval` | `1min` | Cada cuánto se mide |

## Aplicar y verificar

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-units-metrics.yml
# en un nodo
cat /var/lib/node_exporter/textfile/units.prom
```

Prueba local, sin tocar el sistema: `python3 -m unittest discover -s ansible/roles/node_units_metrics/tests`.
