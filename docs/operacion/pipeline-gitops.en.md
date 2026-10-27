# GitOps Pipeline

Each change in [`maceosoft/gitops`](https://github.com/maceosoft/gitops) is validated **before** Argo CD applies it to the cluster. This is done by the reusable workflow
[`gitops.yml`](https://github.com/maceosoft/core-pipelines/blob/main/.github/workflows/gitops.yml)
from `core-pipelines`, called from `gitops/.github/workflows/validate.yml`. It runs on the runner `arc-runners` of the HomeLab (all workflows of
`core-pipelines` run on ARC). The tools it installs (helm, kustomize, kubeconform, gitleaks, argocd) are stored in the [runner cache](cache-arc.md),
verified by `sha256`.

## What It Validates

| Job | When | What It Checks | Fails If… |
|---|---|---|---|
| `render` | PR and push to `main` | yamllint; `kustomize build`; `helm template` of each Application with chart, with its values; the list of the ApplicationSet `bootstrap/root-appset.yaml` | Invalid YAML, a chart or kustomize that does not render, an app in the list without a file (or vice versa) |
| `schemas` | PR and push to `main` | Each manifest, and what it renders, against the Kubernetes schema and CRD (Custom Resource Definition): Application, MetalLB, SUC (System Upgrade Controller) plans… | A field that does not exist or is misplaced, an incorrect type, a resource without a schema |
| `security` | PR and push to `main` | gitleaks on the commits; repo rules | A secret in the code; an Application of `gitops` with another `repoURL` or branch; an Application without `sync-wave`; a `Secret` in plain text |
| `argocd-diff` | Only on PR | What Argo CD would change in the cluster with the PR commit, app by app | Only if Argo CD cannot calculate the diff. Having changes is not an error: that is what is being reviewed |

The diff result appears in the **job summary** (*Actions → the run → Summary*): each app with "no changes" or a collapsible block with the diff. Multi-source apps (external charts with values from `gitops`, like
`arc-runners`) are listed but not compared: their values are reviewed in the Argo CD UI.

## Enable the Cluster Diff (Once)

The diff uses a **read-only** Argo CD account, `ci`, which is already declared in `gitops/argocd/config` (`accounts.ci: apiKey` and
`g, ci, role:readonly`). The token needs to be generated and brought to the runner. This must be done with Argo CD running and `argocd` synchronized. Until it exists, the job skips with a warning and the other jobs run as usual.

1. Generate the token with the Argo CD CLI, logged in as admin:

    ```bash
    argocd login argocd.homelab.local --grpc-web
    argocd account generate-token --account ci
    ```

2. Save the token in 1Password, vault `HomeLab`, item **`argocd-ci`**:

    === "🖱️ From the UI"

        In 1Password, vault `HomeLab`, create the item **`argocd-ci`** (Secure Note)
        with a field **`token`** (Password) and paste the token
        ([how to create an item](../maceosoft/github.md#como-crear-un-item-con-campos-propios)).

    === "⌨️ From the console"

        A single command generates the token and saves it, without showing it on screen (you need the login of `argocd` from step 1
        and 1Password unlocked; if you have multiple 1Password accounts, export `OP_ACCOUNT` first):

        ```bash
        op item create --category "Secure Note" --vault HomeLab --title argocd-ci \
          "token[password]=$(argocd account generate-token --account ci)"
        ```

        To rotate it: `op item edit argocd-ci "token[password]=$(argocd account generate-token --account ci)"`.

3. Bring it to the cluster (create the Secret `arc-runners/argocd-ci`), from
   `ansible/` in `homelab`:

    ```bash
    # tu cuenta
    export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"
    # tiene que mostrar: argocd-ci (opcional) ✓ token
    ../.venv/bin/python scripts/apply_platform_secrets.py --check
    ansible-playbook -i inventory.ini playbook-platform-secrets.yml
    ```

New runners receive it as `ARGOCD_AUTH_TOKEN` (the scale set mounts it with `optional: true`). To rotate it, generate another token, replace the
field, and rerun the playbook.

## Require the Pipeline Before Merging (Optional)

`gitops` is not managed by OpenTofu, so the protection of `main` is configured manually:

=== "🖱️ From the UI"

    *gitops → Settings → Branches → main → Require status checks* and choose
    the checks `validate / render`, `validate / schemas` and `validate / security`.

=== "⌨️ From the console"

    With `gh auth login` done as the owner of the org:

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

    To see how it turned out: `gh api repos/maceosoft/gitops/branches/main/protection --jq '.required_status_checks.contexts'`.
    If the response is `403` (*Upgrade to GitHub Pro or make this repository public*), the organization plan does not allow
    protecting branches in private repos: in that case, only discipline of always opening PRs remains. PR checks are viewed with
    `gh pr checks <número> --repo maceosoft/gitops`.

## Adjustments

Inputs can be passed from the caller (`gitops/.github/workflows/validate.yml`):

| Input | Default | Purpose |
|---|---|---|
| `argocd-diff` | `true` | Disable the diff |
| `allowed-secrets` | `argocd/apps/arc-helm-repo.yaml argocd/apps/nginx-gateway-helm-repo.yaml` | Paths that can have a `Secret` in plain text (space-separated) |
| `no-wave-apps` | `vcluster-platform capn-demo canal cilium` | Applications that can lack `sync-wave` |

In the repo `gitops` itself: `.yamllint.yaml` (yamllint rules) and
`.gitleaks.toml` (gitleaks exceptions; today, the templates
`*.example.yaml`).

## If It Fails

| Symptom | To Check |
|---|---|
| `render`: `helm … not a valid chart repository` | The Helm repo URL for that Application changed or no longer exists (it happened to `sealed-secrets`) |
| `render`: app in the list without a file | A misspelled name in `bootstrap/root-appset.yaml`, or a file of `argocd/apps/` that needs to be added (commented out) to the list |
| `schemas`: `additionalProperties '…' not allowed` | A field misspelled or in the wrong place in that manifest |
| `schemas`: `could not find schema` | A CRD not in the catalog; if intentional, add it to the `-skip` of the job |
| `security`: gitleaks found something | If it's a real secret: rotate it and remove it from history. If it's an example with placeholders, name it `*.example.yaml` |
| `argocd-diff` omitted | The token is missing (section *Enable the Diff*) |
| `argocd-diff`: error comparing | The account `ci` does not exist or does not have `role:readonly` (sync `argocd`), or the token expired |
