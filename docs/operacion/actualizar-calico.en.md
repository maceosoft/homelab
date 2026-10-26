# Calico (CNI) managed by Argo CD

Calico is the CNI (Container Network Interface, the pod network) of the cluster. It is installed in
**two stages**:

1. **Bootstrap, with Ansible** (role `k3s_cni`): when creating the cluster, Argo CD does not yet exist and
   needs pod network to start, so Ansible installs Calico first.
2. **From then on, Argo CD** manages and updates it: two Applications of
   [`maceosoft/gitops`](https://github.com/maceosoft/gitops).

| Application | What it manages | Where |
|---|---|---|
| `calico-operator` | CRDs and the operator (`tigera-operator`) in the chosen version | `cni/calico-operator/kustomization.yaml` |
| `calico-config` | `Installation` (pod pool `10.42.0.0/16`, VXLAN cross-subnet) and `APIServer` | `cni/calico/custom-resources.yaml` |

!!! warning "Manual sync, no prune"
    The two Applications **do not** sync automatically. A version change in Git updates the pod
    network of the 3 nodes, so it is applied manually (Argo CD UI → **Sync**). They also do not have
    `prune` or finalizer: if the Application is deleted, the CNI is not touched.

## What version is running

```bash
kubectl get installation default -o jsonpath='{.status.calicoVersion}{"\n"}'
kubectl -n tigera-operator get deploy tigera-operator -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

## Adopt and update: 3.29.1 → 3.31.7 → 3.33.0 (in two stages)

Calico was installed with **v3.29.1** (operator `v1.36.2`). Version 3.33 only supports upgrading from **v3.31 or v3.32**
(Calico documentation), so the direct jump from 3.29 **is not supported**. It is done in two stages, each
with its own Sync and verification:

| Stage | `cni/calico-operator/kustomization.yaml` | Operator | What it does |
|---|---|---|---|
| 1 | `v3.31.7` | `v1.40.15` | Adopts existing resources and updates the CNI from 3.29.1 to 3.31.7 |
| 2 | `v3.33.0` | `v1.44.0` | Updates from 3.31.7 to 3.33.0 |

Since version 3.31, the CRDs come in a separate file (`operator-crds.yaml`), which already includes the kustomization.

The two Applications carry `argocd.argoproj.io/compare-options: ServerSideDiff=true`: without it, Argo CD shows `OutOfSync`
ghost entries in the Calico CRDs and in the fields that the operator completes (like `assignmentMode` in the pool, new in v3.31),
even if `kubectl diff --server-side` comes up empty.

!!! danger "It is the pod network of the three nodes"
    If a stage fails, the pod network is compromised and **there is no simple rollback**. Do it with maintenance
    window and direct access to the nodes. It is the same error that broke Longhorn when jumping from 1.6 to 1.13:
    never skip more versions than the project documentation supports.

**Before:**

```bash
# calico y apiserver: AVAILABLE=True
kubectl get tigerastatus
# los 3 Ready
kubectl get nodes
# sin pods raros
kubectl get pods -A --no-headers | awk '$4!="Running" && $4!="Completed"'
```

**Preview of what would change** (read-only, against the server):

```bash
kustomize build gitops/cni/calico-operator | kubectl diff --server-side --force-conflicts -f - | grep -cE '^[+-] '
kubectl diff --server-side --force-conflicts -f gitops/cni/calico/custom-resources.yaml
```

The second should come **empty**: the YAML of `calico-config` declares all the fields that the
operator writes, so Argo CD and the operator do not step on each other.

**Sync, in order:**

1. Activate the two Applications: they are already in `bootstrap/root-appset.yaml`; apply the ApplicationSet
   (`kubectl apply -f gitops/bootstrap/root-appset.yaml`).
2. In Argo CD, **Sync** of `calico-operator` (with *Server-Side Apply*, already active). The operator updates and restarts the
   `calico-node` **node by node** (`maxUnavailable: 1`).
3. Monitor: `kubectl -n calico-system get pods -w` and `kubectl get tigerastatus`.
4. When everything is `Available`, **Sync** of `calico-config`.
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

The last one checks that a pod still reaches a service on another node.

## Post-upgrade changes

- **Upgrade:** change the two URLs of `cni/calico-operator/kustomization.yaml`, push
  and **Sync** manually. Upgrade one or two minor versions at a time and review the release notes.
- **Do not change** `cidr`, `encapsulation` or `blockSize` of the pool without a maintenance
  window: they change the network of all pods.
- **Do not run** `--tags cni` of Ansible over an adopted cluster: the role detects that Argo CD is
  managing the `Installation` and skips Calico, to avoid conflicts with it.

## If it fails

| Symptom | What to check |
|---|---|
| `calico-operator` remains `OutOfSync` after Sync | It is normal for a moment due to the fields the operator adds; if it persists, `kubectl diff --server-side` to see what differs |
| `tigerastatus calico` in `Degraded` | `kubectl -n tigera-operator logs deploy/tigera-operator --tail=50` |
| New pods without network | `kubectl -n calico-system get pods`; `calico-node` should be `Running` on the 3 nodes |
| Argo CD cannot sync (because the CNI fell) | Fix the CNI with `kubectl` directly from the station, not through Argo CD |
