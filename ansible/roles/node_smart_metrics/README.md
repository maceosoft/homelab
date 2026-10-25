# node_smart_metrics

Publica, para Prometheus/VictoriaMetrics, la **salud de los discos** de cada nodo, para avisar por Discord antes de que
un disco falle:

- **SSD SATA** (`invincible`, `oliver`): autodiagnóstico SMART, sectores reasignados / pendientes / no corregibles,
  errores CRC, temperatura, horas encendido y vida restante (si el fabricante la publica).
- **eMMC** (`deborah`): la eMMC **no tiene SMART** (`smartctl` responde «Unable to detect device type»). El kernel expone
  su desgaste en `/sys/block/mmcblk*/device/` (`life_time` y `pre_eol_info`, campos estándar JEDEC), y de ahí se lee.

Solo **lee**: no escribe en los discos ni lanza autotests SMART.

## Por qué un script con el textfile collector (y no smartctl_exporter)

- `prometheus-smartctl-exporter` **no existe como paquete en Debian 13**; habría que bajar un binario de GitHub (o una
  imagen) y mantenerlo a mano, y en Kubernetes sería un DaemonSet **privilegiado** con acceso a `/dev`.
- Aun así no cubriría la eMMC (no tiene SMART), que es justo el disco del nodo más importante.
- Un script de ~100 líneas con `smartctl` (paquete `smartmontools` de Debian, ya presente en `deborah`) y `/sys` sirve
  los dos casos, corre como `root` solo unos segundos cada 30 minutos y node-exporter (sin privilegios) únicamente
  lee un archivo. Es el mismo patrón que `node_apt_metrics`.

## Qué hace

1. Instala `smartmontools` **solo en los nodos con discos SATA/SAS** (no en `deborah`).
2. Crea `/var/lib/node_exporter/textfile` (la carpeta que lee el *textfile collector* de node-exporter).
3. Instala `/usr/local/bin/node-smart-metrics` y un servicio + temporizador de systemd (cada 30 min) que escribe
   `smart.prom` de forma atómica.

Métricas (etiqueta `device`): `node_smart_collect_success`, `node_smart_healthy`, `node_smart_attributes_failing`,
`node_smart_reallocated_sectors`, `node_smart_pending_sectors`, `node_smart_offline_uncorrectable_sectors`,
`node_smart_crc_errors_total`, `node_smart_power_on_seconds`, `node_smart_temperature_celsius`,
`node_smart_ssd_life_remaining_percent`, `node_emmc_life_time_estimate` (etiqueta `area` A/B),
`node_emmc_pre_eol_info` y `node_smart_metrics_last_run_timestamp_seconds`. No se publica el número de serie.

Solo se leen los discos de bus `sata`, `ata` o `sas`: los discos virtuales (iSCSI de Longhorn, zram) se ignoran.

## Dependencia: textfile collector de node-exporter

node-exporter tiene que montar `/var/lib/node_exporter/textfile` y arrancar con
`--collector.textfile.directory`. Se configura en el repo `gitops` (`monitoring/values-vm-stack.yaml`, junto con el rol
`node_apt_metrics`). Sin eso el archivo se escribe pero nadie lo lee.

## Playbook

[`playbook-smart-metrics.yml`](../../playbook-smart-metrics.yml) — `hosts: incus_cluster`.

```bash
ansible-playbook -i inventory.ini playbook-smart-metrics.yml --check --diff
ansible-playbook -i inventory.ini playbook-smart-metrics.yml
```

## Variables

Ver `defaults/main.yml`: `node_smart_metrics_dir`, `node_smart_metrics_interval` y
`node_smart_metrics_install_smartmontools`.

## Probar el script sin tocar ningún nodo

```bash
ansible/roles/node_smart_metrics/tests/test.sh      # necesita Docker
```

Lo ejecuta en un Debian 13 con `smartctl` y `lsblk` simulados (SSD sano, disco que falla, SMART apagado, `smartctl`
ausente) y una eMMC falsa en `/sys`, y valida la salida con `promtool`.

## Verificar en un nodo

```bash
systemctl list-timers node-smart-metrics.timer
cat /var/lib/node_exporter/textfile/smart.prom
sudo smartctl -A /dev/sda        # compara con node_smart_ssd_life_remaining_percent
```

**Vida restante del SSD:** cada fabricante usa un atributo distinto (231, 233, 177…). El script toma el menor valor
normalizado entre los atributos con nombre de «vida/desgaste/restante». Si tras la primera ejecución falta
`node_smart_ssd_life_remaining_percent`, ese modelo usa otro atributo: ajusta el filtro del script.

Las alertas que usan estas métricas están en el repo `gitops`: `monitoring/config/rules/homelab-hardware.yaml`.
