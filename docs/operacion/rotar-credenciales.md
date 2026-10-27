# Rotar credenciales

Reemplaza una credencial por otra nueva: periódicamente, o de inmediato si
sospechas que se filtró. En todos los casos la credencial nueva se guarda
primero en 1Password (bóveda `HomeLab`) y después se lleva al clúster.

!!! info "Antes de empezar"
    La app de 1Password desbloqueada, con *Integrate with other apps*, y la
    cuenta en la variable de entorno:

    ```bash
    # tu cuenta
    export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"
    ```

    Los comandos de Ansible se corren desde `ansible/` en `homelab`.

## Resumen

| Credencial | Item en 1Password | Se aplica con |
|---|---|---|
| Private key de una GitHub App (`maceosoft-terraform`, `maceosoft-arc-runners`, `maceosoft-argocd`) | el item con el nombre de la App | `playbook-platform-secrets.yml` |
| Credenciales FTP de un repo | `ftp-<repo>` | `playbook-platform-secrets.yml` + pipeline de `infra` |
| Client secret de Dex (login con GitHub) | `maceosoft-dex` | `playbook-dex-oauth-secrets.yml` |
| Webhooks de Discord, ping URL de healthchecks.io y contraseña de Grafana (monitoreo) | `discord-webhooks`, `healthchecks-ping`, `grafana-admin` | `playbook-platform-secrets.yml` ([ver abajo](#monitoreo-webhooks-de-discord-ping-de-healthchecksio-y-grafana)) |
| Clave de sesión de Open WebUI (asistente de IA) | `open-webui` (campo `WEBUI_SECRET_KEY`) | `playbook-platform-secrets.yml` ([cómo generarla](ia-ollama.md#crear-la-clave-de-open-webui-una-sola-vez)) |
| Tokens del router de Ollama (uno por cliente y el de registro de nodos) | `ollama-router` (campos `registry_token`, `open-webui`, `k8sgpt`, `reports`, `alert-triage`, `translate`) | `playbook-platform-secrets.yml` ([ver abajo](#tokens-de-ollama-y-de-servicios-internos)) |
| Token del webhook de `alert-triage` y clave de API de `mcpo` | `alert-triage-webhook` (campo `token`), `mcp-api-key` (campo `key`) | `playbook-platform-secrets.yml` ([ver abajo](#tokens-de-ollama-y-de-servicios-internos)) |
| Clave de API de Open Terminal | `open-terminal` (campo `api_key`) | `playbook-platform-secrets.yml` ([ver abajo](#tokens-de-ollama-y-de-servicios-internos)) |
| Webhook del canal `#ia` (reportes con IA) | `discord-webhooks` (campo `ai`) | `playbook-platform-secrets.yml` ([crear el canal](logs.md#crear-el-canal-ia-y-su-webhook-una-sola-vez)) |
| Contraseña de root de los nodos | `root@<nodo>` (la crea el playbook) | `playbook-rotate-root-passwords.yml` |
| Llave de Sealed Secrets | `sealed-secrets` | `playbook-platform-secrets.yml` ([ojo: ver abajo](#llave-de-sealed-secrets)) |
| Token de Argo CD del pipeline de `gitops` (cuenta `ci`) | `argocd-ci` | `playbook-platform-secrets.yml` ([cómo generarlo](pipeline-gitops.md#activar-el-diff-contra-el-cluster-una-vez)) |

## Private key de una GitHub App

1. En GitHub: *maceosoft → Settings → Developer settings → GitHub Apps →*
   la App → *Private keys* → **Generate a private key**. Esto se hace **solo desde la web**: ni `gh` ni la API
   permiten generar o borrar llaves de una GitHub App.
2. Guarda la llave nueva en 1Password:

    === "🖱️ Desde la interfaz"

        En 1Password, reemplaza el campo `private_key` del item de esa App por el
        contenido completo del `.pem` nuevo.

    === "⌨️ Desde la consola"

        Con 1Password desbloqueado (si tienes más de una cuenta, exporta `OP_ACCOUNT` antes). El `.pem` se lee del
        archivo, así que la llave no queda escrita en el comando:

        ```bash
        op item edit maceosoft-terraform "private_key[password]=$(cat ~/Downloads/maceosoft-terraform.<fecha>.private-key.pem)"
        # comprueba que tiene contenido, sin mostrarlo
        op read "op://HomeLab/maceosoft-terraform/private_key" | wc -c
        ```

        Cambia `maceosoft-terraform` por el item de la App que rotes (`maceosoft-arc-runners` o `maceosoft-argocd`).

3. Comprueba y aplica:

    ```bash
    ../.venv/bin/python scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

4. Si es la App de ARC (`maceosoft-arc-runners`), reinicia su *listener* para
   que tome la llave nueva: `kubectl -n arc-systems get pods` y borra el pod
   del listener (se recrea solo). Los runners nuevos ya usan la llave nueva. En un solo comando:
   `kubectl -n arc-systems delete pod -l app.kubernetes.io/component=runner-scale-set-listener` (reinicia todos los
   listeners del namespace, lo que no causa problemas).
5. Cuando todo funcione, borra la llave **vieja** en GitHub (misma página,
   *Delete* junto a la llave anterior) y el `.pem` descargado.

??? tip "Con la CLI"
    Para borrar el `.pem` descargado y revisar el App ID y el Installation ID:

    ```bash
    # en macOS: rm -P
    shred -u ~/Downloads/maceosoft-terraform.<fecha>.private-key.pem
    # App ID e Installation ID
    gh api orgs/maceosoft/installations --jq '.installations[] | [.app_slug, .app_id, .id] | @tsv'
    ```

    `gh` necesita el permiso de organización: `gh auth refresh -s admin:read:org`.

## Credenciales FTP de un repo

1. Cambia la contraseña en cPanel y actualiza el item `ftp-<repo>`:

    === "🖱️ Desde la interfaz"

        En la app de 1Password, reemplaza el campo `dev_password` (o `prod_password` para producción) del item.

    === "⌨️ Desde la consola"

        Pega la contraseña cuando te la pida; no se ve en pantalla ni queda en el historial:

        ```bash
        read -rs P; op item edit ftp-<repo> "dev_password[password]=$P"; unset P
        ```

        Usa `prod_password` para producción.

2. Aplica y relanza el pipeline, que carga los secrets nuevos en los
   environments del repo:

    ```bash
    ../.venv/bin/python scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

    Después relanza el pipeline de `maceosoft/infra` sobre `main`:

    === "🖱️ Desde la interfaz"

        En `maceosoft/infra`: *Actions → tofu → Run workflow* sobre `main`.

    === "⌨️ Desde la consola"

        ```bash
        gh workflow run tofu.yml --repo maceosoft/infra --ref main
        gh run watch --repo maceosoft/infra
        ```

## Client secret de Dex

1. En la OAuth App *Maceosoft Dex*: **Generate a new client secret**. GitHub
   lo muestra una sola vez.
   Generar el secret en la OAuth App **solo se hace desde la web**.
2. Guarda el secret nuevo:

    === "🖱️ Desde la interfaz"

        Reemplaza `GITHUB_CLIENT_SECRET` en el item `maceosoft-dex`.

    === "⌨️ Desde la consola"

        Pega el secret cuando te lo pida; no se ve en pantalla ni queda en el historial:

        ```bash
        read -rs S; op item edit maceosoft-dex "GITHUB_CLIENT_SECRET[password]=$S"; unset S
        ```

3. Aplica (actualiza `argocd-secret` y reinicia Dex):

    ```bash
    ansible-playbook -i inventory.ini playbook-dex-oauth-secrets.yml --tags argocd
    ```

4. Prueba el login con GitHub en Argo CD y después borra el secret viejo en la
   OAuth App.

## Monitoreo: webhooks de Discord, ping de healthchecks.io y Grafana

Son opcionales ([4.13](../implementacion/fase-4-gitops.md#413-monitoreo-y-alertas-opcional)). Los tres viven en 1Password y el
playbook los lleva al namespace `monitoring`; nunca se escriben en Git.

1. Genera el valor nuevo:

    === "🖱️ Desde la interfaz"

        - **Webhook de Discord:** Discord no permite regenerar el token de un webhook. En *Server Settings → Integrations → Webhooks*, usa
          **Delete Webhook** y crea uno nuevo ([cómo](../maceosoft/discord-healthchecks.md#4-un-webhook-por-canal)); copia su URL.
        - **Ping URL de healthchecks.io:** crea un check nuevo con la misma configuración (**Period** de 5 minutos, **Grace Time** de 10 y su
          integración con Discord), copia su ping URL y borra el viejo. Los pasos están en
          [Discord y healthchecks.io](../maceosoft/discord-healthchecks.md#parte-2-healthchecksio).
        - **Contraseña de Grafana:** una nueva en 1Password.

    === "⌨️ Desde la consola"

        - **Webhook de Discord:** borrar el viejo se puede con su propia URL (pégala cuando te la pida, no se ve); el
          nuevo se crea **solo desde la web o la app** de Discord
          ([cómo](../maceosoft/discord-healthchecks.md#4-un-webhook-por-canal)):

            ```bash
            read -rs HOOK; curl -fsS -X DELETE "$HOOK"; unset HOOK
            ```

        - **Ping URL de healthchecks.io:** con la [API](https://healthchecks.io/docs/api/) y la API key (read-write) del
          proyecto. Crea el check nuevo con los mismos valores (`timeout` es el *Period* y `grace` el *Grace Time*, en
          segundos; `"channels":"*"` le conecta las integraciones que ya tienes, como la de Discord), guarda su ping URL
          en 1Password y borra el viejo:

            ```bash
            # pega la API key y Enter (no se ve)
            read -rs HC_KEY
            OLD=$(curl -fsS -H "X-Api-Key: $HC_KEY" https://healthchecks.io/api/v3/checks/ \
              | jq -r '.checks[] | select(.name=="homelab-monitoreo") | .uuid')
            NEW_URL=$(curl -fsS -H "X-Api-Key: $HC_KEY" \
              -d '{"name":"homelab-monitoreo","timeout":300,"grace":600,"channels":"*"}' \
              https://healthchecks.io/api/v3/checks/ | jq -r .ping_url)
            op item edit healthchecks-ping "url[password]=$NEW_URL"
            curl -fsS -X DELETE -H "X-Api-Key: $HC_KEY" "https://healthchecks.io/api/v3/checks/$OLD"
            unset HC_KEY NEW_URL OLD
            ```

            Con esto el campo `url` ya queda actualizado y te puedes saltar el paso 2 para la ping URL.

        - **Contraseña de Grafana:** se genera y se guarda en el paso 2, con un solo comando.

2. Reemplaza el campo en su item (`critical`, `warnings` o `deployments` en `discord-webhooks`, `url` en `healthchecks-ping`, `password` en
   `grafana-admin`):

    === "🖱️ Desde la interfaz"

        En la app de 1Password, abre el item y pega el valor nuevo en su campo.

    === "⌨️ Desde la consola"

        Un webhook se pega cuando te lo pida (no se ve ni queda en el historial); la contraseña de Grafana se genera
        dentro del comando:

        ```bash
        read -rs V; op item edit discord-webhooks "critical[password]=$V"; unset V
        op item edit grafana-admin "password[password]=$(openssl rand -base64 24)"
        ```

3. Comprueba y aplica:

    ```bash
    ../.venv/bin/python scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

4. Si tras unos minutos Alertmanager sigue usando el valor anterior, reinicia su pod; para la contraseña de Grafana, reinicia su
   Deployment (el volumen es efímero y vuelve a leerla al arrancar):

    ```bash
    kubectl -n monitoring get pods
    kubectl -n monitoring rollout restart deploy/vm-grafana
    ```

5. Prueba con la alerta de prueba del [paso 7 de 4.13](../implementacion/fase-4-gitops.md#413-monitoreo-y-alertas-opcional).

## Tokens de Ollama y de servicios internos

Los clientes del [router de Ollama](ia-ollama.md) se autentican con un token Bearer, uno por cliente, para poder
rotar uno sin tocar el resto. Todos se generan igual: 32 bytes aleatorios en hexadecimal (64 caracteres).

```bash
openssl rand -hex 32
```

| Item de 1Password | Campos | Quién lo usa |
|---|---|---|
| `ollama-router` | `registry_token` | Los nodos de Ollama, para registrarse en el router |
| `ollama-router` | `open-webui`, `k8sgpt`, `reports`, `alert-triage`, `translate` | Cada cliente del router. `translate` es además el secreto `OLLAMA_TOKEN` de GitHub Actions, que usa la traducción de esta documentación |
| `alert-triage-webhook` | `token` | Alertmanager, al llamar a `alert-triage` |
| `mcp-api-key` | `key` | Open WebUI, al llamar a las herramientas MCP (`mcpo`) |
| `open-terminal` | `api_key` | Open WebUI, al llamar a Open Terminal ([guía](ia-ollama.md#open-terminal-terminal-para-el-asistente)). Tras aplicar, reinicia los pods de Open Terminal y de Open WebUI |

Para rotar uno:

1. Genera el valor nuevo y reemplaza **solo ese campo** en 1Password (mínimo 32 caracteres, sin espacios):

    === "🖱️ Desde la interfaz"

        Genera el valor con el comando de arriba (`openssl rand -hex 32`) y pégalo en el campo del item, en la app de
        1Password.

    === "⌨️ Desde la consola"

        El valor se genera dentro del comando, así que nunca lo ves. Por ejemplo, para el token `reports` y para
        `mcp-api-key`:

        ```bash
        op item edit ollama-router "reports[password]=$(openssl rand -hex 32)"
        op item edit mcp-api-key "key[password]=$(openssl rand -hex 32)"
        ```

        Otros comandos: [Gestión de secretos](../secrets/index.md#ia-local-crear-los-tokens-con-op).

2. Comprueba y aplica:

    ```bash
    cd ansible
    ../.venv/bin/python scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

3. Reinicia el servicio que lo lee para que tome el valor nuevo (`kubectl -n <namespace> rollout restart deploy/<nombre>`):
   el router y el cliente cuyo token cambió (el router también recarga los tokens cada 30 segundos). Para
   `registry_token`, además actualiza el token en cada nodo (Linux: volver a aplicar `playbook-ollama.yml --tags register`;
   Mac: reemplaza el archivo `token` de la carpeta del agente, o el del Keychain, y `ollama-node off` / `ollama-node on`).
4. **Tokens de registro por nodo (opcional).** Si usas una clave `registry_token-<nombre-del-nodo>` en el Secret
   `ai/ollama-router-secrets`, solo ese token registra ese nodo. Para rotarlo: cambia ese valor en el Secret, actualiza
   el token en ese nodo y comprueba que sigue apareciendo en `/_registry/nodes`. El token compartido sigue valiendo para
   los nodos que no tengan uno propio, así que para **retirar por completo** el compartido hay que dar uno propio a
   cada nodo antes.
5. Si rotaste `translate`, actualiza también el secreto `OLLAMA_TOKEN` de GitHub Actions:

    === "🖱️ Desde la interfaz"

        En *maceosoft/homelab → Settings → Secrets and variables → Actions*, edita `OLLAMA_TOKEN` y pega el valor del
        campo `translate`.

    === "⌨️ Desde la consola"

        El valor viaja por una tubería, sin imprimirse:

        ```bash
        op read "op://HomeLab/ollama-router/translate" | gh secret set OLLAMA_TOKEN --repo maceosoft/homelab
        ```

## Contraseña de root de los nodos

Cada corrida genera y aplica una contraseña nueva por nodo, y la guarda en el
item `root@<nodo>`. No afecta al SSH (Secure Shell): el login de root por SSH
ya está deshabilitado; esta contraseña es para la consola.

```bash
# todos
ansible-playbook -i inventory.ini playbook-rotate-root-passwords.yml
ansible-playbook -i inventory.ini playbook-rotate-root-passwords.yml --limit deborah
```

## Llave de Sealed Secrets

**No se rota a la ligera.** Los `SealedSecret` que ya están en Git se cifraron
con la llave actual: si la cambias, esos archivos dejan de poder
descifrarse. La llave no vence en la práctica (el certificado vale 10 años) y
la renovación automática está desactivada.

Solo hay que tocarla si se filtró la llave **privada**. En ese caso:

1. Genera un par nuevo
   ([comando](../maceosoft/github.md#paso-2-repos-app-de-argocd-y-ftp-manual)).
2. **Antes de reemplazar nada**, vuelve a sellar cada secreto con la llave
   nueva (`kubeseal --cert <tls.crt nuevo> …`) y commitea los `SealedSecret`
   nuevos.
3. Reemplaza `certificate` y `private_key` en el item `sealed-secrets`,
   re-corre `playbook-platform-secrets.yml` y reinicia el controlador:
   `kubectl -n kube-system rollout restart deploy/sealed-secrets`.

    === "🖱️ Desde la interfaz"

        En la app de 1Password, pega el contenido de `tls.crt` en `certificate` y el de `tls.key` en `private_key`.

    === "⌨️ Desde la consola"

        Los dos valores se leen de los archivos nuevos, sin quedar escritos en el comando:

        ```bash
        op item edit sealed-secrets "certificate[text]=$(cat tls.crt)" "private_key[password]=$(cat tls.key)"
        ```

**Reinstalar K3s** no es una rotación: con el item en 1Password, el playbook
vuelve a crear el mismo Secret y los `SealedSecret` de Git siguen
funcionando. Hazlo **antes** de activar `sealed-secrets` en
`root-appset.yaml`.

## Verificar

- `apply_platform_secrets.py --check` muestra todo en ✓.
- Argo CD sigue sincronizando `gitops` (`kubectl get applications -n argocd`).
- El runner aparece *Online* en *maceosoft → Settings → Actions → Runners* (con la CLI: `gh api orgs/maceosoft/actions/runners --jq '.runners[] | [.name, .status] | @tsv'`).
- El login con GitHub funciona en Argo CD.
