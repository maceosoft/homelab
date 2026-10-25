# Monitoreo y alertas

Qué se vigila en el HomeLab, dónde mirarlo y qué hacer cuando llega un aviso a Discord. Si eres quien lo **instala**,
ve a [4.13 — Monitoreo y alertas](../implementacion/fase-4-gitops.md#413-monitoreo-y-alertas-opcional).

!!! info "En una línea"
    Cada 30 segundos se leen las métricas de los tres nodos y de la plataforma. Si algo pasa de un umbral durante un rato,
    llega un mensaje a Discord: **🔴 críticas** en `alertas-criticas` (te llegan al móvil) y **🟡 avisos** en `alertas-avisos`.
    Cuando se resuelve, llega un **✅**.

## Ver las temperaturas y el uso

Entra a [`https://grafana.homelab.local`](https://grafana.homelab.local) (solo desde la red local) con el usuario
`admin` y la contraseña del item `grafana-admin` de 1Password. Los paneles de nodos y de Kubernetes ya vienen cargados.

Para una consulta puntual usa *Explore* con estas expresiones:

| Qué | Consulta |
|---|---|
| Temperatura de cada nodo | `max by (nodename) (node_thermal_zone_temp)` |
| Memoria disponible (%) | `100 * node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes` |
| Disco raíz usado (%) | `100 * (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})` |
| Uso de CPU (%) | `100 * (1 - avg by (nodename) (rate(node_cpu_seconds_total{mode="idle"}[5m])))` |

Las temperaturas de referencia, leídas del propio hardware: `deborah` (SoC, system on chip, el chip que reúne CPU y gráficos)
reduce velocidad a 75 °C y otra vez a 85 °C; `invincible` y `oliver` tienen como límite del fabricante 100 °C.

## Qué te puede llegar

| Alerta | Qué significa | Qué hacer |
|---|---|---|
| 🟡 `TemperaturaAlta` | El procesador pasó de 80 °C (75 °C en `deborah`) varios minutos | Mira qué lo carga (`kubectl top pods -A`) y la ventilación del equipo |
| 🔴 `TemperaturaCritica` | Pasó de 90 °C (85 °C en `deborah`) | Revisa ventilación y carga ya; si sigue subiendo, apaga cargas pesadas (p. ej. los runners de ARC) |
| 🔴 `NodoNoListo` | Un nodo no está `Ready` en Kubernetes | Comprueba que está encendido y en red, entra con `ssh` ([acceso](acceso-ssh.md)) y mira `systemctl status k3s` o `k3s-agent` |
| 🔴 `ServicioBaseSinReplicas` | ArgoCD, Kong o cert-manager sin ninguna réplica | `kubectl -n <namespace> get pods`; sin ellos no hay GitOps, Gateway ni certificados |
| 🟡/🔴 `CertificadoPorVencer` | Un certificado vence en menos de 14 / 3 días | `kubectl describe certificate -A`; cert-manager debería renovarlo solo, así que si no lo hace, mira por qué |
| 🟡 `CertificadoNoListo` | Un certificado no se pudo emitir | `kubectl describe certificate -A` y los logs de cert-manager |
| 🔴 `LonghornVolumenDegradado` | Un volumen perdió una réplica: queda una sola copia | Abre la UI de Longhorn (ver [URLs y accesos](urls-y-accesos.md)) y comprueba que ambos discos están sanos |
| 🔴 `LonghornVolumenFallido` | Un volumen sin réplicas utilizables | Urgente: la app que lo usa no funciona; revisa Longhorn y los nodos |
| 🟡 `LonghornDiscoLlenandose` | El disco de Longhorn pasó del 80 % | Borra volúmenes o snapshots que no se usen, o añade un disco ([agregar disco](agregar-disco.md)) |
| 🟡 `ArgoCDAppNoSana` / `Desincronizada` | Una app lleva más de 15 / 30 min fuera de `Healthy` / `Synced` | `kubectl get applications -n argocd` y la UI de ArgoCD |
| 🟡 `NodosSinMetricas` | Algún nodo no envía métricas | `kubectl -n monitoring get pods -o wide` (¿falta un `node-exporter`?) |
| 🟡 `SensoresTemperaturaSinDatos` | Se reciben métricas de un nodo, pero ninguna temperatura | Las alertas de temperatura de ese nodo no funcionarían: revisa `node-exporter` |

Además llegan las alertas estándar de Kubernetes y de los nodos que trae el chart (disco llenándose, memoria alta,
reloj sin sincronizar por NTP o Network Time Protocol, pods que se reinician sin parar o con réplicas de menos). Su
descripción aparece en el propio mensaje. Después del primer despliegue, la lista completa está en la pestaña
*Alerting* de Grafana.

Los mensajes llevan el nombre del nodo y un resumen, **sin direcciones IP**, porque el canal puede ser visto por más
personas. Una alerta crítica se repite cada 4 horas mientras siga activa; una de aviso, cada 12 horas.

## Silenciar una alerta

Para que una alerta deje de avisar un rato (por ejemplo durante un mantenimiento), crea un silencio en Alertmanager:

```bash
kubectl -n monitoring port-forward svc/vmalertmanager-vm-victoria-metrics-k8s-stack 9093:9093
```

Abre [`http://localhost:9093`](http://localhost:9093), pulsa **Silences → New Silence**, escribe `alertname` y el nombre de la
alerta (más `nodename` si es de un solo nodo) y elige la duración. Si el Service no se llama así, busca su nombre con
`kubectl -n monitoring get svc | grep alertmanager`. Un silencio nunca debe quedar sin fecha de fin.

## Si dejan de llegar alertas

El monitoreo vive dentro del clúster, así que un fallo grave podría dejarlo mudo. Por eso hay un **dead man's switch**: cada 5 minutos
Alertmanager envía un ping a [healthchecks.io](https://healthchecks.io/), y si deja de llegar, esa herramienta avisa por Discord en
`alertas-criticas` de que el check `homelab-monitoreo` (o el nombre que le hayas puesto) está caído. Cuando lo recibas:

1. Comprueba si el clúster responde: `kubectl get nodes`.
2. Si responde, mira los pods de monitoreo: `kubectl -n monitoring get pods`.
3. Si no responde, revisa `deborah` (control plane y DNS) y el acceso por llave de emergencia, porque el SSO por Dex también vive en el clúster.

## Lo que todavía no cubre

- La salud de los discos (SMART, el autodiagnóstico de los SSD) y el desgaste del almacenamiento de `deborah`.
- Las métricas propias de Incus (instancias y VMs).
- Silenciar alertas o consultar el estado desde Discord (hoy se hace con `kubectl` y la interfaz de Alertmanager).
