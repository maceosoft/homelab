# GitOps pipeline

Every change in [`maceosoft/gitops`](https://github.com/maceosoft/gitops) is
validated **before** Argo CD applies it to the cluster. The reusable workflow
[`gitops.yml`](https://github.com/maceosoft/core-pipelines/blob/main/.github/workflows/gitops.yml)
from `core-pipelines` does this, called from `gitops/.github/workflows/validate.yml`.
It runs on the `arc-runners` runner in the HomeLab (all `core-pipelines` workflows
run on ARC). The tools it installs (helm, kustomize, kubeconform, gitleaks, argocd) are stored in the [runner cache](cache-arc.md),
verified by `sha256`.

## What it validates

| Job | When | What it checks | Fails if… |
|---|---|---|---|
| `render` | PR and push to `main` | yamllint; `kustomize build`; `helm template` of each Application with a `bootstrap/components/` chart (active and `apagadas/`), with their values; that each file is a single Application named after the file | Invalid YAML, a chart or kustomize that doesn't render, a file whose Application isn't named like it |
| `schemas` | PR and push to `main` | Each manifest, and what's rendered, against the Kubernetes schema and CRDs (Custom Resource Definition): Application, MetalLB, SUC (System Upgrade Controller) plans… | A field that doesn't exist or is misplaced, an incorrect type, a resource without a schema |
| `security` | PR and push to `main` | gitleaks on commits; repo rules | A secret in code; a `gitops` Application with another `repoURL` or branch; an Application without `sync-wave`; a plaintext `Secret` |
| `argocd-diff` | PR only | What Argo CD would change in the cluster with the PR commit, app by app | Only if Argo CD can't compute the diff. That there are changes is not an error: it's what gets reviewed |

The diff result appears in the **job summary** (*Actions → the run → Summary*): each app with "no changes" or a collapsible block with the diff. Multi-source apps (external charts with values from `gitops`, like
`arc-runners`) are listed but not compared: review their values in the Argo CD UI.

## Enable diff against the cluster (once)

The diff uses an Argo CD **read-only** account, `ci`, which is already
declared in `gitops/addons/argocd/config` (`accounts.ci: apiKey` and
`g, ci, role:readonly`). Its token needs to be generated and saved as a **GitHub Actions secret** `ARGOCD_CI_TOKEN` in repo `maceosoft/gitops`. This must be done with Argo CD already working and `argocd` synced. While the secret doesn't exist, the job skips with a notice and the other jobs run the same.

`gitops/.github/workflows/validate.yml` passes that secret as `argocd-token`
to `gitops.yml`, which hands it **only to the diff step** (as
`ARGOCD_AUTH_TOKEN`). GitHub doesn't give it to Dependabot PRs or fork PRs: in those PRs the diff is skipped.

!!! info "Why it's no longer in the runner environment"
    Before, the token reached the runner as Secret `arc-runners/argocd-ci`
    (along with `terraform-app` and `tofu-vars`), which the scale set loaded into the environment of **all** jobs. Thus any job from any repo in the org, including PR code, could read those credentials. Now the runner carries no credentials in its environment, and `playbook-platform-secrets.yml`
    deletes those three Secrets from `arc-runners` if they still exist.

You need the Argo CD CLI (Command Line Interface) with a user who can generate tokens (admin), `op` with 1Password unlocked (if you have more than one account, export `OP_ACCOUNT` first) and `gh` logged in as org owner. The token expires in **90 days** (`--expires-in 2160h`).

1. Log in to Argo CD:

    ```bash
    argocd login argocd.homelab.local --sso --grpc-web
    ```

2. Generate the token and save it in 1Password (vault `HomeLab`, item **`argocd-ci`**,
   field `token`) and in GitHub. The commands chained with `&&` and the
   `test -n` make it so that if `argocd` fails, an empty value isn't saved; the token
   isn't shown on screen:

    ```bash
    TOKEN=$(argocd account generate-token --account ci --expires-in 2160h) && test -n "$TOKEN" \
      && { op item edit argocd-ci --vault HomeLab "token[password]=$TOKEN" >/dev/null \
           || op item create --category "Secure Note" --vault HomeLab --title argocd-ci "token[password]=$TOKEN" >/dev/null; } \
      && printf '%s' "$TOKEN" | gh secret set ARGOCD_CI_TOKEN --repo maceosoft/gitops
    unset TOKEN
    ```

    `op item edit` updates the item if it exists; if it doesn't, it creates it `op item create`.
    The value is passed by argument to `op` and is visible for a moment in `ps` on your own machine; don't do this on a shared machine.

3. Verify the secret exists (GitHub shows only the name and date, never the value):

    ```bash
    gh secret list --repo maceosoft/gitops
    ```

    The next PR in `gitops` must show the diff in the `argocd-diff` job summary.

!!! warning "Renew it before 90 days"
    When the token expires, `argocd-diff` fails to compare. Repeat steps 1 and 2
    **before** 90 days pass (set a calendar reminder): the 1Password item and the GitHub secret are overwritten. To see the account's tokens and when they expire: `argocd account get --account ci`; to revoke an old one: `argocd account delete-token --account ci <id>`.

## Require the pipeline before merging (optional)

`gitops` doesn't manage this via OpenTofu, so `main` protection is configured manually:

=== "🖱️ From the UI"

    *gitops → Settings → Branches → main → Require status checks* and choose
    checks `validate / render`, `validate / schemas` and `validate / security`.

=== "⌨️ From the console"

    With `gh auth login` done as org owner:

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
    If the response is `403` (*Upgrade to GitHub Pro or make this repository public*), the organization plan doesn't allow protecting branches in private repos: in that case only the discipline of always opening PRs remains. A PR's checks are viewed with
    `gh pr checks <número> --repo maceosoft/gitops`.

## Adjustments

From the caller (`gitops/.github/workflows/validate.yml`) you can pass
inputs:

| Input | Default | Purpose |
|---|---|---|
| `argocd-diff` | `true` | Disable the diff |
| `allowed-secrets` | `bootstrap/repositories/arc-helm-repo.yaml bootstrap/repositories/nginx-gateway-helm-repo.yaml` | Paths that may have a plaintext `Secret` (space-separated) |
| `no-wave-apps` | `vcluster-platform capn-demo canal cilium`; gitops passes `vcluster-demo capn-demo canal cilium homelab-bootstrap` | Applications that may lack `sync-wave` |

In the `gitops` repo itself: `.yamllint.yaml` (yamllint rules) and
`.gitleaks.toml` (gitleaks exceptions; today, the `*.example.yaml` templates).

## If it fails

| Symptom | Check |
|---|---|
| `render`: `helm … not a valid chart repository` | The Helm repo URL for that Application changed or no longer exists (happened to `sealed-secrets`) |
| `render`: the file is not a single Application with its name | A `bootstrap/components/` file with another `metadata.name` or with more than one document (the ApplicationSet `homelab` uses `metadata.name`) |
| `schemas`: `additionalProperties '…' not allowed` | A misspelled or misplaced field in that manifest |
| `schemas`: `could not find schema` | A CRD not in the catalog; if intentional, add it to the job's `-skip` |
| `security`: gitleaks found something | If it's a real secret: rotate it and remove it from history. If it's an example with placeholders, name it `*.example.yaml` |
| `argocd-diff` skipped | Missing secret `ARGOCD_CI_TOKEN` in `maceosoft/gitops` (section *Enable the diff*), or it's a Dependabot PR or from a fork |
| `argocd-diff`: error comparing | The `ci` account doesn't exist or lacks `role:readonly` (sync `argocd`), or the token expired (renew it: section *Enable the diff*) |
