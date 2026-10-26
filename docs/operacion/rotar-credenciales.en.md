# Rotate credentials

Replace a credential with a new one: periodically, or immediately if you suspect it was leaked. In all cases the new credential is saved first in 1Password (vault `HomeLab`) and then brought to the cluster.

!!! info "Before you begin"
    The 1Password app unlocked, with *Integrate with other apps*, and the account in the environment variable:

    ```bash
    # tu cuenta
    export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"
    ```

    Ansible commands are run from `ansible/` in `homelab`.

## Summary

| Credential | Item in 1Password | Applied with |
|---|---|---|
| Private key of a GitHub App (`maceosoft-terraform`, `maceosoft-arc-runners`, `maceosoft-argocd`) | the item with the App's name | `playbook-platform-secrets.yml` |
| FTP credentials of a repo | `ftp-<repo>` | `playbook-platform-secrets.yml` + pipeline of `infra` |
| Dex client secret (GitHub login) | `maceosoft-dex` | `playbook-dex-oauth-secrets.yml` |
| Discord webhooks, healthchecks.io ping URL, and Grafana password (monitoring) | `discord-webhooks`, `healthchecks-ping`, `grafana-admin` | `playbook-platform-secrets.yml` ([see below](#monitoring-discord-webhooks-healthchecksio-ping-and-grafana)) |
| Open WebUI session key (AI assistant) | `open-webui` (field `WEBUI_SECRET_KEY`) | `playbook-platform-secrets.yml` ([how to generate it](ia-ollama.md#create-the-open-webui-key-once-only)) |
| Ollama router tokens (one per client and the node registration one) | `ollama-router` (fields `registry_token`, `open-webui`, `k8sgpt`, `reports`, `alert-triage`, `translate`) | `playbook-platform-secrets.yml` ([see below](#ollama-and-internal-service-tokens)) |
| Webhook token of `alert-triage` and API key of `mcpo` | `alert-triage-webhook` (field `token`), `mcp-api-key` (field `key`) | `playbook-platform-secrets.yml` ([see below](#ollama-and-internal-service-tokens)) |
| Open Terminal API key | `open-terminal` (field `api_key`) | `playbook-platform-secrets.yml` ([see below](#ollama-and-internal-service-tokens)) |
| Webhook of channel `#ia` (AI reports) | `discord-webhooks` (field `ai`) | `playbook-platform-secrets.yml` ([create the channel](logs.md#create-the-ia-channel-and-its-webhook-once)) |
| Root password of the nodes | `root@<nodo>` (created by the playbook) | `playbook-rotate-root-passwords.yml` |
| Sealed Secrets key | `sealed-secrets` | `playbook-platform-secrets.yml` ([note: see below](#sealed-secrets-key)) |
| Argo CD token of the `gitops` pipeline (account `ci`) | `argocd-ci` | `playbook-platform-secrets.yml` ([how to generate it](pipeline-gitops.md#enable-the-cluster-diff-once)) |

## Private key of a GitHub App

1. In GitHub: *maceosoft → Settings → Developer settings → GitHub Apps →* the App → *Private keys* → **Generate a private key**.
2. In 1Password, replace the `private_key` field of that App's item with the full content of the new `.pem`.
3. Verify and apply:

    ```bash
    ../.venv/bin/python scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

4. If it's the ARC App (`maceosoft-arc-runners`), restart its *listener* so it picks up the new key: `kubectl -n arc-systems get pods` and delete the listener pod (it recreates itself). New runners already use the new key.
5. When everything works, delete the **old** key in GitHub (same page, *Delete* next to the previous key) and the downloaded `.pem`.

??? tip "With the CLI"
    **Generating and deleting GitHub App keys can only be done from the web**: neither `gh` nor the API allow it. What can be automated is saving the new key and verifying the rest (with 1Password unlocked; if you have more than one 1Password account, export `OP_ACCOUNT` first):

    ```bash
    op item edit maceosoft-terraform "private_key[password]=$(cat ~/Downloads/maceosoft-terraform.<fecha>.private-key.pem)"
    # en macOS: rm -P
    shred -u ~/Downloads/maceosoft-terraform.<fecha>.private-key.pem
    # comprueba que tiene contenido, sin mostrarlo
    op read "op://HomeLab/maceosoft-terraform/private_key" | wc -c
    # App ID e Installation ID
    gh api orgs/maceosoft/installations --jq '.installations[] | [.app_slug, .app_id, .id] | @tsv'
    ```

    Change `maceosoft-terraform` to the item of the App you're rotating (`maceosoft-arc-runners` or `maceosoft-argocd`). `gh` needs the organization permission: `gh auth refresh -s admin:read:org`.

## FTP credentials of a repo

1. Change the password in cPanel and update the item `ftp-<repo>` (with the CLI: `read -rs P; op item edit ftp-<repo> "dev_password[password]=$P"; unset P`, or `prod_password` for production).
2. Apply and re-run the pipeline, which loads the new secrets into the repo's environments:

    ```bash
    ../.venv/bin/python scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

    Then, in `maceosoft/infra`: *Actions → tofu → Run workflow* on `main`; with the GitHub CLI: `gh workflow run tofu.yml --repo maceosoft/infra --ref main` and `gh run watch --repo maceosoft/infra`.

## Dex client secret

1. In the *Maceosoft Dex* OAuth App: **Generate a new client secret**. GitHub shows it only once.
2. Replace `GITHUB_CLIENT_SECRET` in the item `maceosoft-dex` (with the CLI: `read -rs S; op item edit maceosoft-dex "GITHUB_CLIENT_SECRET[password]=$S"; unset S`). Generating the secret in the OAuth App **can only be done from the web**.
3. Apply (updates `argocd-secret` and restarts Dex):

    ```bash
    ansible-playbook -i inventory.ini playbook-dex-oauth-secrets.yml --tags argocd
    ```

4. Test the GitHub login in Argo CD and then delete the old secret in the OAuth App.

## Monitoring: Discord webhooks, healthchecks.io ping, and Grafana

They are optional ([4.13](../implementacion/fase-4-gitops.md#413-monitoring-and-alerts-optional)). All three live in 1Password and the playbook brings them to the namespace `monitoring`; they are never written to Git.

1. Generate the new value:
    - **Discord webhook:** Discord does not allow regenerating a webhook token. In *Server Settings → Integrations → Webhooks*, use **Delete Webhook** and create a new one ([how](../maceosoft/discord-healthchecks.md#4-a-webhook-per-channel)); copy its URL.
    - **healthchecks.io ping URL:** create a new check with the same configuration (**Period** of 5 minutes, **Grace Time** of 10, and its Discord integration), copy its ping URL, and delete the old one. The steps are in [Discord and healthchecks.io](../maceosoft/discord-healthchecks.md#part-2-healthchecksio).
    - **Grafana password:** a new one in 1Password.
2. Replace the field in its item (`critical`, `warnings`, or `deployments` in `discord-webhooks`, `url` in `healthchecks-ping`, `password` in `grafana-admin`). With the 1Password CLI, for example: `read -rs V; op item edit discord-webhooks "critical[password]=$V"; unset V`, or `op item edit grafana-admin "password[password]=$(openssl rand -base64 24)"`.
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

## Ollama and internal service tokens

Clients of the [Ollama router](ia-ollama.md) authenticate with a Bearer token, one per client, so that one can be rotated without affecting the rest. All are generated the same way: 32 random bytes in hexadecimal (64 characters).

```bash
openssl rand -hex 32
```

| 1Password Item | Fields | Who uses it |
|---|---|---|
| `ollama-router` | `registry_token` | Ollama nodes, to register with the router |
| `ollama-router` | `open-webui`, `k8sgpt`, `reports`, `alert-triage`, `translate` | Each router client. `translate` is also the `OLLAMA_TOKEN` GitHub Actions secret, used by the translation of this documentation |
| `alert-triage-webhook` | `token` | Alertmanager, when calling `alert-triage` |
| `mcp-api-key` | `key` | Open WebUI, when calling MCP tools (`mcpo`) |
| `open-terminal` | `api_key` | Open WebUI, when calling Open Terminal ([guide](ia-ollama.md#open-terminal-terminal-for-the-assistant)). After applying, restart the Open Terminal and Open WebUI pods |

To rotate one:

1. Generate the new value and replace **only that field** in 1Password (minimum 32 characters, no spaces). With the CLI, for example for the `reports` token: `op item edit ollama-router "reports[password]=$(openssl rand -hex 32)"`; for `mcp-api-key`: `op item edit mcp-api-key "key[password]=$(openssl rand -hex 32)"`. Other commands: [Secret management](../secrets/index.md#local-ai-create-tokens-with-op).
2. Verify and apply:

    ```bash
    cd ansible
    ../.venv/bin/python scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

3. Restart the service that reads it so it picks up the new value (`kubectl -n <namespace> rollout restart deploy/<nombre>`): the router and the client whose token changed (the router also reloads tokens every 30 seconds). For `registry_token`, also update the token on each node (Linux: reapply `playbook-ollama.yml --tags register`; Mac: replace the `token` file in the agent folder, or the Keychain one, and `ollama-node off` / `ollama-node on`).
4. **Per-node registration tokens (optional).** If you use a `registry_token-<nombre-del-nodo>` key in the `ai/ollama-router-secrets` Secret, only that token registers that node. To rotate it: change that value in the Secret, update the token on that node, and verify it still appears in `/_registry/nodes`. The shared token still works for nodes that don't have their own, so to **fully retire** the shared one you must give each node its own first.
5. If you rotated `translate`, also update the `OLLAMA_TOKEN` secret in *maceosoft/homelab → Settings → Secrets and variables → Actions*. With the GitHub CLI: `op read "op://HomeLab/ollama-router/translate" | gh secret set OLLAMA_TOKEN --repo maceosoft/homelab`.

## Node root password

Each run generates and applies a new password per node, and stores it in the `root@<nodo>` item. It does not affect SSH (Secure Shell): root login via SSH is already disabled; this password is for the console.

```bash
# todos
ansible-playbook -i inventory.ini playbook-rotate-root-passwords.yml
ansible-playbook -i inventory.ini playbook-rotate-root-passwords.yml --limit deborah
```

## Sealed Secrets key

**Do not rotate lightly.** The `SealedSecret` already in Git were encrypted with the current key: if you change it, those files can no longer be decrypted. The key does not expire in practice (the certificate is valid for 10 years) and automatic renewal is disabled.

Only touch it if the **private** key was leaked. In that case:

1. Generate a new key pair ([command](../maceosoft/github.md#paso-2-repos-app-de-argocd-y-ftp-manual)).
2. **Before replacing anything**, reseal each secret with the new key (`kubeseal --cert <tls.crt nuevo> …`) and commit the new `SealedSecret`.
3. Replace `certificate` and `private_key` in the `sealed-secrets` item, re-run `playbook-platform-secrets.yml`, and restart the controller: `kubectl -n kube-system rollout restart deploy/sealed-secrets`.

**Reinstalling K3s** is not a rotation: with the item in 1Password, the playbook recreates the same Secret and the `SealedSecret` in Git keep working. Do it **before** enabling `sealed-secrets` in `root-appset.yaml`.

## Verify

- `apply_platform_secrets.py --check` shows everything as ✓.
- Argo CD keeps syncing `gitops` (`kubectl get applications -n argocd`).
- The runner appears *Online* in *maceosoft → Settings → Actions → Runners* (with the CLI: `gh api orgs/maceosoft/actions/runners --jq '.runners[] | [.name, .status] | @tsv'`).
- GitHub login works in Argo CD.
