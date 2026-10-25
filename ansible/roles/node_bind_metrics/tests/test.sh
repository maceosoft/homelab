#!/usr/bin/env bash
# Prueba files/node-bind-metrics.sh en un Debian 13 en contenedor, con dig y systemctl simulados (salida con
# el formato real de dig 9.20), y valida la salida con promtool. No toca ningún nodo.
#
#   ansible/roles/node_bind_metrics/tests/test.sh        (necesita docker)
set -euo pipefail
cd "$(dirname "$0")/.."
IMG="${DEBIAN_IMAGE:-debian:13}"
PROMTOOL_IMAGE="${PROMTOOL_IMAGE:-prom/prometheus:latest}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/fakebin"

# dig de mentira: imprime DIG_OUT y sale con DIG_RC (9 = timeout, como el dig real). systemctl: is-active según UNIT_ACTIVE.
cat > "$TMP/fakebin/dig" <<'FAKE'
#!/bin/sh
printf '%b' "${DIG_OUT:-}"
exit "${DIG_RC:-0}"
FAKE
cat > "$TMP/fakebin/systemctl" <<'FAKE'
#!/bin/sh
[ "${UNIT_ACTIVE:-1}" = 1 ]
FAKE
chmod +x "$TMP/fakebin/dig" "$TMP/fakebin/systemctl"

OK=';; Got answer:\n;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 22066\n;; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1\n\n;; ANSWER SECTION:\nnodo.mco.local.\t300\tIN\tA\t192.0.2.5\n\n;; Query time: 37 msec\n;; SERVER: 192.0.2.5#53(192.0.2.5) (UDP)\n;; MSG SIZE  rcvd: 70\n'
NX=';; Got answer:\n;; ->>HEADER<<- opcode: QUERY, status: NXDOMAIN, id: 36\n;; flags: qr aa rd ra; QUERY: 1, ANSWER: 0, AUTHORITY: 1, ADDITIONAL: 1\n\n;; Query time: 0 msec\n'
SF=';; Got answer:\n;; ->>HEADER<<- opcode: QUERY, status: SERVFAIL, id: 1\n;; Query time: 5 msec\n'
NOERR_EMPTY=';; Got answer:\n;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 2\n;; flags: qr aa rd ra; QUERY: 1, ANSWER: 0, AUTHORITY: 1, ADDITIONAL: 1\n\n;; Query time: 1 msec\n'
TIMEOUT=';; communications error to 192.0.2.5#53: timed out\n\n; <<>> DiG 9.20.29 <<>> @192.0.2.5 nodo.mco.local A\n; (1 server found)\n;; no servers could be reached\n'

run() {  # DIG_OUT  DIG_RC  UNIT_ACTIVE
  docker run --rm -e DIG_OUT="$1" -e DIG_RC="$2" -e UNIT_ACTIVE="$3" -e BIND_QUERY_NAME=nodo.mco.local -e BIND_SERVER=192.0.2.5 \
    -v "$PWD/files/node-bind-metrics.sh":/usr/local/bin/node-bind-metrics:ro -v "$TMP/fakebin":/fb:ro "$IMG" \
    bash -c 'mkdir -p /out; PATH=/fb:$PATH node-bind-metrics /out && cat /out/bind.prom; ls -A /out | grep -v "^bind.prom$" || true'
}
val() { printf '%s\n' "$1" | grep -E "^$2 " | awk '{print $2}'; }
check() { got="$(val "$2" "$3")"; [ "$got" = "$4" ] && echo "  ✓ $1: $3 = $got" || { echo "  ✗ $1: $3 = '$got' (esperado $4)"; exit 1; }; }

echo "== caso 1: BIND activo y responde"
out="$(run "$OK" 0 1)"
check c1 "$out" node_bind_service_active 1
check c1 "$out" node_bind_query_success 1
check c1 "$out" node_bind_query_duration_seconds 0.037
printf '%s\n' "$out" | grep -E '^(# |node_)' | docker run --rm -i --entrypoint promtool "$PROMTOOL_IMAGE" check metrics && echo "  ✓ c1: promtool acepta el formato"

echo "== caso 2: named activo pero no contesta (timeout)"
out="$(run "$TIMEOUT" 9 1)"
check c2 "$out" node_bind_service_active 1
check c2 "$out" node_bind_query_success 0
check c2 "$out" node_bind_query_duration_seconds 0

echo "== caso 3: unidad parada y sin respuesta"
out="$(run "$TIMEOUT" 9 0)"
check c3 "$out" node_bind_service_active 0
check c3 "$out" node_bind_query_success 0

echo "== caso 4: NXDOMAIN, SERVFAIL y NOERROR sin respuesta cuentan como fallo"
for resp in "$NX" "$SF" "$NOERR_EMPTY"; do
  out="$(run "$resp" 0 1)"
  check c4 "$out" node_bind_query_success 0
done

echo "== caso 5: sin archivos temporales y con marca de última ejecución"
out="$(run "$OK" 0 1)"
printf '%s\n' "$out" | grep -q '^node_bind_metrics_last_run_timestamp_seconds ' && echo "  ✓ c5: hay marca de última ejecución"
[ -z "$(printf '%s\n' "$out" | grep '^\.')" ] && echo "  ✓ c5: no quedan archivos temporales"
echo "OK"
