# Pipeline de gitops

Cada cambio en [`maceosoft/gitops`](https://github.com/maceosoft/gitops) se
valida **antes** de que ArgoCD lo aplique en el clúster. Lo hace el workflow
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
| `argocd-diff` | Solo en PR | Qué cambiaría ArgoCD en el clúster con el commit del PR, app por app | Solo si ArgoCD no puede calcular el diff. Que haya cambios no es un error: es lo que se revisa |

El resultado del diff aparece en el **resumen del job** (*Actions → la
corrida → Summary*): cada app con "sin cambios" o un bloque desplegable con el
diff. Las apps multi-source (charts externos con values de `gitops`, como
`arc-runners`) se listan pero no se comparan: revisa sus values en la UI de
ArgoCD.

## Activar el diff contra el clúster (una vez)

El diff usa una cuenta de ArgoCD de **solo lectura**, `ci`, que ya está
declarada en `gitops/argocd/config` (`accounts.ci: apiKey` y
`g, ci, role:readonly`). Falta generar su token y llevarlo al runner. Hay que
hacerlo con ArgoCD ya funcionando y `argocd` sincronizado. Mientras no
exista, el job se salta con un aviso y los demás jobs corren igual.

1. Genera el token con la CLI (Command Line Interface) de ArgoCD, logueado como admin:

    ```bash
    argocd login argocd.homelab.local --grpc-web
    argocd account generate-token --account ci
    ```

2. En 1Password, bóveda `HomeLab`, crea el item **`argocd-ci`** (Nota segura)
   con un campo **`token`** (Contraseña) y pega el token
   ([cómo crear un item](../maceosoft/github.md#como-crear-un-item-con-campos-propios)).
3. Llévalo al clúster (crea el Secret `arc-runners/argocd-ci`), desde
   `ansible/` en `homelab`:

    ```bash
    export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"  # tu cuenta
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
