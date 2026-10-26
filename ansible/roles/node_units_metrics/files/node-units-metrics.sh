#!/usr/bin/env bash
# Escribe, para el "textfile collector" de node-exporter, cuánta memoria y CPU usa cada servicio importante del host y
# qué procesos fuera de Kubernetes ocupan más memoria. El monitoreo solo ve contenedores: sin esto, un pico de un
# servicio del host (Ollama cargando un modelo, incus, k3s) aparece como "memoria usada" sin dueño.
#
#   node-units-metrics <carpeta textfile> <unidades separadas por coma> <cuántos procesos>
#
# Métricas (pocas series: ~4 por unidad + N procesos):
#   node_systemd_unit_active{unit}               1 si la unidad está activa
#   node_systemd_unit_memory_bytes{unit}         memoria del cgroup de la unidad (MemoryCurrent)
#   node_systemd_unit_cpu_seconds_total{unit}    CPU acumulada de la unidad (CPUUsageNSec)
#   node_memory_kubepods_bytes                   memoria de todos los pods (cgroup kubepods)
#   node_top_process_rss_bytes{rank,comm}        los N procesos con más memoria residente fuera de Kubernetes
set -euo pipefail

DIR="${1:-/var/lib/node_exporter/textfile}"
UNITS="${2:-ollama.service}"
TOP="${3:-5}"
OUT="$DIR/units.prom"
# Raíces configurables para las pruebas (tests/test_units.py); en el nodo son las del sistema.
CGROUP_ROOT="${NODE_UNITS_CGROUP_ROOT:-/sys/fs/cgroup}"
PROC_ROOT="${NODE_UNITS_PROC_ROOT:-/proc}"

mkdir -p "$DIR"
TMP="$(mktemp "$DIR/.units.prom.XXXXXX")"
trap 'rm -f "$TMP"' EXIT

{
  echo "# HELP node_systemd_unit_active 1 si la unidad systemd está activa."
  echo "# TYPE node_systemd_unit_active gauge"
  echo "# HELP node_systemd_unit_memory_bytes Memoria del cgroup de la unidad (MemoryCurrent de systemd)."
  echo "# TYPE node_systemd_unit_memory_bytes gauge"
  echo "# HELP node_systemd_unit_cpu_seconds_total CPU acumulada de la unidad (CPUUsageNSec de systemd)."
  echo "# TYPE node_systemd_unit_cpu_seconds_total counter"
  IFS=',' read -r -a units <<< "$UNITS"
  for unit in "${units[@]}"; do
    # Una unidad que no existe en este nodo (p. ej. k3s-agent en el server) no se publica.
    load="$(systemctl show "$unit" -p LoadState --value 2>/dev/null || true)"
    [ "$load" = "loaded" ] || continue
    active=0
    [ "$(systemctl show "$unit" -p ActiveState --value)" = "active" ] && active=1
    mem="$(systemctl show "$unit" -p MemoryCurrent --value)"
    cpu="$(systemctl show "$unit" -p CPUUsageNSec --value)"
    [[ "$mem" =~ ^[0-9]+$ ]] || mem=0   # "[not set]" cuando está detenida
    [[ "$cpu" =~ ^[0-9]+$ ]] || cpu=0
    echo "node_systemd_unit_active{unit=\"$unit\"} $active"
    echo "node_systemd_unit_memory_bytes{unit=\"$unit\"} $mem"
    echo "node_systemd_unit_cpu_seconds_total{unit=\"$unit\"} $(awk -v n="$cpu" 'BEGIN { printf "%.3f", n / 1e9 }')"
  done

  # K3s usa el driver cgroupfs (kubepods) o systemd (kubepods.slice) según la instalación.
  kube=0
  for f in "$CGROUP_ROOT/kubepods/memory.current" "$CGROUP_ROOT/kubepods.slice/memory.current"; do
    [ -r "$f" ] && kube="$(cat "$f")" && break
  done
  echo "# HELP node_memory_kubepods_bytes Memoria de todos los pods del nodo (cgroup kubepods)."
  echo "# TYPE node_memory_kubepods_bytes gauge"
  echo "node_memory_kubepods_bytes $kube"

  echo "# HELP node_top_process_rss_bytes Procesos con más memoria residente fuera de Kubernetes (rank 1 = el mayor)."
  echo "# TYPE node_top_process_rss_bytes gauge"
  rank=0
  # pid, rss en KiB y nombre corto, del mayor al menor; se saltan los procesos de pods (cgroup kubepods).
  while read -r pid rss comm; do
    [ -r "$PROC_ROOT/$pid/cgroup" ] || continue
    grep -q kubepods "$PROC_ROOT/$pid/cgroup" && continue
    rank=$((rank + 1))
    comm="${comm//[^A-Za-z0-9_.-]/_}"
    echo "node_top_process_rss_bytes{rank=\"$rank\",comm=\"$comm\"} $((rss * 1024))"
    [ "$rank" -ge "$TOP" ] && break
  done < <(ps -eo pid=,rss=,comm= --sort=-rss)

  echo "# HELP node_units_metrics_last_run_timestamp_seconds Última vez que corrió este script."
  echo "# TYPE node_units_metrics_last_run_timestamp_seconds gauge"
  echo "node_units_metrics_last_run_timestamp_seconds $(date +%s)"
} > "$TMP"

chmod 0644 "$TMP"        # node-exporter corre sin privilegios y tiene que poder leerlo
mv "$TMP" "$OUT"         # reemplazo atómico
trap - EXIT
