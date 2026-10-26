# Rotar credenciales

Reemplaza una credencial por otra nueva: periódicamente, o de inmediato si
sospechas que se filtró. En todos los casos la credencial nueva se guarda
primero en 1Password (bóveda `HomeLab`) y después se lleva al clúster.

!!! info "Antes de empezar"
    La app de 1Password desbloqueada, con *Integrate with other apps*, y la
    cuenta en la variable de entorno:

    ```bash
    export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"  # tu cuenta
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
| Token de ArgoCD del pipeline de `gitops` (cuenta `ci`) | `argocd-ci` | `playbook-platform-secrets.yml` ([cómo generarlo](pipeline-gitops.md#activar-el-diff-contra-el-cluster-una-vez)) |

## Private key de una GitHub App

1. En GitHub: *maceosoft → Settings → Developer settings → GitHub Apps →*
   la App → *Private keys* → **Generate a private key**.
2. En 1Password, reemplaza el campo `private_key` del item de esa App por el
   contenido completo del `.pem` nuevo.
3. Comprueba y aplica:

    ```bash
    ../.venv/bin/python scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

4. Si es la App de ARC (`maceosoft-arc-runners`), reinicia su *listener* para
   que tome la llave nueva: `kubectl -n arc-systems get pods` y borra el pod
   del listener (se recrea solo). Los runners nuevos ya usan la llave nueva.
5. Cuando todo funcione, borra la llave **vieja** en GitHub (misma página,
   *Delete* junto a la llave anterior) y el `.pem` descargado.

## Credenciales FTP de un repo

1. Cambia la contraseña en cPanel y actualiza el item `ftp-<repo>`.
2. Aplica y relanza el pipeline, que carga los secrets nuevos en los
   environments del repo:

    ```bash
    ../.venv/bin/python scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

    Después, en `maceosoft/infra`: *Actions → tofu → Run workflow* sobre `main`.

## Client secret de Dex

1. En la OAuth App *Maceosoft Dex*: **Generate a new client secret**. GitHub
   lo muestra una sola vez.
2. Reemplaza `GITHUB_CLIENT_SECRET` en el item `maceosoft-dex`.
3. Aplica (actualiza `argocd-secret` y reinicia Dex):

    ```bash
    ansible-playbook -i inventory.ini playbook-dex-oauth-secrets.yml --tags argocd
    ```

4. Prueba el login con GitHub en ArgoCD y después borra el secret viejo en la
   OAuth App.

## Monitoreo: webhooks de Discord, ping de healthchecks.io y Grafana

Son opcionales ([4.13](../implementacion/fase-4-gitops.md#413-monitoreo-y-alertas-opcional)). Los tres viven en 1Password y el
playbook los lleva al namespace `monitoring`; nunca se escriben en git.

1. Genera el valor nuevo:
    - **Webhook de Discord:** Discord no permite regenerar el token de un webhook. En *Server Settings → Integrations → Webhooks*, usa
      **Delete Webhook** y crea uno nuevo ([cómo](../maceosoft/discord-healthchecks.md#4-un-webhook-por-canal)); copia su URL.
    - **Ping URL de healthchecks.io:** crea un check nuevo con la misma configuración (**Period** de 5 minutos, **Grace Time** de 10 y su
      integración con Discord), copia su ping URL y borra el viejo. Los pasos están en
      [Discord y healthchecks.io](../maceosoft/discord-healthchecks.md#parte-2-healthchecksio).
    - **Contraseña de Grafana:** una nueva en 1Password.
2. Reemplaza el campo en su item (`critical`, `warnings` o `deployments` en `discord-webhooks`, `url` en `healthchecks-ping`, `password` en
   `grafana-admin`).
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

1. Genera el valor nuevo y reemplaza **solo ese campo** en 1Password (mínimo 32 caracteres, sin espacios).
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
5. Si rotaste `translate`, actualiza también el secreto `OLLAMA_TOKEN` en *maceosoft/homelab → Settings → Secrets and
   variables → Actions*.

## Contraseña de root de los nodos

Cada corrida genera y aplica una contraseña nueva por nodo, y la guarda en el
item `root@<nodo>`. No afecta al SSH (Secure Shell): el login de root por SSH
ya está deshabilitado; esta contraseña es para la consola.

```bash
ansible-playbook -i inventory.ini playbook-rotate-root-passwords.yml               # todos
ansible-playbook -i inventory.ini playbook-rotate-root-passwords.yml --limit deborah
```

## Llave de Sealed Secrets

**No se rota a la ligera.** Los `SealedSecret` que ya están en git se cifraron
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

**Reinstalar K3s** no es una rotación: con el item en 1Password, el playbook
vuelve a crear el mismo Secret y los `SealedSecret` de git siguen
funcionando. Hazlo **antes** de activar `sealed-secrets` en
`root-appset.yaml`.

## Verificar

- `apply_platform_secrets.py --check` muestra todo en ✓.
- ArgoCD sigue sincronizando `gitops` (`kubectl get applications -n argocd`).
- El runner aparece *Online* en *maceosoft → Settings → Actions → Runners*.
- El login con GitHub funciona en ArgoCD.
