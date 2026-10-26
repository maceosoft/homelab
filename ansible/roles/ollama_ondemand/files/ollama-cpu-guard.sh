#!/usr/bin/env bash
# Guardia de CPU de Ollama. La corre un temporizador de systemd cada pocos minutos: mide cuánta CPU usó
# ollama.service desde la medición anterior y, si pasa demasiado tiempo saturando el nodo, lo detiene.
#
# Ollama usa toda la CPU mientras responde, pero en el HomeLab cada respuesta dura segundos o minutos. Horas
# seguidas cerca del tope significan que algo está mal (un cliente en bucle, una traducción interminable, un
# modelo que no cabe): se detienen ollama.service y el socket, para que no vuelva a despertar, se deja el aviso
# en el journal y en las métricas de node-exporter (alerta OllamaDetenidoPorCPU). Para volver a activarlo:
#   sudo systemctl start ollama-proxy.socket
#
#   ollama-cpu-guard <carpeta textfile> <umbral %> <horas>
#     umbral %: uso de ollama.service sobre el total de núcleos del nodo que cuenta como saturado
set -euo pipefail

DIR="${1:-/var/lib/node_exporter/textfile}"
THRESHOLD="${2:-60}"
HOURS="${3:-2}"
STATE_DIR="${OLLAMA_CPU_GUARD_STATE_DIR:-/var/lib/ollama-cpu-guard}"
STATE="$STATE_DIR/state"
OUT="$DIR/ollama_cpu_guard.prom"

mkdir -p "$STATE_DIR" "$DIR"
since=0; last_ns=0; last_ts=0; stops=0; last_stop=0
# shellcheck source=/dev/null
[ -f "$STATE" ] && . "$STATE"

now_ts=$(date +%s%N)
cpus=$(nproc)
active=$(systemctl is-active ollama.service || true)
usage_ns=$(systemctl show ollama.service -p CPUUsageNSec --value 2>/dev/null || echo "")
[[ "$usage_ns" =~ ^[0-9]+$ ]] || usage_ns=0

percent=0
if [ "$active" = "active" ] && [ "$last_ts" -gt 0 ] && [ "$usage_ns" -ge "$last_ns" ]; then
  wall=$((now_ts - last_ts))
  [ "$wall" -gt 0 ] && percent=$(( (usage_ns - last_ns) * 100 / (wall * cpus) ))
fi

now=$((now_ts / 1000000000))
if [ "$active" = "active" ] && [ "$percent" -ge "$THRESHOLD" ]; then
  [ "$since" -eq 0 ] && since=$now
else
  since=0
fi

saturated=0
[ "$since" -gt 0 ] && saturated=$((now - since))

if [ "$saturated" -ge $((HOURS * 3600)) ]; then
  logger -t ollama-cpu-guard -p daemon.crit \
    "ollama.service lleva ${saturated}s sobre el ${THRESHOLD}% de la CPU del nodo: se detiene. Reactivar con: systemctl start ollama-proxy.socket"
  systemctl stop ollama-proxy.socket ollama-proxy.service ollama.service || true
  stops=$((stops + 1)); last_stop=$now; since=0; saturated=0
fi

# Si ollama.service está apagado, la próxima medición empieza de cero.
if [ "$active" = "active" ]; then last_ns=$usage_ns; last_ts=$now_ts; else last_ns=0; last_ts=0; fi
printf 'since=%s\nlast_ns=%s\nlast_ts=%s\nstops=%s\nlast_stop=%s\n' "$since" "$last_ns" "$last_ts" "$stops" "$last_stop" > "$STATE"

socket=0
systemctl is-active --quiet ollama-proxy.socket && socket=1

TMP="$(mktemp "$DIR/.ollama_cpu_guard.prom.XXXXXX")"
trap 'rm -f "$TMP"' EXIT
cat > "$TMP" <<METRICS
# HELP ollama_cpu_guard_usage_percent Uso de CPU de ollama.service en el último intervalo, en % del total de núcleos.
# TYPE ollama_cpu_guard_usage_percent gauge
ollama_cpu_guard_usage_percent $percent
# HELP ollama_cpu_guard_saturated_seconds Segundos seguidos de ollama.service sobre el umbral.
# TYPE ollama_cpu_guard_saturated_seconds gauge
ollama_cpu_guard_saturated_seconds $saturated
# HELP ollama_cpu_guard_stops_total Veces que la guardia detuvo Ollama por CPU.
# TYPE ollama_cpu_guard_stops_total counter
ollama_cpu_guard_stops_total $stops
# HELP ollama_cpu_guard_last_stop_timestamp_seconds Última vez que la guardia detuvo Ollama (0 = nunca).
# TYPE ollama_cpu_guard_last_stop_timestamp_seconds gauge
ollama_cpu_guard_last_stop_timestamp_seconds $last_stop
# HELP ollama_cpu_guard_socket_up 1 si ollama-proxy.socket está activo (el nodo acepta peticiones).
# TYPE ollama_cpu_guard_socket_up gauge
ollama_cpu_guard_socket_up $socket
METRICS
chmod 0644 "$TMP"
mv "$TMP" "$OUT"
trap - EXIT
