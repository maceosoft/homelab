# Update K3s

K3s (a lightweight Kubernetes distribution) updates **automatically**: the SUC (System Upgrade Controller) checks the K3s `stable` and, when a new version is released, it updates one node at a time
(first the control plane, the node with the label `node-role.kubernetes.io/control-plane`: `deborah`; then the workers), evacuating them first
(*cordon* and *drain*). This procedure is to verify that it works,
pin a version when needed, and keep Ansible in sync.

The plans are in [`maceosoft/gitops` → `k3s-upgrade/`](https://github.com/maceosoft/gitops/tree/main/k3s-upgrade)
and are applied by the Application `k3s-upgrade` of Argo CD.

## 1. Check that the SUC is installed

The Application `k3s-upgrade` only applies the *plans*. The controller that
runs them is installed manually once
([K3s — Manual Installation, 6.1](../k3s/index.md)):

```bash
kubectl -n system-upgrade get deploy system-upgrade-controller
kubectl -n system-upgrade get plans
```

The controller and the plans `k3s-server` and `k3s-agent` should appear.

## 2. Check the update status

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

To stop following `stable` (for example, to wait before upgrading
to a minor version), change `channel` to `version` in the **two** plans of
`k3s-upgrade/k3s-plans.yaml`, in the repo `gitops`:

```yaml
spec:
  # channel: https://update.k3s.io/v1-release/channels/stable
  version: v1.37.2+k3s1
```

Merge the change: Argo CD applies it and the SUC leaves the nodes at that version.

## 4. Sync Ansible with the real version

Ansible installs new nodes with `k3s_install.core.version`
(`group_vars/incus_cluster/k3s_install.yml` in `homelab`). The SUC does not touch this
file, so after each update it falls out of sync. Update it to the version shown by `kubectl get nodes`:

```yaml
k3s_install:
  core:
    version: "v1.37.0+k3s1"   # la VERSION actual de los nodos
```

This is essential before [adding a node](agregar-nodo.md): otherwise, the new node will join with an older version.

## If it fails

| Symptom | To Check |
|---|---|
| `get plans` does not show anything | The Application `k3s-upgrade` is not syncing: the controller or its CRDs are missing (step 1) |
| A node remains `SchedulingDisabled` | The update was interrupted: check the job with `kubectl -n system-upgrade logs job/<job>` and, when resolved, `kubectl uncordon <nodo>` |
| Nodes with different versions for a long time | The `drain` does not complete (PodDisruptionBudget or pods without a controller); check the jobs from step 2 |
