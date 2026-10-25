#!/usr/bin/env bash
# Escribe, para el "textfile collector" de node-exporter, cuántos paquetes tienen una actualización
# pendiente (separando los de seguridad), si el nodo necesita reiniciarse y cuándo se refrescaron por
# última vez las listas de apt. NO instala ni actualiza ningún paquete: solo simula (apt-get -s) y,
# salvo NODE_APT_UPDATE=0, refresca las listas con apt-get update para que el recuento no sea viejo.
#
#   node-apt-metrics [carpeta]        (por defecto: /var/lib/node_exporter/textfile)
set -euo pipefail

DIR="${1:-/var/lib/node_exporter/textfile}"
OUT="$DIR/apt.prom"
LISTS="/var/lib/apt/lists"

mkdir -p "$DIR"
TMP="$(mktemp "$DIR/.apt.prom.XXXXXX")"
trap 'rm -f "$TMP"' EXIT

update_ts=0
if [ "${NODE_APT_UPDATE:-1}" = "1" ] && timeout 180 apt-get update -qq >/dev/null 2>&1; then
  update_ts="$(date +%s)"          # las listas se acaban de refrescar
fi

# Simulación: no cambia nada. Cada paquete pendiente es una línea "Inst ..." con su origen entre paréntesis.
sim="$(apt-get -s -o Debug::NoLocking=true dist-upgrade 2>/dev/null || true)"
total=$(printf '%s\n' "$sim" | grep -c '^Inst ' || true)
security=$(printf '%s\n' "$sim" | grep '^Inst ' | grep -ci 'security' || true)
other=$((total - security))

reboot=0
[ -e /var/run/reboot-required ] && reboot=1

if [ "$update_ts" = 0 ]; then
  # No se pudo refrescar (sin red, o NODE_APT_UPDATE=0): la fecha real es la del archivo de lista más reciente.
  # No se usa update-success-stamp porque Debian 13 no lo crea por sí solo en estos nodos.
  newest="$(find "$LISTS" -maxdepth 1 -type f \( -name '*InRelease' -o -name '*Release' \) -printf '%T@\n' 2>/dev/null | sort -n | tail -1)"
  update_ts="${newest%%.*}"
  update_ts="${update_ts:-0}"
fi

cat > "$TMP" <<METRICS
# HELP node_apt_upgrades_pending Paquetes con actualización pendiente según apt-get -s dist-upgrade.
# TYPE node_apt_upgrades_pending gauge
node_apt_upgrades_pending{origin="security"} $security
node_apt_upgrades_pending{origin="other"} $other
# HELP node_apt_update_success_timestamp_seconds Último apt-get update correcto (marca de tiempo Unix).
# TYPE node_apt_update_success_timestamp_seconds gauge
node_apt_update_success_timestamp_seconds $update_ts
# HELP node_reboot_required 1 si hay una actualización instalada que pide reiniciar el nodo.
# TYPE node_reboot_required gauge
node_reboot_required $reboot
# HELP node_apt_metrics_last_run_timestamp_seconds Última vez que corrió este script.
# TYPE node_apt_metrics_last_run_timestamp_seconds gauge
node_apt_metrics_last_run_timestamp_seconds $(date +%s)
METRICS

chmod 0644 "$TMP"        # node-exporter corre sin privilegios y tiene que poder leerlo
mv "$TMP" "$OUT"         # reemplazo atómico: nunca queda un archivo a medio escribir
trap - EXIT
