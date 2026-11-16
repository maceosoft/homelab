#!/usr/bin/env bash
# temperaturas.sh -- temperatura de todos los sensores de los nodos del HomeLab, SOLO LECTURA.
#
# Por nodo, cada sensor de temperatura del kernel (hwmon: CPU, núcleos, GPU, placa, batería, NVMe, los sensores del
# SMC de la Mac...). Un NVMe que no aparece en hwmon (el de deborah: por eso tampoco llega a las métricas) se lee con
# smartctl.
# Las zonas térmicas no se listan aparte: son los mismos sensores que hwmon. Marca con ! los que llegan a AVISO_C.
#
# Uso (desde cualquier carpeta):
#   ansible/scripts/temperaturas.sh               # todos los nodos (grupo incus_cluster)
#   ansible/scripts/temperaturas.sh deborah       # un nodo o un patrón de Ansible (deborah:eve)
#
# Variables:
#   AVISO_C       temperatura desde la que se marca un sensor (por defecto 75)
#   ANSIBLE_BIN   ruta de ansible (por defecto el del .venv del repo)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANSIBLE_DIR="${SCRIPT_DIR}/.."
ANSIBLE_BIN="${ANSIBLE_BIN:-${ANSIBLE_DIR}/../.venv/bin/ansible}"
TARGET="${1:-incus_cluster}"
AVISO_C="${AVISO_C:-75}"

# Se ejecuta en cada nodo: una línea "<°C>|<sensor>" por sensor. Comillas simples a propósito: las variables se
# expanden en el nodo, no aquí.
# shellcheck disable=SC2016
REMOTE='for h in /sys/class/hwmon/hwmon*; do
  n=$(cat "$h/name")
  for t in "$h"/temp*_input; do
    v=$(cat "$t" 2>/dev/null) || continue
    l="${t%_input}_label"
    [ -r "$l" ] && n2="$n $(cat "$l")" || n2="$n"
    echo "$((v / 1000))|$n2"
  done
done
for d in /dev/nvme[0-9]; do
  [ -e "$d" ] || continue
  ls -d /sys/class/nvme/"${d#/dev/}"/hwmon* >/dev/null 2>&1 && continue   # ya salió en hwmon
  smartctl -A "$d" 2>/dev/null | sed -nE "s/^(Temperature|Temperature Sensor [0-9]+):[[:space:]]+([0-9]+) Celsius/\2|${d#/dev/} \1/p"
done'

cd "${ANSIBLE_DIR}"
ANSIBLE_DEPRECATION_WARNINGS=False "${ANSIBLE_BIN}" "${TARGET}" -i inventory.ini -b -o -m shell -a "${REMOTE}" \
  | sort \
  | awk -v aviso="${AVISO_C}" '
      {
        host = $1
        if ($0 !~ /\(stdout\) /) { print host ": " $0; next }   # nodo inalcanzable o error
        sub(/.*\(stdout\) /, "")
        n = split($0, lineas, /\\n/)
        print host
        for (i = 1; i <= n; i++) {
          split(lineas[i], c, "|")
          printf "  %s %4s °C  %s\n", (c[1] + 0 >= aviso ? "!" : " "), c[1], c[2]
        }
        print ""
      }'
