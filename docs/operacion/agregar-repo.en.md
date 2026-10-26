# Procedure — Add a Repo

Routine **procedure**: repeated every time the org `maceosoft` needs a new repo. The OpenTofu pipeline of the repo
[`maceosoft/infra`](https://github.com/maceosoft/infra) creates it; you add the entry in the repo map and, if the project deploys to cPanel via FTP (File Transfer Protocol),
its credentials in 1Password.

!!! info "Before you start"
    - The base platform is up and running: [Phase 4 — 4.11](../implementacion/fase-4-gitops.md#411-arc-and-opentofu-pipeline) completed (the pipeline `tofu` of `infra` runs green).
    - The 1Password app is unlocked and `ONEPASSWORD_ACCOUNT_NAME` with your account name ([details](../maceosoft/github.md#items-in-1password)).

## 1. Define the repo

| Data | Example | Purpose |
|---|---|---|
| Name | `web-clientes` | Name of the repo in `maceosoft` |
| Description | `Sitio de clientes` | Description in GitHub |
| Stack | `node` or `php` | Which CI workflow of `core-pipelines` it uses |
| Does it deploy via FTP to cPanel? | yes / no | If yes, create the environments `dev` and `prod` with their credentials |

## 2. Only if it deploys: FTP credentials in 1Password

Create the item **`ftp-<repo>`** (for example `ftp-web-clientes`) in the vault
`HomeLab`, type Secure Note, with these 8 fields
([how to create an item](../maceosoft/github.md#how-to-create-an-item-with-custom-fields)):

| Field | Type | Example |
|---|---|---|
| `dev_host` | Text | `dev.tu-cpanel.example.com` |
| `dev_user` | Text | `usuario_dev` |
| `dev_password` | Password | |
| `dev_remote_dir` | Text | `/home/usuario/dev.maceosoft.example.com` |
| `prod_host` | Text | `tu-cpanel.example.com` |
| `prod_user` | Text | `usuario_prod` |
| `prod_password` | Password | |
| `prod_remote_dir` | Text | `/home/usuario/public_html` |

??? tip "With the 1Password CLI (`op`)"
    Passwords are read without echo (`read -s`) so they don't appear on screen or in history. Replace `web-clientes` with your repo
    and the example values with those of your cPanel. If you have multiple 1Password accounts, export `OP_ACCOUNT` first.

    ```bash
    # pega cada contraseña y Enter
    read -rs FTP_DEV_PASS;  read -rs FTP_PROD_PASS
    op item create --category "Secure Note" --vault HomeLab --title ftp-web-clientes \
      "dev_host[text]=dev.tu-cpanel.example.com" "dev_user[text]=usuario_dev" \
      "dev_password[password]=$FTP_DEV_PASS" "dev_remote_dir[text]=/home/usuario/dev.maceosoft.example.com" \
      "prod_host[text]=tu-cpanel.example.com" "prod_user[text]=usuario_prod" \
      "prod_password[password]=$FTP_PROD_PASS" "prod_remote_dir[text]=/home/usuario/public_html"
    unset FTP_DEV_PASS FTP_PROD_PASS
    ```

Check that it reads correctly and take it to the cluster, from the root of `homelab`.
The OpenTofu runner receives these credentials as `TF_VAR_ftp` from the
cluster, so this step goes **before** the PR (pull request): if not, the
pipeline fails for lack of credentials.

```bash
# tu cuenta
export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"
.venv/bin/python ansible/scripts/apply_platform_secrets.py --check
cd ansible
ansible-playbook -i inventory.ini playbook-platform-secrets.yml
```

`--check` has to show the item `ftp-<repo>` with its 8 fields in ✓.

## 3. Add the repo to the map (PR in `infra`)

In the repo `infra`, add an entry to `local.repos` in
[`github/repos.tf`](https://github.com/maceosoft/infra/blob/main/github/repos.tf):

```hcl
locals {
  repos = {
    # ... repos existentes ...
    web-clientes = {
      description           = "Sitio de clientes"
      stack                 = "node"   # node | php
      deploy                = true     # false si no despliega por FTP
      required_status_check = "ci-cd"  # quitar si el repo no tiene CI
    }
  }
}
```

Optional fields: `ftp_protocol` (`ftp`, `ftps` or `sftp`; default
`ftps`) and `visibility` (`private` or `internal`; default `private`).

Open a PR in `infra`: the pipeline `tofu` shows the `plan` with what it will create. Review it and merge; when it reaches `main`, the pipeline does the `apply`.

??? tip "With the GitHub CLI (`gh`)"
    From your local copy of `infra`, with `gh auth login` done:

    ```bash
    git switch -c agregar-web-clientes
    git commit -am "Agregar repo web-clientes" && git push -u origin agregar-web-clientes
    gh pr create --repo maceosoft/infra --fill
    # espera al plan de tofu
    gh pr checks --watch --repo maceosoft/infra
    # el plan queda como comentario
    gh pr view --comments --repo maceosoft/infra
    # al mergear corre el apply
    gh pr merge --squash --repo maceosoft/infra
    # ver el apply
    gh run list --repo maceosoft/infra --limit 3
    ```

## 4. Push the code

The repo starts with a README (`auto_init`). To push a project you already have on your machine:

```bash
cd <carpeta-del-proyecto>
# si todavía no es un repo git
git init -b main
git add -A && git commit -m "Primer commit"
git remote add origin https://github.com/maceosoft/<repo>.git
git pull origin main --allow-unrelated-histories
# como owner de la org puedes pushear directo a main
git push -u origin main
```

## 5. Only if it has CI/CD: the workflow

Create `.github/workflows/ci-cd.yml` in the new repo calling the workflows
of `core-pipelines` (same schema as the repo `api`). For a Node project that deploys (`develop` → dev, `main` → prod):

```yaml
name: CI/CD

on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [main]

jobs:
  ci:
    uses: maceosoft/core-pipelines/.github/workflows/ci-node.yml@main
    secrets: inherit

  deploy-dev:
    needs: ci
    if: github.ref == 'refs/heads/develop' && github.event_name == 'push'
    uses: maceosoft/core-pipelines/.github/workflows/deploy-ftp.yml@main
    with:
      stack: node
      environment: dev
    secrets: inherit

  deploy-prod:
    needs: ci
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    uses: maceosoft/core-pipelines/.github/workflows/deploy-ftp.yml@main
    with:
      stack: node
      environment: prod
    secrets: inherit
```

For PHP use `ci-php.yml` and `stack: php`. The job name (`ci-cd`) is the
check that enforces the protection of `main` if you set
`required_status_check = "ci-cd"`. When `core-pipelines` starts using the tag
`v1`, change `@main` to `@v1` ([versioning](https://github.com/maceosoft/core-pipelines#versionado)).

## 6. Verify

In GitHub, in the new repo (or with `gh`, below):

- *Settings → Environments*: exist `dev` and `prod` (only if it deploys).
- In each environment, the secrets `FTP_HOST`, `FTP_USER`, `FTP_PASSWORD` and
  `FTP_REMOTE_DIR`, and the variables `PROJECT_STACK` and `FTP_PROTOCOL`.
- *Settings → Branches*: `main` protected.
- *Actions*: the first push runs the workflow on the runner `arc-runners`.

??? tip "With the GitHub CLI (`gh`)"
    ```bash
    # dev, prod
    gh api repos/maceosoft/web-clientes/environments --jq '.environments[].name'
    # FTP_* (solo nombres)
    gh secret list --env prod --repo maceosoft/web-clientes
    # PROJECT_STACK, FTP_PROTOCOL
    gh variable list --env prod --repo maceosoft/web-clientes
    gh api repos/maceosoft/web-clientes/branches/main/protection --jq '.required_status_checks'
    gh run list --repo maceosoft/web-clientes --limit 3
    ```

## If it fails

| Symptom | To check |
|---|---|
| The `plan` of `infra` fails with *deploy = true requires FTP credentials* | Missing the item `ftp-<repo>` or didn't rerun `playbook-platform-secrets.yml` (step 2) |
| `--check` marks fields with ✗ | Exact names of the 8 fields, no section ([details](../maceosoft/github.md#how-to-create-an-item-with-custom-fields)) |
| The `git push` to `main` is rejected | Only org owners can bypass the protection of `main`; otherwise, push the code via PR |
| The deploy fails to connect | Data of the item `ftp-<repo>` and `ftp_protocol` in `repos.tf`; after fixing the item, repeat step 2 and relaunch the pipeline of `infra` |
