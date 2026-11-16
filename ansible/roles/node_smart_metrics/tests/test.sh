#!/usr/bin/env bash
# Prueba files/node-smart-metrics.sh en un Debian 13 en contenedor, con un smartctl y un lsblk simulados
# (formato real de smartctl 7.4) y un /sys falso para la eMMC; valida la salida con promtool.
# No toca ningún nodo.
#
#   ansible/roles/node_smart_metrics/tests/test.sh        (necesita docker)
set -euo pipefail
cd "$(dirname "$0")/.."
IMG="${DEBIAN_IMAGE:-debian:13}"
PROMTOOL_IMAGE="${PROMTOOL_IMAGE:-prom/prometheus:latest}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/fakebin"

# lsblk de mentira: imprime LSBLK_OUT. smartctl de mentira: imprime el contenido de $SMART_FILE.
cat > "$TMP/fakebin/lsblk" <<'FAKE'
#!/bin/sh
printf '%b' "${LSBLK_OUT:-}"
FAKE
cat > "$TMP/fakebin/smartctl" <<'FAKE'
#!/bin/sh
cat "${SMART_FILE:?}"
exit "${SMART_RC:-0}"
FAKE
chmod +x "$TMP/fakebin/lsblk" "$TMP/fakebin/smartctl"

HDR='ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE'
cat > "$TMP/sano.txt" <<EOT
smartctl 7.4 2023-08-01 r5530 [x86_64-linux-6.12.48+deb13-amd64] (local build)

=== START OF INFORMATION SECTION ===
Device Model:     KINGSTON SA400S37240G
Serial Number:    0000000000000000
User Capacity:    240,057,409,536 bytes [240 GB]

=== START OF READ SMART DATA SECTION ===
SMART overall-health self-assessment test result: PASSED

SMART Attributes Data Structure revision number: 1
Vendor Specific SMART Attributes with Thresholds:
$HDR
  1 Raw_Read_Error_Rate     0x0032   100   100   000    Old_age   Always       -       100
  5 Reallocated_Sector_Ct   0x0032   100   100   000    Old_age   Always       -       0
  9 Power_On_Hours          0x0032   100   100   000    Old_age   Always       -       4321
 12 Power_Cycle_Count       0x0032   100   100   000    Old_age   Always       -       50
169 Unknown_Attribute       0x0033   100   100   010    Pre-fail  Always       -       0
194 Temperature_Celsius     0x0022   034   040   000    Old_age   Always       -       34 (Min/Max 20/40)
197 Current_Pending_Sector  0x0032   100   100   000    Old_age   Always       -       0
199 UDMA_CRC_Error_Count    0x0032   100   100   000    Old_age   Always       -       2
231 SSD_Life_Left           0x0031   097   097   000    Pre-fail  Offline      -       0
241 Lifetime_Writes_GiB     0x0032   100   100   000    Old_age   Always       -       3321
EOT
# Disco con problemas: falla el autodiagnóstico, sectores reasignados/pendientes, 12% de vida, raw en hexadecimal.
cat > "$TMP/malo.txt" <<EOT
=== START OF INFORMATION SECTION ===
Device Model:     TECLAST 120GB S500

=== START OF READ SMART DATA SECTION ===
SMART overall-health self-assessment test result: FAILED!

$HDR
  5 Reallocated_Sector_Ct   0x0032   090   090   010    Old_age   Always       -       0x000000000018
  9 Power_On_Hours          0x0032   100   100   000    Old_age   Always       -       0x000000002710
190 Airflow_Temperature_Cel 0x0022   058   050   000    Old_age   Always   FAILING_NOW 42
197 Current_Pending_Sector  0x0032   100   100   000    Old_age   Always       -       3
198 Offline_Uncorrectable   0x0030   100   100   000    Old_age   Offline      -       1
177 Wear_Leveling_Count     0x0013   012   012   005    Pre-fail  Always       -       4000
EOT
# Disco con SMART apagado: smartctl no imprime el bloque de datos.
cat > "$TMP/apagado.txt" <<'EOT'
=== START OF INFORMATION SECTION ===
Device Model:     DISCO SIN SMART
SMART support is: Disabled
EOT
# NVMe (salida real del SK hynix de deborah, sin el número de serie): con -c trae los umbrales de temperatura.
cat > "$TMP/nvme.txt" <<'EOT'
smartctl 7.4 2023-08-01 r5530 [aarch64-linux-5.10.160-rockchip-rk3588] (local build)

=== START OF INFORMATION SECTION ===
Model Number:                       SK hynix BC501 HFM256GDJTNG-8310A
Firmware Version:                   80002C00
Warning  Comp. Temp. Threshold:     81 Celsius
Critical Comp. Temp. Threshold:     82 Celsius

Supported Power States
St Op     Max   Active     Idle   RL RT WL WT  Ent_Lat  Ex_Lat
 0 +   3.5000W       -        -    0  0  0  0        5       5
 4 -   0.0050W       -        -    3  3  3  3     1000    5000

=== START OF SMART DATA SECTION ===
SMART overall-health self-assessment test result: PASSED

SMART/Health Information (NVMe Log 0x02)
Critical Warning:                   0x04
Temperature:                        68 Celsius
Available Spare:                    100%
Percentage Used:                    1%
Data Units Written:                 2,058,465 [1.05 TB]
Power On Hours:                     1,072
Media and Data Integrity Errors:    0
Temperature Sensor 1:               68 Celsius
Temperature Sensor 2:               76 Celsius
EOT
: > "$TMP/vacio.txt"   # smartctl que no imprime nada (el SSD de Apple detrás del T2)
mkdir -p "$TMP/sys/block/mmcblk1/device" "$TMP/sys/block/mmcblk0/device"   # mmcblk0 sin life_time (p. ej. tarjeta SD)
printf '0x01 0x00\n' > "$TMP/sys/block/mmcblk1/device/life_time"
printf '0x01\n' > "$TMP/sys/block/mmcblk1/device/pre_eol_info"
printf 'A3A564\n' > "$TMP/sys/block/mmcblk1/device/name"
mkdir -p "$TMP/sys/class/nvme/nvme0/hwmon0"
printf '36850\n' > "$TMP/sys/class/nvme/nvme0/hwmon0/temp1_input"

run() {  # LSBLK_OUT  archivo_smart  [sysfs=con|sin]  [smartctl=con|sin]  -> imprime smart.prom
  local sysdir=/nada; [ "${3:-sin}" = con ] && sysdir=/t/sys
  docker run --rm -e LSBLK_OUT="$1" -e SMART_FILE="/t/$2" -e NODE_SMART_SYSFS="$sysdir" -e SIN_SMARTCTL="${4:-con}" \
    -v "$PWD/files/node-smart-metrics.sh":/usr/local/bin/node-smart-metrics:ro -v "$TMP":/t:ro "$IMG" \
    bash -c 'mkdir -p /out /nada; cp -r /t/fakebin /fb; [ "$SIN_SMARTCTL" = sin ] && rm /fb/smartctl
             PATH=/fb:$PATH node-smart-metrics /out && cat /out/smart.prom; ls -A /out'
}
val() { printf '%s\n' "$1" | grep -F "$2 " | awk '{print $NF}'; }
check() {  # descripción  métricas  serie  esperado
  got="$(val "$2" "$3")"; [ "$got" = "$4" ] && echo "  ✓ $1: $3 = $got" || { echo "  ✗ $1: $3 = '$got' (esperado $4)"; exit 1; }
}
promtool_ok() { printf '%s\n' "$1" | grep -v '^[a-z.]*prom$' | docker run --rm -i --entrypoint promtool "$PROMTOOL_IMAGE" check metrics && echo "  ✓ $2: promtool acepta el formato"; }

echo "== caso 1: SSD sano + disco iSCSI y zram (se ignoran)"
out="$(run 'sda sata\nsdb iscsi\nzram0 \nmmcblk1 mmc\n' sano.txt sin)"
check c1 "$out" 'node_smart_collect_success{device="sda"}' 1
check c1 "$out" 'node_smart_healthy{device="sda"}' 1
check c1 "$out" 'node_smart_reallocated_sectors{device="sda"}' 0
check c1 "$out" 'node_smart_pending_sectors{device="sda"}' 0
check c1 "$out" 'node_smart_crc_errors_total{device="sda"}' 2
check c1 "$out" 'node_smart_power_on_seconds{device="sda"}' $((4321*3600))
check c1 "$out" 'node_smart_temperature_celsius{device="sda"}' 34
check c1 "$out" 'node_smart_ssd_life_remaining_percent{device="sda"}' 97
check c1 "$out" 'node_smart_attributes_failing{device="sda"}' 0
printf '%s\n' "$out" | grep -q 'device="sdb"' && { echo "  ✗ c1: no debía leer el disco iSCSI"; exit 1; } || echo "  ✓ c1: el disco iSCSI se ignora"
printf '%s\n' "$out" | grep -q 'model="KINGSTON SA400S37240G"' && echo "  ✓ c1: modelo en la etiqueta"
printf '%s\n' "$out" | grep -q 'Serial' && { echo "  ✗ c1: no debe publicarse el número de serie"; exit 1; } || echo "  ✓ c1: sin número de serie"
promtool_ok "$out" c1

echo "== caso 2: disco que falla (FAILED, sectores, raw hexadecimal, FAILING_NOW)"
out="$(run 'sda sata\n' malo.txt sin)"
check c2 "$out" 'node_smart_healthy{device="sda"}' 0
check c2 "$out" 'node_smart_reallocated_sectors{device="sda"}' 24
check c2 "$out" 'node_smart_pending_sectors{device="sda"}' 3
check c2 "$out" 'node_smart_offline_uncorrectable_sectors{device="sda"}' 1
check c2 "$out" 'node_smart_power_on_seconds{device="sda"}' $((10000*3600))
check c2 "$out" 'node_smart_temperature_celsius{device="sda"}' 42
check c2 "$out" 'node_smart_ssd_life_remaining_percent{device="sda"}' 12
check c2 "$out" 'node_smart_attributes_failing{device="sda"}' 1
promtool_ok "$out" c2

echo "== caso 3: SMART apagado y smartctl ausente -> collect_success = 0, sin otras series del disco"
out="$(run 'sda sata\n' apagado.txt sin)"
check c3 "$out" 'node_smart_collect_success{device="sda"}' 0
printf '%s\n' "$out" | grep -q 'node_smart_healthy' && { echo "  ✗ c3: no debía haber salud"; exit 1; } || echo "  ✓ c3: sin series de salud"
out="$(run 'sda sata\n' sano.txt sin sin)"
check c3b "$out" 'node_smart_collect_success{device="sda"}' 0

echo "== caso 4: eMMC (sin SMART): desgaste 0-10 %, aviso de fin de vida normal; la tarjeta SD sin life_time se ignora"
out="$(run 'mmcblk1 mmc\n' sano.txt con)"
check c4 "$out" 'node_emmc_life_time_estimate{device="mmcblk1",area="A"}' 1
check c4 "$out" 'node_emmc_life_time_estimate{device="mmcblk1",area="B"}' 0
check c4 "$out" 'node_emmc_pre_eol_info{device="mmcblk1"}' 1
printf '%s\n' "$out" | grep -q 'node_smart_collect_success' && { echo "  ✗ c4: la eMMC no debe pasar por smartctl"; exit 1; } || echo "  ✓ c4: la eMMC no se lee con smartctl"
printf '%s\n' "$out" | grep -q 'mmcblk0' && { echo "  ✗ c4: mmcblk0 no tiene life_time"; exit 1; } || echo "  ✓ c4: dispositivo sin life_time ignorado"
promtool_ok "$out" c4

echo "== caso 5: eMMC desgastada (0x0A / 0x0B y pre-EOL 0x03)"
printf '0x0a 0x0b\n' > "$TMP/sys/block/mmcblk1/device/life_time"; printf '0x03\n' > "$TMP/sys/block/mmcblk1/device/pre_eol_info"
out="$(run 'mmcblk1 mmc\n' sano.txt con)"
check c5 "$out" 'node_emmc_life_time_estimate{device="mmcblk1",area="A"}' 10
check c5 "$out" 'node_emmc_life_time_estimate{device="mmcblk1",area="B"}' 11
check c5 "$out" 'node_emmc_pre_eol_info{device="mmcblk1"}' 3

echo "== caso 6: NVMe con SMART (temperatura, sensores, umbrales, desgaste, aviso crítico)"
out="$(run 'nvme0n1 nvme\nmmcblk1 mmc\n' nvme.txt sin)"
check c6 "$out" 'node_smart_collect_success{device="nvme0n1"}' 1
check c6 "$out" 'node_smart_healthy{device="nvme0n1"}' 1
check c6 "$out" 'node_smart_temperature_celsius{device="nvme0n1"}' 68
check c6 "$out" 'node_smart_temperature_sensor_celsius{device="nvme0n1",sensor="1"}' 68
check c6 "$out" 'node_smart_temperature_sensor_celsius{device="nvme0n1",sensor="2"}' 76
check c6 "$out" 'node_smart_temperature_warning_celsius{device="nvme0n1"}' 81
check c6 "$out" 'node_smart_temperature_critical_celsius{device="nvme0n1"}' 82
check c6 "$out" 'node_smart_ssd_life_remaining_percent{device="nvme0n1"}' 99
check c6 "$out" 'node_smart_power_on_seconds{device="nvme0n1"}' $((1072*3600))
check c6 "$out" 'node_nvme_critical_warning{device="nvme0n1"}' 4
check c6 "$out" 'node_nvme_media_errors_total{device="nvme0n1"}' 0
printf '%s\n' "$out" | grep -q 'model="SK hynix BC501 HFM256GDJTNG-8310A"' && echo "  ✓ c6: modelo en la etiqueta"
printf '%s\n' "$out" | grep -q 'node_smart_reallocated_sectors' && { echo "  ✗ c6: las filas de estados de energía no son atributos SATA"; exit 1; } || echo "  ✓ c6: la tabla de estados de energía no se confunde con atributos"
promtool_ok "$out" c6

echo "== caso 7: NVMe que smartctl no lee pero publica la temperatura en hwmon -> solo la temperatura"
out="$(run 'nvme0n1 nvme\n' vacio.txt con)"
check c7 "$out" 'node_smart_temperature_celsius{device="nvme0n1"}' 36
printf '%s\n' "$out" | grep -q 'node_smart_collect_success' && { echo "  ✗ c7: no debía avisar de SMART ilegible"; exit 1; } || echo "  ✓ c7: sin collect_success"
promtool_ok "$out" c7
out="$(run 'nvme0n1 nvme\n' vacio.txt sin)"
check c7b "$out" 'node_smart_collect_success{device="nvme0n1"}' 0

echo "== caso 8: sin ningún disco con datos -> solo la marca de última ejecución, sin archivos temporales"
out="$(run '' sano.txt sin)"
printf '%s\n' "$out" | grep -q '^node_smart_metrics_last_run_timestamp_seconds ' && echo "  ✓ c8: hay marca de última ejecución"
[ "$(printf '%s\n' "$out" | grep -c '^\.')" = 0 ] && echo "  ✓ c8: no quedan archivos temporales"
echo "OK"
