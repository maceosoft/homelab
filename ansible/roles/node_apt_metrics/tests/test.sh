#!/usr/bin/env bash
# Prueba files/node-apt-metrics.sh en un Debian 13 en contenedor, con un apt-get simulado que devuelve
# líneas con el formato real de los nodos, y valida la salida con promtool. No toca ningún nodo.
#
#   ansible/roles/node_apt_metrics/tests/test.sh        (necesita docker)
set -euo pipefail
cd "$(dirname "$0")/.."
IMG="${DEBIAN_IMAGE:-debian:13}"
PROMTOOL_IMAGE="${PROMTOOL_IMAGE:-prom/prometheus:latest}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/fakebin"

# apt-get de mentira: "update" sale con FAKE_UPDATE_RC; la simulación imprime FAKE_SIM (formato real de apt).
cat > "$TMP/fakebin/apt-get" <<'FAKE'
#!/bin/sh
case " $* " in
  *" update "*)       exit "${FAKE_UPDATE_RC:-0}" ;;
  *" dist-upgrade "*) printf '%b' "${FAKE_SIM:-}" ;;
esac
FAKE
chmod +x "$TMP/fakebin/apt-get"

SEC1='Inst bind9 [1:9.20.29-1~deb13u1] (1:9.20.30-1~deb13u1 Debian-Security:13/stable-security [arm64]) []\n'
SEC2='Inst libssl3t64 [3.5.7-1~deb13u2] (3.5.7-1~deb13u3 Debian-Security:13/stable-security [amd64])\n'
SEC3='Inst linux-image-6.12.111+deb13-amd64 (6.12.111-1 Debian-Security:13/stable-security [amd64])\n'
OTH1='Inst curl [8.14.1-2] (8.14.1-2+deb13u2 Debian:13.2/stable [amd64])\n'
OTH2='Inst vim-tiny [2:9.1.1230-2] (2:9.1.1230-3 Debian:13.2/stable-updates [amd64])\n'
NOISE='Reading package lists...\nConf bind9 (1:9.20.30-1~deb13u1 Debian-Security:13/stable-security [arm64])\n'

run() {  # nombre  FAKE_SIM  FAKE_UPDATE_RC  reboot(0/1)  -> imprime las métricas
  docker run --rm -e FAKE_SIM="$2" -e FAKE_UPDATE_RC="$3" -e REBOOT="$4" \
    -v "$PWD/files/node-apt-metrics.sh":/usr/local/bin/node-apt-metrics:ro -v "$TMP/fakebin":/fakebin:ro "$IMG" \
    bash -c 'mkdir -p /var/lib/apt/periodic /var/run; [ "$REBOOT" = 1 ] && touch /var/run/reboot-required;
             [ "$3" = lists ] && { mkdir -p /var/lib/apt/lists; touch -d "3 days ago" /var/lib/apt/lists/deb.debian.org_dists_trixie_InRelease; };
             PATH=/fakebin:$PATH node-apt-metrics /out && cat /out/apt.prom' _ x y "${5:-nolists}"
}
val() { printf '%s\n' "$1" | grep -E "^$2 " | awk '{print $2}'; }
check() {  # descripción  métricas  métrica  esperado
  got="$(val "$2" "$3")"; [ "$got" = "$4" ] && echo "  ✓ $1: $3 = $got" || { echo "  ✗ $1: $3 = '$got' (esperado $4)"; exit 1; }
}

echo "== caso 1: 3 de seguridad + 2 de otro origen, con líneas ajenas en la simulación, actualización correcta"
out="$(run c1 "$NOISE$SEC1$SEC2$SEC3$OTH1$OTH2" 0 0 nolists)"
check c1 "$out" 'node_apt_upgrades_pending{origin="security"}' 3
check c1 "$out" 'node_apt_upgrades_pending{origin="other"}' 2
check c1 "$out" 'node_reboot_required' 0
ts="$(val "$out" node_apt_update_success_timestamp_seconds)"; now=$(date +%s)
[ $((now - ts)) -lt 600 ] && echo "  ✓ c1: actualización correcta -> la marca es de hace menos de 10 minutos" || { echo "  ✗ c1: marca $ts"; exit 1; }
printf '%s\n' "$out" | docker run --rm -i --entrypoint promtool "$PROMTOOL_IMAGE" check metrics && echo "  ✓ c1: promtool acepta el formato"

echo "== caso 2: nada pendiente"
out="$(run c2 "$NOISE" 0 0 nolists)"
check c2 "$out" 'node_apt_upgrades_pending{origin="security"}' 0
check c2 "$out" 'node_apt_upgrades_pending{origin="other"}' 0

echo "== caso 3: apt-get update falla (sin red) y no hay ninguna lista: la marca es 0 y el recuento sigue saliendo"
out="$(run c3 "$SEC1$OTH1" 100 0 nolists)"
check c3 "$out" 'node_apt_update_success_timestamp_seconds' 0
check c3 "$out" 'node_apt_upgrades_pending{origin="security"}' 1

echo "== caso 3b: apt-get update falla pero hay listas de hace 3 días: la marca es la de esas listas"
out="$(run c3b "$SEC1" 100 0 lists)"
ts="$(val "$out" node_apt_update_success_timestamp_seconds)"; now=$(date +%s); age=$((now - ts))
[ "$age" -gt $((2*86400)) ] && [ "$age" -lt $((4*86400)) ] && echo "  ✓ c3b: edad de la marca = $((age/86400)) días" || { echo "  ✗ c3b: edad $age s"; exit 1; }

echo "== caso 4: reinicio pendiente"
out="$(run c4 "$SEC3" 0 1 nolists)"
check c4 "$out" 'node_reboot_required' 1

echo "== caso 5: con el apt REAL de Debian 13 (sin simulación; necesita red)"
real="$(docker run --rm -v "$PWD/files/node-apt-metrics.sh":/usr/local/bin/node-apt-metrics:ro "$IMG" bash -c 'node-apt-metrics /out && cat /out/apt.prom')"
printf '%s\n' "$real" | grep -E '^node_' | sed 's/^/    /'
printf '%s\n' "$real" | docker run --rm -i --entrypoint promtool "$PROMTOOL_IMAGE" check metrics && echo "  ✓ c5: promtool acepta la salida real"
echo "OK"
