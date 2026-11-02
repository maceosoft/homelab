# Plataforma maceosoft — GitHub

Cómo se conecta la org GitHub **`maceosoft`** con el clúster HomeLab:
- **Argo CD** despliega desde el repo privado `maceosoft/gitops`.
- **ARC (Actions Runner Controller)** corre un runner self-hosted de GitHub Actions dentro del clúster
  (un scale set por organización: `arc-runners` para `maceosoft` y `arc-runners-symintel` para la org antigua; ver
  [Dos organizaciones](#dos-organizaciones-un-scale-set-por-org)).
- **OpenTofu** gestiona la org desde un pipeline que corre en uno de esos
  runners, y guarda su estado en el clúster.

!!! tip "Dónde se ejecuta en la guía de implementación"
    - **Pasos 1 y 2 (manuales):** [Fase 0 — GitHub y 1Password](../implementacion/fase-0-preparacion.md#github-y-1password-org-maceosoft-manual-una-sola-vez)
    - **Paso 3 (secretos de plataforma):** [Fase 4 — 4.2](../implementacion/fase-4-gitops.md#42-bootstrap-gitops-applicationset), antes del ApplicationSet de bootstrap
    - **Pasos 4 y 5 (ARC y pipeline):** [Fase 4 — 4.11](../implementacion/fase-4-gitops.md#411-arc-y-pipeline-de-opentofu)

    Esta página es la referencia completa: permisos, campos, verificación y rotación.

!!! info "Repos involucrados"
    | Repo | Qué contiene |
    |---|---|
    | [`maceosoft/homelab`](https://github.com/maceosoft/homelab) | Este sitio. Ansible: k3s, Argo CD y los **secretos de plataforma** (1Password → clúster) |
    | [`maceosoft/gitops`](https://github.com/maceosoft/gitops) | Applications de Argo CD, incluidos ARC y el runner de OpenTofu |
    | [`maceosoft/core-pipelines`](https://github.com/maceosoft/core-pipelines) | Workflows reutilizables (`tofu.yml`, CI, deploy FTP) |
    | [`maceosoft/infra`](https://github.com/maceosoft/infra) | OpenTofu: repos, environments y secrets de la org |

## Cómo encaja

```mermaid
flowchart LR
  OP[1Password<br/>bóveda HomeLab] -->|playbook-platform-secrets.yml| K8S
  subgraph K8S[Clúster k3s]
    ARGO[ArgoCD] -->|App maceosoft-argocd| GITOPS[(maceosoft/gitops)]
    ARGO --> ARC[ARC controller]
    ARC --> RT[arc-runners]
    RT --> STATE[(ns terraform<br/>Secret tfstate-default-github)]
  end
  INFRA[maceosoft/infra] -->|tofu.yml de core-pipelines| RT
  RT -->|App maceosoft-terraform| GH[org maceosoft]
```

Hay piezas que **tienen que existir antes** de que Argo CD o el pipeline
puedan funcionar. Esas se crean **a mano, una sola vez**, y OpenTofu no las
gestiona ni las importa:

| Qué | Por qué a mano |
|---|---|
| Repos `gitops`, `infra`, `core-pipelines` | Sin ellos no hay de dónde desplegar ni pipeline que corra OpenTofu |
| App `maceosoft-argocd` | Argo CD la necesita para leer el repo privado que despliega todo lo demás |
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
# tu cuenta
export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"
```

| Item | Tipo de item | Campos | Lo usa |
|---|---|---|---|
| `maceosoft-terraform` | Nota segura | `app_id`, `installation_id`, `private_key` | Runner de OpenTofu (`TF_VAR_github_app_*`) |
| `maceosoft-arc-runners` | Nota segura | `app_id`, `installation_id`, `private_key` | ARC (registro del runner) |
| `maceosoft-argocd` | Nota segura | `app_id`, `installation_id`, `private_key` | Argo CD lee `maceosoft/gitops` (`argocd/repo-gitops`) |
| `symintel-arc-runners` *(opcional)* | Nota segura | `app_id`, `installation_id`, `private_key` | ARC de la **org antigua** (`symintel`): registro de su scale set. Ver [Dos organizaciones](#dos-organizaciones-un-scale-set-por-org) |
| `symintel-terraform` *(opcional)* | Nota segura | `app_id`, `installation_id`, `private_key` | OpenTofu de la org antigua; sin él, esos runners no tienen credenciales de OpenTofu |
| `sealed-secrets` | Nota segura | `certificate`, `private_key` *(opcional hasta la Fase 6)* | Llave de cifrado de Sealed Secrets: sobrevive si reinstalas K3s |
| `maceosoft-dex` | Nota segura | `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` (+ `VCLUSTER_CLIENT_SECRET`, que genera el playbook) | Dex (login con GitHub) |
| `discord-webhooks` | Nota segura | `critical`, `warnings`: URL de un webhook de Discord por canal; `deployments` *(opcional)*: el del canal `despliegues` para las notificaciones de Argo CD *(opcional: monitoreo)* | Alertmanager envía las alertas ([4.13](../implementacion/fase-4-gitops.md#413-monitoreo-y-alertas-opcional)). Cómo crearlos: [Discord y healthchecks.io](discord-healthchecks.md#parte-1-discord) |
| `healthchecks-ping` | Nota segura | `url`: ping URL del check de healthchecks.io *(opcional: monitoreo)* | Alertmanager le manda un ping cada 5 minutos para avisar que el monitoreo sigue vivo. Cómo crearla: [Discord y healthchecks.io](discord-healthchecks.md#parte-2-healthchecksio) |
| `grafana-admin` | Nota segura | `password` y, si quieres, `username` (por defecto `admin`) *(opcional: monitoreo)* | Administrador de Grafana |
| `ftp-<repo>` | Nota segura | `dev_host`, `dev_user`, `dev_password`, `dev_remote_dir`, `prod_host`, `prod_user`, `prod_password`, `prod_remote_dir` | OpenTofu → secrets FTP de `<repo>` (`TF_VAR_ftp`) |

### Cómo crear un item con campos propios

El playbook busca cada valor por su ruta `op://HomeLab/<item>/<campo>`, así
que **el título del item y el nombre de cada campo tienen que ser exactos**
(minúsculas, con guion bajo).

=== "🖱️ Desde la interfaz"

    1. En 1Password abre la bóveda **`HomeLab`** → **Nuevo elemento** → **Nota
       segura** (*Secure Note*).
    2. En **Título** escribe el nombre del item, por ejemplo `maceosoft-terraform`.
    3. Por cada campo: **+ Añadir más** → elige el tipo (**Texto** o
       **Contraseña**) → en la etiqueta del campo escribe el nombre exacto
       (por ejemplo `app_id`) → pega el valor.
    4. Agrega los campos directamente en el item. **No crees una sección** para
       agruparlos: con sección la ruta cambia y el playbook no los encuentra.
    5. Guarda.

    Usa **Contraseña** para los valores secretos (se ocultan) y **Texto** para
    el resto. Cada tabla de abajo dice qué tipo lleva cada campo.

=== "⌨️ Desde la consola"

    También puedes crear el item con la CLI de 1Password (`op`), con 1Password desbloqueado. Cada campo se escribe como
    `nombre[tipo]=valor`, donde el tipo es `password` (valor secreto) o `text`; `op` crea los campos sueltos, sin sección.
    Los valores secretos no se escriben en el comando: se pegan sin eco con `read -rs`:

    ```bash
    # pega la contraseña y Enter (no se ve)
    read -rs FTP_DEV_PASS
    op item create --category "Secure Note" --vault HomeLab --title ftp-mi-repo \
      "dev_host[text]=ftp.ejemplo.com" "dev_user[text]=usuario" "dev_password[password]=$FTP_DEV_PASS"
    unset FTP_DEV_PASS
    ```

    Si tienes más de una cuenta de 1Password, exporta antes `OP_ACCOUNT` con la tuya. Para un valor aleatorio usa
    `$(openssl rand -hex 32)`. Los items de la IA local (tokens del router, Open Terminal…) ya tienen sus comandos en
    [Gestión de secretos](../secrets/index.md#ia-local-crear-los-tokens-con-op).

## Paso 1 — GitHub Apps y OAuth App (manual)

Hazlo con una cuenta **owner de la organización** `maceosoft`.

### `maceosoft-terraform`

[maceosoft → Settings → Developer settings → GitHub Apps → New GitHub App](https://github.com/organizations/maceosoft/settings/apps/new)

| Campo | Valor |
|---|---|
| GitHub App name | `maceosoft-terraform` |
| Homepage URL | `https://github.com/maceosoft` |
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
**`maceosoft-terraform`** de 1Password (Nota segura, ver
[cómo crearlo](#como-crear-un-item-con-campos-propios)):

| Campo en 1Password | Tipo | Dato | Dónde está en GitHub |
|---|---|---|---|
| `app_id` | Texto | App ID | Página de la App, pestaña *General*: línea **App ID** (un número, por ejemplo `1234567`) |
| `private_key` | Contraseña | Private key | Misma página, abajo en *Private keys* → **Generate a private key**. Se descarga un archivo `maceosoft-terraform.<fecha>.private-key.pem`. Ábrelo con un editor de texto y copia **todo**, incluidas las líneas `-----BEGIN RSA PRIVATE KEY-----` y `-----END RSA PRIVATE KEY-----` |
| `installation_id` | Texto | Installation ID | Menú izquierdo de la App → **Install App** → *Install* junto a `maceosoft` → **All repositories** → *Install*. GitHub te lleva a `https://github.com/organizations/maceosoft/settings/installations/<número>`: ese número final |

Así queda el item:

```text
maceosoft-terraform        (Nota segura · bóveda HomeLab)
├── app_id                1234567
├── installation_id       87654321
└── private_key           ••••••••   (el .pem completo)
```

**Se hacen solo desde la web:** crear la App, generar su llave privada (*Generate a private key*) y instalarla. GitHub no
ofrece CLI ni API para eso (la creación de Apps por manifiesto también exige confirmar en el navegador). Guardar los datos
en 1Password lo puedes hacer de las dos formas:

=== "🖱️ Desde la interfaz"

    Al pegar el `.pem` en un campo Contraseña se pierden los saltos de línea. No
    importa: el playbook reconstruye la llave. Cuando el item esté guardado,
    **borra el `.pem`** de Descargas.

=== "⌨️ Desde la consola"

    Lo que sí se automatiza es leer los dos números y guardar el item.

    1. Lista las Apps instaladas en la org y saca `App ID` e `Installation ID` (necesita el permiso de organización:
       `gh auth refresh -s admin:read:org` una sola vez):

        ```bash
        gh api orgs/maceosoft/installations --jq '.installations[] | [.app_slug, .app_id, .id, .repository_selection] | @tsv'
        ```

    2. Con el `.pem` descargado, crea el item (1Password desbloqueado; si tienes más de una cuenta de 1Password, exporta
       `OP_ACCOUNT` antes). El valor del `.pem` se lee del archivo y nunca se escribe en el comando:

        ```bash
        APP=maceosoft-terraform
        read -r APP_ID INST_ID < <(gh api orgs/maceosoft/installations \
          --jq ".installations[] | select(.app_slug==\"$APP\") | \"\(.app_id) \(.id)\"")
        op item create --category "Secure Note" --vault HomeLab --title "$APP" \
          "app_id[text]=$APP_ID" "installation_id[text]=$INST_ID" \
          "private_key[password]=$(cat ~/Downloads/$APP.*.private-key.pem)"
        ```

    3. Verifica sin mostrar valores y borra el `.pem`:

        ```bash
        python3 ansible/scripts/apply_platform_secrets.py --check
        # en macOS: rm -P
        shred -u ~/Downloads/$APP.*.private-key.pem
        ```

    El mismo comando sirve para las demás Apps: solo cambia `APP` (`maceosoft-arc-runners`, `maceosoft-argocd`, y
    `symintel-arc-runners` / `symintel-terraform` si usas la org antigua, cambiando `orgs/maceosoft` por `orgs/symintel`).

### `maceosoft-arc-runners`

Es la App con la que ARC registra el runner `arc-runners` en la org. Se
crea en el mismo formulario que `maceosoft-terraform`, pero es **otra App**:
nombre, permisos y credenciales propios.

[maceosoft → Settings → Developer settings → GitHub Apps → New GitHub App](https://github.com/organizations/maceosoft/settings/apps/new)

| Campo | Valor |
|---|---|
| GitHub App name | `maceosoft-arc-runners` |
| Homepage URL | `https://github.com/maceosoft` |
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
**`maceosoft-arc-runners`** de 1Password (Nota segura, ver
[cómo crearlo](#como-crear-un-item-con-campos-propios)):

| Campo en 1Password | Tipo | Dato | Dónde está en GitHub |
|---|---|---|---|
| `app_id` | Texto | App ID | Página de la App, pestaña *General*: línea **App ID** |
| `private_key` | Contraseña | Private key | Misma página, abajo en *Private keys* → **Generate a private key**. Se descarga `maceosoft-arc-runners.<fecha>.private-key.pem`. Ábrelo con un editor de texto y copia **todo**, incluidas las líneas `-----BEGIN RSA PRIVATE KEY-----` y `-----END RSA PRIVATE KEY-----` |
| `installation_id` | Texto | Installation ID | Menú izquierdo de la App → **Install App** → *Install* junto a `maceosoft` → **All repositories** → *Install*. El número al final de la URL `https://github.com/organizations/maceosoft/settings/installations/<número>` |

Así queda el item:

```text
maceosoft-arc-runners      (Nota segura · bóveda HomeLab)
├── app_id                2345678
├── installation_id       98765432
└── private_key           ••••••••   (el .pem completo)
```

Crear la App, su llave e instalarla es **solo desde la web**; guardar el item lo puedes hacer de las dos formas:

=== "🖱️ Desde la interfaz"

    Los tres valores son **distintos** de los de `maceosoft-terraform`: cada App
    tiene su App ID, su llave y su instalación. No copies los de la otra. Cuando
    el item esté guardado, **borra el `.pem`** de Descargas.

=== "⌨️ Desde la consola"

    El mismo comando de [`maceosoft-terraform`](#maceosoft-terraform) con `APP=maceosoft-arc-runners`: `gh api` saca los
    números de esta App, así que no se mezclan con los de la otra.

    ```bash
    APP=maceosoft-arc-runners
    read -r APP_ID INST_ID < <(gh api orgs/maceosoft/installations \
      --jq ".installations[] | select(.app_slug==\"$APP\") | \"\(.app_id) \(.id)\"")
    op item create --category "Secure Note" --vault HomeLab --title "$APP" \
      "app_id[text]=$APP_ID" "installation_id[text]=$INST_ID" \
      "private_key[password]=$(cat ~/Downloads/$APP.*.private-key.pem)"
    python3 ansible/scripts/apply_platform_secrets.py --check
    # en macOS: rm -P
    shred -u ~/Downloads/$APP.*.private-key.pem
    ```

### OAuth App `Maceosoft Dex`

[maceosoft → Settings → Developer settings → OAuth Apps → New OAuth App](https://github.com/organizations/maceosoft/settings/applications/new)

| Campo | Valor |
|---|---|
| Application name | `Maceosoft Dex` |
| Homepage URL | `https://argocd.homelab.local` |
| Redirect URIs | `https://argocd.homelab.local/api/dex/callback` (solo esta) |

Después de *Register application*, crea el item **`maceosoft-dex`** en la
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
maceosoft-dex              (Nota segura · bóveda HomeLab)
├── GITHUB_CLIENT_ID      Ov23li…
├── GITHUB_CLIENT_SECRET  ••••••••
└── VCLUSTER_CLIENT_SECRET ••••••••  (lo genera el playbook)
```

**Crear la OAuth App y generar su client secret se hace solo desde la web**: GitHub no tiene API para OAuth Apps. Guardar
los dos valores en 1Password lo puedes hacer de las dos formas:

=== "🖱️ Desde la interfaz"

    Crea la Nota segura `maceosoft-dex` y pega cada valor de la tabla en su campo
    ([cómo crearlo](#como-crear-un-item-con-campos-propios)).

=== "⌨️ Desde la consola"

    Una vez que tienes los dos valores, guárdalos sin que se vean en pantalla (si tienes más de una cuenta de 1Password,
    exporta `OP_ACCOUNT` antes):

    ```bash
    # pega el Client ID y Enter
    read -r  GH_CID
    # pega el Client secret y Enter
    read -rs GH_CSEC
    op item create --category "Secure Note" --vault HomeLab --title maceosoft-dex \
      "GITHUB_CLIENT_ID[text]=$GH_CID" "GITHUB_CLIENT_SECRET[password]=$GH_CSEC"
    unset GH_CID GH_CSEC
    ```

Para comprobar que alguien está en el team `devops` (o agregarlo) desde la consola:
`gh api orgs/maceosoft/teams/devops/memberships/<usuario>` (devuelve `"state": "active"`) y, para sumarlo como miembro,
`gh api -X PUT orgs/maceosoft/teams/devops/memberships/<usuario> -f role=member`.

Solo puede entrar el team **`devops`** de `maceosoft`, y sus miembros quedan
como admin de Argo CD. Se aplica en el
[paso 4.7 de la Fase 4](../implementacion/fase-4-gitops.md#47-secretos-oauth-github-vcluster-incus-ui).

## Paso 2 — Repos, App de Argo CD y FTP (manual) {#paso-2-repos-app-de-argocd-y-ftp-manual}

1. **Repos** (privados), creados en `maceosoft` y con su contenido subido con git:
    - `gitops`.
    - `core-pipelines`: después hay que dejarlo accesible para los demás repos de la org (abajo).
      Mientras pruebas, los demás repos lo usan con `@main`; el tag `v1` se
      crea cuando todo funcione (ver el README de `core-pipelines`).
    - `infra`.

    === "🖱️ Desde la interfaz"

        Crea cada repo en la org con **New repository** (privado) y sube su contenido con git. Después, en
        `core-pipelines`: *Settings → Actions → General → Access*,
        elige "Accessible from repositories in the 'maceosoft' organization".

    === "⌨️ Desde la consola"

        Con la CLI de GitHub, desde la carpeta de cada proyecto:

        ```bash
        gh repo create maceosoft/gitops --private --source . --remote origin --push
        # igual para core-pipelines e infra
        gh repo list maceosoft --json name,visibility --jq '.[] | [.name, .visibility] | @tsv'
        # core-pipelines accesible desde los demás repos de la org
        gh api -X PUT repos/maceosoft/core-pipelines/actions/permissions/access -f access_level=organization
        ```
2. **GitHub App `maceosoft-argocd`**, con la que Argo CD lee el repo privado
   `gitops`. Va después de los repos porque se instala **solo** en `gitops`.
   (Las deploy keys están deshabilitadas en la organización, por eso se usa
   una App.)

    [maceosoft → Settings → Developer settings → GitHub Apps → New GitHub App](https://github.com/organizations/maceosoft/settings/apps/new)

    | Campo | Valor |
    |---|---|
    | GitHub App name | `maceosoft-argocd` |
    | Homepage URL | `https://github.com/maceosoft` |
    | Webhook → Active | desmarcado |
    | Where can this GitHub App be installed? | Only on this account |

    El resto del formulario se deja vacío o sin marcar.

    | Repository permission | Acceso | Para qué |
    |---|---|---|
    | Contents | Read-only | Clonar el repo |
    | Metadata | Read-only | Obligatorio |

    Sin permisos de organización. Todos los demás quedan en *No access*.

    Después de *Create GitHub App*, guarda sus tres datos en el item
    **`maceosoft-argocd`** de 1Password (Nota segura, ver
    [cómo crearlo](#como-crear-un-item-con-campos-propios)):

    | Campo en 1Password | Tipo | Dato | Dónde está en GitHub |
    |---|---|---|---|
    | `app_id` | Texto | App ID | Página de la App, pestaña *General*: línea **App ID** |
    | `private_key` | Contraseña | Private key | Misma página, abajo en *Private keys* → **Generate a private key**. Copia **todo** el `.pem` descargado, incluidas las líneas `BEGIN`/`END` |
    | `installation_id` | Texto | Installation ID | Menú izquierdo → **Install App** → *Install* junto a `maceosoft` → **Only select repositories** → elige **`gitops`** → *Install*. El número al final de la URL `…/settings/installations/<número>` |

    Instálala **solo en `gitops`**: con esa llave se puede leer el código de
    todos los repos donde esté instalada. Borra el `.pem` al terminar.

    Crear la App, su llave e instalarla es **solo desde la web**; guardar el item lo puedes hacer de las dos formas:

    === "🖱️ Desde la interfaz"

        Crea la Nota segura `maceosoft-argocd` y pega cada dato de la tabla en su campo
        ([cómo crearlo](#como-crear-un-item-con-campos-propios)).

    === "⌨️ Desde la consola"

        El mismo comando de [`maceosoft-terraform`](#maceosoft-terraform), con `APP=maceosoft-argocd`:

        ```bash
        APP=maceosoft-argocd
        read -r APP_ID INST_ID < <(gh api orgs/maceosoft/installations \
          --jq ".installations[] | select(.app_slug==\"$APP\") | \"\(.app_id) \(.id)\"")
        op item create --category "Secure Note" --vault HomeLab --title "$APP" \
          "app_id[text]=$APP_ID" "installation_id[text]=$INST_ID" \
          "private_key[password]=$(cat ~/Downloads/$APP.*.private-key.pem)"
        # en macOS: rm -P
        shred -u ~/Downloads/$APP.*.private-key.pem
        ```

3. **Credenciales FTP (File Transfer Protocol) del repo `api`**, el primer
   proyecto del mapa con `deploy = true`: título **`ftp-api`**, tipo Nota
   segura. Para cada repo que agregues después, sigue el
   [procedimiento — Agregar un repo](../operacion/agregar-repo.md). Campos, [creado igual que los otros](#como-crear-un-item-con-campos-propios):

    === "🖱️ Desde la interfaz"

        | Campo | Tipo | Ejemplo |
        |---|---|---|
        | `dev_host` | Texto | `dev.tu-cpanel.example.com` |
        | `dev_user` | Texto | `usuario_dev` |
        | `dev_password` | Contraseña | |
        | `dev_remote_dir` | Texto | `/home/usuario/dev.maceosoft.example.com` |
        | `prod_host` | Texto | `tu-cpanel.example.com` |
        | `prod_user` | Texto | `usuario_prod` |
        | `prod_password` | Contraseña | |
        | `prod_remote_dir` | Texto | `/home/usuario/public_html` |

    === "⌨️ Desde la consola"

        Cambia los hosts, usuarios y carpetas por los tuyos; las dos contraseñas se pegan sin eco (si tienes más de
        una cuenta de 1Password, exporta `OP_ACCOUNT` antes):

        ```bash
        # pega cada contraseña y Enter
        read -rs FTP_DEV_PASS;  read -rs FTP_PROD_PASS
        op item create --category "Secure Note" --vault HomeLab --title ftp-api \
          "dev_host[text]=dev.tu-cpanel.example.com" "dev_user[text]=usuario_dev" \
          "dev_password[password]=$FTP_DEV_PASS" "dev_remote_dir[text]=/home/usuario/dev.maceosoft.example.com" \
          "prod_host[text]=tu-cpanel.example.com" "prod_user[text]=usuario_prod" \
          "prod_password[password]=$FTP_PROD_PASS" "prod_remote_dir[text]=/home/usuario/public_html"
        unset FTP_DEV_PASS FTP_PROD_PASS
        ```

4. **Llave de Sealed Secrets** *(opcional: hace falta cuando empieces a
   guardar `SealedSecret` en Git, p. ej. en la Fase 6)*. Sealed Secrets
   cifra los secretos con un par de llaves que, por defecto, el controlador
   genera dentro del clúster: si reinstalas K3s se pierde, y los
   `SealedSecret` que ya estaban en Git dejan de poder descifrarse. Por eso
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

    === "🖱️ Desde la interfaz"

        | Campo | Tipo | Valor |
        |---|---|---|
        | `certificate` | Texto | El contenido completo de `tls.crt` (la llave **pública**), con las líneas `-----BEGIN CERTIFICATE-----` y `-----END CERTIFICATE-----` |
        | `private_key` | Contraseña | El contenido completo de `tls.key` (la llave **privada**), con sus líneas `BEGIN`/`END` |

        Para copiar un archivo: `pbcopy < tls.crt` (macOS) o ábrelo con un editor
        y copia todo.

    === "⌨️ Desde la consola"

        Con la CLI de 1Password los archivos se leen directamente (si tienes más de una cuenta de 1Password, exporta
        `OP_ACCOUNT` antes):

        ```bash
        op item create --category "Secure Note" --vault HomeLab --title sealed-secrets \
          "certificate[text]=$(cat tls.crt)" "private_key[password]=$(cat tls.key)"
        python3 ansible/scripts/apply_platform_secrets.py --check
        ```

    Cuando el item esté guardado, **borra los archivos**:

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

Con k3s instalado ([Fase 3](../implementacion/fase-3-k3s.md), Argo CD incluido):

```bash
# tu cuenta
export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"
cd ansible
ansible-playbook -i inventory.ini playbook-platform-secrets.yml
```

[`playbook-platform-secrets.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-platform-secrets.yml)
crea los namespaces `argocd`, `arc-runners` (PSS `baseline`) y `terraform`
(solo guarda el state de OpenTofu), y estos Secrets:

| Secret | Namespace | Contenido |
|---|---|---|
| `repo-gitops` | `argocd` | App `maceosoft-argocd`: Argo CD puede clonar `https://github.com/maceosoft/gitops.git` |
| `arc-runners-github-app` | `arc-runners` | App de ARC |
| `terraform-app` | `arc-runners` | `TF_VAR_github_app_id`, `TF_VAR_github_app_installation_id`, `TF_VAR_github_app_private_key` |
| `tofu-vars` | `arc-runners` | `TF_VAR_ftp` (todos los items `ftp-<repo>`) |
| `arc-runners-github-app`, `terraform-app` | `arc-runners-symintel` | Lo mismo para la org antigua, desde `symintel-arc-runners` y `symintel-terraform` (solo si existen). El namespace se crea con PSS `baseline` |
| `sealed-secrets-key-homelab` | `kube-system` | Par de llaves de Sealed Secrets (item `sealed-secrets`, si existe) |
| `discord-webhooks`, `healthchecks-ping`, `grafana-admin` | `monitoring` | Webhooks de Discord, ping URL de healthchecks.io y contraseña de Grafana (los items del mismo nombre; solo si existen los tres). El namespace se crea con PSS `privileged`, porque `node-exporter` usa el disco y la red del nodo |

!!! note "Un solo runner"
    Es un HomeLab: el único scale set (`arc-runners`, grupo Default) corre CI (integración continua),
    deploys y OpenTofu, y tiene las credenciales de OpenTofu como variables de
    entorno. Cualquier repo de `maceosoft` que corra un job ahí puede
    alcanzarlas. Mantén la org solo con repos tuyos.

!!! warning "Siempre contra el HomeLab"
    El playbook usa `~/.kube/homelab-k3s.yaml` (el que deja
    `k3s_fetch_kubeconfig`), **no** el contexto actual de `kubectl`. Así no
    escribe secretos en otro clúster. Para otro kubeconfig:
    `-e platform_kubeconfig=/ruta`.

Es idempotente: vuelve a correrlo cada vez que rotes algo en 1Password o agregues
un item `ftp-<repo>`.

## Dos organizaciones: un scale set por org

Un scale set de ARC se registra en **una sola** organización de GitHub (`githubConfigUrl`). Para que los mismos runners
atiendan a la org nueva (`maceosoft`) y a la antigua (`symintel`) hay **dos scale sets**, con un solo controller
(`arc-controller`) que atiende a los dos:

| | Org `maceosoft` | Org `symintel` (antigua) |
|---|---|---|
| Application | `arc-runners` | `arc-runners-symintel` |
| Namespace | `arc-runners` | `arc-runners-symintel` |
| App de ARC (item de 1Password) | `maceosoft-arc-runners` | `symintel-arc-runners` |
| Nombre en `runs-on:` | `arc-runners` | `arc-runners` (el mismo) |
| Caché `/cache` (RWX, Longhorn) | 20 GiB | 10 GiB, propia |
| Docker (`dind`) | No | Sí, con un sidecar privilegiado; namespace con `enforce=privileged` |
| OpenTofu y FTP | Sí (`terraform-app`, `tofu-vars`) | Solo si existe el item `symintel-terraform` |

Los dos usan **la misma plantilla** de runner
([`values-scaleset.yaml`](https://github.com/maceosoft/gitops/blob/main/arc/values-scaleset.yaml)); la org antigua cambia
`githubConfigUrl` ([`values-scaleset-symintel.yaml`](https://github.com/maceosoft/gitops/blob/main/arc/values-scaleset-symintel.yaml)).
Cada namespace tiene sus propios Secrets, con **el mismo nombre**, así que los de una org no los ve la otra, y la caché tampoco se
comparte (una caché envenenada en una org no llega a la otra).

Para activar la org antigua: crea en `symintel` la App de ARC (igual que [`maceosoft-arc-runners`](#maceosoft-arc-runners), pero en esa
org) y guárdala en el item `symintel-arc-runners`; después corre `playbook-platform-secrets.yml`. Si el item no existe, el script no
crea el namespace ni el Secret y el scale set de la org antigua no arranca. Para quitarla, borra la Application
`arc-runners-symintel` y los items.

## Paso 4 — GitOps

```bash
kubectl apply -f gitops/bootstrap/root-appset.yaml
```

Argo CD sincroniza, entre otras, estas Applications:

| Application | Qué despliega |
|---|---|
| `arc-controller` | Controller de ARC (`arc-systems`) |
| `terraform-rbac` | ServiceAccount `tofu-runner` + Role (solo Secrets/Leases del namespace `terraform`) |
| `arc-runners` | El runner (hasta 3 en paralelo), con los Secrets del namespace como variables de entorno |

## Paso 5 — Primer pipeline de OpenTofu

Haz un push a `main` de `infra`, o lánzalo desde *Actions → tofu →
Run workflow* (con la CLI: `gh workflow run tofu.yml --repo maceosoft/infra --ref main` y `gh run watch --repo maceosoft/infra`). El workflow
[`tofu.yml`](https://github.com/maceosoft/core-pipelines/blob/main/.github/workflows/tofu.yml)
corre en `arc-runners`: hace `plan` en los PRs (pull requests) y `apply` en `main`. En la
primera ejecución crea `api`.

## Verificar

Antes del clúster, que 1Password tenga todo (desde la raíz de `homelab`):

```bash
# tu cuenta
export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"
# items y campos: todo ✓
.venv/bin/python ansible/scripts/apply_platform_secrets.py --check
# Secrets que se van a crear, sin valores
.venv/bin/python ansible/scripts/apply_platform_secrets.py --dry-run
```

Después del playbook y de GitOps:

```bash
kubectl -n argocd get secret repo-gitops
kubectl -n arc-runners get secret \
  arc-runners-github-app terraform-app tofu-vars
# org antigua, si la usas:
kubectl -n arc-runners-symintel get secret arc-runners-github-app
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
| Private key de una GitHub App | Genera una nueva en GitHub (solo web), reemplaza `private_key` en 1Password (`op item edit <item> "private_key[password]=$(cat llave.pem)"`), re-corre `playbook-platform-secrets.yml` y borra la vieja en GitHub |
| Private key de `maceosoft-argocd` | Igual que las otras Apps: nueva llave en GitHub, reemplaza `private_key`, re-corre el playbook y borra la vieja |
| Credenciales FTP | Edita `ftp-<repo>` (`op item edit ftp-<repo> "prod_password[password]=..."`), re-corre el playbook y lanza el pipeline de `infra` (`gh workflow run tofu.yml --repo maceosoft/infra --ref main`) |
| Webhook de Discord, ping URL de healthchecks.io o contraseña de Grafana | Cambia el campo en su item, re-corre `playbook-platform-secrets.yml` y sigue [Operación — Rotar credenciales](../operacion/rotar-credenciales.md#monitoreo-webhooks-de-discord-ping-de-healthchecksio-y-grafana) |
| Client secret de Dex | Nuevo secret en la OAuth App, actualiza `GITHUB_CLIENT_SECRET` y corre `playbook-dex-oauth-secrets.yml` |
