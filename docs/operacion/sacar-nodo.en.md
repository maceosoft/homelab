# Remove or Replace a Node

Remove a **worker** from K3s (a lightweight Kubernetes distribution) and an **Incus member**: first empty it, then remove it from each cluster, and finally from the inventory. To **replace** a node, remove the old one using this procedure and add the new one with [Add a Node](agregar-nodo.md).

!!! danger "Nodes Not Removed by This Procedure"
    - **The K3s control plane node** (`deborah`): removing it will shut down the cluster. First, you need to [move the control plane](mover-control-plane.md) to another node or rebuild it (see the [bootstrap runbook](https://github.com/maceosoft/homelab/blob/main/ansible/bootstrap/README.md)).
    - **`deborah`** also serves as the DNS (BIND) for the LAN: move the DNS before removing it.
    - **`invincible`** is the Incus *leader* and hosts the Incus UI: move those roles to another node before removing it.
    - **Incus Quorum:** the cluster has 3 members. With 2, it still functions but can no longer tolerate another failure. Add the replacement soon.

In the examples, the node to be removed is **`nolan`**.

## 1. Empty the Node in K3s

```bash
kubectl cordon nolan
kubectl drain nolan --ignore-daemonsets --delete-emptydir-data
```

If the node provides disk space to Longhorn (`node.longhorn.io/create-default-disk: "true"`), disable its *Scheduling* and request that it be emptied:

=== "🖱️ From the UI"

    In the Longhorn UI: *Node → nolan → Edit* → disable *Scheduling* and mark *Eviction Requested*.

=== "⌨️ From the console"

    Do the same on the resource `nodes.longhorn.io` of that node:

    ```bash
    kubectl -n longhorn-system patch nodes.longhorn.io nolan --type merge \
      -p '{"spec":{"allowScheduling":false,"evictionRequested":true}}'
    # réplicas que siguen en nolan (repite hasta que no salga ninguna)
    kubectl -n longhorn-system get replicas.longhorn.io \
      -o custom-columns=NOMBRE:.metadata.name,NODO:.spec.nodeID | grep nolan
    ```

Wait for its replicas to move to other nodes before proceeding.

## 2. Empty the Node in Incus

From any node in the Incus cluster:

```bash
# instancias en nolan
sudo incus list --all-projects --format csv --columns nL | grep nolan
# las mueve o detiene
sudo incus cluster evacuate nolan
```

## 3. Remove It from K3s

```bash
kubectl delete node nolan
cd ansible
ansible-playbook -i inventory.ini playbook-k3s-uninstall.yml --limit nolan
```

On a worker, the playbook only removes the agent (it never touches the control plane).

## 4. Remove It from Incus

From the leader (`invincible`). The `ssh` logs in with [SSO access](acceso-ssh.md) (`opkssh login` before):

```bash
ssh devops@invincible.homelab.local sudo incus cluster remove nolan
```

## 5. Inventory and DNS

1. Delete the node's line in `inventory.ini` (architecture group and `k3s_agent`) and its file `host_vars/nolan.yml`.
2. If it was in `reboot_schedule` (`group_vars/incus_cluster/k3s_install.yml`), remove it from there.
3. Regenerate the DNS to remove `nolan.mco.local`:

```bash
ansible-playbook -i inventory.ini playbook-bind-dns.yml
```

## Verify

```bash
# nolan ya no aparece
kubectl get nodes
# nolan ya no aparece
ssh devops@invincible.homelab.local sudo incus cluster list
# sin respuesta
dig +short nolan.mco.local @192.168.20.5
```

In Longhorn, the volumes must remain *Healthy* (without replicas on `nolan`).

## If It Fails

| Symptom | Check |
|---|---|
| `drain` hangs | A pod with PodDisruptionBudget or without a controller; check with `kubectl get pods -A -o wide \| grep nolan` |
| Longhorn volumes *Degraded* | You did not wait for replica evacuation (step 1); re-add the disk or wait for Longhorn to rebuild |
| `incus cluster remove` refuses | Instances remain on the node: repeat `incus cluster evacuate nolan` |
| The node no longer boots | Skip steps that require connecting to it and use `sudo incus cluster remove --force nolan` |
