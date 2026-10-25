# Monitoreo y alertas

Qué se vigila en el HomeLab, dónde mirarlo y qué hacer cuando llega un aviso a Discord. Si eres quien lo **instala**,
ve a [4.13 — Monitoreo y alertas](../implementacion/fase-4-gitops.md#413-monitoreo-y-alertas-opcional).

!!! info "En una línea"
    Cada 30 segundos se leen las métricas de los tres nodos y de la plataforma. Si algo pasa de un umbral durante un rato,
    llega un mensaje a Discord: **🔴 críticas** en `alertas-criticas` (te llegan al móvil) y **🟡 avisos** en `alertas-avisos`.
    Cuando se resuelve, llega un **✅**.

## Ver las temperaturas y el uso

Entra a [`https://grafana.homelab.local`](https://grafana.homelab.local) (solo desde la red local) y pulsa
**Sign in with SSO (GitHub)**: es el mismo inicio de sesión que Argo CD, y solo entran los miembros del team `devops` de la
organización `maceosoft`, que reciben el rol **Admin**. Cualquier otra persona es rechazada. Los paneles de nodos y de Kubernetes
ya vienen cargados.

??? note "Si el SSO no funciona: entrar con el usuario local"
    El administrador local sigue activo como respaldo, porque el SSO depende de Dex, que vive en Argo CD, y de que el clúster
    resuelva el DNS. Entra con el usuario `admin` y la contraseña del item `grafana-admin` de 1Password (en el formulario de la
    misma pantalla, sin pulsar el botón SSO). Si el botón falla con *Failed to get token from provider*, mira el log de Grafana:
    `kubectl -n monitoring logs deploy/vm-grafana -c grafana | grep oauth`.

Para una consulta puntual usa *Explore* con estas expresiones:

| Qué | Consulta |
|---|---|
| Temperatura de cada nodo | `max by (nodename) (node_thermal_zone_temp)` |
| Memoria disponible (%) | `100 * node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes` |
| Disco raíz usado (%) | `100 * (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})` |
| Uso de CPU (%) | `100 * (1 - avg by (nodename) (rate(node_cpu_seconds_total{mode="idle"}[5m])))` |

## Paneles de Grafana

Los de la etiqueta **`homelab`** son los que se añadieron para esta plataforma; el resto vienen con el chart.

| Panel | Para qué sirve | Origen |
|---|---|---|
| **HomeLab / Temperaturas** | Temperatura de `deborah` y de los dos Intel, ahora y en 24 horas, con líneas en los umbrales de las alertas, y las alertas de temperatura activas | propio (`homelab`) |
| **ArgoCD** | Estado de sincronización y salud de las apps, operaciones de sync, uso del repo-server | grafana.com 14584 (`homelab`) |
| **Longhorn Example** | Volúmenes, réplicas, uso y salud de los discos | grafana.com 13032 (`homelab`) |
| **Cert-manager-Kubernetes** | Certificados, su vencimiento y su estado | grafana.com 20842 (`homelab`) |
| **Incus** | CPU, memoria, disco y red de cada proyecto e instancia de Incus (sin la fila de logs de Loki, que no se usa) | grafana.com 19727 (`homelab`) |
| **Node Exporter Full** | CPU, memoria, disco y red de cada nodo, y sensores de hardware | chart |
| **Kubernetes / Views** (Global, Namespaces, Pods, Nodes) | Uso de recursos del clúster | chart |
| **VictoriaMetrics** (single node, vmagent, vmalert, operator) y **Alertmanager** | Salud del propio monitoreo | chart |

!!! warning "Revísalos tras el primer despliegue"
    Los cinco de la etiqueta `homelab` se probaron cargándolos en un Grafana de la misma versión, pero **no contra las métricas reales de
    tu clúster**. Si un panel sale vacío, mira en *Explore* si existe la métrica base (por ejemplo `argocd_app_info`,
    `longhorn_volume_robustness` o `certmanager_certificate_expiration_timestamp_seconds`): puede faltar el scrape o que las etiquetas no
    coincidan. El de Longhorn es de 2020, hecho para la versión 1.1: con la 1.13 algunos paneles pueden salir vacíos.

!!! note "Kong: alertas sí, panel todavía no"
    El plugin `prometheus` de Kong ya está activo (códigos HTTP y latencia por servicio) y hay alertas de errores 5xx, pero no se ha generado
    el panel oficial de Kong (grafana.com 7424). Hay que revisar que sus consultas coincidan con las etiquetas reales antes de fijarlo.

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
| 🔴 `WebInaccesible` | ArgoCD, Dex o Grafana no responden `200` por su URL (lo que ve el usuario, aunque los pods estén bien) | Abre la URL; `kubectl -n kong get pods`, el Gateway y la ruta (`kubectl get httproute -A`) |
| 🟡 `RedirectHttpRoto` / `DnsInternoFalla` / `CertificadoWebPorVencer` | El `http://` no redirige a `https://`; un nombre no resuelve dentro del clúster (CoreDNS o BIND); el certificado de un Gateway vence pronto | Comprueba el Gateway, el BIND de `deborah` y los certificados (`kubectl describe certificate -A`) |
| 🔴/🟡 `KongErrores5xx` | Más del 5 % de las peticiones de un servicio devuelven 5xx (crítica si es ArgoCD, Grafana o Dex y pasa del 25 %) | Mira los logs del servicio y de Kong |
| 🟡 `KongConfiguracionNoSeAplica` / `KongRecursosInvalidos` | El controlador de Kong no logra aplicar una ruta o hay recursos rotos | `kubectl -n kong logs deploy/kong-controller` y el `HTTPRoute` afectado |
| 🔴 `CalicoNodoCaido` | Un nodo no tiene el pod de Calico: sus pods se quedan sin red | `kubectl -n calico-system get pods -o wide` |
| 🟡 Calico, MetalLB, Sealed Secrets, ARC y ArgoCD (`CalicoFelix…`, `MetalLB…`, `SealedSecretsError…`, `ARC…`, `ArgoCDApplicationSetConErrores`) | Un componente de la plataforma falla, queda sin réplicas o sin métricas | El nombre de la alerta dice cuál; `kubectl -n <namespace> get pods` y sus logs |
| 🔴/🟡 Discos y BIND (`DiscoSmartFalla`, `EmmcDesgastada`, `BindCaido`…) | SMART en fallo, SSD o eMMC desgastados, o el DNS de la LAN no responde | [Salud de los discos y del DNS](salud-de-discos.md) |
| 🟡 `ParchesDeSeguridadPendientes` | Un nodo lleva más de 3 días con parches de seguridad sin instalar | Sigue [Parchear los nodos](parchear-nodos.md) |
| 🟡 `ReinicioPendiente` | Una actualización ya instalada pide reiniciar el nodo, desde hace más de 7 días | Reinicia el nodo con el mismo procedimiento |
| 🟡 `ListasDePaquetesViejas` | Las listas de apt llevan más de 7 días sin actualizarse: los avisos de parches pueden no ser reales | Mira `systemctl status node-apt-metrics.timer` en el nodo |
| 🟡 `SinDatosDePaquetes` | `node-exporter` responde pero no publica los paquetes pendientes | Falta aplicar `playbook-apt-metrics.yml` en ese nodo |

Además llegan las alertas estándar de Kubernetes y de los nodos que trae el chart (disco llenándose, memoria alta,
reloj sin sincronizar por NTP o Network Time Protocol, pods que se reinician sin parar o con réplicas de menos). Su
descripción aparece en el propio mensaje. Después del primer despliegue, la lista completa está en la pestaña
*Alerting* de Grafana.

Los mensajes llevan el nombre del nodo y un resumen, **sin direcciones IP**, porque el canal puede ser visto por más
personas. Una alerta crítica se repite cada 4 horas mientras siga activa; una de aviso, cada 12 horas.

## Qué llega al canal de despliegues

Además de las alertas, ArgoCD escribe en tu canal `despliegues` cada vez que una app termina un sync correcto
([4.14](../implementacion/fase-4-gitops.md#414-notificaciones-de-argocd-a-discord-opcional)):

- **🚀 `<app>` desplegada**: con la revisión, el estado y las imágenes que usa la app. Si ArgoCD, Longhorn u otro producto se
  actualizó solo, la versión nueva aparece en esas imágenes (por ejemplo `quay.io/argoproj/argocd:v3.5.6`).
- **🟡 `<app>`: el sync falló**: llega a `alertas-avisos` con el mensaje de error. Mira `kubectl describe application -n argocd <app>`.

Esto es un **registro de lo que pasó**, no algo que atender: no hace falta responder a un 🚀.

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

- Los paneles de Kong, MetalLB y ARC de grafana.com (hay métricas y alertas, no panel).
- Qué hace cada login en Dex (solo publica telemetría gRPC), las entregas fallidas de las notificaciones de ArgoCD y el estado de los planes de actualización de K3s.
- OpenEBS, que no publica métricas útiles; solo lo cubren las alertas de réplicas.
- Silenciar alertas o consultar el estado desde Discord (hoy se hace con `kubectl` y la interfaz de Alertmanager).
