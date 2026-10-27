# Monitoreo y alertas

Qué se vigila en el HomeLab, dónde mirarlo y qué hacer cuando llega un aviso a Discord. Si eres quien lo **instala**,
ve a [4.13 — Monitoreo y alertas](../implementacion/fase-4-gitops.md#413-monitoreo-y-alertas-opcional).

!!! info "En una línea"
    Cada 60 segundos se leen las métricas de los tres nodos y de la plataforma. Si algo pasa de un umbral durante un rato,
    llega un mensaje a Discord: **🔴 críticas** en `alertas-criticas` (te llegan al móvil) y **🟡 avisos** en `alertas-avisos`.
    Cuando se resuelve, llega un **✅**.

**Esta decisión en otros entornos**

=== "🏠 En casa"

    VictoriaMetrics guarda las métricas, vmagent las recoge, vmalert evalúa las reglas, Alertmanager avisa a Discord y
    Grafana las muestra. Es **liviano a propósito**: lee cada 60 segundos y cabe en la poca memoria de tres nodos.

=== "🏢 En la empresa"

    - **Beneficios:** te enteras de un problema **antes que el usuario** y puedes medir si cumples lo prometido con
      [SLO](https://sre.google/sre-book/service-level-objectives/) (objetivos de nivel de servicio), en vez de
      discutir con sensaciones.
    - **Guardias (*on-call*):** las alertas no van a un canal de chat, sino a una herramienta que llama o escribe a
      quien está de turno y escala si nadie responde, como [PagerDuty](https://www.pagerduty.com/),
      [Grafana Cloud IRM](https://grafana.com/products/cloud/irm/) o
      [Jira Service Management](https://www.atlassian.com/software/jira/service-management) (Atlassian está
      migrando ahí a los clientes de Opsgenie).
    - **Retención y escala:** se guardan meses o años de métricas para comparar y planificar capacidad, con alta
      disponibilidad del propio monitoreo.
    - **Soporte comercial:** es común pagar [Grafana Cloud](https://grafana.com/products/cloud/) o
      [Grafana Enterprise](https://grafana.com/products/grafana-enterprise/), o una plataforma completa como
      [Datadog](https://www.datadoghq.com/), a cambio de no operar el monitoreo tú mismo.
    - **Cuándo lo del HomeLab sí conviene:** cuando quieres los datos en tu infraestructura, un costo predecible o
      monitorear sitios con poca conexión; el mismo stack open source escala bastante antes de necesitar otra cosa.

=== "☁️ En la nube"

    | Nube | Servicio equivalente |
    |---|---|
    | GCP | [Google Cloud Managed Service for Prometheus](https://docs.cloud.google.com/stackdriver/docs/managed-prometheus) |
    | AWS | [Amazon Managed Service for Prometheus](https://aws.amazon.com/prometheus/) + [Amazon Managed Grafana](https://aws.amazon.com/grafana/) |
    | Azure | [Azure Monitor managed service for Prometheus](https://learn.microsoft.com/en-us/azure/azure-monitor/metrics/prometheus-metrics-overview) + [Azure Managed Grafana](https://learn.microsoft.com/en-us/azure/managed-grafana/overview) |
    | Oracle Cloud (OCI) | [OCI Monitoring](https://docs.oracle.com/en-us/iaas/Content/Monitoring/home.htm) |

    Ganas almacenamiento y consultas administrados, con alta disponibilidad, escala y SLA, sin cuidar la base de
    métricas. Pierdes control sobre la configuración, pagas por métrica guardada y consultada, y quedas más atado a
    ese proveedor.

## Estado general: qué mirar primero

Si solo vas a mirar un dashboard, que sea **HomeLab / Estado general**: resume en una pantalla si el HomeLab está bien. Está pensado para
quien empieza: cada recuadro (*tile*) se pinta **verde** si todo está bien, **ámbar** si conviene mirarlo y **rojo** si hay que actuar, y
**cada uno enlaza al dashboard de detalle** de ese tema. Se lee de arriba abajo:

| Fila | Qué muestra |
|---|---|
| **Resumen** | Los tiles verde/ámbar/rojo de cada área: lo primero que miras |
| **Alertas activas** | Las alertas que están sonando ahora, con su gravedad |
| **Nodos** | CPU, memoria, disco y temperatura de cada nodo; parches de seguridad pendientes y si alguno pide reinicio |
| **Kubernetes** | Pods con problemas, reinicios recientes, workloads con menos réplicas de las pedidas y volúmenes (PVC) sin enlazar |
| **Almacenamiento (Longhorn)** | Estado de los volúmenes de Longhorn. Un volumen **desconectado** (*detached*, sin ninguna app usándolo) aparece como `unknown`: es normal, no es un fallo |
| **Plataforma** | ArgoCD (apps sanas y sincronizadas), certificados, sondas de las webs, errores 5xx de Kong e Incus |
| **IA y logs** | El router de Ollama (nodos vivos, peticiones) y la llegada de logs. Sus tiles muestran **«sin datos»** en color neutro hasta que despliegues el router y Vector: no es un error |

Las tablas de problemas (pods, workloads, alertas…) que aparecen **vacías, con el texto «Sin problemas»**, son lo esperado: significa
que no hay nada que atender. Un tile en rojo **enlaza a su dashboard de detalle**: haz clic en él para ver qué falla. Arriba, el menú
**Paneles del HomeLab** lleva a todos los dashboards de la etiqueta `homelab`.

Qué hacer si un tile se pone en rojo:

| Tile en rojo | Dónde seguir |
|---|---|
| Nodo caído o sin métricas | [Entrar por SSH](acceso-ssh.md) y la fila de alertas; si el nodo no vuelve, [Sacar o reemplazar un nodo](sacar-nodo.md) |
| Temperatura | Mira qué lo carga (`kubectl top pods -A`) y la ventilación; ver la tabla de alertas de abajo |
| Disco o DNS | [Salud de los discos y del DNS](salud-de-discos.md) |
| Parches o reinicio pendientes | [Parchear los nodos](parchear-nodos.md) |
| Pods o workloads con problemas | `kubectl get pods -A`, y el dashboard de detalle del tile |
| Longhorn degradado o fallido | La UI de Longhorn ([URLs y accesos](urls-y-accesos.md)) y [Agregar un disco](agregar-disco.md) si se llena |
| ArgoCD | `kubectl get applications -n argocd` y la UI de ArgoCD; para actualizarlo, [Actualizar ArgoCD](actualizar-argocd.md) |
| Certificados | `kubectl describe certificate -A`; si es una credencial vencida, [Rotar credenciales](rotar-credenciales.md) |
| Calico | [Calico (CNI) con ArgoCD](actualizar-calico.md) |
| Kong 5xx o webs inaccesibles | Los logs del servicio y de Kong, y [URLs y accesos](urls-y-accesos.md) |
| IA (router sin nodos) | [Asistente de IA local](ia-ollama.md) y [Agregar un nodo de Ollama](agregar-nodo-ollama.md) |
| Logs sin ingesta | [Logs centralizados y reportes con IA](logs.md) |

Es el **dashboard de inicio** de Grafana: lo fija el repo `gitops` (`default_home_dashboard_path` en
[`values-vm-stack.yaml`](https://github.com/maceosoft/gitops/blob/main/monitoring/values-vm-stack.yaml)), así que se abre al entrar.
Si quieres otro inicio solo para tu usuario, elígelo en *Profile → Preferences → Home Dashboard*.

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

Hay **13 dashboards** propios o de la comunidad (los de la etiqueta **`homelab`**), versionados como código en
[`monitoring/config/dashboards`](https://github.com/maceosoft/gitops/tree/main/monitoring/config/dashboards) del repo `gitops`: no se
editan a mano en Grafana. Los de grafana.com se guardan con la revisión fijada.

| Dashboard | Para qué sirve | Origen |
|---|---|---|
| **HomeLab / Estado general** | La pantalla de inicio: el resumen de [arriba](#estado-general-que-mirar-primero) | propio |
| **HomeLab / Temperaturas** | Temperatura de `deborah` y de los dos Intel, ahora y en 24 horas, con los umbrales de las alertas | propio |
| **HomeLab / Sealed Secrets** | El controlador de Sealed Secrets: descifrados, errores, CPU y memoria | propio (no hay ninguno en grafana.com) |
| **HomeLab / Logs** | Volumen de logs por nivel, errores por servicio y por nodo, reinicios ([Logs](logs.md)) | propio |
| **HomeLab / Ollama** | Router de Ollama: nodos con latido, peticiones en curso, errores 5xx, tokens y latencia por modelo y nodo ([IA local](ia-ollama.md)) | propio |
| **ArgoCD** | Sincronización y salud de las apps, operaciones de sync, uso del repo-server | grafana.com 14584 |
| **Kong (official)** | Peticiones, códigos HTTP y latencia por servicio y ruta | grafana.com 7424 |
| **Longhorn Example v1.1.0** | Volúmenes, réplicas, uso y salud de los discos | grafana.com 13032 |
| **Calico: Felix** | El agente de Calico en cada nodo: reglas aplicadas, tiempos y errores del dataplane | grafana.com 12175 |
| **Cert-manager-Kubernetes** | Certificados, su vencimiento y su estado | grafana.com 20842 |
| **Metallb** | Speakers de MetalLB, anuncios L2 y uso de los pools de IP | grafana.com 20162 |
| **Incus** | CPU, memoria, disco y red de cada proyecto e instancia (sin la fila de logs de Loki, que no se usa) | grafana.com 19727 |
| **GitHub Actions ARC - Runner Scale Set** | Runners de CI: en cola, ocupados, jobs y tiempos | grafana.com 25015 |

Además, el chart de VictoriaMetrics trae unos **41 dashboards** propios: *Node Exporter Full* (CPU, memoria, disco y red de cada nodo),
*Kubernetes / Views* (global, namespaces, pods, nodos), *Alertmanager / Overview* y los del propio VictoriaMetrics (single node,
vmagent, vmalert, operator), entre otros.

!!! tip "Si un panel sale vacío"
    Mira en *Explore* si existe la métrica base (por ejemplo `argocd_app_info`, `longhorn_volume_robustness`,
    `kong_http_requests_total` o `certmanager_certificate_expiration_timestamp_seconds`): puede faltar el scrape o que las etiquetas no
    coincidan. El de Longhorn está hecho para la versión 1.1 y con la actual algunos paneles salen vacíos. Los de IA y logs muestran «sin
    datos» hasta desplegar el router y Vector.

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
| 🟡 `KongLatenciaUpstreamAlta` / `KongLatenciaPropiaAlta` / `KongControladorConErrores` | Un servicio responde lento, Kong añade demasiada latencia o su controlador acumula errores | Dashboard *Kong (official)* y `kubectl -n kong logs deploy/kong-controller` |
| 🟡 `PlataformaMetricasCaidas` / `PlataformaComponenteSinReplicas` | Un componente de la plataforma dejó de publicar métricas o se quedó sin réplicas | `kubectl -n <namespace> get pods` del componente que nombra la alerta |
| 🟡 `ActualizacionK3sFallida` | Falló un job de actualización de K3s del SUC (*System Upgrade Controller*) | [Actualizar K3s](actualizar-k3s.md) |
| 🟡 `SondasSinDatos` | No llegan métricas de las sondas externas: la web podría estar rota sin que nada avise | `kubectl -n monitoring get pods` (blackbox-exporter) |
| 🟡 `RafagaDeErroresEnLogs` | Un namespace escribió más de 200 errores en 5 minutos | Dashboard *HomeLab / Logs*; consulta de ejemplo en [Logs](logs.md) |
| 🟡 `OOMKillerEnNodo` | El kernel mató procesos por falta de memoria | Logs del kernel del nodo ([Logs](logs.md)) y qué consume memoria (`kubectl top pods -A`); si es Ollama, baja su `MemoryMax` |
| 🟡 `LogsSinIngestaEnNodo` / `VectorCaido` | Vector no envía logs desde un nodo, o no se leen sus métricas | `kubectl -n monitoring get pods -o wide` (el pod de Vector de ese nodo) y [Logs](logs.md) |
| 🟡 `OllamaRouterCaido` / `OllamaRouterSinNodos` | El router de Ollama no responde, o no tiene ningún nodo con latido | `kubectl -n ai get pods` y [Asistente de IA local](ia-ollama.md); para los nodos, [Agregar un nodo de Ollama](agregar-nodo-ollama.md) |

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

=== "🖱️ Desde la interfaz"

    ```bash
    kubectl -n monitoring port-forward svc/vmalertmanager-vm-victoria-metrics-k8s-stack 9093:9093
    ```

    Abre [`http://localhost:9093`](http://localhost:9093), pulsa **Silences → New Silence**, escribe `alertname` y el nombre de la
    alerta (más `nodename` si es de un solo nodo) y elige la duración. Si el Service no se llama así, busca su nombre con
    `kubectl -n monitoring get svc | grep alertmanager`.

=== "⌨️ Desde la consola"

    La imagen de Alertmanager trae [`amtool`](https://github.com/prometheus/alertmanager#amtool), así que puedes crear el
    silencio desde dentro del pod, sin port-forward. Cambia el nombre de la alerta, el nodo y la duración:

    ```bash
    kubectl -n monitoring exec statefulset/vmalertmanager-vm-victoria-metrics-k8s-stack -c alertmanager -- \
      amtool silence add alertname=TemperaturaAlta nodename=oliver \
      --duration=2h --author=devops --comment="mantenimiento" \
      --alertmanager.url=http://localhost:9093
    ```

    Quita `nodename=…` si la alerta no es de un solo nodo. Con `amtool silence query` (mismos flags de conexión) ves los
    silencios activos y con `amtool silence expire <id>` terminas uno antes de tiempo. Si el StatefulSet no se llama así,
    búscalo con `kubectl -n monitoring get statefulset | grep alertmanager`.

Un silencio nunca debe quedar sin fecha de fin.

## Si dejan de llegar alertas

El monitoreo vive dentro del clúster, así que un fallo grave podría dejarlo mudo. Por eso hay un **dead man's switch**: cada 5 minutos
Alertmanager envía un ping a [healthchecks.io](https://healthchecks.io/), y si deja de llegar, esa herramienta avisa por Discord en
`alertas-criticas` de que el check `homelab-monitoreo` (o el nombre que le hayas puesto) está caído. Cuando lo recibas:

1. Comprueba si el clúster responde: `kubectl get nodes`.
2. Si responde, mira los pods de monitoreo: `kubectl -n monitoring get pods`.
3. Si no responde, revisa el nodo del control plane (hoy `deborah`, que además es el DNS) y el acceso por llave de emergencia, porque el SSO por Dex también vive en el clúster.

## Lo que todavía no cubre

- Qué hace cada login en Dex (solo publica telemetría gRPC), las entregas fallidas de las notificaciones de ArgoCD y el estado de los planes de actualización de K3s.
- OpenEBS, que no publica métricas útiles; solo lo cubren las alertas de réplicas.
- Silenciar alertas o consultar el estado desde Discord (hoy se hace con `kubectl` y la interfaz de Alertmanager).
