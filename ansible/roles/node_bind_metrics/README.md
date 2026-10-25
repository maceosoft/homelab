# node_bind_metrics

Publica, para Prometheus/VictoriaMetrics, si **BIND (`named`) está activo** y si **responde a una consulta DNS real**
(resuelve un registro propio del servidor), para avisar por Discord si el DNS de la LAN se cae.

**No cambia la configuración de BIND ni lo reinicia.**

## Por qué una sonda y no bind_exporter

BIND en `deborah` no tiene `statistics-channels`, así que `prometheus-bind-exporter` (que sí está en Debian 13) no
tendría de dónde leer. Activarlo implica editar `named.conf.options` en el rol `bind_dns` y reiniciar el DNS de toda la
LAN, para obtener contadores (consultas, SERVFAIL, caché) que hoy no se usan en ninguna alerta. Lo que importa
—«¿contesta?»— lo cubre una consulta real cada minuto. Si más adelante se necesitan estadísticas, se añade ese cambio al
rol `bind_dns` (ver su README).

## Qué hace

1. Instala `/usr/local/bin/node-bind-metrics` y un servicio + temporizador de systemd (cada minuto).
2. El script comprueba `systemctl is-active named` y hace una consulta `A` con `dig` (2 s de límite, sin reintentos)
   al servidor. Cuenta como éxito solo `NOERROR` con respuesta. Escribe `bind.prom` de forma atómica.

Métricas: `node_bind_service_active`, `node_bind_query_success`, `node_bind_query_duration_seconds` y
`node_bind_metrics_last_run_timestamp_seconds`.

## Dependencia: textfile collector de node-exporter

Igual que en [`node_smart_metrics`](../node_smart_metrics/README.md): node-exporter tiene que montar
`/var/lib/node_exporter/textfile` (repo `gitops`, `monitoring/values-vm-stack.yaml`).

## Playbook

[`playbook-bind-metrics.yml`](../../playbook-bind-metrics.yml) — `hosts: deborah`.

```bash
ansible-playbook -i inventory.ini playbook-bind-metrics.yml --check --diff
ansible-playbook -i inventory.ini playbook-bind-metrics.yml
```

## Variables

Ver `defaults/main.yml`: `node_bind_metrics_server` (por defecto `dns_primary`), `node_bind_metrics_query_name`
(por defecto `<nodo>.mco.local`, que genera el rol `bind_dns`), `node_bind_metrics_interval` y `node_bind_metrics_unit`.

## Probar el script sin tocar ningún nodo

```bash
ansible/roles/node_bind_metrics/tests/test.sh      # necesita Docker
```

## Verificar en el nodo

```bash
systemctl list-timers node-bind-metrics.timer
cat /var/lib/node_exporter/textfile/bind.prom
```

La sonda local no detecta un fallo de red entre los pods y el DNS: para eso, una sonda externa (módulo `dns` de
blackbox-exporter contra el DNS de la LAN). Las alertas están en el repo `gitops`:
`monitoring/config/rules/homelab-hardware.yaml`.
