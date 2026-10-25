# node_apt_metrics

Publica, para Prometheus/VictoriaMetrics, cuántos **paquetes tienen una actualización pendiente** (separando los
de seguridad), si el nodo **necesita reiniciarse** y **cuándo se refrescaron las listas de apt**. Pensado para
avisar por Discord sin instalar nada automáticamente.

## Qué hace

1. Crea `/var/lib/node_exporter/textfile` (la carpeta que lee el *textfile collector* de node-exporter).
2. Instala `/usr/local/bin/node-apt-metrics` y un servicio + temporizador de systemd que lo ejecuta cada 6 horas.
3. El script refresca las listas (`apt-get update`, que solo baja listas), **simula** `apt-get dist-upgrade` para contar los
   paquetes pendientes y escribe `apt.prom`. **No instala ni actualiza ningún paquete.**

Métricas: `node_apt_upgrades_pending{origin="security"|"other"}`, `node_reboot_required`,
`node_apt_update_success_timestamp_seconds` y `node_apt_metrics_last_run_timestamp_seconds`.

## Playbook

[`playbook-apt-metrics.yml`](../../playbook-apt-metrics.yml) — `hosts: incus_cluster`.

```bash
ansible-playbook -i inventory.ini playbook-apt-metrics.yml --check --diff
ansible-playbook -i inventory.ini playbook-apt-metrics.yml
```

## Variables

Ver `defaults/main.yml`: `node_apt_metrics_dir`, `node_apt_metrics_interval` y `node_apt_metrics_refresh_lists`.

## Probar el script sin tocar ningún nodo

```bash
ansible/roles/node_apt_metrics/tests/test.sh      # necesita Docker
```

Lo ejecuta en un Debian 13 con un `apt-get` simulado (con seguridad, sin nada, sin red, con reinicio pendiente), lo valida con
`promtool` y lo prueba una vez con el `apt` real.

## Verificar en un nodo

```bash
systemctl list-timers node-apt-metrics.timer
cat /var/lib/node_exporter/textfile/apt.prom
```

Las alertas que usan estas métricas están en el repo `gitops`: `monitoring/config/rules/homelab-nodos.yaml`.
