# Procedure — Add a repo

**Routine** procedure: repeats every time the org `maceosoft` needs
a new repo. The repo
[`maceosoft/infra`](https://github.com/maceosoft/infra)'s OpenTofu pipeline creates it; you add the
entry to the repo map and, if the project deploys to cPanel via FTP (File Transfer Protocol),
its credentials in 1Password.

!!! info "Before you start"
    - The base platform is already working: [Phase 4 — 4.11](../implementacion/fase-4-gitops.md#411-arc-and-opentofu-pipeline)
      completed (the `tofu` pipeline of `infra` runs green).
    - The 1Password app unlocked and `ONEPASSWORD_ACCOUNT_NAME` with your
      account name ([detail](../maceosoft/github.md#items-in-1password)).

## 1. Define the repo

| Field | Example | Purpose |
|---|---|---|
| Name | `web-clientes` | Repo name in `maceosoft` |
| Description | `Sitio de clientes` | Description on GitHub |
| Stack | `node` or `php` | Which `core-pipelines` CI workflow to use |
| Deploys via FTP to cPanel? | yes / no | If yes, create the `dev` and `prod` environments with their credentials |

## 2. Only if it deploys: FTP credentials in 1Password

Create the item **`ftp-<repo>`** (e.g. `ftp-web-clientes`) in the
`HomeLab` vault, type Secure Note, with these 8 fields
([how to create an item](../maceosoft/github.md#como-crear-un-item-con-campos-propios)):

=== "🖱️ From the UI"

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

=== "⌨️ From the console"

    Passwords are read without echo (`read -rs`) so they don't remain on screen or in history. Change `web-clientes` to your repo
    and the example values to your cPanel's. If you have more than one 1Password account, export `OP_ACCOUNT` first.

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

!!! warning "These credentials no longer reach the runner"
    Previously `playbook-platform-secrets.yml` gathered all `ftp-<repo>` items into the `arc-runners/tofu-vars` Secret and the
    OpenTofu runner received them as `TF_VAR_ftp` in its environment. That left them within reach of any job of
    any repo, including a PR's code, so the playbook no longer creates it (and deletes it if it exists). Until
    `tofu.yml` receives the credentials as GitHub Actions secrets from the repo that calls it, the `infra` pipeline
    has no `TF_VAR_ftp`: still save the item in 1Password, which remains the credentials source.

## 3. Add the repo to the map (PR in `infra`)

In the `infra` repo, add an entry to `local.repos` in
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

Open a PR in `infra`: the `tofu` pipeline shows the `plan` with what it will
create. Review and merge; when it reaches `main`, the pipeline does the `apply`.

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

The repo is born with a README (`auto_init`). To push a project you already
have on your machine:

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

Create `.github/workflows/ci-cd.yml` in the new repo calling the
workflows of `core-pipelines` (same scheme as the `api` repo). For a Node
project that deploys (`develop` → dev, `main` → prod):

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
check required by `main` protection if you set
`required_status_check = "ci-cd"`. When `core-pipelines` switches to using the
`v1` tag, change `@main` to `@v1` ([versioning](https://github.com/maceosoft/core-pipelines#versionado)).

## 6. Verify

=== "🖱️ From the UI"

    In GitHub, in the new repo:

    - *Settings → Environments*: `dev` and `prod` exist (only if it deploys).
    - In each environment, the secrets `FTP_HOST`, `FTP_USER`, `FTP_PASSWORD` and
      `FTP_REMOTE_DIR`, and the variables `PROJECT_STACK` and `FTP_PROTOCOL`.
    - *Settings → Branches*: `main` protected.
    - *Actions*: the first push runs the workflow on the `arc-runners` runner.

=== "⌨️ From the console"

    Same with `gh` (change `web-clientes` to your repo):

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

| Symptom | Check |
|---|---|
| The `plan` of `infra` fails with *deploy = true requires ftp credentials* | The runner no longer carries `TF_VAR_ftp` (see the warning in step 2) |
| `--check` marks fields with ✗ | Exact names of the 8 fields, no section ([detail](../maceosoft/github.md#como-crear-un-item-con-campos-propios)) |
| The `git push` to `main` is rejected | Only org owners can bypass `main` protection; if not, push the code via PR |
| Deploy fails to connect | Data of the `ftp-<repo>` item and `ftp_protocol` in `repos.tf`; after fixing the item, re-run the `infra` pipeline |
