# Plataforma symintel — GitHub

Cómo se conecta la org GitHub **`symintel`** con el clúster HomeLab:
- **ArgoCD** despliega desde el repo privado `symintel/gitops`.
- **ARC (Actions Runner Controller)** corre un runner self-hosted de GitHub Actions dentro del clúster
  (un solo scale set, `arc-runners`, para CI, deploys y OpenTofu).
- **OpenTofu** gestiona la org desde un pipeline que corre en uno de esos
  runners, y guarda su state en el clúster.

!!! tip "Dónde se ejecuta en la guía de implementación"
    - **Pasos 1 y 2 (manuales):** [Fase 0 — GitHub y 1Password](../implementacion/fase-0-preparacion.md#github-y-1password-org-symintel-manual-una-sola-vez)
    - **Paso 3 (secretos de plataforma):** [Fase 4 — 4.2](../implementacion/fase-4-gitops.md#42-bootstrap-gitops-applicationset), antes del ApplicationSet de bootstrap
    - **Pasos 4 y 5 (ARC y pipeline):** [Fase 4 — 4.11](../implementacion/fase-4-gitops.md#411-arc-y-pipeline-de-opentofu)

    Esta página es la referencia completa: permisos, campos, verificación y rotación.

!!! info "Repos involucrados"
    | Repo | Qué contiene |
    |---|---|
    | [`symintel/homelab`](https://github.com/symintel/homelab) | Este sitio. Ansible: k3s, ArgoCD y los **secretos de plataforma** (1Password → clúster) |
    | [`symintel/gitops`](https://github.com/symintel/gitops) | Applications de ArgoCD, incluidos ARC y el runner de OpenTofu |
    | [`symintel/core-pipelines`](https://github.com/symintel/core-pipelines) | Workflows reutilizables (`tofu.yml`, CI, deploy FTP) |
    | [`symintel/infra`](https://github.com/symintel/infra) | OpenTofu: repos, environments y secrets de la org |

## Cómo encaja

```mermaid
flowchart LR
  OP[1Password<br/>bóveda HomeLab] -->|playbook-platform-secrets.yml| K8S
  subgraph K8S[Clúster k3s]
    ARGO[ArgoCD] -->|App symintel-argocd| GITOPS[(symintel/gitops)]
    ARGO --> ARC[ARC controller]
    ARC --> RT[arc-runners]
    RT --> STATE[(ns terraform<br/>Secret tfstate-default-github)]
  end
  INFRA[symintel/infra] -->|tofu.yml de core-pipelines| RT
  RT -->|App symintel-terraform| GH[org symintel]
```

Hay piezas que **tienen que existir antes** de que ArgoCD o el pipeline
puedan funcionar. Esas se crean **a mano, una sola vez**, y OpenTofu no las
gestiona ni las importa:

| Qué | Por qué a mano |
|---|---|
| Repos `gitops`, `infra`, `core-pipelines` | Sin ellos no hay de dónde desplegar ni pipeline que corra OpenTofu |
| App `symintel-argocd` | ArgoCD la necesita para leer el repo privado que despliega todo lo demás |
| GitHub Apps y OAuth App | GitHub no permite crear OAuth Apps por API, y las GitHub Apps piden confirmación en el navegador |

Todo lo demás (el repo `api` y los repos futuros) lo crea el pipeline de
`infra`.

## Items en 1Password

Todos en la bóveda **`HomeLab`**. Los scripts los leen a través de la app de
escritorio de 1Password, que tiene que estar desbloqueada y con *Settings →
Developer → Integrate with other apps* activado. Para indicar **qué cuenta**
usar se define **`ONEPASSWORD_ACCOUNT_NAME`** con el nombre de tu cuenta tal
como aparece arriba a la izquierda en la barra lateral de la app (por
ejemplo `Mi Cuenta`; si no la defines, usa `Personal`):

```bash
export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"  # tu cuenta
```

| Item | Tipo de item | Campos | Lo usa |
|---|---|---|---|
| `symintel-terraform` | Nota segura | `app_id`, `installation_id`, `private_key` | Runner de OpenTofu (`TF_VAR_github_app_*`) |
| `symintel-arc-runners` | Nota segura | `app_id`, `installation_id`, `private_key` | ARC (registro del runner) |
| `symintel-argocd` | Nota segura | `app_id`, `installation_id`, `private_key` | ArgoCD lee `symintel/gitops` (`argocd/repo-gitops`) |
| `sealed-secrets` | Nota segura | `certificate`, `private_key` *(opcional hasta la Fase 6)* | Llave de cifrado de Sealed Secrets: sobrevive si reinstalas K3s |
| `symintel-dex` | Nota segura | `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` (+ `VCLUSTER_CLIENT_SECRET`, que genera el playbook) | Dex (login con GitHub) |
| `discord-webhooks` | Nota segura | `critical`, `warnings`: URL de un webhook de Discord por canal *(opcional: monitoreo)* | Alertmanager envía las alertas ([4.13](../implementacion/fase-4-gitops.md#413-monitoreo-y-alertas-opcional)). Cómo crearlos: [Discord y healthchecks.io](discord-healthchecks.md#parte-1-discord) |
| `healthchecks-ping` | Nota segura | `url`: ping URL del check de healthchecks.io *(opcional: monitoreo)* | Alertmanager le manda un ping cada 5 minutos para avisar que el monitoreo sigue vivo. Cómo crearla: [Discord y healthchecks.io](discord-healthchecks.md#parte-2-healthchecksio) |
| `grafana-admin` | Nota segura | `password` y, si quieres, `username` (por defecto `admin`) *(opcional: monitoreo)* | Administrador de Grafana |
| `ftp-<repo>` | Nota segura | `dev_host`, `dev_user`, `dev_password`, `dev_remote_dir`, `prod_host`, `prod_user`, `prod_password`, `prod_remote_dir` | OpenTofu → secrets FTP de `<repo>` (`TF_VAR_ftp`) |

### Cómo crear un item con campos propios

El playbook busca cada valor por su ruta `op://HomeLab/<item>/<campo>`, así
que **el título del item y el nombre de cada campo tienen que ser exactos**
(minúsculas, con guion bajo).

1. En 1Password abre la bóveda **`HomeLab`** → **Nuevo elemento** → **Nota
   segura** (*Secure Note*).
2. En **Título** escribe el nombre del item, por ejemplo `symintel-terraform`.
3. Por cada campo: **+ Añadir más** → elige el tipo (**Texto** o
   **Contraseña**) → en la etiqueta del campo escribe el nombre exacto
   (por ejemplo `app_id`) → pega el valor.
4. Agrega los campos directamente en el item. **No crees una sección** para
   agruparlos: con sección la ruta cambia y el playbook no los encuentra.
5. Guarda.

Usa **Contraseña** para los valores secretos (se ocultan) y **Texto** para
el resto. Cada tabla de abajo dice qué tipo lleva cada campo.

## Paso 1 — GitHub Apps y OAuth App (manual)

Hazlo con una cuenta **owner de la organización** `symintel`.

### `symintel-terraform`

[symintel → Settings → Developer settings → GitHub Apps → New GitHub App](https://github.com/organizations/symintel/settings/apps/new)

| Campo | Valor |
|---|---|
| GitHub App name | `symintel-terraform` |
| Homepage URL | `https://github.com/symintel` |
| Webhook → Active | desmarcado |
| Where can this GitHub App be installed? | Only on this account |

El resto del formulario (Callback URL, Setup URL, *Request user
authorization*, eventos) se deja vacío o sin marcar.

| Repository permission | Acceso | Para qué |
|---|---|---|
| Actions | Read and write | Gestión de Actions en los repos |
| Administration | Read and write | Crear repos y branch protection |
| Contents | Read and write | Archivos del repo |
| Environments | Read and write | Environments `dev` / `prod` |
| Metadata | Read-only | Obligatorio |
| Secrets | Read and write | Secrets FTP por environment |
| Variables | Read and write | `PROJECT_STACK`, `FTP_PROTOCOL` |
| Workflows | Read and write | Archivos `.github/workflows/*` |

| Organization permission | Acceso | Para qué |
|---|---|---|
| Administration | Read and write | Crear repos en la org |

Todos los demás permisos quedan en *No access*.

Después de *Create GitHub App*, junta tres datos y guárdalos en el item
**`symintel-terraform`** de 1Password (Nota segura, ver
[cómo crearlo](#como-crear-un-item-con-campos-propios)):

| Campo en 1Password | Tipo | Dato | Dónde está en GitHub |
|---|---|---|---|
| `app_id` | Texto | App ID | Página de la App, pestaña *General*: línea **App ID** (un número, por ejemplo `1234567`) |
| `private_key` | Contraseña | Private key | Misma página, abajo en *Private keys* → **Generate a private key**. Se descarga un archivo `symintel-terraform.<fecha>.private-key.pem`. Ábrelo con un editor de texto y copia **todo**, incluidas las líneas `-----BEGIN RSA PRIVATE KEY-----` y `-----END RSA PRIVATE KEY-----` |
| `installation_id` | Texto | Installation ID | Menú izquierdo de la App → **Install App** → *Install* junto a `symintel` → **All repositories** → *Install*. GitHub te lleva a `https://github.com/organizations/symintel/settings/installations/<número>`: ese número final |

Así queda el item:

```text
symintel-terraform        (Nota segura · bóveda HomeLab)
├── app_id                1234567
├── installation_id       87654321
└── private_key           ••••••••   (el .pem completo)
```

Al pegar el `.pem` en un campo Contraseña se pierden los saltos de línea. No
importa: el playbook reconstruye la llave. Cuando el item esté guardado,
**borra el `.pem`** de Descargas.

### `symintel-arc-runners`

Es la App con la que ARC registra el runner `arc-runners` en la org. Se
crea en el mismo formulario que `symintel-terraform`, pero es **otra App**:
nombre, permisos y credenciales propios.

[symintel → Settings → Developer settings → GitHub Apps → New GitHub App](https://github.com/organizations/symintel/settings/apps/new)

| Campo | Valor |
|---|---|
| GitHub App name | `symintel-arc-runners` |
| Homepage URL | `https://github.com/symintel` |
| Webhook → Active | desmarcado |
| Where can this GitHub App be installed? | Only on this account |

El resto del formulario (Callback URL, Setup URL, *Request user
authorization*, eventos) se deja vacío o sin marcar.

| Repository permission | Acceso | Para qué |
|---|---|---|
| Actions | Read-only | Ver los jobs en cola que tiene que tomar el runner |
| Administration | Read and write | Registrar runners (lo pide ARC) |
| Metadata | Read-only | Obligatorio |

| Organization permission | Acceso | Para qué |
|---|---|---|
| Self-hosted runners | Read and write | Registrar y borrar el runner `arc-runners` en la org |

Todos los demás permisos quedan en *No access*.

Después de *Create GitHub App*, guarda sus tres datos en el item
**`symintel-arc-runners`** de 1Password (Nota segura, ver
[cómo crearlo](#como-crear-un-item-con-campos-propios)):

| Campo en 1Password | Tipo | Dato | Dónde está en GitHub |
|---|---|---|---|
| `app_id` | Texto | App ID | Página de la App, pestaña *General*: línea **App ID** |
| `private_key` | Contraseña | Private key | Misma página, abajo en *Private keys* → **Generate a private key**. Se descarga `symintel-arc-runners.<fecha>.private-key.pem`. Ábrelo con un editor de texto y copia **todo**, incluidas las líneas `-----BEGIN RSA PRIVATE KEY-----` y `-----END RSA PRIVATE KEY-----` |
| `installation_id` | Texto | Installation ID | Menú izquierdo de la App → **Install App** → *Install* junto a `symintel` → **All repositories** → *Install*. El número al final de la URL `https://github.com/organizations/symintel/settings/installations/<número>` |

Así queda el item:

```text
symintel-arc-runners      (Nota segura · bóveda HomeLab)
├── app_id                2345678
├── installation_id       98765432
└── private_key           ••••••••   (el .pem completo)
```

Los tres valores son **distintos** de los de `symintel-terraform`: cada App
tiene su App ID, su llave y su instalación. No copies los de la otra. Cuando
el item esté guardado, **borra el `.pem`** de Descargas.

### OAuth App `Symintel Dex`

[symintel → Settings → Developer settings → OAuth Apps → New OAuth App](https://github.com/organizations/symintel/settings/applications/new)

| Campo | Valor |
|---|---|
| Application name | `Symintel Dex` |
| Homepage URL | `https://argocd.homelab.local` |
| Redirect URIs | `https://argocd.homelab.local/api/dex/callback` (solo esta) |

Después de *Register application*, crea el item **`symintel-dex`** en la
bóveda `HomeLab` (Nota segura, ver [cómo crearlo](#como-crear-un-item-con-campos-propios))
con estos dos campos:

| Campo en 1Password | Tipo | Dato | Dónde está en GitHub |
|---|---|---|---|
| `GITHUB_CLIENT_ID` | Texto | Client ID | Página de la OAuth App: línea **Client ID** |
| `GITHUB_CLIENT_SECRET` | Contraseña | Client secret | Misma página → **Generate a new client secret**. GitHub lo muestra **una sola vez**: cópialo en ese momento |

Así queda el item (el último campo lo agrega solo
`playbook-dex-oauth-secrets.yml` la primera vez que corre: es el secreto
del cliente vCluster de Dex, no viene de GitHub):

```text
symintel-dex              (Nota segura · bóveda HomeLab)
├── GITHUB_CLIENT_ID      Ov23li…
├── GITHUB_CLIENT_SECRET  ••••••••
└── VCLUSTER_CLIENT_SECRET ••••••••  (lo genera el playbook)
```

Solo puede entrar el team **`devops`** de `symintel`, y sus miembros quedan
como admin de ArgoCD. Se aplica en el
[paso 4.7 de la Fase 4](../implementacion/fase-4-gitops.md#47-secretos-oauth-github-vcluster-incus-ui).

## Paso 2 — Repos, App de ArgoCD y FTP (manual)

1. **Repos** (privados), creados en `symintel` y con su contenido subido con git:
    - `gitops`.
    - `core-pipelines`: después, en *Settings → Actions → General → Access*,
      elige "Accessible from repositories in the 'symintel' organization".
      Mientras pruebas, los demás repos lo usan con `@main`; el tag `v1` se
      crea cuando todo funcione (ver el README de `core-pipelines`).
    - `infra`.
2. **GitHub App `symintel-argocd`**, con la que ArgoCD lee el repo privado
   `gitops`. Va después de los repos porque se instala **solo** en `gitops`.
   (Las deploy keys están deshabilitadas en la organización, por eso se usa
   una App.)

    [symintel → Settings → Developer settings → GitHub Apps → New GitHub App](https://github.com/organizations/symintel/settings/apps/new)

    | Campo | Valor |
    |---|---|
    | GitHub App name | `symintel-argocd` |
    | Homepage URL | `https://github.com/symintel` |
    | Webhook → Active | desmarcado |
    | Where can this GitHub App be installed? | Only on this account |

    El resto del formulario se deja vacío o sin marcar.

    | Repository permission | Acceso | Para qué |
    |---|---|---|
    | Contents | Read-only | Clonar el repo |
    | Metadata | Read-only | Obligatorio |

    Sin permisos de organización. Todos los demás quedan en *No access*.

    Después de *Create GitHub App*, guarda sus tres datos en el item
    **`symintel-argocd`** de 1Password (Nota segura, ver
    [cómo crearlo](#como-crear-un-item-con-campos-propios)):

    | Campo en 1Password | Tipo | Dato | Dónde está en GitHub |
    |---|---|---|---|
    | `app_id` | Texto | App ID | Página de la App, pestaña *General*: línea **App ID** |
    | `private_key` | Contraseña | Private key | Misma página, abajo en *Private keys* → **Generate a private key**. Copia **todo** el `.pem` descargado, incluidas las líneas `BEGIN`/`END` |
    | `installation_id` | Texto | Installation ID | Menú izquierdo → **Install App** → *Install* junto a `symintel` → **Only select repositories** → elige **`gitops`** → *Install*. El número al final de la URL `…/settings/installations/<número>` |

    Instálala **solo en `gitops`**: con esa llave se puede leer el código de
    todos los repos donde esté instalada. Borra el `.pem` al terminar.

3. **Credenciales FTP (File Transfer Protocol) del repo `api`**, el primer
   proyecto del mapa con `deploy = true`: título **`ftp-api`**, tipo Nota
   segura. Para cada repo que agregues después, sigue el
   [procedimiento — Agregar un repo](../operacion/agregar-repo.md). Campos, [creado igual que los otros](#como-crear-un-item-con-campos-propios):

    | Campo | Tipo | Ejemplo |
    |---|---|---|
    | `dev_host` | Texto | `dev.tu-cpanel.example.com` |
    | `dev_user` | Texto | `usuario_dev` |
    | `dev_password` | Contraseña | |
    | `dev_remote_dir` | Texto | `/home/usuario/dev.symintel.example.com` |
    | `prod_host` | Texto | `tu-cpanel.example.com` |
    | `prod_user` | Texto | `usuario_prod` |
    | `prod_password` | Contraseña | |
    | `prod_remote_dir` | Texto | `/home/usuario/public_html` |

4. **Llave de Sealed Secrets** *(opcional: hace falta cuando empieces a
   guardar `SealedSecret` en git, p. ej. en la Fase 6)*. Sealed Secrets
   cifra los secretos con un par de llaves que, por defecto, el controlador
   genera dentro del clúster: si reinstalas K3s se pierde, y los
   `SealedSecret` que ya estaban en git dejan de poder descifrarse. Por eso
   se genera **una sola vez**, se guarda en 1Password, y el playbook de
   secretos la lleva al clúster antes de que el controlador arranque.

    Genera el par en una carpeta temporal (`openssl` viene en macOS y Linux):

    ```bash
    cd "$(mktemp -d)"
    openssl req -x509 -days 3650 -nodes -newkey rsa:4096 \
      -keyout tls.key -out tls.crt -subj "/CN=sealed-secret/O=sealed-secret"
    ```

    Crea en 1Password el item **`sealed-secrets`** (Nota segura,
    [creado igual que los otros](#como-crear-un-item-con-campos-propios)):

    | Campo | Tipo | Valor |
    |---|---|---|
    | `certificate` | Texto | El contenido completo de `tls.crt` (la llave **pública**), con las líneas `-----BEGIN CERTIFICATE-----` y `-----END CERTIFICATE-----` |
    | `private_key` | Contraseña | El contenido completo de `tls.key` (la llave **privada**), con sus líneas `BEGIN`/`END` |

    Para copiar un archivo: `pbcopy < tls.crt` (macOS) o ábrelo con un editor
    y copia todo. Cuando el item esté guardado, **borra los archivos**:

    ```bash
    rm -f tls.key tls.crt
    ```

    El certificado vale 10 años. El playbook comprueba que el certificado y
    la llave sean un par (si copiaste archivos de pares distintos, se
    detiene con un mensaje claro) y crea el Secret
    `kube-system/sealed-secrets-key-homelab`, que el controlador detecta por su
    etiqueta `sealedsecrets.bitnami.com/sealed-secrets-key: active`. Mientras
    el item no exista, el playbook avisa y sigue: Sealed Secrets generaría su
    propia llave.

## Paso 3 — Clúster y secretos de plataforma

Con k3s instalado ([Fase 3](../implementacion/fase-3-k3s.md), ArgoCD incluido):

```bash
export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"  # tu cuenta
cd ansible
ansible-playbook -i inventory.ini playbook-platform-secrets.yml
```

[`playbook-platform-secrets.yml`](https://github.com/symintel/homelab/blob/main/ansible/playbook-platform-secrets.yml)
crea los namespaces `argocd`, `arc-runners` (PSS `baseline`) y `terraform`
(solo guarda el state de OpenTofu), y estos Secrets:

| Secret | Namespace | Contenido |
|---|---|---|
| `repo-gitops` | `argocd` | App `symintel-argocd`: ArgoCD puede clonar `https://github.com/symintel/gitops.git` |
| `arc-runners-github-app` | `arc-runners` | App de ARC |
| `symintel-terraform-app` | `arc-runners` | `TF_VAR_github_app_id`, `TF_VAR_github_app_installation_id`, `TF_VAR_github_app_private_key` |
| `tofu-vars` | `arc-runners` | `TF_VAR_ftp` (todos los items `ftp-<repo>`) |
| `sealed-secrets-key-homelab` | `kube-system` | Par de llaves de Sealed Secrets (item `sealed-secrets`, si existe) |
| `discord-webhooks`, `healthchecks-ping`, `grafana-admin` | `monitoring` | Webhooks de Discord, ping URL de healthchecks.io y contraseña de Grafana (los items del mismo nombre; solo si existen los tres). El namespace se crea con PSS `privileged`, porque `node-exporter` usa el disco y la red del nodo |

!!! note "Un solo runner"
    Es un HomeLab: el único scale set (`arc-runners`, grupo Default) corre CI (integración continua),
    deploys y OpenTofu, y tiene las credenciales de OpenTofu como variables de
    entorno. Cualquier repo de `symintel` que corra un job ahí puede
    alcanzarlas. Mantén la org solo con repos tuyos.

!!! warning "Siempre contra el HomeLab"
    El playbook usa `~/.kube/homelab-k3s.yaml` (el que deja
    `k3s_fetch_kubeconfig`), **no** el contexto actual de `kubectl`. Así no
    escribe secretos en otro clúster. Para otro kubeconfig:
    `-e platform_kubeconfig=/ruta`.

Es idempotente: re-córrelo cada vez que rotes algo en 1Password o agregues
un item `ftp-<repo>`.

## Paso 4 — GitOps

```bash
kubectl apply -f gitops/bootstrap/root-appset.yaml
```

ArgoCD sincroniza, entre otras, estas Applications:

| Application | Qué despliega |
|---|---|
| `arc-controller` | Controller de ARC (`arc-systems`) |
| `terraform-rbac` | ServiceAccount `tofu-runner` + Role (solo Secrets/Leases del namespace `terraform`) |
| `arc-runners` | El runner (hasta 3 en paralelo), con los Secrets del namespace como variables de entorno |

## Paso 5 — Primer pipeline de OpenTofu

Haz un push a `main` de `infra`, o lánzalo desde *Actions → tofu →
Run workflow*. El workflow
[`tofu.yml`](https://github.com/symintel/core-pipelines/blob/main/.github/workflows/tofu.yml)
corre en `arc-runners`: hace `plan` en los PRs (pull requests) y `apply` en `main`. En la
primera ejecución crea `api`.

## Verificar

Antes del clúster, que 1Password tenga todo (desde la raíz de `homelab`):

```bash
export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"  # tu cuenta
# items y campos: todo ✓
.venv/bin/python ansible/scripts/apply_platform_secrets.py --check
# Secrets que se van a crear, sin valores
.venv/bin/python ansible/scripts/apply_platform_secrets.py --dry-run
```

Después del playbook y de GitOps:

```bash
kubectl -n argocd get secret repo-gitops
kubectl -n arc-runners get secret \
  arc-runners-github-app symintel-terraform-app tofu-vars
kubectl -n argocd get applications | grep -E 'arc|terraform'
# controller + listener del scale set
kubectl -n arc-systems get pods
# después del primer apply de OpenTofu
kubectl -n terraform get secret tfstate-default-github
```

## Rotar credenciales

Paso a paso completo: [Operación — Rotar credenciales](../operacion/rotar-credenciales.md).

| Qué | Cómo |
|---|---|
| Private key de una GitHub App | Genera una nueva en GitHub, reemplaza `private_key` en 1Password, re-corre `playbook-platform-secrets.yml` y borra la vieja en GitHub |
| Private key de `symintel-argocd` | Igual que las otras Apps: nueva llave en GitHub, reemplaza `private_key`, re-corre el playbook y borra la vieja |
| Credenciales FTP | Edita `ftp-<repo>`, re-corre el playbook y lanza el pipeline de `infra` |
| Webhook de Discord, ping URL de healthchecks.io o contraseña de Grafana | Cambia el campo en su item, re-corre `playbook-platform-secrets.yml` y sigue [Operación — Rotar credenciales](../operacion/rotar-credenciales.md#monitoreo-webhooks-de-discord-ping-de-healthchecksio-y-grafana) |
| Client secret de Dex | Nuevo secret en la OAuth App, actualiza `GITHUB_CLIENT_SECRET` y corre `playbook-dex-oauth-secrets.yml` |
