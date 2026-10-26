# Upgrade K3s

K3s (lightweight Kubernetes distribution) upgrades **itself**: the SUC (System Upgrade Controller) watches the K3s
`stable` channel and, when a new version comes out, upgrades one node at a time
(first the control plane, the node with the `node-role.kubernetes.io/control-plane` label: `deborah` today, and `oliver` after the [move](mover-control-plane.md), when `deborah` becomes a worker; then the workers), draining it first
(*cordon* and *drain*). This procedure is for checking that this works,
pinning a version when needed and keeping Ansible aligned.

The plans live in [`maceosoft/gitops` → `k3s-upgrade/`](https://github.com/maceosoft/gitops/tree/main/k3s-upgrade)
and are applied by the `k3s-upgrade` Argo CD Application.

## 1. Check that the SUC is installed

The `k3s-upgrade` Application only applies the *plans*. The controller that
runs them is installed by hand once
([K3s — Manual installation, 6.1](../k3s/index.md)):

```bash
kubectl -n system-upgrade get deploy system-upgrade-controller
kubectl -n system-upgrade get plans
```

The controller and the `k3s-server` and `k3s-agent` plans must show up.

## 2. Check the upgrade status

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

To stop following `stable` (for example, to wait before a minor version
upgrade), replace `channel` with `version` in **both** plans of
`k3s-upgrade/k3s-plans.yaml`, in the `gitops` repo:

```yaml
spec:
  # channel: https://update.k3s.io/v1-release/channels/stable
  version: v1.36.5+k3s1
```

Merge the change: Argo CD applies it and the SUC keeps the nodes on that version.

## 4. Align Ansible with the actual version

Ansible installs **new** nodes with `k3s_install.core.version`
(`group_vars/incus_cluster/k3s_install.yml` in `homelab`). The SUC does not touch that
file, so after every upgrade it falls behind. Update it to
the version shown by `kubectl get nodes`:

```yaml
k3s_install:
  core:
    version: "v1.37.0+k3s1"   # la VERSION actual de los nodos
```

This is essential before [adding a node](agregar-nodo.md): otherwise the new
node joins with an older version.

## If it fails

| Symptom | Check |
|---|---|
| `get plans` shows nothing | The `k3s-upgrade` Application does not sync: the controller or its CRDs are missing (step 1) |
| A node stays `SchedulingDisabled` | The upgrade stopped halfway: check the job with `kubectl -n system-upgrade logs job/<job>` and, once resolved, `kubectl uncordon <nodo>` |
| Nodes on different versions for a long time | The `drain` does not finish (PodDisruptionBudget or pods without a controller); check the jobs from step 2 |
