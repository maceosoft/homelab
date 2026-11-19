# Calico (CNI) managed by Argo CD

Calico is the cluster's CNI (Container Network Interface, the pod network). It is installed in
**two stages**:

1. **Bootstrap, with Ansible** (role `k3s_cni`): when creating the cluster, Argo CD does not yet exist and
   needs a pod network to start, so Ansible installs Calico first.
2. **From then on, Argo CD** manages and updates it: two Applications from
   [`maceosoft/gitops`](https://github.com/maceosoft/gitops).

| Application | What it manages | Where |
|---|---|---|
| `calico-operator` | CRDs and the operator (`tigera-operator`) in the chosen version | `addons/network/calico-operator/kustomization.yaml` |
| `calico-config` | `Installation` (pod CIDR `10.42.0.0/16`, VXLAN cross-subnet) and `APIServer` | `addons/network/calico/custom-resources.yaml` |

!!! warning "Manual sync, no prune"
    The two Applications **do not** auto-sync. A version change in Git updates the
    pod network on all nodes, so it is applied manually (Argo CD UI → **Sync**). They also lack
    `prune` or a finalizer: if the Application is deleted, the CNI is untouched.

## Which version is running

```bash
kubectl get installation default -o jsonpath='{.status.calicoVersion}{"\n"}'
kubectl -n tigera-operator get deploy tigera-operator -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

## Adopt and upgrade: 3.29.1 → 3.31.7 → 3.33.0 (in two stages)

Calico was installed with **v3.29.1** (operator `v1.36.2`). v3.33 only supports upgrading from **v3.31 or v3.32**
(Calico documentation), so a direct jump from 3.29 **is not supported**. It is done in two stages, each
with its own Sync and verification:

| Stage | `addons/network/calico-operator/kustomization.yaml` | Operator | What it does |
|---|---|---|---|
| 1 | `v3.31.7` | `v1.40.15` | Adopts existing resources and upgrades the CNI from 3.29.1 to 3.31.7 |
| 2 | `v3.33.0` | `v1.44.0` | Upgrades from 3.31.7 to 3.33.0 |

Since v3.31 the CRDs come in a separate file (`operator-crds.yaml`), which already includes the kustomization.

Both Applications carry `argocd.argoproj.io/compare-options: ServerSideDiff=true`: without it, Argo CD shows phantom
`OutOfSync` on Calico CRDs and on fields the operator populates (like `assignmentMode` in the pool, new in v3.31),
even though `kubectl diff --server-side` comes out empty.

!!! danger "It is the pod network of all nodes"
    If a stage fails, the pod network is compromised and **there is no simple rollback**. Do it during a maintenance
    window and with direct access to the nodes. It is the same mistake that broke Longhorn when jumping from 1.6 to 1.13:
    never skip more versions than the project documentation supports.

**Before:**

```bash
# calico y apiserver: AVAILABLE=True
kubectl get tigerastatus
# todos Ready
kubectl get nodes
# sin pods raros
kubectl get pods -A --no-headers | awk '$4!="Running" && $4!="Completed"'
```

**Preview of what would change** (read-only, against the server):

```bash
kustomize build gitops/addons/network/calico-operator | kubectl diff --server-side --force-conflicts -f - | grep -cE '^[+-] '
kubectl diff --server-side --force-conflicts -f gitops/addons/network/calico/custom-resources.yaml
```

The second one must come out **empty**: the `calico-config` YAML declares all fields the
operator writes, so Argo CD and the operator don't step on each other.

**Sync, in order:**

1. Both Applications are already in `gitops/bootstrap/components/` (`calico-operator.yaml` and `calico-config.yaml`):
   the ApplicationSet `homelab` creates them with wave `manual`, without syncing them. Nothing to apply.
2. **Sync** `calico-operator` (with *Server-Side Apply*, already enabled). The operator
   updates and restarts the `calico-node` **node by node** (`maxUnavailable: 1`).

    === "🖱️ From the UI"

        In Argo CD, **Sync** `calico-operator`.

    === "⌨️ From the console"

        With the Argo CD CLI (the Application already brings `ServerSideApply=true`, so no need to pass it):

        ```bash
        argocd login argocd.homelab.local --sso --grpc-web
        argocd app sync calico-operator
        ```

3. Watch: `kubectl -n calico-system get pods -w` and `kubectl get tigerastatus`.
4. When everything is `Available`, **Sync** `calico-config`.

    === "🖱️ From the UI"

        In Argo CD, **Sync** `calico-config`.

    === "⌨️ From the console"

        ```bash
        argocd app sync calico-config
        ```

5. Verify stage 1 (next block) and **repeat steps 2–4 for stage 2**, after changing the URLs to `v3.33.0`
   and pushing.

**After:**

```bash
# v3.31.7 tras la etapa 1; v3.33.0 tras la 2
kubectl get installation default -o jsonpath='{.status.calicoVersion}{"\n"}'
kubectl get tigerastatus
kubectl -n argocd run curl-test --rm -i --restart=Never --image=curlimages/curl --quiet -- \
  curl -s -o /dev/null -w "%{http_code}\n" http://kong-gateway-proxy.kong.svc:80/
```

The last one checks that a pod can still reach a service on another node.

## Subsequent changes

- **Upgrade version:** change the two `addons/network/calico-operator/kustomization.yaml` URLs, push
  and **Sync** manually. Raise one or two minor versions at a time and review the release notes for each version.
- **Do not change** `cidr`, `encapsulation` or `blockSize` of the pool without a maintenance
  window: they change the network of all pods.
- **Do not run** `--tags cni` from Ansible again on an already adopted cluster: the role detects
  that Argo CD manages the `Installation` and skips Calico, to avoid fighting with it.

## If it fails

| Symptom | What to check |
|---|---|
| `calico-operator` stays `OutOfSync` after Sync | Normal for a moment due to fields the operator adds; if it persists, `kubectl diff --server-side` to see what differs |
| `tigerastatus calico` in `Degraded` | `kubectl -n tigera-operator logs deploy/tigera-operator --tail=50` |
| New pods without network | `kubectl -n calico-system get pods`; `calico-node` must be `Running` on all nodes |
| Argo CD cannot sync (because the CNI went down) | Fix the CNI with `kubectl` directly from the workstation, not through Argo CD |
