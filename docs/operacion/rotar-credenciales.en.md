# Rotate credentials

Replace a credential with a new one: periodically, or immediately if you suspect it was leaked. In all cases the new credential is saved first in 1Password (vault `HomeLab`) and then brought to the cluster.

!!! info "Before you start"
    The 1Password app unlocked, with *Integrate with other apps*, and the account in the environment variable:

    ```bash
    # tu cuenta
    export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"
    ```

    Ansible commands are run from `ansible/` in `homelab`.

## Summary

| Credential | 1Password item | Applied with |
|---|---|---|
| Private key of a GitHub App (`maceosoft-arc-runners`, `maceosoft-argocd`) | the item named after the App | `playbook-platform-secrets.yml` (`maceosoft-terraform` no longer reads it: runners don't carry OpenTofu credentials) |
| FTP credentials of a repo | `ftp-<repo>` | No longer reach the cluster: `playbook-platform-secrets.yml` doesn't read them ([see Add a repo](agregar-repo.md#2-only-if-it-deploys-ftp-credentials-in-1password)) |
| Dex client secret (GitHub login) | `maceosoft-dex` | `playbook-dex-oauth-secrets.yml` |
| Discord webhooks, healthchecks.io ping URL, and Grafana password (monitoring) | `discord-webhooks`, `healthchecks-ping`, `grafana-admin` | `playbook-platform-secrets.yml` ([see below](#monitoring-discord-webhooks-healthchecksio-ping-and-grafana)) |
| Open WebUI session key (AI assistant) | `open-webui` (field `WEBUI_SECRET_KEY`) | `playbook-platform-secrets.yml` ([how to generate it](ia-ollama.md#create-the-open-webui-key-once)) |
| Ollama router tokens (one per client and the node registration token) | `ollama-router` (fields `registry_token`, `open-webui`, `k8sgpt`, `reports`, `alert-triage`, `translate`) | `playbook-platform-secrets.yml` ([see below](#ollama-and-internal-services-tokens)) |
| `alert-triage` webhook token and `mcpo` API key | `alert-triage-webhook` (field `token`), `mcp-api-key` (field `key`) | `playbook-platform-secrets.yml` ([see below](#ollama-and-internal-services-tokens)) |
| Open Terminal API key | `open-terminal` (field `api_key`) | `playbook-platform-secrets.yml` ([see below](#ollama-and-internal-services-tokens)) |
| `#ia` channel webhook (AI reports) | `discord-webhooks` (field `ai`) | `playbook-platform-secrets.yml` ([create the channel](logs.md#create-the-ia-channel-and-its-webhook-once-only)) |
| Password of the `homelab_agent` role in the platform PostgreSQL | `postgres-homelab-agent` (field `password`; the playbook generates it if missing) | `playbook-platform-secrets.yml` ([see below](#platform-postgresql)) |
| Incus bucket `postgres-backups` key (PostgreSQL backups) | `postgres-s3` (fields `access_key`, `secret_key`) | Incus + `playbook-platform-secrets.yml` ([see below](#platform-postgresql)) |
| Incus S3 certificate (not a secret: renewed yearly) | — | `playbook-incus-s3.yml -e incus_s3_confirm=true` ([renewal](../storage/postgres.md#renovacion)) |
| Root password of nodes | `root@<nodo>` (created by the playbook) | `playbook-rotate-root-passwords.yml` |
| Sealed Secrets key | `sealed-secrets` | `playbook-platform-secrets.yml` ([note: see below](#sealed-secrets-key)) |
| Argo CD token of the `gitops` pipeline (account `ci`, expires in 90 days) | `argocd-ci` | GitHub Actions secret `ARGOCD_CI_TOKEN` of `maceosoft/gitops`, not the playbook ([how to generate and renew it](pipeline-gitops.md#activar-el-diff-contra-el-cluster-una-vez)) |

## Private key of a GitHub App

1. In GitHub: *maceosoft → Settings → Developer settings → GitHub Apps →* the App → *Private keys* → **Generate a private key**. This is done **only from the web**: neither `gh` nor the API allow generating or deleting keys of a GitHub App.
2. Save the new key in 1Password:

    === "🖱️ From the UI"

        In 1Password, replace the `private_key` field of that App's item with the full content of the new `.pem`.

    === "⌨️ From the console"

        With 1Password unlocked (if you have more than one account, export `OP_ACCOUNT` first). The `.pem` is read from the file, so the key is not written in the command:

        ```bash
        op item edit maceosoft-terraform "private_key[password]=$(cat ~/Downloads/maceosoft-terraform.<fecha>.private-key.pem)"
        # comprueba que tiene contenido, sin mostrarlo
        op read "op://HomeLab/maceosoft-terraform/private_key" | wc -c
        ```

        Change `maceosoft-terraform` to the item of the App you are rotating (`maceosoft-arc-runners` or `maceosoft-argocd`).

3. Verify and apply:

    ```bash
    ../.venv/bin/python scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

4. If it's the ARC App (`maceosoft-arc-runners`), restart its *listener* so it picks up the new key: `kubectl -n arc-systems get pods` and delete the listener pod (it recreates itself). New runners already use the new key. In a single command: `kubectl -n arc-systems delete pod -l app.kubernetes.io/component=runner-scale-set-listener` (restarts all listeners in the namespace, which causes no issues).
5. When everything works, delete the **old** key in GitHub (same page, *Delete* next to the previous key) and the downloaded `.pem`.

??? tip "With the CLI"
    To delete the downloaded `.pem` and review the App ID and Installation ID:

    ```bash
    # en macOS: rm -P
    shred -u ~/Downloads/maceosoft-terraform.<fecha>.private-key.pem
    # App ID e Installation ID
    gh api orgs/maceosoft/installations --jq '.installations[] | [.app_slug, .app_id, .id] | @tsv'
    ```

    `gh` needs the organization permission: `gh auth refresh -s admin:read:org`.

## FTP credentials of a repo

1. Change the password in cPanel and update the `ftp-<repo>` item:

    === "🖱️ From the UI"

        In the 1Password app, replace the `dev_password` field (or `prod_password` for production) of the item.

    === "⌨️ From the console"

        Paste the password when prompted; it is not shown on screen or kept in history:

        ```bash
        read -rs P; op item edit ftp-<repo> "dev_password[password]=$P"; unset P
        ```

        Use `prod_password` for production.

2. Apply and re-run the pipeline, which loads the new secrets into the repo environments:

    ```bash
    ../.venv/bin/python scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

    Then re-run the `maceosoft/infra` pipeline on `main`:

    === "🖱️ From the UI"

        In `maceosoft/infra`: *Actions → tofu → Run workflow* on `main`.

    === "⌨️ From the console"

        ```bash
        gh workflow run tofu.yml --repo maceosoft/infra --ref main
        gh run watch --repo maceosoft/infra
        ```

## Dex client secret

1. In the OAuth App *Maceosoft Dex*: **Generate a new client secret**. GitHub shows it only once. Generating the secret in the OAuth App **is only done from the web**.
2. Save the new secret:

    === "🖱️ From the UI"

        Replace `GITHUB_CLIENT_SECRET` in the `maceosoft-dex` item.

    === "⌨️ From the console"

        Paste the secret when prompted; it is not shown on screen or kept in history:

        ```bash
        read -rs S; op item edit maceosoft-dex "GITHUB_CLIENT_SECRET[password]=$S"; unset S
        ```

3. Apply (updates `argocd-secret` and restarts Dex):

    ```bash
    ansible-playbook -i inventory.ini playbook-dex-oauth-secrets.yml --tags argocd
    ```

4. Test GitHub login in Argo CD and then delete the old secret in the OAuth App.

## Monitoring: Discord webhooks, healthchecks.io ping, and Grafana

They are optional ([4.13](../implementacion/fase-4-gitops.md#413-monitoring-and-alerts-optional)). All three live in 1Password and the playbook places them in the `monitoring` namespace; they are never written to Git.

1. Generate the new value:

    === "🖱️ From the UI"

        - **Discord webhook:** Discord does not allow regenerating a webhook token. In *Server Settings → Integrations → Webhooks*, use **Delete Webhook** and create a new one ([how](../maceosoft/discord-healthchecks.md#4-one-webhook-per-channel)); copy its URL.
        - **healthchecks.io ping URL:** create a new check with the same configuration (**Period** of 5 minutes, **Grace Time** of 10, and its Discord integration), copy its ping URL, and delete the old one. The steps are in [Discord and healthchecks.io](../maceosoft/discord-healthchecks.md#part-2-healthchecksio).
        - **Grafana password:** a new one in 1Password.

    === "⌨️ From the console"

        - **Discord webhook:** deleting the old one can be done with its own URL (paste it when prompted, it is not shown); the new one is created **only from the Discord web UI or app** ([how](../maceosoft/discord-healthchecks.md#4-one-webhook-per-channel)):

            ```bash
            read -rs HOOK; curl -fsS -X DELETE "$HOOK"; unset HOOK
            ```

        - **healthchecks.io ping URL:** using the [API](https://healthchecks.io/docs/api/) and the project's API key (read-write). Create the new check with the same values (`timeout` is the *Period* and `grace` the *Grace Time*, in seconds; `"channels":"*"` connects the integrations you already have, such as Discord), save its ping URL in 1Password, and delete the old one:

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

            With this, the `url` field is already updated and you can skip step 2 for the ping URL.

        - **Grafana password:** generated and saved in step 2, with a single command.

2. Replace the field in its item (`critical`, `warnings`, or `deployments` in `discord-webhooks`, `url` in `healthchecks-ping`, `password` in `grafana-admin`):

    === "🖱️ From the UI"

        In the 1Password app, open the item and paste the new value into its field.

    === "⌨️ From the console"

        A webhook is pasted when prompted (not shown and not kept in history); the Grafana password is generated inside the command:

        ```bash
        read -rs V; op item edit discord-webhooks "critical[password]=$V"; unset V
        op item edit grafana-admin "password[password]=$(openssl rand -base64 24)"
        ```

3. Verify and apply:

    ```bash
    ../.venv/bin/python scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

4. If after a few minutes Alertmanager is still using the previous value, restart its pod; for the Grafana password, restart its Deployment (the volume is ephemeral and reads it again on startup):

    ```bash
    kubectl -n monitoring get pods
    kubectl -n monitoring rollout restart deploy/vm-grafana
    ```

5. Test with the test alert from [step 7 of 4.13](../implementacion/fase-4-gitops.md#413-monitoring-and-alerts-optional).

## Ollama and internal services tokens

Clients of the [Ollama router](ia-ollama.md) authenticate with a Bearer token, one per client, so one can be rotated without affecting the rest. All are generated the same way: 32 random bytes in hexadecimal (64 characters).

```bash
openssl rand -hex 32
```

| 1Password Item | Fields | Used by |
|---|---|---|
| `ollama-router` | `registry_token` | Ollama nodes, to register with the router |
| `ollama-router` | `open-webui`, `k8sgpt`, `reports`, `alert-triage`, `translate` | Each router client. `translate` is also the `OLLAMA_TOKEN` secret in GitHub Actions, used by the translation of this documentation |
| `alert-triage-webhook` | `token` | Alertmanager, when calling `alert-triage` |
| `mcp-api-key` | `key` | Open WebUI, when calling MCP tools (`mcpo`) |
| `open-terminal` | `api_key` | Open WebUI, when calling Open Terminal ([guide](ia-ollama.md#open-terminal-terminal-for-the-assistant)). After applying, restart the Open Terminal and Open WebUI pods |

To rotate one:

1. Generate the new value and replace **only that field** in 1Password (minimum 32 characters, no spaces):

    === "🖱️ From the UI"

        Generate the value with the command above (`openssl rand -hex 32`) and paste it into the item's field in the 1Password app.

    === "⌨️ From the console"

        The value is generated inside the command, so you never see it. For example, for the `reports` token and for `mcp-api-key`:

        ```bash
        op item edit ollama-router "reports[password]=$(openssl rand -hex 32)"
        op item edit mcp-api-key "key[password]=$(openssl rand -hex 32)"
        ```

        Other commands: [Secrets management](../secrets/index.md#local-ai-create-tokens-with-op).

2. Verify and apply:

    ```bash
    cd ansible
    ../.venv/bin/python scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

3. Restart the service that reads it so it picks up the new value (`kubectl -n <namespace> rollout restart deploy/<nombre>`): the router and the client whose token changed (the router also reloads tokens every 30 seconds). For `registry_token`, also update the token on each node (Linux: re-apply `playbook-ollama.yml --tags register`; Mac: replace the `token` file in the agent folder, or the Keychain one, and `ollama-node off` / `ollama-node on`).
4. **Per-node registration tokens (optional).** If you use a `registry_token-<nombre-del-nodo>` key in the `ai/ollama-router-secrets` Secret, only that token registers that node. To rotate it: change that value in the Secret, update the token on that node, and verify it still appears in `/_registry/nodes`. The shared token still works for nodes without their own, so to **fully retire** the shared one you must give each node its own first.
5. If you rotated `translate`, also update the `OLLAMA_TOKEN` secret in GitHub Actions:

    === "🖱️ From the UI"

        In *maceosoft/homelab → Settings → Secrets and variables → Actions*, edit `OLLAMA_TOKEN` and paste the value from the `translate` field.

    === "⌨️ From the console"

        The value travels through a pipe, without being printed:

        ```bash
        op read "op://HomeLab/ollama-router/translate" | gh secret set OLLAMA_TOKEN --repo maceosoft/homelab
        ```

## Platform PostgreSQL

The [shared PostgreSQL](../storage/postgres.md) uses two credentials. CloudNativePG re-reads its Secrets when they change (label `cnpg.io/reload`), so there's no need to restart the database.

**`homelab_agent` password:**

1. Replace the `password` field of the `postgres-homelab-agent` item (the value is generated inside the command):

    ```bash
    op item edit postgres-homelab-agent "password[password]=$(openssl rand -hex 32)" >/dev/null
    ```

2. Apply and restart the application so it picks up the new `DATABASE_URL`:

    ```bash
    cd ansible
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    kubectl -n ai rollout restart deploy/<deployment-de-homelab-agent>
    ```

**`postgres-backups` bucket key:** a new key is created, swapped in, and only then is the old one deleted, so the WAL (Write-Ahead Log, the PostgreSQL change log) file isn't interrupted.

1. New values in 1Password and the new key (`cnpg-<fecha>`) in Incus, without displaying them:

    ```bash
    op item edit postgres-s3 "access_key[password]=$(openssl rand -hex 16)" "secret_key[password]=$(openssl rand -hex 32)" >/dev/null
    AK=$(op read "op://HomeLab/postgres-s3/access_key") && SK=$(op read "op://HomeLab/postgres-s3/secret_key") \
      && test -n "$AK" && test -n "$SK" \
      && printf 'description: CloudNativePG (postgres)\naccess-key: %s\nsecret-key: %s\n' "$AK" "$SK" \
      | ssh invincible "sudo incus storage bucket key create local postgres-backups cnpg-$(date +%Y%m%d) --role admin >/dev/null"
    unset AK SK
    ```

2. Apply the Secrets: `ansible-playbook -i inventory.ini playbook-platform-secrets.yml`.
3. Verify the archive is still working: `kubectl -n postgres get cluster postgres -o jsonpath='{.status.conditions}'` (`ContinuousArchiving` in `True`) or request a manual backup.
4. Delete the old key: `ssh invincible 'sudo incus storage bucket key list local postgres-backups'` and `ssh invincible 'sudo incus storage bucket key delete local postgres-backups <llave-vieja>'`.

## Node root password

Each run generates and applies a new password per node, and stores it in the `root@<nodo>` item. It doesn't affect SSH (Secure Shell): root login via SSH is already disabled; this password is for the console.

```bash
# todos
ansible-playbook -i inventory.ini playbook-rotate-root-passwords.yml
ansible-playbook -i inventory.ini playbook-rotate-root-passwords.yml --limit deborah
```

## Sealed Secrets key

**Do not rotate lightly.** The `SealedSecret` already in Git were encrypted with the current key: if you change it, those files can no longer be decrypted. The key doesn't expire in practice (the certificate is valid for 10 years) and automatic renewal is disabled.

Only touch it if the **private** key was leaked. In that case:

1. Generate a new key pair ([command](../maceosoft/github.md#step-2-repos-argocd-app-and-ftp-manual)).
2. **Before replacing anything**, re-seal each secret with the new key (`kubeseal --cert <tls.crt nuevo> …`) and commit the new `SealedSecret`.
3. Replace `certificate` and `private_key` in the `sealed-secrets` item, re-run `playbook-platform-secrets.yml` and restart the controller: `kubectl -n kube-system rollout restart deploy/sealed-secrets`.

    === "🖱️ From the UI"

        In the 1Password app, paste the contents of `tls.crt` into `certificate` and `tls.key` into `private_key`.

    === "⌨️ From the console"

        The two values are read from the new files, without being written to the command:

        ```bash
        op item edit sealed-secrets "certificate[text]=$(cat tls.crt)" "private_key[password]=$(cat tls.key)"
        ```

**Reinstalling K3s** is not a rotation: with the item in 1Password, the playbook recreates the same Secret and the `SealedSecret` in Git keep working. Do it **before** the GitOps bootstrap (`sealed-secrets` is in `gitops/bootstrap/components/`).

## Verify

- `apply_platform_secrets.py --check` shows everything as ✓.
- Argo CD keeps syncing `gitops` (`kubectl get applications -n argocd`).
- The runner appears *Online* in *maceosoft → Settings → Actions → Runners* (via CLI: `gh api orgs/maceosoft/actions/runners --jq '.runners[] | [.name, .status] | @tsv'`).
- GitHub login works in Argo CD.
