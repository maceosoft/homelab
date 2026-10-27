# Fase 0 — Preparación

## Objetivo

Tener el repo clonado, Ansible operativo, inventario validado y (opcional)
un informe de hardware medido antes de tocar red o clústeres.

## Qué aprendes

Cómo Ansible usa un **inventario** como fuente de verdad de hosts, y por qué
un **discovery** opcional evita suposiciones sobre RAM, disco y arquitectura
al elegir roles (control plane, Longhorn, etc.).

!!! abstract "Aprende esta fase"
    **En simple:** Ansible es como una lista de tareas que entregas a varios ayudantes: todos la
    ejecutan igual, sin que tengas que ir uno por uno. El **inventario** es la agenda con el nombre,
    la dirección y el rol de cada ayudante (cada nodo).

    **Conceptos clave**

    - **Inventario:** el archivo que dice qué equipos existen y cómo conectarse a ellos.
    - **Playbook:** la receta de tareas que Ansible aplica a esos equipos.
    - **Idempotencia:** repetir un playbook deja el mismo resultado; no rompe lo que ya estaba bien.
    - **Modo simulación (`-C`):** muestra qué cambiaría sin tocar nada.
    - **SSH (Secure Shell):** el canal cifrado con el que Ansible entra a cada nodo.

    **Reto práctico (seguro, solo lectura):** comprueba que Ansible llega a los tres nodos y ve qué cambiaría
    un playbook sin aplicarlo.

    ```bash
    ansible -i ansible/inventory.ini incus_cluster -m ping
    ansible-playbook -i ansible/inventory.ini ansible/playbook-discovery.yml -C
    ```

    ??? question "¿Para qué sirve un inventario?"
        Para que Ansible sepa qué equipos administrar, cómo llegar a ellos y a qué grupo pertenece cada uno.
        Es la fuente de verdad de los nodos.

    ??? question "¿Por qué se puede repetir un playbook idempotente sin miedo?"
        Porque cada tarea revisa primero el estado actual y solo cambia lo que falta. Si todo ya está bien,
        no hace nada.

    ??? question "¿Qué diferencia hay entre ejecutar un playbook y ejecutarlo con `-C`?"
        Con `-C` Ansible simula: informa qué cambiaría pero no modifica los equipos.

    ¿Dudas? Usa el botón **Aprende con IA** junto a cada título, o la página [Aprende](../aprende.md).

## Stack de esta fase

```mermaid
flowchart LR
  Op[Operador] --> Repo[Repo_homelab]
  Op --> Ansible[Ansible]
  Ansible --> Inv[inventory.ini]
  Ansible --> Disc[playbook_discovery]
  Disc --> Reports[reports_md]
```

- **[Ansible](https://docs.ansible.com/)** — Orquestador de bootstrap; Fase 0–3.
- **[Debian](https://www.debian.org/)** — SO en invincible, oliver y deborah.

Profundización: [Discovery de hardware](../hardware/discovery.md) · [Inventario](../hardware/inventory.md)

## Antes de empezar

- [x] Tres nodos accesibles por SSH (aunque aún con DHCP está bien).
- [x] Python 3.11+ en tu estación.
- [x] Clave SSH configurada hacia los nodos.
- [x] **GitHub:** la organización **`maceosoft`** creada, con un team
      **`devops`** (sus miembros son quienes pueden entrar a Argo CD) y una
      cuenta que sea **owner** de la organización para crear las Apps.
      Detalle en [Plataforma maceosoft — GitHub](../maceosoft/github.md).
      Crear la organización es **solo desde la web**; el team lo puedes crear de las dos formas:

    === "🖱️ Desde la interfaz"

        En la org: **Teams** → **New team** → nombre `devops`, visibilidad *Visible* → **Create team**, y después
        **Add a member** por cada persona que deba entrar a Argo CD.

    === "⌨️ Desde la consola"

        Necesita el permiso de administración de la org (`gh auth refresh -s admin:org`, una sola vez). Quien crea el
        team queda como su *maintainer*; los demás se suman con el segundo comando:

        ```bash
        gh api orgs/maceosoft/teams -f name=devops -f privacy=closed
        gh api -X PUT orgs/maceosoft/teams/devops/memberships/<usuario> -f role=member
        ```

- [x] **1Password:** la app de escritorio instalada, con una bóveda llamada
      **`HomeLab`** y *Settings → Developer → Integrate with other apps*
      activado. Ahí se guardan las credenciales que usan los playbooks
      ([qué items y campos](../maceosoft/github.md#items-en-1password)).
      La integración con la app se activa **solo desde la app**; la bóveda la puedes crear de las dos formas:

    === "🖱️ Desde la interfaz"

        En la app de 1Password: barra lateral → **+** junto a las bóvedas (*New Vault*) → nombre `HomeLab` → **Create**.

    === "⌨️ Desde la consola"

        Con la app desbloqueada y la integración ya activada (si tienes más de una cuenta, exporta `OP_ACCOUNT` antes):

        ```bash
        op vault create HomeLab
        op vault list
        ```

## Ejecutar

### Clonar repo y entorno Ansible

```bash
git clone https://github.com/maceosoft/homelab.git
cd homelab
python3 -m venv .venv
source .venv/bin/activate
# Ansible, mkdocs, ansible-lint, etc.
pip install -r requirements.txt
ansible-galaxy collection install -r ansible/requirements.yml
```

!!! warning "Ruta del requirements.txt"
    `requirements.txt` vive en la **raíz del repo**, no en `ansible/` — es un
    error común confundirlo con `ansible/requirements.yml` (ese es el
    manifiesto de *collections* de Galaxy, un archivo YAML distinto, no algo
    que `pip install -r` pueda instalar).

### Día 0 — nodos recién instalados (solo la primera vez por nodo)

Un nodo recién flasheado (Debian netinst) todavía no tiene `python3` ni
`sudo` listos, y el usuario admin no está en el grupo `sudo` — el `ping`
de más abajo (usa el módulo `ansible.builtin.ping`, que sí necesita Python
en el destino) va a fallar sin este paso primero:

```bash
cd ansible
ansible-playbook -i bootstrap/inventory.ini bootstrap/setup_sudo.yml --ask-pass
cd ..
```

**Qué usuario recibe `sudo`.** El playbook da `sudo` sin contraseña al usuario administrador que creaste al
instalar Debian. Por defecto es el **mismo nombre que usas en tu estación**, porque Ansible se conecta después con
ese nombre. Si en el nodo se llama distinto, indícalo y dile a Ansible cómo conectarse:

```bash
ansible-playbook -i bootstrap/inventory.ini bootstrap/setup_sudo.yml --ask-pass -e bootstrap_admin_user=<usuario>
```

y agrega `ansible_user=<usuario>` a los nodos en `inventory.ini`. El usuario tiene que existir ya en el nodo (el
playbook se detiene si no) y solo admite minúsculas, dígitos, `_` y `-`.

Detalle completo (por qué conecta como `root` y dónde encaja en el resto
del bootstrap) en
[`ansible/bootstrap/README.md`](https://github.com/maceosoft/homelab/blob/main/ansible/bootstrap/README.md).
Si tus 3 nodos ya tienen un usuario admin con sudo funcionando, omite
este paso.

### Validar inventario

Revisa [`ansible/inventory.ini`][inventory-ini]: `ansible_host`, `static_ip`,
`bridge_iface` por nodo.

[inventory-ini]: https://github.com/maceosoft/homelab/blob/main/ansible/inventory.ini

```bash
ansible -i ansible/inventory.ini incus_cluster -m ping
```

### Discovery opcional (recomendado la primera vez)

=== "Recomendado (Ansible)"

    ```bash
    cd ansible
    ansible-playbook -i inventory.ini playbook-discovery.yml
    ```

    Salida en `ansible/reports/` (gitignored): ficha por nodo + `summary.md`.

=== "Alternativa manual"

    Recopila CPU, RAM, disco y red con `lscpu`, `free -h`, `lsblk`, `ip -br link`
    y compara con [Inventario de hardware](../hardware/inventory.md).

### GitHub y 1Password — org maceosoft (manual, una sola vez)

Aquí se preparan, una sola vez, las cuentas y credenciales de GitHub que el
HomeLab necesita: las Apps con las que el clúster habla con GitHub (entre
ellas la que usa Argo CD para leer el repo privado `maceosoft/gitops`) y los
repos base (`gitops`, `core-pipelines` e `infra`). Todo se crea a mano, y las credenciales se
guardan en 1Password para que después los playbooks las lean desde ahí. El
detalle de cada una (permisos, dónde encontrar cada dato en GitHub y cómo
cargarlo en 1Password) está en
[Plataforma maceosoft — GitHub](../maceosoft/github.md).

Los items de 1Password van en la bóveda **`HomeLab`**, casi todos como
**Nota segura** con campos propios. El título del item y el nombre de cada
campo tienen que ser **exactos**, porque el playbook los busca por nombre:
[cómo crear el item](../maceosoft/github.md#como-crear-un-item-con-campos-propios).

Con una cuenta **owner de la organización** `maceosoft`:

1. **GitHub App `maceosoft-terraform`** → item `maceosoft-terraform`.
   [Permisos y dónde está cada dato](../maceosoft/github.md#maceosoft-terraform).
   Crear la App, generar su llave privada (`.pem`) e instalarla se hace **solo desde la web**; guardar sus datos en
   1Password lo puedes hacer de las dos formas:

    === "🖱️ Desde la interfaz"

        Nota segura en la bóveda `HomeLab` con los campos `app_id` (Texto), `installation_id` (Texto) y
        `private_key` (Contraseña, el `.pem` completo).

    === "⌨️ Desde la consola"

        `gh api` te da el `app_id` y el `installation_id` de la App instalada (una sola vez antes:
        `gh auth refresh -s admin:read:org`), y el `.pem` se lee del archivo, así que ningún valor queda escrito en
        el comando:

        ```bash
        APP=maceosoft-terraform
        read -r APP_ID INST_ID < <(gh api orgs/maceosoft/installations \
          --jq ".installations[] | select(.app_slug==\"$APP\") | \"\(.app_id) \(.id)\"")
        op item create --category "Secure Note" --vault HomeLab --title "$APP" \
          "app_id[text]=$APP_ID" "installation_id[text]=$INST_ID" \
          "private_key[password]=$(cat ~/Downloads/$APP.*.private-key.pem)"
        ```

2. **GitHub App `maceosoft-arc-runners`** → item `maceosoft-arc-runners`.
   [Permisos y pasos](../maceosoft/github.md#maceosoft-arc-runners).
   Igual que la anterior: la App se crea e instala **solo desde la web**.

    === "🖱️ Desde la interfaz"

        Los mismos tres campos pero con los datos de esta App: `app_id` (Texto), `installation_id` (Texto) y
        `private_key` (Contraseña), en una Nota segura de la bóveda `HomeLab`.

    === "⌨️ Desde la consola"

        ```bash
        APP=maceosoft-arc-runners
        read -r APP_ID INST_ID < <(gh api orgs/maceosoft/installations \
          --jq ".installations[] | select(.app_slug==\"$APP\") | \"\(.app_id) \(.id)\"")
        op item create --category "Secure Note" --vault HomeLab --title "$APP" \
          "app_id[text]=$APP_ID" "installation_id[text]=$INST_ID" \
          "private_key[password]=$(cat ~/Downloads/$APP.*.private-key.pem)"
        ```

3. **OAuth (Open Authorization) App `Maceosoft Dex`** → item `maceosoft-dex`.
   [Pasos](../maceosoft/github.md#oauth-app-maceosoft-dex).
   Crear la OAuth App y generar su *client secret* es **solo desde la web** (GitHub no tiene API para OAuth Apps).

    === "🖱️ Desde la interfaz"

        Campos `GITHUB_CLIENT_ID` (Texto) y `GITHUB_CLIENT_SECRET` (Contraseña) en el item `maceosoft-dex` (Nota
        segura, bóveda `HomeLab`).

    === "⌨️ Desde la consola"

        Pega cada valor cuando te lo pida; el secreto no se ve en pantalla ni queda en el historial:

        ```bash
        # pega el Client ID y Enter
        read -r  GH_CID
        # pega el Client secret y Enter
        read -rs GH_CSEC
        op item create --category "Secure Note" --vault HomeLab --title maceosoft-dex \
          "GITHUB_CLIENT_ID[text]=$GH_CID" "GITHUB_CLIENT_SECRET[password]=$GH_CSEC"
        unset GH_CID GH_CSEC
        ```

4. **Repos privados**, con su contenido subido con git:
    - `gitops`.
    - `core-pipelines`: accesible desde los demás repos de la org. No hace
      falta crear tags: mientras pruebas, los demás repos lo usan con `@main`.
    - `infra`.

    === "🖱️ Desde la interfaz"

        Crea cada repo en la org con **New repository** (privado) y sube su contenido con git. En `core-pipelines`,
        en *Settings → Actions → General → Access*, elige
        "Accessible from repositories in the 'maceosoft' organization".

    === "⌨️ Desde la consola"

        Desde la carpeta de cada proyecto:

        ```bash
        gh repo create maceosoft/gitops --private --source . --remote origin --push
        # igual para core-pipelines e infra
        gh api -X PUT repos/maceosoft/core-pipelines/actions/permissions/access -f access_level=organization
        ```

5. **GitHub App `maceosoft-argocd`** (solo lectura, instalada **solo en
   `gitops`**) → item `maceosoft-argocd`. Va
   después de los repos porque se instala en `gitops`.
   [Permisos y pasos](../maceosoft/github.md#paso-2-repos-app-de-argocd-y-ftp-manual).
   La App se crea e instala **solo desde la web**.

    === "🖱️ Desde la interfaz"

        Los mismos tres campos: `app_id` (Texto), `installation_id` (Texto) y `private_key` (Contraseña), en una
        Nota segura de la bóveda `HomeLab`.

    === "⌨️ Desde la consola"

        ```bash
        APP=maceosoft-argocd
        read -r APP_ID INST_ID < <(gh api orgs/maceosoft/installations \
          --jq ".installations[] | select(.app_slug==\"$APP\") | \"\(.app_id) \(.id)\"")
        op item create --category "Secure Note" --vault HomeLab --title "$APP" \
          "app_id[text]=$APP_ID" "installation_id[text]=$INST_ID" \
          "private_key[password]=$(cat ~/Downloads/$APP.*.private-key.pem)"
        ```

6. **Llave de Sealed Secrets** *(opcional hasta la Fase 6)*: un par de llaves
   generado con `openssl`, en el item `sealed-secrets`, para que sobreviva si reinstalas K3s.
   [Comando y pasos](../maceosoft/github.md#paso-2-repos-app-de-argocd-y-ftp-manual).

    === "🖱️ Desde la interfaz"

        Nota segura en la bóveda `HomeLab` con `certificate` (Texto, todo `tls.crt`) y `private_key` (Contraseña,
        todo `tls.key`).

    === "⌨️ Desde la consola"

        Genera el par en una carpeta temporal, guárdalo leyendo los archivos y bórralos:

        ```bash
        cd "$(mktemp -d)"
        openssl req -x509 -days 3650 -nodes -newkey rsa:4096 \
          -keyout tls.key -out tls.crt -subj "/CN=sealed-secret/O=sealed-secret"
        op item create --category "Secure Note" --vault HomeLab --title sealed-secrets \
          "certificate[text]=$(cat tls.crt)" "private_key[password]=$(cat tls.key)"
        rm -f tls.key tls.crt
        ```

7. **Credenciales FTP (File Transfer Protocol) del repo `api`**: `api` es el
   primer proyecto del mapa de repos y despliega por FTP, así que necesita su
   item `ftp-api` (Nota segura) desde el primer pipeline. Cada repo que
   agregues después sigue el
   [procedimiento de rutina — Agregar un repo](../operacion/agregar-repo.md).
   [Tabla con ejemplos](../maceosoft/github.md#paso-2-repos-app-de-argocd-y-ftp-manual).

    === "🖱️ Desde la interfaz"

        El item lleva 8 campos: `dev_host`, `dev_user`,
        `dev_password`, `dev_remote_dir` y los mismos cuatro con `prod_`. Los
        `*_password` van como Contraseña y el resto como Texto.

    === "⌨️ Desde la consola"

        Cambia los hosts, usuarios y carpetas por los tuyos; las dos contraseñas se pegan sin eco:

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

Todos los comandos para crear estos items con la CLI `op` (y los de GitHub con `gh`) están en las secciones de
[Plataforma maceosoft — GitHub](../maceosoft/github.md): las Apps y la OAuth App se **crean solo desde la web**, y de ahí en
adelante guardar los datos en 1Password, listar instalaciones y crear los repos se hace con `op` y `gh`.

Comprueba que todas las credenciales se pueden leer de 1Password. Son dos
comandos, y ninguno toca un clúster ni muestra valores secretos:

- **`--check`**: revisa cada item esperado y marca con ✓ los campos que están
  bien y con ✗ los que faltan, tienen otro nombre o están dentro de una
  sección. Córrelo primero: si algo está mal, dice exactamente qué.
- **`--dry-run`**: lee todos los valores y lista los Secrets que se van a
  crear en el clúster, con los valores ocultos (`<redacted>`). Confirma que
  las llaves se pueden interpretar.

El script lee 1Password a través de la app de escritorio, así que la app
tiene que estar **desbloqueada** y con *Settings → Developer → Integrate with
other apps* activado. Además hay que decirle **qué cuenta** usar con la
variable **`ONEPASSWORD_ACCOUNT_NAME`**: es el nombre de tu cuenta tal como
aparece arriba a la izquierda en la barra lateral de la app (por ejemplo
`Mi Cuenta`). Si no la defines, usa `Personal`.

```bash
# tu cuenta
export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"
.venv/bin/python ansible/scripts/apply_platform_secrets.py --check
.venv/bin/python ansible/scripts/apply_platform_secrets.py --dry-run
```

`--check` termina bien cuando todos los items tienen ✓ (el aviso de que no
hay items `ftp-<repo>` es solo informativo si ningún repo despliega).

## Opciones

| Opción | Cuándo |
|---|---|
| Saltar discovery | Re-despliegue y hardware ya conocido |
| Actualizar inventario | Tras cambiar IPs en Fase 1 |

<div class="card">
  <div class="card-kicker">Análisis de trade-offs</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">Discovery Ansible</div>
      <div class="text-muted">RAM/disco/I/O medidos → <code>reports/</code></div>
      <div class="text-muted">Requiere SSH y unos minutos por nodo</div>
    </div>
    <div class="card-col">
      <div class="card-title">Discovery manual</div>
      <div class="text-muted">Sin playbook</div>
      <div class="text-muted">Valores desactualizados; errores de planificación</div>
    </div>
    <div class="card-col">
      <div class="card-title">Saltar discovery</div>
      <div class="text-muted">Más rápido en re-despliegues</div>
      <div class="text-muted">Presupuesto RAM/disco puede no coincidir con la realidad</div>
    </div>
  </div>
</div>

## Verificar

```bash
ansible -i ansible/inventory.ini incus_cluster -m ping
# todos → SUCCESS

# tu cuenta
export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"
.venv/bin/python ansible/scripts/apply_platform_secrets.py --check
# todos los items con ✓
.venv/bin/python ansible/scripts/apply_platform_secrets.py --dry-run
# lista los Secrets de plataforma (valores <redacted>), sin errores de 1Password
```

## Si falla

| Síntoma | Revisar |
|---|---|
| `UNREACHABLE` | `ansible_host`, firewall, clave SSH |
| `ping` falla por Python ausente | Nodo recién instalado — correr `setup_sudo.yml` (paso "Día 0" arriba) |
| Discovery sin reports | Ejecutar desde `ansible/`; permisos de escritura |
| `--check` o `--dry-run` no leen 1Password | App desbloqueada con *Integrate with other apps* y `ONEPASSWORD_ACCOUNT_NAME` con el nombre de tu cuenta. Si dice *field cannot be found* o *Bóveda no encontrada*, mira la salida de `--check`: marca qué item o campo no coincide ([nombres esperados](../maceosoft/github.md#items-en-1password)) |

## Siguiente

**[→ Fase 1 — Red](fase-1-red.md)**
