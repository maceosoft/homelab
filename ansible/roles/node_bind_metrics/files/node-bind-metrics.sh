#!/usr/bin/env bash
# Escribe, para el "textfile collector" de node-exporter, si BIND (named) está activo y si responde a una
# consulta DNS real. Solo consulta: no cambia nada en BIND.
#
#   node-bind-metrics [carpeta]        (por defecto: /var/lib/node_exporter/textfile)
#
# Variables: BIND_SERVER (a quién se consulta), BIND_QUERY_NAME (qué nombre se resuelve; tiene que
# existir en una zona propia del servidor), BIND_UNIT (unidad de systemd).
set -euo pipefail

DIR="${1:-/var/lib/node_exporter/textfile}"
SERVER="${BIND_SERVER:-127.0.0.1}"
NAME="${BIND_QUERY_NAME:?falta BIND_QUERY_NAME}"
UNIT="${BIND_UNIT:-named.service}"
OUT="$DIR/bind.prom"

mkdir -p "$DIR"
TMP="$(mktemp "$DIR/.bind.prom.XXXXXX")"
trap 'rm -f "$TMP"' EXIT

active=0
systemctl is-active --quiet "$UNIT" && active=1

# Éxito = estado NOERROR con al menos una respuesta. Un timeout, SERVFAIL o NXDOMAIN cuentan como fallo.
success=0
duration=0
resp="$(dig "@$SERVER" "$NAME" A +time=2 +tries=1 +noall +comments +answer +stats 2>/dev/null || true)"
if printf '%s\n' "$resp" | grep -q 'status: NOERROR' && printf '%s\n' "$resp" | grep -qE '^[^;].*[[:space:]]IN[[:space:]]+A[[:space:]]'; then
  success=1
  ms="$(printf '%s\n' "$resp" | sed -n 's/^;; Query time: \([0-9]*\) msec.*/\1/p' | head -1)"
  duration="$(awk -v ms="${ms:-0}" 'BEGIN { printf "%.3f", ms / 1000 }')"
fi

cat >"$TMP" <<METRICS
# HELP node_bind_service_active 1 si la unidad de systemd de BIND (named) está activa.
# TYPE node_bind_service_active gauge
node_bind_service_active $active
# HELP node_bind_query_success 1 si BIND respondió NOERROR con respuesta a la consulta de prueba; 0 si no respondió o falló.
# TYPE node_bind_query_success gauge
node_bind_query_success $success
# HELP node_bind_query_duration_seconds Duración de la consulta de prueba (resolución de 1 ms; 0 si falló).
# TYPE node_bind_query_duration_seconds gauge
node_bind_query_duration_seconds $duration
# HELP node_bind_metrics_last_run_timestamp_seconds Última vez que corrió este script.
# TYPE node_bind_metrics_last_run_timestamp_seconds gauge
node_bind_metrics_last_run_timestamp_seconds ${NODE_BIND_NOW:-$(date +%s)}
METRICS

chmod 0644 "$TMP"        # node-exporter corre sin privilegios y tiene que poder leerlo
mv "$TMP" "$OUT"         # reemplazo atómico
trap - EXIT
