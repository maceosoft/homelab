# Update Argo CD

Argo CD updates **itself**, always to the latest stable version. The
Application `argocd` from [`maceosoft/gitops`](https://github.com/maceosoft/gitops)
installs the official manifest from the `stable` branch of the Argo CD repo and adds
its own configuration (Dex, RBAC —role-based access control—, health check, `ci` account): when a new
version comes out, Argo CD applies it to itself.

| Piece | What it does |
|---|---|
| `argocd/apps/argocd.yaml` | The Application: follows `argocd/config` with auto-sync and `ServerSideApply` |
| `argocd/config/kustomization.yaml` | Base: [`https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml`](https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml). On top, `configMapGenerator` with `behavior: merge` for `argocd-cm`, `argocd-rbac-cm` and `argocd-cmd-params-cm` |
| Ansible role `k3s_argocd` | First install and major version jumps (`version: latest` in `k3s_install.yml`) |

!!! warning "Unattended update"
    A new version is applied without asking you, and Argo CD is what deploys
    everything else. It already goes through the `gitops` pipeline (the manifests of the
    new version are validated when your repo changes), but **not** when the
    Argo CD repo changes. If a new version causes issues, see
    [If a new version fails](#if-a-new-version-fails).

## How long until it notices

The repo-server caches generated manifests for one hour
(`reposerver.default.cache.expiration: 1h` in `argocd-cmd-params-cm`), so
a new version is detected at most **one hour after** release.
To speed it up:

```bash
kubectl -n argocd annotate application argocd argocd.argoproj.io/refresh=hard --overwrite
```

## The first time: update manually, then enable the app

!!! danger "Order matters"
    An old Argo CD (2.x) **cannot diff itself** on a cluster
    with Kubernetes 1.36 (`.status.terminatingReplicas: field not declared in schema`), so it cannot be the one to update itself. The first
    update is done by the Ansible role. **Do not `git push` the
    `gitops` change before** (replace `argocd-config` with `argocd` in the
    ApplicationSet).

1. **Check the current version and the one to be installed:**

    ```bash
    export KUBECONFIG=~/.kube/homelab-k3s.yaml
    kubectl -n argocd get deploy argocd-server -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
    curl -s https://raw.githubusercontent.com/argoproj/argo-cd/stable/VERSION
    ```

2. **Dry-run on the server, changing nothing** (must finish without
   errors; *failed to migrate last-applied-configuration* warnings are
   normal):

    ```bash
    curl -sL https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml \
      | kubectl apply -n argocd --server-side --force-conflicts --dry-run=server -f -
    ```

3. **Update with Ansible** (from `ansible/` in `homelab`):

    ```bash
    ansible-playbook -i inventory.ini playbook-k3s.yml --tags argocd
    ```

    The role resolves `version: latest` (latest stable) and applies the official
    manifest with `--server-side --force-conflicts` (mandatory since Argo CD 3.3,
    whose `ApplicationSet` CRD exceeds the normal apply limit).

4. **Verify** everything goes back to healthy. With the new version the
   app diff error disappears:

    ```bash
    kubectl -n argocd get pods
    kubectl -n argocd get deploy argocd-server -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
    kubectl -n argocd get applications
    ```

5. **Now `git push`** `gitops`. The ApplicationSet changes `argocd-config`
   to `argocd`: the old Application is deleted **without** deleting its
   resources (Dex and RBAC ConfigMaps remain), and the new one adopts them.
   Check again with `kubectl -n argocd get applications`.

## Pin a version (pause updates)

To pin a version, change the base of `argocd/config/kustomization.yaml`,
in `gitops`, from `stable` to a tag:

```yaml
resources:
  - https://raw.githubusercontent.com/argoproj/argo-cd/v3.5.3/manifests/install.yaml
```

To resume automatic updates, set it back to `stable`. In the
Ansible role, the equivalent is `k3s_install.gitops_argocd.version: v3.5.3`.

## If a new version fails

1. **Pin the previous version** in `gitops` (previous section) and wait for it to
   apply.
2. If Argo CD won't start and can't apply anything, reinstall the version that
   worked directly with `kubectl` (doesn't depend on Argo CD):

    ```bash
    kubectl apply -n argocd --server-side --force-conflicts \
      -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.5.3/manifests/install.yaml
    ```

3. The Argo CD [upgrade notes](https://argo-cd.readthedocs.io/en/stable/operator-manual/upgrading/overview/)
   explain what changes in each minor version.

## If it fails

| Symptom | Check |
|---|---|
| `ComparisonError … terminatingReplicas: field not declared in schema` | Argo CD is before 3.5: must do the first update with Ansible (above) |
| `argocd` stays `OutOfSync` after enabling | Normal for a few minutes: Argo CD adds its tracking annotation to each resource |
| `The CustomResourceDefinition "applicationsets.argoproj.io" is invalid: metadata.annotations: Too long` | Applied without `--server-side`; use the commands on this page |
| GitHub login lost after update | `argocd-cm` must have the `dex.config` key (`kubectl -n argocd get cm argocd-cm -o jsonpath='{.data.dex\.config}'`) and the Secret `argocd-secret` its `dex.*` keys ([Dex](../implementacion/fase-4-gitops.md)) |
| New version not detected | Wait an hour, or force: `kubectl -n argocd annotate application argocd argocd.argoproj.io/refresh=hard --overwrite` |
