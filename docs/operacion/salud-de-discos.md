# Salud de los discos y del DNS

Qué se vigila del hardware de los nodos que antes no tenía alertas, y qué hacer cuando salta cada una. Los avisos llegan
por Discord igual que los demás del monitoreo.

| Qué | Dónde | Cómo se lee |
|---|---|---|
| Autodiagnóstico SMART (Self-Monitoring, Analysis and Reporting Technology), sectores dañados, temperatura y vida restante de los SSD | `invincible`, `oliver` (SSD SATA, Serial ATA) | `smartctl` (paquete `smartmontools`) |
| Desgaste y aviso de fin de vida de la eMMC (embedded MultiMediaCard) | `deborah` | Archivos de `/sys/block/mmcblk*/device/` |
| BIND (Berkeley Internet Name Domain, el DNS de la LAN) activo y respondiendo | `deborah` | Una consulta de prueba cada minuto |

La eMMC de `deborah` **no tiene SMART**: `smartctl` responde «Unable to detect device type». Lo que sí hace el controlador
es llevar la cuenta de su desgaste, y el kernel la publica en `life_time` y `pre_eol_info`. Son campos estándar de JEDEC
(Joint Electron Device Engineering Council), así que valen para cualquier eMMC.

## Cómo llegan las métricas

En cada nodo, un temporizador de systemd ejecuta un script que escribe un archivo `.prom` en
`/var/lib/node_exporter/textfile`. node-exporter lo lee con su *textfile collector* y VictoriaMetrics lo guarda. Solo se
**lee**: no se escribe en los discos ni se lanzan autotests SMART, y BIND no se toca. El autotest SMART se lanza solo a
mano, con Ansible (ver [Autotest SMART](#autotest-smart)).

| Pieza | Dónde |
|---|---|
| Rol de discos | [`ansible/roles/node_smart_metrics`](https://github.com/maceosoft/homelab/tree/main/ansible/roles/node_smart_metrics) y [`playbook-smart-metrics.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-smart-metrics.yml) |
| Rol de BIND | [`ansible/roles/node_bind_metrics`](https://github.com/maceosoft/homelab/tree/main/ansible/roles/node_bind_metrics) y [`playbook-bind-metrics.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-bind-metrics.yml) |
| Alertas | [`gitops/monitoring/config/rules/homelab-hardware.yaml`](https://github.com/maceosoft/gitops/blob/main/monitoring/config/rules/homelab-hardware.yaml) |
| Pruebas de las alertas | [`gitops/monitoring/tests/rules-test.yaml`](https://github.com/maceosoft/gitops/blob/main/monitoring/tests/rules-test.yaml) |

!!! note "Requisito: textfile collector"
    node-exporter tiene que montar `/var/lib/node_exporter/textfile` (configuración en
    [`gitops/monitoring/values-vm-stack.yaml`](https://github.com/maceosoft/gitops/blob/main/monitoring/values-vm-stack.yaml)).
    Sin eso los archivos se escriben pero nadie los lee, y a las 24 h salta `SinDatosDeDiscos`.

### Por qué un script y no `smartctl_exporter`

`prometheus-smartctl-exporter` no está empaquetado en Debian 13: habría que mantener un binario o una imagen aparte, y en
Kubernetes correría como DaemonSet privilegiado con acceso a `/dev`. Además no cubriría la eMMC, que es el disco del nodo
más importante. El script usa solo `smartctl` (paquete de Debian) y `/sys`, corre como `root` unos segundos cada 30
minutos y node-exporter no necesita privilegios.

### Por qué una sonda y no `bind_exporter`

BIND no tiene `statistics-channels` activado, así que `prometheus-bind-exporter` no tendría qué leer. Activarlo implica
editar la configuración de BIND y reiniciarlo, y el DNS de toda la LAN depende de ese reinicio. Para saber si el DNS
funciona basta con **preguntarle**: la sonda resuelve un nombre propio (`deborah.mco.local`) cada minuto.

## Alertas y qué hacer

Los avisos de **fallo inminente** (`critical`) piden actuar el mismo día; los `warning`, planificar.

### Discos SATA (SSD)

| Alerta | Cuándo salta | Qué hacer |
|---|---|---|
| `DiscoSmartFalla` (crítica) | El autodiagnóstico SMART dice FAILED durante 5 min | El disco predice que va a fallar. Verifica los backups, copia los datos y reemplázalo. Detalle: `sudo smartctl -a /dev/sdX` |
| `DiscoAtributoSmartEnFallo` | Un atributo SMART está por debajo de su umbral (`FAILING_NOW`) durante 1 h | Mira cuál con `sudo smartctl -A /dev/sdX`; casi siempre precede a `DiscoSmartFalla` |
| `DiscoSectoresInestables` | Sectores pendientes o no corregibles mayores que 0 durante 1 h | El disco no lee algunas zonas de forma fiable. Comprueba backups y planifica el reemplazo |
| `DiscoSectoresReasignadosCreciendo` | Los sectores reasignados aumentaron en los últimos 3 días | Un valor fijo no es problema; que crezca sí. Planifica el reemplazo y vigila la tendencia |
| `SsdVidaBaja` | Vida restante menor que 20 % durante 1 h | Compra el reemplazo antes de que llegue a 0 |
| `DiscoTemperaturaAlta` | 60 °C o más durante 15 min | El máximo habitual de un SSD SATA es 70 °C. Revisa ventilación y polvo del nodo |

### eMMC de `deborah`

El campo `life_time` tiene dos áreas (A y B) y el valor sube de 1 a 11 según el desgaste:

| Valor | Significado |
|---|---|
| 1 a 10 | Entre 0-10 % y 90-100 % de la vida estimada usada (cada paso, un 10 %) |
| 11 | Superó la vida estimada |

Y `pre_eol_info` (aviso de fin de vida, EOL, End Of Life) vale 1 si está normal, 2 si se consumió el 80 % de los bloques de
reserva y 3 si se consumió el 90 %.

| Alerta | Cuándo salta | Qué hacer |
|---|---|---|
| `EmmcDesgastada` (aviso) | Nivel 9 o más (más del 80 % usado) durante 1 h | Haz un respaldo (el control plane de K3s vive ahí) y planifica el reemplazo |
| `EmmcDesgastada` (crítica) | Nivel 11: superó la vida estimada | Puede fallar en cualquier momento: respalda ya y reemplázala |
| `EmmcFinDeVida` (aviso) | `pre_eol_info` = 2 | Planifica respaldo y reemplazo |
| `EmmcFinDeVida` (crítica) | `pre_eol_info` = 3 | Respalda ya y reemplázala |

Para ver los valores a mano: `cat /sys/block/mmcblk1/device/life_time /sys/block/mmcblk1/device/pre_eol_info`.

!!! tip "Cómo reducir el desgaste de la eMMC"
    Es la causa habitual de llegar al fin de vida antes de tiempo: muchas escrituras pequeñas (logs, etcd, base de datos
    de K3s). Si el nivel sube rápido, mueve esas cargas a otro disco.

### Que no se pierda la vigilancia

| Alerta | Cuándo salta | Qué hacer |
|---|---|---|
| `DiscoSmartNoLegible` | `smartctl` no puede leer el estado SMART de un disco durante 2 h | Prueba `sudo smartctl -a /dev/sdX`. Puede que SMART esté apagado (`smartctl -s on`), que falte `smartmontools` o que el disco no responda |
| `DatosDeDiscosViejos` | El archivo de métricas lleva más de 2 h sin actualizarse | `systemctl status node-smart-metrics.timer node-smart-metrics.service` y `journalctl -u node-smart-metrics` |
| `SinDatosDeDiscos` | node-exporter responde pero no hay métricas de discos durante 1 día | Falta aplicar `playbook-smart-metrics.yml` en ese nodo, o node-exporter no monta la carpeta del textfile collector |

### BIND (DNS)

| Alerta | Cuándo salta | Qué hacer |
|---|---|---|
| `BindCaido` (crítica) | `named` no está activo durante 2 min | En `deborah`: `systemctl status named` y `journalctl -u named -e`. Comprueba la sintaxis con `named-checkconf` antes de reiniciar. Sin DNS no se resuelven los nombres internos de la LAN |
| `DnsSinRespuesta` (crítica) | `named` está activo pero la consulta de prueba falla o da error durante 3 min | `dig @<IP del DNS> deborah.mco.local`. Revisa `rndc status`, el espacio en disco y los registros de `named` |
| `DnsLento` | La consulta tarda más de 0,5 s durante 10 min | Normalmente tarda milisegundos. Mira la carga del nodo y los reenviadores (*forwarders*) |
| `MetricasDeBindViejas` | La sonda lleva más de 10 min sin ejecutarse | `systemctl status node-bind-metrics.timer`. Mientras tanto no se sabe si el DNS responde |
| `SinDatosDeBind` | node-exporter de `deborah` no publica la sonda durante 1 h | Falta aplicar `playbook-bind-metrics.yml` o el textfile collector no está montado |

!!! note "Qué no cubre la sonda local"
    Corre en el propio `deborah`: avisa si BIND cae o no contesta, pero no si falla la red entre los pods y el DNS. Para eso
    sirve una sonda externa (módulo `dns` de blackbox-exporter apuntando al DNS de la LAN).

## Aplicar los playbooks

Desde la carpeta `ansible/` del repo `homelab`, y **después** de que `gitops` monte el textfile collector:

```bash
ansible-playbook -i inventory.ini playbook-smart-metrics.yml --check --diff
ansible-playbook -i inventory.ini playbook-smart-metrics.yml
ansible-playbook -i inventory.ini playbook-bind-metrics.yml --check --diff
ansible-playbook -i inventory.ini playbook-bind-metrics.yml
```

Instalan `smartmontools` solo donde hay discos SATA (`invincible` y `oliver`), crean la carpeta y los temporizadores, y no
reinician nada. Verifica en cada nodo con `cat /var/lib/node_exporter/textfile/smart.prom` (o `bind.prom` en `deborah`).

!!! warning "Vida restante del SSD"
    Cada fabricante publica el desgaste en un atributo SMART distinto. Tras la primera ejecución comprueba que existe
    `node_smart_ssd_life_remaining_percent` en `smart.prom`; si falta, ese modelo usa otro atributo y hay que ajustar el
    filtro del script (ver el README del rol). Mientras falte, `SsdVidaBaja` no puede avisar.

## Autotest SMART

Un autotest le pide al propio disco que revise su superficie y su electrónica. No borra ni escribe datos: el disco lo hace
en segundo plano y el nodo sigue funcionando (puede ir algo más lento mientras dura). Sirve para confirmar un aviso como
`DiscoSectoresInestables` o para revisar un disco de vez en cuando. Solo aplica a los SSD SATA (`invincible`, `oliver`); la
eMMC de `deborah` no tiene SMART.

Desde `ansible/`, la simulación muestra en qué discos se lanzaría; la segunda orden lo lanza:

```bash
ansible-playbook -i inventory.ini playbook-smart-metrics.yml --tags smart_selftest --check
ansible-playbook -i inventory.ini playbook-smart-metrics.yml --tags smart_selftest
```

La salida dice cuántos minutos tarda (el autotest largo de un SSD suele tardar de minutos a una hora). Pasado ese tiempo:

```bash
ansible-playbook -i inventory.ini playbook-smart-metrics.yml --tags smart_selftest_result
```

Estas tareas no corren en una ejecución normal del playbook. Para otro disco o un autotest corto:
`-e '{"node_smart_metrics_selftest_devices": ["sda"], "node_smart_metrics_selftest_type": "short"}'`.

### Cómo leer el resultado

En `autotests` aparece el registro del disco, el más reciente primero (`# 1`):

| `Status` | Qué significa |
|---|---|
| `Completed without error` | El disco no encontró problemas |
| `Self-test routine in progress` | Aún no termina: vuelve a leerlo más tarde |
| `Aborted by host` o `Interrupted` | Se cortó (reinicio o apagado); lánzalo de nuevo |
| `Completed: read failure` (u otro `failure`) | Hay zonas que no se pueden leer; la columna `LBA_of_first_error` dice dónde. Respalda y planifica el reemplazo |

En `atributos` se muestran cuatro contadores; mira la última columna (`RAW_VALUE`):

| ID | Atributo | Qué indica |
|---|---|---|
| 5 | `Reallocated_Sector_Ct` | Sectores que el disco ya reemplazó por reserva |
| 187 | `Reported_Uncorrect` | Errores que el disco no pudo corregir |
| 197 | `Current_Pending_Sector` | Sectores dudosos, a la espera de reasignarse |
| 198 | `Offline_Uncorrectable` | Sectores que no se pudieron leer en las revisiones del disco |

Lo normal es 0 en los cuatro. Un valor fijo distinto de 0 no es urgente, pero que suba entre dos lecturas sí: respalda y
planifica el reemplazo, como con las alertas de la tabla de discos SATA.
