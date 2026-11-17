# Update K3s

K3s (lightweight Kubernetes distribution) updates **automatically**: the SUC (System Upgrade Controller) checks the K3s `stable` channel and, when a new version is released, updates one node at a time (first the control plane, the node with the label `node-role.kubernetes.io/control-plane`: `deborah`; then the workers), cordoning and draining it first (*cordon* and *drain*). This procedure is to verify that it works, pin a version when needed, and keep Ansible aligned.

The plans are in [`maceosoft/gitops` → `addons/cluster/k3s-upgrade/`](https://github.com/maceosoft/gitops/tree/main/addons/cluster/k3s-upgrade) and are applied by the Argo CD Application `k3s-upgrade`.

## 1. Verify that SUC is installed

Application `k3s-upgrade` only applies the *plans*. The controller that executes them is installed manually once ([K3s — Manual Installation, 6.1](../k3s/index.md)):

```bash
kubectl -n system-upgrade get deploy system-upgrade-controller
kubectl -n system-upgrade get plans
```

The controller and plans `k3s-server` and `k3s-agent` must appear.

## 2. View update status

```bash
# columna VERSION de cada nodo
kubectl get nodes -o wide
# versión objetivo (LATESTVERSION)
kubectl -n system-upgrade get plans -o wide
# un job por nodo actualizado
kubectl -n system-upgrade get jobs
```

All nodes should end up with the same `VERSION`.

## 3. Pin a version (optional)

To stop following `stable` (for example, to wait before upgrading to a new minor version), change `channel` to `version` in **both** plans of `addons/cluster/k3s-upgrade/k3s-plans.yaml`, in the `gitops` repo:

```yaml
spec:
  # channel: https://update.k3s.io/v1-release/channels/stable
  version: v1.37.2+k3s1
```

Merge the change: Argo CD applies it and SUC leaves the nodes at that version.

## 4. Align Ansible with the actual version

Ansible installs **new** nodes with `k3s_install.core.version` (`group_vars/incus_cluster/k3s_install.yml` in `homelab`). SUC doesn't touch that file, so it becomes out of sync after each update. Update it to the version shown by `kubectl get nodes`:

```yaml
k3s_install:
  core:
    version: "v1.37.0+k3s1"   # la VERSION actual de los nodos
```

This is essential before [adding a node](agregar-nodo.md): otherwise, the new node joins with an older version.

## If it fails

| Symptom | Check |
|---|---|
| `get plans` shows nothing | Application `k3s-upgrade` doesn't sync: controller or its CRDs missing (step 1) |
| A node stays `SchedulingDisabled` | Update was cut off mid-way: check the job with `kubectl -n system-upgrade logs job/<job>` and, when resolved, `kubectl uncordon <nodo>` |
| Nodes with different versions for a long time | The `drain` doesn't finish (PodDisruptionBudget or pods without controller); check the jobs from step 2 |
