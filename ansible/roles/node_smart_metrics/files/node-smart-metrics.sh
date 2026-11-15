#!/usr/bin/env bash
# Escribe, para el "textfile collector" de node-exporter, la salud de los discos del nodo:
#   - SSD/discos SATA: autodiagnóstico SMART (smartctl, solo lectura), sectores problemáticos,
#     temperatura, horas encendido y vida restante (si el disco la publica).
#   - NVMe: lo mismo desde el registro de salud NVMe, más los sensores de temperatura extra, los umbrales de
#     temperatura del propio disco, el aviso crítico y los errores de datos. Si smartctl no lo lee (el SSD de
#     Apple detrás del chip T2), solo la temperatura de hwmon.
#   - eMMC: nivel de desgaste (life_time) y aviso de fin de vida (pre_eol_info) que el kernel expone en
#     /sys; la eMMC no tiene SMART, así que smartctl no sirve ahí.
# No escribe nada en los discos ni lanza autotests: solo lee.
#
#   node-smart-metrics [carpeta]        (por defecto: /var/lib/node_exporter/textfile)
#
# Variables para pruebas: NODE_SMART_SYSFS (raíz de /sys), NODE_SMART_NOW (hora fija).
set -euo pipefail

DIR="${1:-/var/lib/node_exporter/textfile}"
SYS="${NODE_SMART_SYSFS:-/sys}"
OUT="$DIR/smart.prom"

mkdir -p "$DIR"
TMP="$(mktemp "$DIR/.smart.prom.XXXXXX")"
SAMPLES="$(mktemp)"
trap 'rm -f "$TMP" "$SAMPLES"' EXIT

# Escapa un valor para usarlo como etiqueta de Prometheus.
esc() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | tr -d '\n'; }

# --- Discos SATA/SAS/NVMe (con SMART) ----------------------------------------------------------
# Se filtra por tipo de bus: así se ignoran los discos virtuales (iSCSI de Longhorn, zram, loop).
while read -r name tran; do
  case "$tran" in sata | ata | sas | nvme) ;; *) continue ;; esac
  out=""
  if command -v smartctl >/dev/null 2>&1; then
    # -n standby: no despierta un disco dormido. El código de salida es una máscara de bits
    # (también avisa de atributos viejos): se ignora y se decide por lo que imprime.
    # -c en NVMe: trae los umbrales de temperatura del disco.
    extra=""; [ "$tran" = nvme ] && extra="-c"
    out="$(timeout 60 smartctl -i -H -A $extra -n standby "/dev/$name" 2>/dev/null || true)"
  fi
  # Temperatura de respaldo del NVMe en hwmon (nvme0n1 -> controlador nvme0), por si smartctl no lo lee.
  hwtemp=""
  if [ "$tran" = nvme ]; then
    for t in "$SYS"/class/nvme/"${name%n[0-9]*}"/hwmon*/temp1_input; do
      [ -r "$t" ] && hwtemp="$(($(cat "$t") / 1000))" && break
    done
  fi
  printf '%s\n' "$out" | awk -v dev="$name" -v hwtemp="$hwtemp" '
    function hex(s,   i, c, n) {
      n = 0; s = tolower(substr(s, 3))
      for (i = 1; i <= length(s); i++) { c = index("0123456789abcdef", substr(s, i, 1)) - 1; n = n * 16 + c }
      return n
    }
    function num(s) { return (s ~ /^0[xX][0-9a-fA-F]+$/) ? hex(s) : s + 0 }
    function esc(s) { gsub(/\\/, "\\\\", s); gsub(/"/, "\\\"", s); return s }
    # Valor de una línea "Nombre: 1,234 [x]" o "Nombre: 5%": el primer número, sin comas de miles.
    function campo(   v) { v = $0; sub(/^[^:]*:[ \t]*/, "", v); sub(/[ %].*/, "", v); gsub(/,/, "", v); return v }
    /^(Device Model|Model Number|Product):/ { m = $0; sub(/^[^:]*:[ \t]*/, "", m); model = m }
    /SMART overall-health self-assessment test result:/ { have = 1; health = ($NF == "PASSED") ? 1 : 0 }
    /^SMART Health Status:/ { have = 1; health = ($NF == "OK") ? 1 : 0 }
    # NVMe: registro de salud (los números pueden traer comas de miles).
    /^Temperature:/ { temp = campo() + 0 }
    /^Temperature Sensor [0-9]+:/ { sensor[$3 + 0] = campo() + 0 }
    /^Warning  Comp\. Temp\. Threshold:/ { twarn = campo() + 0 }
    /^Critical Comp\. Temp\. Threshold:/ { tcrit = campo() + 0 }
    /^Percentage Used:/ { life = 100 - campo(); if (life < 0) life = 0 }
    /^Power On Hours:/ { hours = campo() + 0 }
    /^Media and Data Integrity Errors:/ { media = campo() + 0 }
    /^Critical Warning:/ { cwarn = num(campo()) }
    # Tabla de atributos: ID NOMBRE FLAG VALOR PEOR UMBRAL TIPO ACTUALIZA CUANDO_FALLA RAW
    $1 ~ /^[0-9]+$/ && $2 ~ /^[A-Za-z0-9_-]+$/ && NF >= 10 && $3 ~ /^0x/ {
      id = $1 + 0; val = $4 + 0; raw = num($10)
      if (id == 5) realloc = raw
      else if (id == 197) pending = raw
      else if (id == 198) uncorr = raw
      else if (id == 199) crc = raw
      else if (id == 9) hours = raw
      else if (id == 194 || (id == 190 && temp == "")) { temp = raw; if (temp > 150) temp = temp % 256 }
      if ($9 == "FAILING_NOW") failing++
      # Vida restante: el valor normalizado baja de 100 a 0. Cada fabricante usa un ID distinto.
      if ((id == 169 || id == 177 || id == 202 || id == 231 || id == 233) && $2 ~ /[Ll]ife|[Ww]ear|[Rr]emain/) {
        if (life == "" || val < life) life = val
      }
    }
    END {
      # NVMe que smartctl no lee pero publica su temperatura en hwmon: solo la temperatura, sin
      # collect_success (no es un disco roto, es un SSD sin registro SMART accesible).
      if (!have && hwtemp != "") { printf "node_smart_temperature_celsius{device=\"%s\"} %d\n", dev, hwtemp; exit }
      printf "node_smart_collect_success{device=\"%s\"} %d\n", dev, have
      if (!have) exit
      printf "node_smart_device_info{device=\"%s\",model=\"%s\"} 1\n", dev, esc(model)
      printf "node_smart_healthy{device=\"%s\"} %d\n", dev, health
      printf "node_smart_attributes_failing{device=\"%s\"} %d\n", dev, failing + 0
      if (realloc != "") printf "node_smart_reallocated_sectors{device=\"%s\"} %d\n", dev, realloc
      if (pending != "") printf "node_smart_pending_sectors{device=\"%s\"} %d\n", dev, pending
      if (uncorr != "") printf "node_smart_offline_uncorrectable_sectors{device=\"%s\"} %d\n", dev, uncorr
      if (crc != "") printf "node_smart_crc_errors_total{device=\"%s\"} %d\n", dev, crc
      if (hours != "") printf "node_smart_power_on_seconds{device=\"%s\"} %d\n", dev, hours * 3600
      if (temp != "") printf "node_smart_temperature_celsius{device=\"%s\"} %d\n", dev, temp
      if (life != "") printf "node_smart_ssd_life_remaining_percent{device=\"%s\"} %d\n", dev, life
      for (i in sensor) printf "node_smart_temperature_sensor_celsius{device=\"%s\",sensor=\"%d\"} %d\n", dev, i, sensor[i]
      if (twarn > 0) printf "node_smart_temperature_warning_celsius{device=\"%s\"} %d\n", dev, twarn
      if (tcrit > 0) printf "node_smart_temperature_critical_celsius{device=\"%s\"} %d\n", dev, tcrit
      if (cwarn != "") printf "node_nvme_critical_warning{device=\"%s\"} %d\n", dev, cwarn
      if (media != "") printf "node_nvme_media_errors_total{device=\"%s\"} %d\n", dev, media
    }' >>"$SAMPLES"
done < <(lsblk -dn -o NAME,TRAN 2>/dev/null || true)

# --- eMMC (sin SMART: el kernel expone el desgaste en sysfs) -------------------------------------
for dev in "$SYS"/block/mmcblk*; do
  [ -r "$dev/device/life_time" ] || continue
  name="$(basename "$dev")"
  read -r life_a life_b <"$dev/device/life_time" || continue
  eol="$(cat "$dev/device/pre_eol_info" 2>/dev/null || echo 0)"
  label="$(esc "$(cat "$dev/device/name" 2>/dev/null || echo desconocido)")"
  {
    echo "node_emmc_info{device=\"$name\",name=\"$label\"} 1"
    echo "node_emmc_life_time_estimate{device=\"$name\",area=\"A\"} $((life_a))"
    echo "node_emmc_life_time_estimate{device=\"$name\",area=\"B\"} $((life_b))"
    echo "node_emmc_pre_eol_info{device=\"$name\"} $((eol))"
  } >>"$SAMPLES"
done

emit() { # nombre tipo ayuda
  grep -E "^$1[{ ]" "$SAMPLES" >/dev/null 2>&1 || return 0
  printf '# HELP %s %s\n# TYPE %s %s\n' "$1" "$3" "$1" "$2"
  grep -E "^$1[{ ]" "$SAMPLES"
}

{
  emit node_smart_collect_success gauge "1 si smartctl pudo leer el autodiagnóstico SMART del disco; 0 si no (SMART apagado, smartctl ausente o el disco no responde)."
  emit node_smart_device_info gauge "Modelo del disco SATA (siempre 1)."
  emit node_smart_healthy gauge "Resultado del autodiagnóstico SMART: 1 = PASSED, 0 = FAILED (el disco predice que va a fallar)."
  emit node_smart_attributes_failing gauge "Atributos SMART que están ahora por debajo de su umbral (FAILING_NOW)."
  emit node_smart_reallocated_sectors gauge "Sectores reasignados (atributo 5): el disco ya sustituyó sectores dañados."
  emit node_smart_pending_sectors gauge "Sectores pendientes de reasignar (atributo 197): lecturas inestables."
  emit node_smart_offline_uncorrectable_sectors gauge "Sectores no corregibles (atributo 198)."
  emit node_smart_crc_errors_total counter "Errores CRC en el cable/enlace SATA (atributo 199)."
  emit node_smart_power_on_seconds gauge "Tiempo encendido en segundos (atributo 9, que el disco da en horas)."
  emit node_smart_temperature_celsius gauge "Temperatura del disco en grados Celsius (atributo 194 o 190; en NVMe, la temperatura compuesta)."
  emit node_smart_temperature_sensor_celsius gauge "Sensores de temperatura extra del NVMe (Temperature Sensor N), en grados Celsius."
  emit node_smart_temperature_warning_celsius gauge "Umbral de aviso de temperatura que declara el propio NVMe (WCTEMP)."
  emit node_smart_temperature_critical_celsius gauge "Umbral crítico de temperatura que declara el propio NVMe (CCTEMP)."
  emit node_nvme_critical_warning gauge "Aviso crítico del NVMe (máscara de bits): 0 = sin avisos; distinto de 0 = poca reserva, temperatura, fiabilidad, solo lectura o fallo del respaldo."
  emit node_nvme_media_errors_total counter "Errores de datos no recuperados del NVMe (Media and Data Integrity Errors)."
  emit node_smart_ssd_life_remaining_percent gauge "Vida restante del SSD en porcentaje (valor normalizado del atributo de desgaste del fabricante)."
  emit node_emmc_info gauge "Modelo de la eMMC (siempre 1)."
  emit node_emmc_life_time_estimate gauge "Desgaste de la eMMC (JEDEC): 0 sin dato, 1 = 0-10% usado ... 10 = 90-100% usado, 11 = superó la vida estimada. Áreas A (SLC) y B (MLC)."
  emit node_emmc_pre_eol_info gauge "Aviso de fin de vida de la eMMC (JEDEC): 0 sin dato, 1 normal, 2 aviso (80% de bloques de reserva consumidos), 3 urgente (90%)."
  printf '# HELP node_smart_metrics_last_run_timestamp_seconds Última vez que corrió este script.\n'
  printf '# TYPE node_smart_metrics_last_run_timestamp_seconds gauge\n'
  printf 'node_smart_metrics_last_run_timestamp_seconds %s\n' "${NODE_SMART_NOW:-$(date +%s)}"
} >"$TMP"

chmod 0644 "$TMP"        # node-exporter corre sin privilegios y tiene que poder leerlo
mv "$TMP" "$OUT"         # reemplazo atómico: nunca queda un archivo a medio escribir
trap 'rm -f "$SAMPLES"' EXIT
