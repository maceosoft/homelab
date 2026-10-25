# Procedimiento — Agregar un repo

Procedimiento **de rutina**: se repite cada vez que la org `maceosoft` necesita
un repo nuevo. Lo crea el pipeline de OpenTofu del repo
[`maceosoft/infra`](https://github.com/maceosoft/infra); tú agregas la
entrada en el mapa de repos y, si el proyecto despliega a cPanel por FTP (File Transfer Protocol),
sus credenciales en 1Password.

!!! info "Antes de empezar"
    - La plataforma base ya funciona: [Fase 4 — 4.11](../implementacion/fase-4-gitops.md#411-arc-y-pipeline-de-opentofu)
      completada (el pipeline `tofu` de `infra` corre en verde).
    - La app de 1Password desbloqueada y `ONEPASSWORD_ACCOUNT_NAME` con el
      nombre de tu cuenta ([detalle](../maceosoft/github.md#items-en-1password)).

## 1. Define el repo

| Dato | Ejemplo | Para qué |
|---|---|---|
| Nombre | `web-clientes` | Nombre del repo en `maceosoft` |
| Descripción | `Sitio de clientes` | Descripción en GitHub |
| Stack | `node` o `php` | Qué workflow de CI de `core-pipelines` usa |
| ¿Despliega por FTP a cPanel? | sí / no | Si es sí, crea los environments `dev` y `prod` con sus credenciales |

## 2. Solo si despliega: credenciales FTP en 1Password

Crea el item **`ftp-<repo>`** (por ejemplo `ftp-web-clientes`) en la bóveda
`HomeLab`, tipo Nota segura, con estos 8 campos
([cómo crear un item](../maceosoft/github.md#como-crear-un-item-con-campos-propios)):

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

Comprueba que se lee bien y llévalo al clúster, desde la raíz de `homelab`.
El runner de OpenTofu recibe estas credenciales como `TF_VAR_ftp` desde el
clúster, así que este paso va **antes** del PR (pull request): si no, el
pipeline falla por falta de credenciales.

```bash
export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"  # tu cuenta
.venv/bin/python ansible/scripts/apply_platform_secrets.py --check
cd ansible
ansible-playbook -i inventory.ini playbook-platform-secrets.yml
```

`--check` tiene que mostrar el item `ftp-<repo>` con sus 8 campos en ✓.

## 3. Agrega el repo al mapa (PR en `infra`)

En el repo `infra`, agrega una entrada a `local.repos` en
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

Campos opcionales: `ftp_protocol` (`ftp`, `ftps` o `sftp`; por defecto
`ftps`) y `visibility` (`private` o `internal`; por defecto `private`).

Abre un PR en `infra`: el pipeline `tofu` muestra el `plan` con lo que va a
crear. Revísalo y mergea; al llegar a `main`, el pipeline hace el `apply`.

## 4. Sube el código

El repo nace con un README (`auto_init`). Para subir un proyecto que ya
tienes en tu máquina:

```bash
cd <carpeta-del-proyecto>
git init -b main            # si todavía no es un repo git
git add -A && git commit -m "Primer commit"
git remote add origin https://github.com/maceosoft/<repo>.git
git pull origin main --allow-unrelated-histories
git push -u origin main     # como owner de la org puedes pushear directo a main
```

## 5. Solo si tiene CI/CD: el workflow

Crea `.github/workflows/ci-cd.yml` en el repo nuevo llamando a los workflows
de `core-pipelines` (mismo esquema que el repo `api`). Para un proyecto Node
que despliega (`develop` → dev, `main` → prod):

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

Para PHP usa `ci-php.yml` y `stack: php`. El nombre del job (`ci-cd`) es el
check que exige la protección de `main` si pusiste
`required_status_check = "ci-cd"`. Cuando `core-pipelines` pase a usar el tag
`v1`, cambia `@main` por `@v1` ([versionado](https://github.com/maceosoft/core-pipelines#versionado)).

## 6. Verifica

En GitHub, en el repo nuevo:

- *Settings → Environments*: existen `dev` y `prod` (solo si despliega).
- En cada environment, los secrets `FTP_HOST`, `FTP_USER`, `FTP_PASSWORD` y
  `FTP_REMOTE_DIR`, y las variables `PROJECT_STACK` y `FTP_PROTOCOL`.
- *Settings → Branches*: `main` protegida.
- *Actions*: el primer push corre el workflow en el runner `arc-runners`.

## Si falla

| Síntoma | Revisar |
|---|---|
| El `plan` de `infra` falla con *deploy = true requiere credenciales ftp* | Falta el item `ftp-<repo>` o no re-corriste `playbook-platform-secrets.yml` (paso 2) |
| `--check` marca campos con ✗ | Nombres exactos de los 8 campos, sin sección ([detalle](../maceosoft/github.md#como-crear-un-item-con-campos-propios)) |
| El `git push` a `main` es rechazado | Solo los owners de la org pueden saltarse la protección de `main`; si no, sube el código por PR |
| El deploy falla al conectar | Datos del item `ftp-<repo>` y `ftp_protocol` en `repos.tf`; tras corregir el item, repite el paso 2 y relanza el pipeline de `infra` |
