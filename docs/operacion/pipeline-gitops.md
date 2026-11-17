# Pipeline de gitops

Cada cambio en [`maceosoft/gitops`](https://github.com/maceosoft/gitops) se
valida **antes** de que Argo CD lo aplique en el clúster. Lo hace el workflow
reutilizable
[`gitops.yml`](https://github.com/maceosoft/core-pipelines/blob/main/.github/workflows/gitops.yml)
de `core-pipelines`, llamado desde `gitops/.github/workflows/validate.yml`.
Corre en el runner `arc-runners` del HomeLab (todos los workflows de
`core-pipelines` corren en ARC). Las herramientas que instala (helm, kustomize,
kubeconform, gitleaks, argocd) se guardan en la [caché de los runners](cache-arc.md),
verificadas por `sha256`.

## Qué valida

| Job | Cuándo | Qué revisa | Falla si… |
|---|---|---|---|
| `render` | PR y push a `main` | yamllint; `kustomize build`; `helm template` de cada Application con chart, con sus values; la lista del ApplicationSet `bootstrap/root-appset.yaml` | YAML inválido, un chart o kustomize que no renderiza, una app de la lista sin archivo (o al revés) |
| `schemas` | PR y push a `main` | Cada manifiesto, y lo renderizado, contra el esquema de Kubernetes y de los CRD (Custom Resource Definition): Application, MetalLB, planes del SUC (System Upgrade Controller)… | Un campo que no existe o está mal ubicado, un tipo incorrecto, un recurso sin esquema |
| `security` | PR y push a `main` | gitleaks sobre los commits; reglas del repo | Un secreto en el código; una Application de `gitops` con otro `repoURL` o rama; una Application sin `sync-wave`; un `Secret` en texto plano |
| `argocd-diff` | Solo en PR | Qué cambiaría Argo CD en el clúster con el commit del PR, app por app | Solo si Argo CD no puede calcular el diff. Que haya cambios no es un error: es lo que se revisa |

El resultado del diff aparece en el **resumen del job** (*Actions → la
corrida → Summary*): cada app con "sin cambios" o un bloque desplegable con el
diff. Las apps multi-source (charts externos con values de `gitops`, como
`arc-runners`) se listan pero no se comparan: revisa sus values en la UI de
Argo CD.

## Activar el diff contra el clúster (una vez)

El diff usa una cuenta de Argo CD de **solo lectura**, `ci`, que ya está
declarada en `gitops/argocd/config` (`accounts.ci: apiKey` y
`g, ci, role:readonly`). Falta generar su token y guardarlo como **secreto de
GitHub Actions** `ARGOCD_CI_TOKEN` del repo `maceosoft/gitops`. Hay que hacerlo
con Argo CD ya funcionando y `argocd` sincronizado. Mientras el secreto no
exista, el job se salta con un aviso y los demás jobs corren igual.

`gitops/.github/workflows/validate.yml` pasa ese secreto como `argocd-token`
a `gitops.yml`, que se lo entrega **solo al paso del diff** (como
`ARGOCD_AUTH_TOKEN`). GitHub no se lo da a los PR de Dependabot ni de forks: en
esos PR el diff se omite.

!!! info "Por qué ya no está en el entorno del runner"
    Antes el token llegaba al runner como el Secret `arc-runners/argocd-ci`
    (junto con `terraform-app` y `tofu-vars`), que el scale set cargaba en el
    entorno de **todos** los jobs. Así cualquier job de cualquier repo de la
    org, incluido el código de un PR, podía leer esas credenciales. Ahora el
    runner no lleva credenciales en su entorno, y `playbook-platform-secrets.yml`
    borra esos tres Secrets de `arc-runners` si todavía existen.

Necesitas la CLI (Command Line Interface) de Argo CD con un usuario que pueda
generar tokens (admin), `op` con 1Password desbloqueado (si tienes más de una
cuenta, exporta `OP_ACCOUNT` antes) y `gh` logueado como owner de la org.
El token vence a los **90 días** (`--expires-in 2160h`).

1. Entra a Argo CD:

    ```bash
    argocd login argocd.homelab.local --sso --grpc-web
    ```

2. Genera el token y guárdalo en 1Password (bóveda `HomeLab`, item **`argocd-ci`**,
   campo `token`) y en GitHub. Los comandos encadenados con `&&` y el
   `test -n` hacen que, si `argocd` falla, no se guarde un valor vacío; el token
   no se muestra en pantalla:

    ```bash
    TOKEN=$(argocd account generate-token --account ci --expires-in 2160h) && test -n "$TOKEN" \
      && { op item edit argocd-ci --vault HomeLab "token[password]=$TOKEN" >/dev/null \
           || op item create --category "Secure Note" --vault HomeLab --title argocd-ci "token[password]=$TOKEN" >/dev/null; } \
      && printf '%s' "$TOKEN" | gh secret set ARGOCD_CI_TOKEN --repo maceosoft/gitops
    unset TOKEN
    ```

    `op item edit` actualiza el item si existe; si no existe, lo crea `op item create`.
    El valor pasa por argumento a `op` y se ve un instante en `ps` dentro de tu
    propio equipo; no lo hagas en un equipo compartido.

3. Comprueba que el secreto existe (GitHub muestra solo el nombre y la fecha, nunca el valor):

    ```bash
    gh secret list --repo maceosoft/gitops
    ```

    El próximo PR en `gitops` tiene que mostrar el diff en el resumen del job `argocd-diff`.

!!! warning "Renovarlo antes de los 90 días"
    Cuando el token vence, `argocd-diff` falla al comparar. Repite los pasos 1 y 2
    **antes** de que pasen 90 días (deja un recordatorio en tu calendario): se
    sobrescriben el item de 1Password y el secreto de GitHub. Para ver los tokens
    de la cuenta y cuándo vencen: `argocd account get --account ci`; para
    revocar uno viejo: `argocd account delete-token --account ci <id>`.

## Exigir el pipeline antes de mergear (opcional)

`gitops` no lo gestiona OpenTofu, así que la protección de `main` se configura
a mano:

=== "🖱️ Desde la interfaz"

    *gitops → Settings → Branches → main → Require status checks* y elige
    los checks `validate / render`, `validate / schemas` y `validate / security`.

=== "⌨️ Desde la consola"

    Con `gh auth login` hecho como owner de la org:

    ```bash
    gh api -X PUT repos/maceosoft/gitops/branches/main/protection --input - <<'JSON'
    {
      "required_status_checks": {"strict": false,
        "contexts": ["validate / render", "validate / schemas", "validate / security"]},
      "enforce_admins": false,
      "required_pull_request_reviews": null,
      "restrictions": null
    }
    JSON
    ```

    Para ver cómo quedó: `gh api repos/maceosoft/gitops/branches/main/protection --jq '.required_status_checks.contexts'`.
    Si la respuesta es `403` (*Upgrade to GitHub Pro or make this repository public*), el plan de la organización no permite
    proteger ramas en repos privados: en ese caso solo queda la disciplina de abrir siempre PR. Los checks de un PR se miran con
    `gh pr checks <número> --repo maceosoft/gitops`.

## Ajustes

Desde el caller (`gitops/.github/workflows/validate.yml`) se pueden pasar
inputs:

| Input | Default | Para qué |
|---|---|---|
| `argocd-diff` | `true` | Desactivar el diff |
| `allowed-secrets` | `argocd/apps/arc-helm-repo.yaml argocd/apps/nginx-gateway-helm-repo.yaml` | Rutas que pueden tener un `Secret` en texto plano (separadas por espacio) |
| `no-wave-apps` | `vcluster-platform capn-demo canal cilium` | Applications que pueden no tener `sync-wave` |

En el propio repo `gitops`: `.yamllint.yaml` (reglas de yamllint) y
`.gitleaks.toml` (excepciones de gitleaks; hoy, las plantillas
`*.example.yaml`).

## Si falla

| Síntoma | Revisar |
|---|---|
| `render`: `helm … not a valid chart repository` | La URL del repo de Helm de esa Application cambió o dejó de existir (le pasó a `sealed-secrets`) |
| `render`: app de la lista sin archivo | Un nombre mal escrito en `bootstrap/root-appset.yaml`, o un archivo de `argocd/apps/` que falta agregar (comentado) a la lista |
| `schemas`: `additionalProperties '…' not allowed` | Un campo mal escrito o en el lugar equivocado en ese manifiesto |
| `schemas`: `could not find schema` | Un CRD que no está en el catálogo; si es a propósito, hay que agregarlo a los `-skip` del job |
| `security`: gitleaks encontró algo | Si es un secreto real: rótalo y sácalo del historial. Si es un ejemplo con placeholders, nómbralo `*.example.yaml` |
| `argocd-diff` omitido | Falta el secreto `ARGOCD_CI_TOKEN` en `maceosoft/gitops` (sección *Activar el diff*), o es un PR de Dependabot o de un fork |
| `argocd-diff`: error al comparar | La cuenta `ci` no existe o no tiene `role:readonly` (sincroniza `argocd`), o el token venció (renuévalo: sección *Activar el diff*) |
