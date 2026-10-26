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
`g, ci, role:readonly`). Falta generar su token y llevarlo al runner. Hay que
hacerlo con Argo CD ya funcionando y `argocd` sincronizado. Mientras no
exista, el job se salta con un aviso y los demás jobs corren igual.

1. Genera el token con la CLI (Command Line Interface) de Argo CD, logueado como admin:

    ```bash
    argocd login argocd.homelab.local --grpc-web
    argocd account generate-token --account ci
    ```

2. En 1Password, bóveda `HomeLab`, crea el item **`argocd-ci`** (Nota segura)
   con un campo **`token`** (Contraseña) y pega el token
   ([cómo crear un item](../maceosoft/github.md#como-crear-un-item-con-campos-propios)).

    ??? tip "Con la CLI de 1Password (`op`)"
        Un solo comando genera el token y lo guarda, sin que se vea en pantalla (necesitas el login de `argocd` del paso 1
        y 1Password desbloqueado; si tienes más de una cuenta de 1Password, exporta `OP_ACCOUNT` antes):

        ```bash
        op item create --category "Secure Note" --vault HomeLab --title argocd-ci \
          "token[password]=$(argocd account generate-token --account ci)"
        ```

        Para rotarlo: `op item edit argocd-ci "token[password]=$(argocd account generate-token --account ci)"`.
3. Llévalo al clúster (crea el Secret `arc-runners/argocd-ci`), desde
   `ansible/` en `homelab`:

    ```bash
    # tu cuenta
    export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"
    # tiene que mostrar: argocd-ci (opcional) ✓ token
    ../.venv/bin/python scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

Los runners nuevos ya lo reciben como `ARGOCD_AUTH_TOKEN` (el scale set lo
monta con `optional: true`). Para rotarlo, genera otro token, reemplaza el
campo y re-corre el playbook.

## Exigir el pipeline antes de mergear (opcional)

`gitops` no lo gestiona OpenTofu, así que la protección de `main` se configura
a mano: *gitops → Settings → Branches → main → Require status checks* y elige
los checks `validate / render`, `validate / schemas` y `validate / security`.

??? tip "Con la CLI de GitHub (`gh`)"
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
| `argocd-diff` omitido | Falta el token (sección *Activar el diff*) |
| `argocd-diff`: error al comparar | La cuenta `ci` no existe o no tiene `role:readonly` (sincroniza `argocd`), o el token venció |
