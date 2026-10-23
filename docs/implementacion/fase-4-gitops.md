# Fase 4 — GitOps

## Objetivo

Desplegar la plataforma completa vía **Argo CD** desde
[`gitops/`](https://github.com/symintel/gitops): storage, MetalLB, Gateway API, Dex +
GitHub OAuth, y waves de operaciones.

## Qué aprendes

**GitOps**: el clúster converge al estado declarado en Git; un solo
`kubectl apply` (ApplicationSet `homelab-root`) y Argo CD sincroniza el resto. Separación clara:
Ansible bootstrap vs GitOps continuo.

!!! abstract "Aprende esta fase"
    **En simple:** Git es la receta aprobada y Argo CD es el chef que compara la cocina con la receta
    y corrige cualquier diferencia. Si alguien cambia algo a mano en el clúster, Argo CD lo deja
    como dice Git. El equipo no "ejecuta comandos": cambia la receta.

    **Conceptos clave**

    - **GitOps:** el repositorio es la fuente de verdad; el clúster converge a lo que dice.
    - **Application y sync:** Argo CD vigila una carpeta de Git y la aplica; "Synced" significa que coinciden.
    - **Drift y self-heal:** drift es la diferencia entre Git y el clúster; el self-heal la corrige solo.
    - **Olas (sync-waves):** el orden de despliegue; la base (red, certificados) va antes que las aplicaciones.
    - **Secretos fuera de Git:** las claves viven en 1Password y se entregan al clúster sin subirlas al repositorio.
    - **Gateway y TLS (Transport Layer Security):** la puerta de entrada HTTPS y el certificado que la protege.

    **Reto práctico (solo lectura):** compara el estado del clúster con lo que declara Git.

    ```bash
    kubectl -n argocd get applications
    kubectl get gateway homelab -n gateway
    ```

    Abre `gateway/kong/gateway.yaml` en el repositorio `gitops` y busca los mismos puertos y el
    nombre `homelab` que ves en el clúster.

    ??? question "¿Qué significa que una Application esté Synced y Healthy?"
        Synced: lo que hay en el clúster coincide con Git. Healthy: los recursos funcionan.

    ??? question "¿Por qué los secretos no se guardan en Git?"
        Porque cualquiera con acceso al repositorio los vería, y el historial de Git conserva todo lo que se subió.

    ??? question "¿Qué hace el self-heal si alguien cambia algo a mano?"
        Detecta la diferencia con Git y vuelve a aplicar lo declarado.

    ¿Dudas? Usa el botón **Aprende con IA** junto a cada título, o la página [Aprende](../aprende.md).

## Stack de esta fase

```mermaid
flowchart LR
  subgraph wave0 [Wave_0]
    GA[Gateway_API_CRDs]
    CM[cert_manager]
    SS[Sealed_Secrets]
    OB[OpenEBS]
    SC[StorageClasses]
    ML[MetalLB]
  end
  subgraph wave1 [Wave_1]
    MLC[MetalLB_config]
    CMC[CA_del_HomeLab]
    GW[Gateway_Kong]
    LH[Longhorn]
  end
  subgraph wave2 [Wave_2]
    AR[ArgoCD_HTTPRoute]
    ACFG[ArgoCD_Dex]
  end
  subgraph wave3 [Wave_3]
    UPG[K3s_upgrade]
  end
  subgraph manual [Manual]
    VC[vCluster]
    CAPN[CAPN_demo]
  end
  root[root_app] --> wave0 --> wave1 --> wave2 --> wave3
  wave2 -.-> manual
```

- **[Argo CD](https://argo-cd.readthedocs.io/)** — GitOps; toda la fase.
- **[MetalLB](https://metallb.universe.tf/)** — LoadBalancer LAN (red local); wave 0–1.
- **[Gateway API](https://gateway-api.sigs.k8s.io/)** — API estándar de Kubernetes para publicar servicios HTTP(S) (reemplaza a `Ingress`); sus CRDs van en wave 0.
- **[Kong Ingress Controller](https://developer.konghq.com/kubernetes-ingress-controller/)** (KIC) — controlador de Gateway API predeterminado; wave 1. Alternativas: [Traefik](https://doc.traefik.io/traefik/routing/providers/kubernetes-gateway/) y [NGINX Gateway Fabric](https://docs.nginx.com/nginx-gateway-fabric/).
- **[cert-manager](https://cert-manager.io/docs/)** — emite los certificados TLS con una CA (autoridad certificadora) propia del HomeLab; waves 0–1.
- **[OpenEBS](https://openebs.io/docs)** / **[Longhorn](https://longhorn.io/docs/)** — Storage; waves 0–1.
- **[Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)** — Secretos en git; wave 0.
- **[Dex](https://dexidp.io/docs/)** + **[GitHub](https://docs.github.com/en/apps/oauth-apps)** — SSO (inicio de sesión único); wave 2.
- **[1Password Python SDK](https://github.com/1Password/onepassword-sdk-python)** — OAuth fuera de git; paso 4.7 (app local, DesktopAuth).
- **[system-upgrade-controller](https://github.com/rancher/system-upgrade-controller)** — Upgrades K3s (distribución ligera de Kubernetes); wave 3.

!!! note "Por qué Gateway API y no Ingress"
    El proyecto Ingress NGINX se archivó en marzo de 2026 y `Ingress` está
    congelado en Kubernetes. El HomeLab publica todo con `Gateway` y
    `HTTPRoute`. Se activa **un solo** controlador a la vez (Kong, Traefik o
    NGINX Gateway Fabric): ver [Cambiar el controlador de Gateway](../operacion/cambiar-gateway.md).

Profundización: [Catálogo GitOps](../gitops/index.md) · [Storage](../storage/index.md) · [Secretos](../secrets/index.md)

## Antes de empezar

- [ ] [Fase 3 — K3s](fase-3-k3s.md) completada (`argocd-server` Running).
- [ ] `kubectl` configurado en tu estación.
- [ ] [Fase 0 — GitHub y 1Password](fase-0-preparacion.md#github-y-1password-org-symintel-manual-una-sola-vez)
      completado (Apps, repos e items de 1Password).
- [ ] En el router, el rango **`192.168.23.200–192.168.23.220`** fuera del
      DHCP (reservado): es el pool de MetalLB para los servicios
      `LoadBalancer`, como el Gateway ([esquema de IPs](../networking/index.md#esquema-de-ips)).

---

## 4.1 — Acceso kubectl

Copia a tu estación el kubeconfig del control plane (`deborah`), como
`~/.kube/homelab-k3s.yaml`: es el archivo que usan los playbooks y los
procedimientos de esta guía. Si en la Fase 3 corriste `playbook-k3s.yml`
completo, ya lo tienes (`k3s_install.fetch_kubeconfig.enabled: true`).

=== "Recomendado (Ansible)"

    ```bash
    cd ansible
    ansible-playbook -i inventory.ini playbook-k3s.yml --tags kubeconfig
    cd ..
    ```

    El rol `k3s_fetch_kubeconfig` lee `/etc/rancher/k3s/k3s.yaml` en
    `deborah`, cambia la dirección del API (Application Programming
    Interface) por la IP real del control plane (o la VIP si usas kube-vip)
    y lo guarda en `~/.kube/homelab-k3s.yaml` con permisos `0600`.

=== "Alternativa manual"

    El archivo en el nodo es de root con permisos `600`, así que se lee con
    `sudo`; después se cambia `127.0.0.1` por la IP del control plane. `<usuario-admin>` es tu usuario
    administrador del nodo ([Fase 0, Día 0](fase-0-preparacion.md#dia-0-nodos-recien-instalados-solo-la-primera-vez-por-nodo)):
    aquí todavía no existe el acceso por SSO ([4.12](#412-ssh-a-los-hosts-con-dex-opcional)), que necesita a Dex.

    ```bash
    mkdir -p ~/.kube
    ssh <usuario-admin>@192.168.20.5 sudo cat /etc/rancher/k3s/k3s.yaml \
      | sed 's#https://127.0.0.1:6443#https://192.168.20.5:6443#' \
      > ~/.kube/homelab-k3s.yaml
    chmod 600 ~/.kube/homelab-k3s.yaml
    ```

Úsalo y comprueba el acceso:

```bash
export KUBECONFIG=~/.kube/homelab-k3s.yaml
kubectl get nodes
```

!!! tip "Alternativa web (Fase 5)"
    Tras desplegar [vCluster Platform](fase-5-vcluster.md), puedes descargar
    el kubeconfig del **management K3s** desde
    [`https://vcluster.homelab.local`](https://vcluster.homelab.local) (connected cluster), con SSO GitHub vía Dex.
    El kubeconfig local de arriba sigue siendo el camino para el bootstrap, antes de la Fase 5.

<div class="card">
  <div class="card-kicker">Acceso kubectl</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">Kubeconfig local (Ansible o manual)</div>
      <div class="text-muted">Funciona antes del Gateway y vCluster</div>
      <div class="text-muted">Archivo en disco; rotación manual</div>
    </div>
    <div class="card-col">
      <div class="card-title">vCluster Platform (Fase 5)</div>
      <div class="text-muted">Kubeconfig vía SSO; connected cluster</div>
      <div class="text-muted">Requiere Fase 4+5 y permisos asignados</div>
    </div>
  </div>
</div>

---

## 4.2 — Bootstrap GitOps (ApplicationSet)

Un único apply manual; a partir de aquí Argo CD gestiona el resto (auto).

**Primero, los secretos de plataforma.** `symintel/gitops` es privado: sin
las credenciales de la App `symintel-argocd`, ArgoCD no puede leer el repo. El playbook los lee de
1Password y los deja en el clúster. Igual que en la Fase 0, la app de
1Password tiene que estar desbloqueada y `ONEPASSWORD_ACCOUNT_NAME` con el
nombre de tu cuenta (el de la barra lateral de la app).

```bash
export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"  # tu cuenta
cd ansible
ansible-playbook -i inventory.ini playbook-platform-secrets.yml
cd ..
```

| Secret | Namespace | Para qué |
|---|---|---|
| `repo-gitops` | `argocd` | App `symintel-argocd` para `https://github.com/symintel/gitops.git` |
| `arc-runners-github-app` | `arc-runners` | Registro del runner de ARC |
| `symintel-terraform-app`, `tofu-vars` | `arc-runners` | Credenciales de OpenTofu (`TF_VAR_*`) para el pipeline |

También crea el namespace `terraform`, donde OpenTofu guarda su state. Usa
siempre `~/.kube/homelab-k3s.yaml`, no el contexto actual de `kubectl`. Es
idempotente: re-córrelo cuando rotes algo en 1Password. Detalle:
[Plataforma symintel — GitHub](../symintel/github.md#paso-3-cluster-y-secretos-de-plataforma).

**Después, el ApplicationSet de bootstrap:**

```bash
kubectl apply -f gitops/bootstrap/root-appset.yaml
```

[`bootstrap/root-appset.yaml`](https://github.com/symintel/gitops/blob/main/bootstrap/root-appset.yaml)
genera una Application raíz, `homelab-root`, con las apps que están
**descomentadas** en su lista `apps`. Al principio solo está `argocd` (ArgoCD administrándose a sí mismo)
(Dex, RBAC y el health check que necesitan las olas), para ir probando cada
componente de a uno:

1. Descomenta la siguiente app de la lista (van en orden de ola) y haz push
   al repo `gitops`.
2. **Vuelve a aplicar el ApplicationSet**: ArgoCD no lo gestiona (lo creaste
   tú con `kubectl`), así que el push solo no cambia la lista:

    ```bash
    kubectl apply -f gitops/bootstrap/root-appset.yaml
    ```

3. ArgoCD la despliega; espera a que quede `Healthy`
   (`kubectl get applications -n argocd`).
4. Sigue con la próxima.

**Olas:** como todas las apps se sincronizan juntas en `homelab-root`, ArgoCD
respeta su anotación `argocd.argoproj.io/sync-wave` y despliega por olas
(-1 → 0 → 1 → 2 → 3), esperando a que cada una esté `Healthy` antes de la
siguiente. Las secciones 4.3 a 4.9 siguen ese orden.

Para desactivar una app, vuelve a comentarla: `homelab-root` borra su
Application (los recursos que creó quedan en el clúster).

**Verificar:**

```bash
kubectl get applications -n argocd
```

UI (interfaz de usuario) provisional (sin Gateway aún; `argocd-server` habla HTTP, abre [`http://localhost:8080`](http://localhost:8080)):

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:80
kubectl get secret argocd-initial-admin-secret -n argocd \
  -o jsonpath='{.data.password}' | base64 -d; echo
```

---

## 4.3 — Wave 0: secretos + storage + MetalLB controller

Espera `Healthy` en: `gateway-api`, `cert-manager`, `sealed-secrets`, `openebs`, `homelab-storage`, `metallb`.

| Application | Producto | Para qué sirve |
|---|---|---|
| `gateway-api` | [Gateway API](https://gateway-api.sigs.k8s.io/) | CRDs (Custom Resource Definition) `Gateway`, `HTTPRoute`, etc., canal standard |
| `cert-manager` | [cert-manager](https://cert-manager.io/docs/) | Emite certificados; crea el de cada Gateway con la anotación `cert-manager.io/cluster-issuer` |
| `sealed-secrets` | [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) | Descifra `SealedSecret` en el clúster; usa la llave de 1Password (item `sealed-secrets`) si el playbook de secretos ya la creó |
| `openebs` | [OpenEBS](https://openebs.io/docs) | LocalPV default |
| `homelab-storage` | — | StorageClasses `openebs-hostpath` y `longhorn-mixto` ([cuál usar y sus trade-offs](../storage/index.md#storageclasses-del-cluster)) |
| `metallb` | [MetalLB](https://metallb.universe.tf/) | Controller LoadBalancer |

**Verificar:**

```bash
kubectl get storageclass
kubectl get pods -n metallb-system
kubectl get pods -n openebs
```

---

## 4.4 — Wave 1: pool MetalLB + Gateway + Longhorn

Espera `Healthy` en: `metallb-config`, `cert-manager-config`, `kong` y `longhorn`.

| Application | Producto | Para qué sirve |
|---|---|---|
| `metallb-config` | [MetalLB](https://metallb.universe.tf/) | Pool L2 `192.168.23.200–.220` |
| `cert-manager-config` | [cert-manager](https://cert-manager.io/docs/) | CA propia del HomeLab (`ClusterIssuer homelab-ca`) |
| `kong` | [Kong Ingress Controller](https://developer.konghq.com/kubernetes-ingress-controller/) | Controlador de Gateway API y `Gateway homelab` (HTTP 80 y HTTPS 443, `*.homelab.local`) |
| `longhorn` | [Longhorn](https://longhorn.io/docs/) | Storage replicado HA |

```bash
kubectl get gateway homelab -n gateway
# ADDRESS en rango 192.168.23.200–.220 y PROGRAMMED=True
```

**Verificar:**

```bash
kubectl get ipaddresspool -n metallb-system
kubectl get pods -n longhorn-system
```

---

## 4.5 — Wave 2: ArgoCD en LAN + Dex

Espera `Healthy` en `argocd-route` y `argocd`.

| Recurso | Producto | Para qué sirve |
|---|---|---|
| `argocd-route` | [Gateway API](https://gateway-api.sigs.k8s.io/) | `HTTPRoute` hacia `https://argocd.homelab.local` (el Gateway termina el TLS; `argocd-server` queda en HTTP con `server.insecure`) |
| `argocd` | [ArgoCD](https://argo-cd.readthedocs.io/) y [Dex](https://dexidp.io/docs/) | ArgoCD se actualiza solo (tag `stable`); suma el connector GitHub, los staticClients de vCluster e Incus UI, el RBAC y el health check de Application ([Actualizar ArgoCD](../operacion/actualizar-argocd.md)) |

---

## 4.6 — kube-vip vs MetalLB

| | [kube-vip](https://kube-vip.io/) | [MetalLB](https://metallb.universe.tf/) |
|---|---|---|
| **Quién lo instala** | Ansible (Fase 3) | Argo CD (Fase 4) |
| **Qué VIPea** | Solo API `:6443` | Services `LoadBalancer` |
| **Config clave** | `svc_enable=false` | Pool `192.168.23.200–.220` |

No uses kube-vip para Services de aplicación.

### Análisis de trade-offs — kube-vip vs MetalLB

| Alternativa | Ventaja | Coste / riesgo |
|---|---|---|
| kube-vip (Fase 3) | VIP fija solo para API `:6443` | No expone Gateways ni Services LB |
| MetalLB (Fase 4) | `LoadBalancer` para el Gateway y apps | Pool L2 `192.168.23.200–.220` debe estar libre en LAN |
| Ambos (default HomeLab) | Responsabilidades separadas | Dos mecanismos VIP distintos — no mezclar roles |

---

## 4.7 — Secretos OAuth (GitHub + vCluster + Incus UI)

Los valores sensibles **no van en git**. Guárdalos en 1Password e inyecta
`argocd-secret`.

!!! note "OAuth App ya creada en la Fase 0"
    Si seguiste la [Fase 0](fase-0-preparacion.md#github-y-1password-org-symintel-manual-una-sola-vez),
    la OAuth App `Symintel Dex` y sus campos `GITHUB_*` ya existen: solo
    falta correr el playbook de más abajo.

**GitHub OAuth App** en la **org `symintel`** ([symintel → Settings → Developer settings → OAuth Apps → New OAuth App](https://github.com/organizations/symintel/settings/applications/new)).
Creada en la org, Dex puede leer sus teams sin aprobarla como app de terceros:

| Campo GitHub | Valor |
|---|---|
| Application name | `Symintel Dex` (o similar) |
| Homepage URL | `https://argocd.homelab.local` |
| Redirect URIs | `https://argocd.homelab.local/api/dex/callback` (solo esta) |

**Homepage URL** es informativa; el campo crítico es **Redirect URIs** (en versiones anteriores de GitHub se llamaba *Authorization callback URL*): tiene que ser exactamente la URL de arriba.

Ítems 1Password (cuenta **personal**, bóveda **`HomeLab`** por defecto): ver
[`argocd/secrets/1password.md`](https://github.com/symintel/gitops/blob/main/argocd/secrets/1password.md).

Probar lectura (mismo módulo que el apply):

```bash
export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"   # tu cuenta personal
export ONEPASSWORD_VAULT="HomeLab"             # o HomeLab
python3 ansible/scripts/test-1password.py GITHUB_CLIENT_ID
```

Inyectar en el clúster (recomendado — Ansible):

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-dex-oauth-secrets.yml
```

El campo `VCLUSTER_CLIENT_SECRET` se genera en
1Password automáticamente si no existe. Crea antes en 1Password (manual)
`GITHUB_CLIENT_ID` y `GITHUB_CLIENT_SECRET` desde la OAuth App de GitHub.

Alternativa script Python:

```bash
pip install onepassword-sdk
python3 gitops/argocd/secrets/apply-from-1password.py.example
kubectl rollout restart deployment argocd-dex-server -n argocd
```

Connector **GitHub** (solo el team `devops` de la org `symintel`) y staticClients **vCluster** e **Incus UI**
en [`dex.config`](https://github.com/symintel/gitops/blob/main/argocd/config/dex.config).

`VCLUSTER_CLIENT_SECRET` **no** viene de GitHub.
Ansible lo genera en 1Password si falta y lo aplica según destino. Incus **no usa secreto**:
es un cliente OIDC público (PKCE) en Dex.

| Campo | Destinos (tags Ansible) |
|---|---|
| `VCLUSTER_CLIENT_SECRET` | `argocd-secret` (`argocd`) + Helm Platform (`vcluster`) |

### Probar el login: URLs y qué esperar

Primero comprueba que las cuatro claves llegaron a `argocd-secret` y que Dex se reinició:

```bash
kubectl -n argocd get secret argocd-secret -o jsonpath='{.data}' | python3 -c "import sys,json;print(list(json.load(sys.stdin)))"
kubectl -n argocd get pods -l app.kubernetes.io/name=argocd-dex-server
```

Tienen que aparecer `dex.github.clientId`, `dex.github.clientSecret` y
`dex.vcluster.platform.clientSecret`. Las URLs necesitan el [DNS de `*.homelab.local`](#48-dns-de-homelablocal)
(o `/etc/hosts`); el certificado lo firma la CA del HomeLab, así que el navegador avisa hasta que la
importes (y `curl` necesita `-k`).

| Qué probar | URL | Qué debes ver |
|---|---|---|
| **ArgoCD** (UI) | [`https://argocd.homelab.local`](https://argocd.homelab.local) | Pantalla de login con el botón **Log in via GitHub**. Al pulsarlo pasa por GitHub y vuelve a ArgoCD con las Applications |
| ArgoCD (HTTP) | [`http://argocd.homelab.local`](http://argocd.homelab.local) | Redirige (`301`) a la versión HTTPS |
| ArgoCD (API) | [`https://argocd.homelab.local/api/version`](https://argocd.homelab.local/api/version) | `{"Version":"v3.x.x"}`: el servidor responde a través del Gateway |
| **Dex** (descubrimiento) | [`https://argocd.homelab.local/api/dex/.well-known/openid-configuration`](https://argocd.homelab.local/api/dex/.well-known/openid-configuration) | JSON con `"issuer": "https://argocd.homelab.local/api/dex"` |
| Dex (callback) | `https://argocd.homelab.local/api/dex/callback` | **No se abre a mano.** Es la URL que tiene que estar en *Redirect URIs* de la OAuth App de GitHub |
| **vCluster Platform** | [`https://vcluster.homelab.local`](https://vcluster.homelab.local) | Login SSO con GitHub (Fase 5; antes no existe) |
| **Incus UI** | [`https://incus.homelab.local:8443`](https://incus.homelab.local:8443) | **Login with SSO** → GitHub (ver más abajo) |

Desde la terminal:

```bash
curl -sk https://argocd.homelab.local/api/version
curl -sk https://argocd.homelab.local/api/dex/.well-known/openid-configuration
curl -s -o /dev/null -w "%{http_code} -> %{redirect_url}\n" http://argocd.homelab.local/
```

| Si ves… | Causa | Qué hacer |
|---|---|---|
| GitHub responde **404** y la URL trae `client_id=.github.clientId` | Faltan las claves `dex.*` en `argocd-secret`: Dex no pudo sustituir `$dex.github.clientId` | Corre el playbook de arriba (`--tags argocd`) y vuelve a probar |
| GitHub dice **redirect_uri mismatch** | *Redirect URIs* de la OAuth App distinto | Debe ser exactamente `https://argocd.homelab.local/api/dex/callback` |
| El login termina bien pero ArgoCD **no muestra Applications** | Tu cuenta no está en el team `devops` de `symintel` | Agrégala al team; el claim `groups` es `symintel:devops` |
| `invalid_client` o `bad credentials` | `GITHUB_CLIENT_SECRET` incorrecto o rotado | Actualiza el campo en 1Password y vuelve a correr el playbook |

### Incus UI OIDC

Requisitos: UI instalada en [Fase 2](fase-2-incus.md#ui-de-administracion),
`argocd` Healthy, secretos inyectados y Dex reiniciado.

Incus (7.x) solo conoce cinco claves OIDC: `oidc.issuer`, `oidc.client.id`, `oidc.audience`,
`oidc.claim` y `oidc.scopes`. **No** tiene `oidc.client.secret`, ni `oidc.groups.claim`, ni el
comando `incus auth` (esas son de LXD). Por eso en Dex el cliente `incus-ui` es **público**
(`public: true`, PKCE, sin secreto): está en [`dex.config`](https://github.com/symintel/gitops/blob/main/argocd/config/dex.config).

**Ansible** (recomendado) — `group_vars/dex_oauth_secrets.yml` ya trae `apply_incus: true`. Con
las claves `dex.*` ya cargadas ([Probar el login](#probar-el-login-urls-y-que-esperar)), corre:

```bash
export KUBECONFIG=~/.kube/homelab-k3s.yaml
export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"
cd ansible
ansible-playbook -i inventory.ini playbook-dex-oauth-secrets.yml --tags ensure,argocd,incus
```

Eso aplica las claves en `argocd-secret`, reinicia Dex, instala la CA del HomeLab en **invincible**
y configura `oidc.issuer` y `oidc.client.id` en Incus.

!!! warning "Incus tiene que confiar en la CA del HomeLab"
    Incus valida el certificado HTTPS de Dex (`https://argocd.homelab.local/api/dex`), que
    firma la CA propia del HomeLab. Si `invincible` no la conoce, el login falla (`curl` desde
    el nodo da `ssl_verify=20`). El playbook, con el tag `incus`, la lee del clúster
    (`kubectl -n cert-manager get secret homelab-ca`), la instala en
    `/usr/local/share/ca-certificates/` y **reinicia el servicio `incus`** (las instancias
    siguen corriendo; la API queda unos segundos sin responder). Solo ese paso:
    `--tags incus_ca`.

Comprueba en el nodo que ya confía y que OIDC quedó configurado:

```bash
curl -s -o /dev/null -w "%{http_code} ssl_verify=%{ssl_verify_result}\n" https://argocd.homelab.local/api/dex/.well-known/openid-configuration
incus config get oidc.issuer
incus config get oidc.client.id
```

Deben dar `200 ssl_verify=0`, `https://argocd.homelab.local/api/dex` e `incus-ui`.

Alternativa manual en el nodo bootstrap (**invincible**), después de instalar la CA
([manual](../incus/cluster-setup.md#oidc-via-dex-fase-4)):

```bash
incus config set oidc.issuer=https://argocd.homelab.local/api/dex
incus config set oidc.client.id=incus-ui
```

#### Quién puede entrar y qué puede hacer

- **Quién inicia sesión:** el conector GitHub de Dex solo deja pasar a miembros del team
  `devops` de la org `symintel` (`orgs`/`teams` en `dex.config`). Quien no está en el team no
  llega a Incus.
- **Qué puede hacer:** con la configuración por defecto de Incus, cualquier usuario que se
  autentica con el proveedor OIDC tiene **acceso completo** al servidor. Para permisos
  granulares (solo un proyecto, solo lectura) Incus usa [OpenFGA](https://linuxcontainers.org/incus/docs/main/authentication/)
  como motor de autorización: no está configurado en el HomeLab. Mientras tanto, el control es
  la pertenencia al team `devops`.

Verificar:

- [`https://incus.homelab.local:8443`](https://incus.homelab.local:8443) → **Login with SSO** → GitHub → entras a la UI de Incus
- Una cuenta que **no** está en el team `devops` → GitHub/Dex rechaza el login antes de llegar a Incus

### Flujo SSO

```mermaid
sequenceDiagram
  participant U as Usuario
  participant Argo as argocd_homelab_local
  participant Dex as Dex
  participant GH as GitHub
  U->>Argo: Login_SSO
  Argo->>Dex: OIDC
  Dex->>GH: OAuth
  GH->>Dex: token
  Dex->>U: sesion
```

| Decisión | Opción A (default HomeLab) | Opción B |
|---|---|---|
| Secretos OAuth | SDK local; cuenta **Personal**, bóveda **`HomeLab`** | `ONEPASSWORD_ACCOUNT_NAME` / `ONEPASSWORD_VAULT` o `kubectl patch` |

### Análisis de trade-offs — secretos OAuth

| Alternativa | Ventaja | Coste / riesgo |
|---|---|---|
| Ansible + 1Password SDK | Genera `INCUS_*` / `VCLUSTER_*`; idempotente | App 1Password desbloqueada en la estación |
| Script Python manual | Mismo SDK sin playbook | Pasos sueltos; fácil olvidar restart Dex |
| `kubectl patch` directo | Sin 1Password | Secretos en historial; no reproducible |

---

## 4.8 — DNS de `*.homelab.local`

Los nombres los resuelve el DNS de la LAN (BIND en `deborah`,
[`playbook-bind-dns.yml`](https://github.com/symintel/homelab/blob/main/ansible/playbook-bind-dns.yml)).
La zona `homelab.local` trae:

| Registro | Apunta a |
|---|---|
| `incus.homelab.local` | invincible (`192.168.20.6`) |
| `invincible.homelab.local`, `oliver.homelab.local`, `deborah.homelab.local` | cada servidor, con su IP fija (`192.168.20.6`, `.7` y `.5`) |
| `argocd.homelab.local`, `vcluster.homelab.local`, `api.homelab.local`, `grafana.homelab.local` | el Gateway: `gateway_ip` = `192.168.23.200` (primera IP del pool de MetalLB) |

No hay comodín: cada nombre es un registro explícito en
[`db.homelab.local.j2`](https://github.com/symintel/homelab/blob/main/ansible/roles/bind_dns/templates/db.homelab.local.j2).
Para publicar una app con un `HTTPRoute` nuevo, añade su registro a esa plantilla y aplica
el playbook; hasta entonces su nombre no resuelve.

La IP del Gateway es **fija**: los Service de `kong`, `traefik` y `nginx-gateway`
la piden con una anotación de MetalLB, y la misma variable `gateway_ip`
(`ansible/group_vars/all.yml`) alimenta el DNS. Si la cambias, cámbiala en los dos
lados. Aplica el DNS (desde `ansible/` en `homelab`):

```bash
ansible-playbook -i inventory.ini playbook-bind-dns.yml
dig @192.168.20.5 argocd.homelab.local +short   # 192.168.23.200
dig @192.168.20.5 oliver.homelab.local +short   # 192.168.20.7
```

Tu estación tiene que usar `192.168.20.5` como DNS. Si no puedes, el respaldo es
`/etc/hosts`:

```
192.168.23.200  argocd.homelab.local vcluster.homelab.local api.homelab.local grafana.homelab.local
192.168.20.6    incus.homelab.local invincible.homelab.local
192.168.20.7    oliver.homelab.local
192.168.20.5    deborah.homelab.local
```

Comprueba que el Gateway tiene esa IP:

```bash
kubectl get gateway homelab -n gateway -o jsonpath='{.status.addresses[0].value}'; echo
```

El certificado lo firma la CA del HomeLab: para que el navegador confíe,
importa su certificado raíz (`kubectl -n cert-manager get secret homelab-ca -o jsonpath='{.data.ca\.crt}' | base64 -d > homelab-ca.crt`)
o usa `curl -k` mientras tanto.

```bash
curl -kI https://argocd.homelab.local
curl -kI https://incus.homelab.local:8443
```

---

## 4.9 — Wave 3: actualizaciones K3s (opcional)

Espera `Healthy` en `k3s-upgrade` ([system-upgrade-controller](https://github.com/rancher/system-upgrade-controller)).

---

## 4.10 — Checklist Fase 4

| Comprobación | Criterio |
|---|---|
| Nodos Ready | `kubectl get nodes` → 3 Ready |
| Apps auto Healthy | `kubectl get applications -n argocd` |
| Storage default | PVC `openebs-hostpath` provisiona |
| Gateway responde | `curl -k https://argocd.homelab.local` |
| SSO Dex | Login GitHub en ArgoCD |
| Incus UI OIDC | Login SSO en [`https://incus.homelab.local:8443`](https://incus.homelab.local:8443) |
| Runner ARC | `arc-runners` Healthy; runner listado en *symintel → Settings → Actions → Runners* ([4.11](#411-arc-y-pipeline-de-opentofu)) |
| Pipeline OpenTofu | Primer `tofu apply` de `infra` en verde; existe `terraform/tfstate-default-github` ([4.11](#411-arc-y-pipeline-de-opentofu)) |
| SSH con Dex *(opcional)* | `opkssh login` y `ssh devops@oliver.homelab.local` entran ([4.12](#412-ssh-a-los-hosts-con-dex-opcional)) |
| Monitoreo *(opcional)* | Grafana abre, el panel de nodos muestra temperaturas y una alerta de prueba llega a Discord ([4.13](#413-monitoreo-y-alertas-opcional)) |

Checklist global (URLs, `/etc/hosts`, nodos): **[Resumen del HomeLab](resumen-homelab.md)**.

---

## 4.11 — ARC y pipeline de OpenTofu

Con `arc-helm-repo`, `arc-controller`, `terraform-rbac` y `arc-runners` descomentadas en `homelab-root`, ArgoCD despliega el runner de GitHub Actions:

| Application | Qué despliega |
|---|---|
| `arc-controller` | Controller de ARC (`arc-systems`) |
| `terraform-rbac` | ServiceAccount `tofu-runner`, con acceso solo a Secrets/Leases del namespace `terraform` |
| `arc-runners` | El único scale set (hasta 3 runners), para CI, deploys y OpenTofu |
| `arc-runners` (caché) | Volumen compartido `arc-cache` montado en `/cache` de los runners ([Caché de los runners](../operacion/cache-arc.md)) |

```bash
kubectl get applications -n argocd | grep -E 'arc|terraform'
kubectl get pods -n arc-systems        # controller + listener de arc-runners
```

El runner aparece en *symintel → Settings → Actions → Runners*.

**Primer pipeline.** En `symintel/infra`, lanza *Actions → tofu → Run
workflow* sobre `main`, o haz un push a `main`. El workflow reusable
[`tofu.yml`](https://github.com/symintel/core-pipelines/blob/main/.github/workflows/tofu.yml)
corre en `arc-runners`: hace `plan` en los PRs (pull requests) y `apply` en `main`. La
primera ejecución crea el repo `api` con sus environments y secrets FTP (File Transfer Protocol).

```bash
kubectl -n terraform get secret tfstate-default-github   # state tras el primer apply
```

A partir de acá, cada repo nuevo se agrega con el
[procedimiento de rutina — Agregar un repo](../operacion/agregar-repo.md): credenciales FTP en
1Password (si despliega), entrada en el mapa de
[`infra`](https://github.com/symintel/infra) por PR y el
workflow de CI/CD.

## 4.12 — SSH a los hosts con Dex (opcional)

Los miembros del team `devops` de la org `symintel` en GitHub entran por SSH (Secure Shell, conexión cifrada por
terminal) a `invincible`, `oliver` y `deborah` con la identidad de Dex, sin repartir llaves. Las instancias de
Incus no entran aquí: se manejan con `incus exec` y el login SSO de la UI. Cómo entra una persona:
[Entrar por SSH a los servidores](../operacion/acceso-ssh.md).

**Requisitos.**

- Dex funcionando ([4.5](#45-wave-2-argocd-en-lan-dex) y [4.7](#47-secretos-oauth-github-vcluster-incus-ui)).
- El DNS de `homelab.local` aplicado ([4.8](#48-dns-de-homelablocal)) y **cada nodo usando el BIND de `deborah`**
  en su `/etc/resolv.conf` (se fija en la [Fase 1](fase-1-red.md) con `playbook-set-static-ip.yml`). Sin eso un nodo
  no puede validar ningún login.
- `kubectl` con el kubeconfig del HomeLab: el rol lee la CA de cert-manager para que los nodos confíen en Dex.
- Tu llave normal en `authorized_keys` de cada nodo ([hardening](fase-1-red.md#hardening-recomendado-antes-de-seguir)).
  Este acceso se **suma** a las llaves, no las reemplaza: es tu vía de emergencia si Dex o K3s caen.

### Cómo funciona

SSH no habla OIDC (OpenID Connect, protocolo de inicio de sesión). [opkssh](https://github.com/openpubkey/opkssh),
basado en [OpenPubkey](https://github.com/openpubkey/openpubkey), hace de puente:

```mermaid
sequenceDiagram
    participant U as Estación del usuario
    participant D as Dex + GitHub
    participant H as Host (sshd + opkssh)
    U->>D: opkssh login (navegador, PKCE)
    D-->>U: token firmado (solo miembros del team devops)
    U->>H: ssh devops@host (llave efímera + token)
    H->>H: opkssh verify (proveedor, firma, grupo)
    H-->>U: sesión como devops
```

1. `opkssh login` autentica contra Dex (GitHub) y deja una llave SSH que caduca a las 24 horas.
2. Al conectar, `sshd` ejecuta `opkssh verify` (vía `AuthorizedKeysCommand`), que valida la firma del token
   y que el emisor es Dex.
3. Un *policy plugin* de opkssh exige el grupo `symintel:devops` y el usuario Linux `devops`.

### Pasos

1. **Cliente en Dex.** El cliente `opkssh` (público, PKCE, con los tres callbacks en `localhost`) está en
   [`dex.config`](https://github.com/symintel/gitops/blob/main/argocd/config/dex.config). Cuando ArgoCD
   sincronice, reinicia Dex para que lo cargue:

    ```bash
    kubectl -n argocd rollout restart deploy/argocd-dex-server
    ```

2. **Comprobar que los nodos resuelven Dex** (desde `ansible/` en `homelab`):

    ```bash
    ansible incus_cluster -i inventory.ini -b -m command -a "getent hosts argocd.homelab.local"
    ```

    Los tres deben dar `192.168.23.200`. Si alguno no, arregla primero su DNS (ver *Si falla* abajo).

3. **Un nodo de prueba primero** (`oliver`), con `--check` antes de aplicar:

    ```bash
    export KUBECONFIG=~/.kube/homelab-k3s.yaml
    cd ansible && source ../.venv/bin/activate
    ansible-playbook -i inventory.ini playbook-opkssh.yml --limit oliver --check --diff
    ansible-playbook -i inventory.ini playbook-opkssh.yml --limit oliver
    ```

    El rol se detiene antes de instalar nada si el nodo no resuelve a Dex o no confía en su certificado.

4. **Probar el login** siguiendo [Entrar por SSH a los servidores](../operacion/acceso-ssh.md) y, con la sesión
   funcionando, extender al resto: `--limit invincible,deborah`.

Qué instala el rol
[`opkssh`](https://github.com/symintel/homelab/blob/main/ansible/roles/opkssh/README.md) en cada nodo: el binario
con versión fijada y su checksum, `/etc/opk/` (proveedor Dex y el plugin), la cuenta Linux `devops`, la CA del
HomeLab y un archivo en `/etc/ssh/sshd_config.d/`.

### Quién entra

El acceso depende de **pertenecer al team `devops` en GitHub**. No hay listas de usuarios ni de emails.

- **Dex** solo emite tokens a miembros del team
  ([conector GitHub](https://github.com/symintel/gitops/blob/main/argocd/config/dex.config)) y pone el team en
  el claim `groups` como `symintel:devops`.
- **Cada nodo** exige ese grupo con un policy plugin (`/etc/opk/devops-team.sh`). El grupo se cambia con
  `opkssh_allowed_group` en el rol.

Dar de alta o de baja es cambiar el team en GitHub. Una baja impide obtener tokens nuevos, pero la llave que ya
tenga la persona vale hasta que caduque (24 horas).

!!! note "Por qué un plugin y no `/etc/opk/auth_id`"
    La regla normal `oidc:groups:symintel:devops` no funciona con grupos de GitHub: opkssh separa la regla por
    `:` y solo compara el último trozo (`devops`) con el grupo completo (`symintel:devops`), así que nunca
    coinciden, y poner el valor entre comillas tampoco sirve. Por eso `auth_id` queda sin reglas y decide el
    plugin. Se comprobó leyendo `policy/enforcer.go` de opkssh.

!!! warning "Cuenta compartida con `sudo`"
    Todos entran como `devops`, con `sudo` sin contraseña (`opkssh_login_user_sudo_nopasswd`): quien está en el
    team es administrador de los tres nodos y el registro de sesiones no distingue personas por el usuario Linux.
    Para exigir contraseña de `sudo`, pon esa variable en `false` y asigna una contraseña a la cuenta.

### Análisis de trade-offs — cómo entrar por SSH

| Alternativa | Ventaja | Coste / riesgo |
|---|---|---|
| **opkssh con Dex** (esta guía) | Reutiliza Dex y el team; llaves de 24 h; sin listas que mantener | Proyecto joven; hace falta un plugin por los grupos con `:`; Dex corre en K3s sobre estos mismos nodos |
| CA SSH con certificados efímeros (step-ca) | Muy madura | Otro componente con su propia llave raíz que operar. Plan B |
| Llaves públicas de GitHub filtradas por team | Simple | No usa Dex; las llaves no caducan |
| `authorized_keys` por Ansible | Sin piezas nuevas | Cada alta o baja es un cambio manual |
| Teleport / Boundary | Auditoría y grabación de sesiones | Pesado para tres nodos; Teleport Community no ofrece OIDC genérico |

### Deshacer

[`playbook-uninstall-opkssh.yml`](https://github.com/symintel/homelab/blob/main/ansible/playbook-uninstall-opkssh.yml)
quita lo que instala el rol (configuración de `sshd`, binario, `/etc/opk` y la cuenta `devops`). Es seguro por
defecto: sin `-e opkssh_uninstall_confirm=true` solo muestra qué quitaría.

```bash
ansible-playbook -i inventory.ini playbook-uninstall-opkssh.yml --limit oliver
ansible-playbook -i inventory.ini playbook-uninstall-opkssh.yml --limit oliver -e opkssh_uninstall_confirm=true
```

No toca `authorized_keys` ni el hardening. La CA del HomeLab se conserva; para quitarla también:
`-e opkssh_uninstall_remove_ca=true`.

### Si falla (en el servidor)

| Síntoma | Causa probable | Qué revisar |
|---|---|---|
| El rol se detiene: "no resuelve argocd.homelab.local" | El nodo no usa el BIND del HomeLab. Pasó en `deborah`: NetworkManager, sin `dns=none`, reescribió `/etc/resolv.conf` con el DNS del router | `cat /etc/resolv.conf` y `getent hosts argocd.homelab.local` en el nodo. Corrige con `playbook-set-static-ip.yml --limit <nodo>` ([Fase 1](fase-1-red.md)) |
| `Permission denied`; en `/var/log/opkssh.log`: `no policy to allow …` | El token no trae el grupo `symintel:devops`, o se pidió otro usuario Linux | `opkssh inspect ~/.ssh/id_ecdsa-cert.pub` (debe listar `groups`); `/etc/opk/policy.d/devops-team.yml` |
| `Permission denied`; en `/var/log/opkssh.log`: `lookup … no such host` | Igual que la primera fila | DNS del nodo |
| `x509: certificate signed by unknown authority` en el nodo | El nodo no confía en la CA del HomeLab | `curl -s -o /dev/null -w "%{http_code} ssl_verify=%{ssl_verify_result}\n" https://argocd.homelab.local/api/dex/.well-known/openid-configuration` debe dar `200 ssl_verify=0` |
| Nadie entra con SSO y Dex no responde | Dex vive en K3s sobre estos mismos nodos | Entra con la llave de emergencia de `authorized_keys` |

## 4.13 — Monitoreo y alertas (opcional)

Da visibilidad de los tres nodos (temperatura, memoria, disco, estado de Kubernetes y de la plataforma) y avisa por
Discord solo de lo que requiere atención. Usa [VictoriaMetrics](https://docs.victoriametrics.com/) para las métricas y
las alertas, Alertmanager para enrutarlas y [Grafana](https://grafana.com/docs/grafana/latest/) para los paneles. Qué
significa cada alerta y qué hacer: [Monitoreo y alertas](../operacion/monitoreo.md).

**Requisitos.**

- Longhorn `Healthy` ([4.4](#44-wave-1-pool-metallb-gateway-longhorn)): el volumen de métricas usa la clase `longhorn`, la misma que la caché de ARC.
- El Gateway y el DNS de `homelab.local` ([4.8](#48-dns-de-homelablocal)): Grafana se publica en `grafana.homelab.local`.
- El clúster con salida a internet: tras cada despliegue, un Job descarga de GitHub los paneles y reglas estándar.
- Una cuenta de [healthchecks.io](https://healthchecks.io/) (el plan gratuito basta) y un servidor de Discord.

### Cómo funciona

```mermaid
flowchart LR
  subgraph fuentes [Fuentes]
    NE[node-exporter\nen los 3 nodos]
    KS[kube-state-metrics]
    PL[cert-manager\nLonghorn · ArgoCD]
  end
  AG[vmagent]
  DB[(vmsingle\nvolumen Longhorn)]
  AL[vmalert]
  AM[Alertmanager]
  GF[Grafana]
  DC[Discord\ncríticas · avisos]
  HC[healthchecks.io]
  NE --> AG
  KS --> AG
  PL --> AG
  AG --> DB
  DB --> AL
  DB --> GF
  AL --> AM
  AM -->|critical / warning| DC
  AM -->|Watchdog cada 5 min| HC
  HC -.->|si el ping deja de llegar| DC
```

El ping a healthchecks.io es lo que avisa si **todo** el clúster cae: `deborah` es el único control plane, así que un monitoreo
que vive en el clúster no podría avisar de su propia caída. La alerta `Watchdog` siempre está activa y Alertmanager la envía
cada 5 minutos a healthchecks.io (un *dead man's switch*); si el ping deja de llegar, healthchecks.io avisa por su cuenta.

### Pasos

Haz los pasos 1 a 5 **antes** de activar la app en GitOps (paso 6): ArgoCD necesita que el namespace y los Secrets existan.

1. **Discord** (a mano, sin bot: solo webhooks). Crea un rol y una categoría privada con dos canales, `alertas-criticas` y
   `alertas-avisos`, y un webhook por canal. Paso a paso, con los nombres exactos de los menús:
   [Discord y healthchecks.io — Parte 1](../symintel/discord-healthchecks.md#parte-1-discord). Tu servidor puede tener personas
   ajenas a infraestructura, así que no uses un canal existente.

2. **healthchecks.io.** Crea una cuenta y un check (`Period` de 5 minutos, `Grace Time` de 10), copia su **ping URL** y conéctalo a
   `alertas-criticas` con su integración de Discord:
   [Parte 2](../symintel/discord-healthchecks.md#parte-2-healthchecksio).

3. **1Password** (bóveda `HomeLab`). Tres items, como **Nota segura** y con los campos **fuera de cualquier sección**. El título del
   item y el nombre de cada campo tienen que ser exactos, porque el script los busca por nombre:

    | Item | Campo | Contenido |
    |---|---|---|
    | `discord-webhooks` | `critical` | Webhook de `alertas-criticas` |
    | | `warnings` | Webhook de `alertas-avisos` |
    | `healthchecks-ping` | `url` | Ping URL del check |
    | `grafana-admin` | `password` | Contraseña del administrador de Grafana |
    | | `username` | *(opcional)* usuario; por defecto `admin` |

    Cómo crearlos y comprobarlos: [Parte 3](../symintel/discord-healthchecks.md#parte-3-guardarlo-en-1password).

4. **Secrets en el clúster.** Necesita la app de 1Password desbloqueada (*Integrate with other apps*) y el kubeconfig del homelab,
   como el resto de [secretos de plataforma](../symintel/github.md). Son opcionales: si no existe ninguno de los tres items el script no hace nada; si existe
   alguno, exige los tres. Comprueba primero y aplica después (desde `ansible/`):

    ```bash
    python3 scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

    Crea el namespace `monitoring` (con `pod-security enforce=privileged`, porque `node-exporter` usa el disco y la red del
    nodo) y los Secrets `discord-webhooks`, `healthchecks-ping` y `grafana-admin`. El script rechaza una URL de Discord que
    no tenga el formato `https://discord.com/api/webhooks/<id>/<token>`, para no mandar alertas a otro destino.

5. **DNS.** Añade el registro `grafana` y aplícalo:

    ```bash
    ansible-playbook -i inventory.ini playbook-bind-dns.yml
    dig @192.168.20.5 grafana.homelab.local +short   # 192.168.23.200
    ```

6. **Activar en GitOps.** `victoria-metrics` (ola 2) y `victoria-metrics-config` (ola 3, sus reglas y la ruta de Grafana) ya
   están en la lista de [`root-appset.yaml`](https://github.com/symintel/gitops/blob/main/bootstrap/root-appset.yaml).
   Fusiona ese cambio en `main` del repo `gitops` y **después aplica el ApplicationSet**: el `homelab-root` del clúster se creó
   a mano con `kubectl apply` y ArgoCD no lo actualiza solo desde git, así que sin este comando no pasa nada.

    ```bash
    kubectl apply -f gitops/bootstrap/root-appset.yaml
    kubectl get applications -n argocd | grep victoria
    kubectl get pods -n monitoring -o wide
    kubectl top pods -n monitoring
    ```

    El consumo esperado es de **~1 a 1,5 GB** en total (estimación; confírmalo con `kubectl top`). `vmsingle`, `vmagent`,
    `vmalert`, Alertmanager y Grafana prefieren `invincible` y nunca van a `oliver` (el nodo ligero); `node-exporter` corre en los tres.

7. **Probar de punta a punta.** Entra a [`https://grafana.homelab.local`](https://grafana.homelab.local) con `admin` y la
   contraseña de 1Password, y comprueba que el panel de nodos muestra las temperaturas. Luego manda una alerta de prueba:

    ```bash
    kubectl -n monitoring port-forward svc/vmalertmanager-vm-victoria-metrics-k8s-stack 9093:9093 &
    curl -s -XPOST localhost:9093/api/v2/alerts -H 'Content-Type: application/json' -d \
      '[{"labels":{"alertname":"PruebaManual","severity":"warning","nodename":"prueba"},"annotations":{"summary":"Alerta de prueba: si la ves, Discord funciona."}}]'
    ```

    Debe llegar a `alertas-avisos` (cambia `severity` a `critical` para probar `alertas-criticas`). Si el Service no se llama
    así, busca el nombre con `kubectl -n monitoring get svc | grep alertmanager`. Para probar el ping, crea un silencio de
    30 minutos para `alertname=Watchdog` en la interfaz de Alertmanager (*Silences*): el ping se corta y healthchecks.io avisa
    a los ~15 minutos; al expirar el silencio, se recupera.

### Qué vigila

| Alerta | Cuándo | Severidad |
|---|---|---|
| `TemperaturaAlta` / `TemperaturaCritica` | `deborah` desde 75 / 85 °C (el SoC reduce velocidad en esos puntos); `invincible` y `oliver` desde 80 / 90 °C (límite del fabricante: 100 °C) | aviso / crítica |
| `NodoNoListo` | un nodo deja de estar Ready más de 2 minutos | crítica |
| `ServicioBaseSinReplicas` | ArgoCD, Kong o cert-manager sin ninguna réplica | crítica |
| `CertificadoPorVencer` | un certificado vence en menos de 14 días / 3 días | aviso / crítica |
| `LonghornVolumenDegradado` / `Fallido` | un volumen pierde una réplica / queda sin réplicas | crítica |
| `ArgoCDAppNoSana` / `Desincronizada` | una app lleva más de 15 / 30 minutos fuera de `Healthy` / `Synced` | aviso |
| Disco, memoria, reloj y pods | reglas por defecto del chart | aviso / crítica |

Los umbrales de temperatura salen de los puntos de disparo que el propio hardware publica en `/sys`. Las reglas están en
[`monitoring/config/rules`](https://github.com/symintel/gitops/tree/main/monitoring/config/rules) y tienen pruebas en
[`monitoring/tests`](https://github.com/symintel/gitops/tree/main/monitoring/tests) (`monitoring/tests/run.sh`, con Docker): si cambias un
umbral, actualiza la prueba.

### Deshacer

Quita `victoria-metrics` y `victoria-metrics-config` de la lista de `root-appset.yaml`, fusiona el cambio y vuelve a aplicarlo
(`kubectl apply -f gitops/bootstrap/root-appset.yaml`): la raíz borra las Applications, pero **los recursos quedan en el clúster**
(la convención de este repo). Para borrar también el historial de métricas y los Secrets,
elimina el namespace: `kubectl delete namespace monitoring` (destructivo: se pierde el volumen de métricas).

### Si falla

| Síntoma | Causa probable | Qué revisar |
|---|---|---|
| `victoria-metrics` no sincroniza: *namespace "monitoring" not found* | Falta el paso 4 | `kubectl get ns monitoring`; corre `playbook-platform-secrets.yml` |
| `node-exporter` rechazado: *violates PodSecurity* | El namespace no tiene la etiqueta `privileged` | `kubectl get ns monitoring --show-labels`; vuelve a correr el paso 4 |
| `vmsingle` en `Pending` | El volumen `longhorn` no se crea | `kubectl -n monitoring describe pvc`; estado de Longhorn ([4.4](#44-wave-1-pool-metallb-gateway-longhorn)) |
| No llegan alertas a Discord | Alertmanager no lee el webhook | `kubectl -n monitoring logs` del Alertmanager (busca `discord`) y que existan los archivos en `/etc/alertmanager-secrets/` |
| Grafana sin paneles | El Job de descarga no llegó a GitHub | `kubectl -n monitoring get jobs` y sus logs; salida a internet del clúster |
| `grafana.homelab.local` no abre | Falta el registro DNS o la ruta | paso 5; `kubectl -n monitoring get httproute` |
| `TargetDown` de etcd, scheduler o controller-manager | Se activaron los monitores de K3s | Deben estar `enabled: false` en [`values-vm-stack.yaml`](https://github.com/symintel/gitops/blob/main/monitoring/values-vm-stack.yaml) |

---

## Opciones post-Fase 4

| Componente | Sync | Siguiente paso |
|---|---|---|
| [vCluster Platform](https://www.vcluster.com/docs/platform/) | manual | [Fase 5](fase-5-vcluster.md) |
| [CAPN](https://capn.linuxcontainers.org/) | manual | [Fase 6](fase-6-capn.md) |
| CNI externo (Canal / Calico / Cilium) | manual | [Fase 3 — CNI](fase-3-k3s.md#cni); normalmente vía Ansible `k3s_cni`, no Fase 4 |

### Análisis de trade-offs — post-Fase 4

| Alternativa | Ventaja | Coste / riesgo |
|---|---|---|
| Terminar en Fase 4 | Management GitOps completo; menos superficie | Sin vClusters ni workload clusters CAPN |
| Fase 5 vCluster | Kubeconfig web; clústeres virtuales ligeros | Más RAM en K3s; OAuth + permisos Platform |
| Fase 6 CAPN | Clusters kubeadm reales sobre Incus | Alto consumo RAM; sync manual obligatorio |
| CNI vía GitOps | Reinstalar Canal/Calico/Cilium sin Ansible | Solo con K3s en `flannel-backend=none`; no mezclar CNIs |
| Sync manual (5/6) | No borra clusters efímeros por prune | Paso extra en Argo CD UI |

## Si falla

| Síntoma | Revisar |
|---|---|
| Application `Degraded` | `kubectl describe application -n argocd <nombre>` |
| Gateway sin dirección | `metallb-config`, pool libre |
| SSO falla | Secretos 1Password + restart `argocd-dex-server` |
| `homelab-root` `ComparisonError` / repo no accesible | Falta `argocd/repo-gitops`, o la App `symintel-argocd` no está instalada en `symintel/gitops`: re-correr `playbook-platform-secrets.yml` |
| `arc-runners` `OutOfSync` y el pod del listener se reinicia cada pocos minutos | ArgoCD poda en bucle los recursos que crea el controlador de ARC (`AutoscalingListener`, `Role`, `RoleBinding`: copian la etiqueta `app.kubernetes.io/instance`). Se corrige con `application.resourceTrackingMethod: annotation` en `argocd-cm` (ya está en `gitops/argocd/config`). Comprueba: `kubectl -n argocd get cm argocd-cm -o jsonpath='{.data.application\.resourceTrackingMethod}'` → `annotation`; si no, sincroniza `argocd` y reinicia el controlador: `kubectl -n argocd rollout restart statefulset argocd-application-controller` |
| Apps en `Error`: `ComparisonError … terminatingReplicas: field not declared in schema` | ArgoCD es anterior a la 3.5 y el clúster tiene Kubernetes 1.34 o más nuevo: [Actualizar ArgoCD](../operacion/actualizar-argocd.md#la-primera-vez-actualizar-a-mano-y-despues-activar-la-app) |
| Login con GitHub da 404 (`client_id=.github.clientId`) | Faltan `dex.*` en `argocd-secret`: corre `playbook-dex-oauth-secrets.yml --tags argocd` ([4.7](#47-secretos-oauth-github-vcluster-incus-ui)) |
| Runner no aparece en GitHub | `kubectl logs -n arc-systems` del listener; Secret `arc-runners/arc-runners-github-app` (App instalada en `symintel`) |
| Pipeline `tofu` sin runner o sin credenciales | Runner `arc-runners` Online; Secrets `symintel-terraform-app`/`tofu-vars` en `arc-runners` |
| Longhorn pending | Etiquetas Longhorn ([playbook-options](../k3s/playbook-options.md)) |

Catálogo y troubleshooting extendido: [GitOps — profundización](../gitops/index.md).

## Siguiente

Opcional:

- **[→ Fase 5 — vCluster](fase-5-vcluster.md)**
- **[→ Fase 6 — CAPN](fase-6-capn.md)**

O terminar aquí si solo necesitas el management cluster GitOps.
