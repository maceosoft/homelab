# URLs y accesos de los productos

Dónde está cada herramienta del HomeLab, cómo se entra y con qué credenciales. Todas las direcciones `*.homelab.local` solo
resuelven **dentro de la LAN**, porque las sirve el DNS (sistema de nombres de dominio) del propio HomeLab: BIND en `deborah`, `192.168.20.5`.
Si tu equipo no usa ese DNS, agrega las entradas a tu archivo `hosts` (ver [Resumen del HomeLab](../implementacion/resumen-homelab.md)).

<div class="card">
  <div class="card-kicker">Accesos principales</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">Argo CD</div>
      <div class="text-muted">GitOps · inicio de sesión con GitHub</div>
      <div class="text-muted"><a href="https://argocd.homelab.local">argocd.homelab.local</a></div>
    </div>
    <div class="card-col">
      <div class="card-title">Incus UI</div>
      <div class="text-muted">Instancias, redes y balanceadores · SSO o TLS</div>
      <div class="text-muted"><a href="https://incus.homelab.local:8443/ui/">incus.homelab.local:8443</a></div>
    </div>
    <div class="card-col">
      <div class="card-title">Grafana <span class="tag">Opcional</span></div>
      <div class="text-muted">Temperaturas y uso de los nodos · SSO con GitHub</div>
      <div class="text-muted"><a href="https://grafana.homelab.local">grafana.homelab.local</a></div>
    </div>
    <div class="card-col">
      <div class="card-title">Longhorn <span class="tag">Por túnel</span></div>
      <div class="text-muted">Almacenamiento replicado · sin login</div>
      <div class="text-muted"><code>kubectl port-forward</code> → <code>127.0.0.1:8080</code></div>
    </div>
    <div class="card-col">
      <div class="card-title">Documentación</div>
      <div class="text-muted">Esta guía</div>
      <div class="text-muted"><a href="https://homelab.maceo.cl">homelab.maceo.cl</a></div>
    </div>
  </div>
</div>

## Catálogo

Todo lo que tiene una dirección, agrupado por para qué sirve y ordenado por prioridad dentro de cada grupo.

| Prioridad | Qué significa |
|---|---|
| ⭐ **Diaria** | La usas para operar el HomeLab con regularidad |
| 🔧 **Ocasional** | La abres cuando haces una tarea concreta |
| 🔍 **Diagnóstico** | Solo cuando algo falla o un panel sale vacío |

| Cómo se entra | Qué significa |
|---|---|
| 🌐 **Publicada** | Tiene nombre propio en el DNS y ruta en el Gateway: se abre con el navegador |
| 🔌 **Por túnel** | No está publicada: se abre con `kubectl port-forward` desde tu equipo ([ver comandos](#consolas-de-monitoreo)) |
| 💻 **Servidor** | Se usa con una herramienta de línea de comandos, no con navegador |

### 1. Gestión

Lo que usas para **operar y cambiar** el HomeLab.

| Prioridad | Producto | Dirección | Cómo se entra | Acceso | Para qué |
|---|---|---|---|---|---|
| ⭐ | **Argo CD** | [`https://argocd.homelab.local`](https://argocd.homelab.local) | 🌐 | SSO con GitHub (team `devops`) | Ver qué está desplegado, sincronizar y comparar con git |
| 🔧 | **Open WebUI** (asistente de IA) | [`https://open-webui.homelab.local`](https://open-webui.homelab.local) | 🌐 | SSO con GitHub (team `devops`) | Chat con el asistente local del HomeLab; un mensaje real puede despertar un nodo de Ollama ([guía](ia-ollama.md)) |
| ⭐ | **Incus UI** | [`https://incus.homelab.local:8443/ui/`](https://incus.homelab.local:8443/ui/) | 🌐 | SSO con GitHub o certificado TLS | Máquinas virtuales, contenedores, redes y balanceadores |
| ⭐ | **SSH a los servidores** | `ssh devops@<servidor>.homelab.local` (`invincible`, `oliver`, `deborah`) | 💻 | Identidad de GitHub con `opkssh` ([guía](acceso-ssh.md)) | Entrar a los nodos |
| ⭐ | **API de Kubernetes** | `https://192.168.20.5:6443` (`deborah`) | 💻 | `kubeconfig` | `kubectl` sobre el clúster |
| 🔧 | **Longhorn UI** | [`http://127.0.0.1:8080`](http://127.0.0.1:8080) | 🔌 | Sin login | Volúmenes, réplicas y discos del almacenamiento |
| 🔧 | **vCluster Platform** | [`https://vcluster.homelab.local`](https://vcluster.homelab.local) | 🌐 | SSO con GitHub | Clústeres virtuales. Se activa en la Fase 5; sin ella la URL responde 404 |

### 2. Observabilidad

Para **ver cómo está** el HomeLab y atender las alertas. La principal es Grafana; las demás son consolas técnicas de cada pieza.

| Prioridad | Producto | Dirección | Cómo se entra | Acceso | Para qué |
|---|---|---|---|---|---|
| ⭐ | **Grafana** | [`https://grafana.homelab.local`](https://grafana.homelab.local) | 🌐 | SSO con GitHub (team `devops`, rol Admin); respaldo: usuario `admin` del item `grafana-admin` | Paneles de nodos, temperaturas, Argo CD, Longhorn, Kong, Incus… ([qué mirar](monitoreo.md)) |
| 🔧 | **Alertmanager** | [`http://127.0.0.1:9093`](http://127.0.0.1:9093) | 🔌 | Sin login | Alertas activas y **silenciar** una un rato |
| 🔍 | **vmui** (en `vmsingle`) | [`http://127.0.0.1:8428/vmui/`](http://127.0.0.1:8428/vmui/) | 🔌 | Sin login | Consultar métricas; *Cardinality explorer* para ver qué ocupa más |
| 🔍 | **vmagent** | [`http://127.0.0.1:8429/targets`](http://127.0.0.1:8429/targets) | 🔌 | Sin login | Qué se recoge y cuáles fallan |
| 🔍 | **vmalert** | [`http://127.0.0.1:8880`](http://127.0.0.1:8880) | 🔌 | Sin login | Reglas de alerta y su último error |
| 🔍 | **blackbox-exporter** | [`http://127.0.0.1:9115`](http://127.0.0.1:9115) | 🔌 | Sin login | Resultado de las sondas externas |

### 3. Plataforma (sin interfaz que abras a diario)

Piezas de las que dependen las demás. Sirven para diagnosticar.

| Prioridad | Producto | Dirección | Cómo se entra | Acceso | Para qué |
|---|---|---|---|---|---|
| 🔍 | **Dex** (SSO) | [`https://argocd.homelab.local/api/dex`](https://argocd.homelab.local/api/dex/.well-known/openid-configuration) | 🌐 | Sin interfaz propia | Emisor OIDC: lo usan Argo CD, Incus UI, vCluster, Grafana y el SSH con `opkssh` |
| 🔍 | **Gateway** (Kong) | `192.168.23.200` | 💻 | — | Recibe el tráfico de `argocd`, `grafana`, `vcluster`, `api`, `open-webui` y `ollama` |
| 🔍 | **Ollama** (API de IA) | `https://ollama.homelab.local` | 💻 | Token Bearer (un token por cliente) | Router único de los nodos de Ollama; solo HTTPS. Dentro del clúster: `http://ollama-router.ai.svc`. La usan Open WebUI, K8sGPT, los reportes y la traducción ([guía](ia-ollama.md), [agregar un nodo](agregar-nodo-ollama.md)) |
| 🔍 | **DNS** (BIND) | `192.168.20.5` | 💻 | — | Zonas `homelab.local` y `mco.local` |

### 4. Documentación y código

| Prioridad | Qué | Dirección |
|---|---|---|
| 🔧 | **Documentación** | [`https://homelab.maceo.cl`](https://homelab.maceo.cl) (pública) |
| 🔧 | **Código** (Ansible, OpenTofu, documentación) | [`maceosoft/homelab`](https://github.com/maceosoft/homelab) |
| 🔧 | **Manifiestos GitOps** | [`maceosoft/gitops`](https://github.com/maceosoft/gitops) |
| 🔍 | **Pipelines reutilizables** | [`maceosoft/core-pipelines`](https://github.com/maceosoft/core-pipelines) |

!!! note "Cada nombre tiene su registro en BIND"
    La zona `homelab.local` apunta `argocd`, `vcluster`, `api`, `grafana`, `open-webui` y `ollama` a la IP del Gateway (`192.168.23.200`), `incus` al líder del clúster
    (`invincible`, `192.168.20.6`) y cada servidor (`invincible`, `oliver`, `deborah`) a su propia IP. No hay comodín: un nombre
    nuevo no resuelve hasta que se añade su registro. Solo tienen ruta en el Gateway Argo CD, Grafana, Open WebUI y Ollama; por eso `vcluster.homelab.local` resuelve pero responde 404.

!!! info "Si añades una interfaz nueva"
    Documéntala aquí en el mismo cambio: una fila en el grupo que corresponda (con su prioridad y cómo se entra) y, si no está publicada, su comando
    de túnel en [Consolas de monitoreo](#consolas-de-monitoreo) o en su propia sección.

## Argo CD

La interfaz de GitOps. Pide iniciar sesión con GitHub (Dex); solo entran los miembros del team `devops` de la organización `maceosoft`.

??? note "Ver captura: inicio de sesión de Argo CD"
    ![Pantalla de inicio de sesión de Argo CD con el botón «Log in via GitHub»](../assets/screenshots/argocd-login.jpg){ loading=lazy }

Dentro, la aplicación raíz `homelab-root` agrupa todas las demás (vista de árbol):

??? note "Ver captura: árbol de homelab-root"
    ![Árbol de la aplicación homelab-root en Argo CD, con las aplicaciones arc-controller, arc-runners, argocd y argocd-route sincronizadas y sanas](../assets/screenshots/argocd-homelab-root.jpg){ loading=lazy }

Más sobre el catálogo y los problemas frecuentes: [GitOps — catálogo y troubleshooting](../gitops/index.md).

## Incus UI

La interfaz web del clúster de Incus. Está en el nodo `invincible` (el líder), puerto `8443`; cada nodo expone además su propia API en
ese puerto. Ofrece dos formas de entrar:

??? note "Ver captura: acceso a Incus UI"
    ![Pantalla de acceso de Incus UI con las opciones «Login with SSO» y «Login with TLS»](../assets/screenshots/incus-ui-login.jpg){ loading=lazy }

- **Login with SSO:** GitHub a través de Dex (OIDC, estándar de inicio de sesión). Ver [Clúster Incus — OIDC vía Dex](../incus/cluster-setup.md#oidc-via-dex-fase-4).
- **Login with TLS:** con un certificado de cliente instalado en el navegador.

Los balanceadores de red están en **Networks → `ovn-lan` → pestaña «Load balancers»** (ver [Balanceo de carga y OVN](../incus/cluster-setup.md#balanceo-de-carga-y-ovn)).

## Longhorn UI

El almacenamiento replicado tiene su propio panel, **sin pantalla de login y sin ruta en el Gateway**: es un Service interno. Se abre con un
túnel temporal desde tu equipo:

```bash
export KUBECONFIG=~/.kube/homelab-k3s.yaml
kubectl -n longhorn-system port-forward svc/longhorn-frontend 8080:80
# y abre http://127.0.0.1:8080  (Ctrl+C para cerrar el túnel)
```

??? note "Ver captura: panel de Longhorn"
    ![Panel de Longhorn v1.13.0 con 1 volumen, 471 Gi de almacenamiento programable y 3 nodos](../assets/screenshots/longhorn-dashboard.jpg){ loading=lazy }

Más sobre las clases de almacenamiento: [Storage](../storage/index.md#actualizar-y-reinstalar-longhorn).

## Consolas de monitoreo

La interfaz principal del monitoreo es [Grafana](https://grafana.homelab.local) (con SSO). Debajo hay consolas más técnicas de cada
pieza, útiles para diagnosticar. **No tienen login ni ruta en el Gateway**: son Services internos del namespace `monitoring`, y por eso se
abren con un túnel temporal desde tu equipo (cada comando deja la consola en `127.0.0.1`; `Ctrl+C` cierra el túnel):

```bash
export KUBECONFIG=~/.kube/homelab-k3s.yaml
# vmui
kubectl -n monitoring port-forward svc/vmsingle-vm-victoria-metrics-k8s-stack 8428:8428
# vmagent
kubectl -n monitoring port-forward svc/vmagent-vm-victoria-metrics-k8s-stack 8429:8429
# vmalert
kubectl -n monitoring port-forward svc/vmalert-vm-victoria-metrics-k8s-stack 8880:8080
# Alertmanager
kubectl -n monitoring port-forward svc/vmalertmanager-vm-victoria-metrics-k8s-stack 9093:9093
# blackbox-exporter
kubectl -n monitoring port-forward svc/blackbox-exporter 9115:9115
```

Cada uno necesita su propia terminal, y el puerto de `vmalert` es `8880` para no chocar con el `8080` de Longhorn.

| Consola | Dirección | Para qué sirve |
|---|---|---|
| **vmui** (VictoriaMetrics) | `http://127.0.0.1:8428/vmui/` | Consultar y graficar métricas sin Grafana. La pestaña **Cardinality explorer** muestra qué métricas ocupan más (útil para recortar), y **Top queries** las consultas más lentas |
| **vmagent** | `http://127.0.0.1:8429/targets` | Qué se está recogiendo, cuáles fallan y con qué error. Es lo primero que se mira cuando un panel sale vacío |
| **vmalert** | `http://127.0.0.1:8880` | Las reglas de alerta, su estado (`firing`, `pending`) y el último error de evaluación |
| **Alertmanager** | `http://127.0.0.1:9093` | Alertas activas, silencios (para callar una alerta un rato) y la configuración de rutas a Discord |
| **blackbox-exporter** | `http://127.0.0.1:9115` | Resultado de las sondas externas (Argo CD, Dex, Grafana, redirecciones y DNS) y sus módulos |

!!! warning "Por qué no están publicadas"
    Ninguna de estas consolas pide usuario: quien llegue a la dirección podría ver todas las métricas o crear silencios en Alertmanager. Grafana y
    Argo CD sí tienen SSO. Si algún día se publican, hay que ponerles delante autenticación (por ejemplo, un proxy con Dex) y un registro en BIND
    ([cada nombre tiene el suyo](#catalogo)).

Qué se vigila y qué hacer ante cada aviso: [Monitoreo y alertas](monitoreo.md).

## vCluster Platform

Su dirección es [`https://vcluster.homelab.local`](https://vcluster.homelab.local), pero **no se despliega por defecto**: su Application está comentada en
`gitops/bootstrap/root-appset.yaml` y no hay `HTTPRoute`, así que hasta activarla en la [Fase 5](../implementacion/fase-5-vcluster.md) la URL responde 404.

## Sin interfaz propia

Estas piezas no tienen UI; se revisan con `kubectl` o con Argo CD:

| Producto | Cómo mirarlo |
|---|---|
| **MetalLB** (IP de los `LoadBalancer`) | `kubectl get ipaddresspool,l2advertisement -n metallb-system`; pool `192.168.23.200–.220` |
| **Calico** (red de los pods) | `kubectl get tigerastatus` y `kubectl get installation default` |
| **Kong** (Gateway) | `kubectl get gateway,httproute -A` |
| **cert-manager** (certificados) | `kubectl get clusterissuer,certificate -A` |
| **OVN** (red virtual de Incus) | `incus network list` y `ovn-nbctl lb-list` en un nodo |
| **ARC** (runners de GitHub Actions) | `kubectl get pods -n arc-runners` |

## Otros enlaces

Los repositorios están en el [catálogo](#4-documentacion-y-codigo). Además:

| Qué | Dónde |
|---|---|
| Documentación completa en texto plano (para IA) | [`llms-full.txt`](https://homelab.maceo.cl/llms-full.txt) |
| Cuaderno de estudio con IA | [Aprende con IA](../aprende.md) |

## Comprobar que responden

```bash
for u in https://argocd.homelab.local/ https://grafana.homelab.local/api/health https://incus.homelab.local:8443/ui/; do
  echo "$u -> $(curl -sk -o /dev/null -w '%{http_code}' --max-time 6 $u)"
done
# debe dar 192.168.23.200
dig @192.168.20.5 argocd.homelab.local +short
```

Si una URL no abre, empieza por el DNS (`dig`) y por el Gateway (`curl -k https://192.168.23.200`); la tabla de
[resolución de problemas de GitOps](../gitops/index.md#resolucion-de-problemas-rapida) cubre los casos más comunes.
