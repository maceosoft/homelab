# Remove or replace a node

Removes a K3s (lightweight Kubernetes distribution) **worker** and Incus **member**: first it is drained, then
it is removed from each cluster and finally from the inventory. To **replace** a
machine, remove the old one with this procedure and add the new one with
[Add a node](agregar-nodo.md).

!!! danger "Nodes that are not removed with this procedure"
    - **The K3s control plane node** (`deborah` today; `oliver` once the
      [move](mover-control-plane.md) is done): removing it shuts the cluster down. First you have to
      [move the control plane](mover-control-plane.md) to another node or rebuild it (see the
      [bootstrap runbook](https://github.com/maceosoft/homelab/blob/main/ansible/bootstrap/README.md)).
    - **`deborah`** is also the LAN DNS (BIND): before removing it you have to move the DNS.
    - **`invincible`** is the Incus *leader* and hosts the Incus UI (user interface):
      those roles have to be moved to another node first.
    - **Incus quorum:** the cluster has 3 members. With 2 it keeps
      working but no longer tolerates another failure. Add the replacement soon.

In the examples, the node being removed is **`nolan`**.

## 1. Drain the node in K3s

```bash
kubectl cordon nolan
kubectl drain nolan --ignore-daemonsets --delete-emptydir-data
```

If the node contributes a disk to Longhorn (`node.longhorn.io/create-default-disk: "true"`), in the Longhorn UI: *Node → nolan → Edit* → turn off
*Scheduling* and check *Eviction Requested*. Wait for its replicas to
move to other nodes before continuing.

## 2. Drain the node in Incus

From any node of the Incus cluster:

```bash
# instancias en nolan
sudo incus list --all-projects --format csv --columns nL | grep nolan
# las mueve o detiene
sudo incus cluster evacuate nolan
```

## 3. Remove it from K3s

```bash
kubectl delete node nolan
cd ansible
ansible-playbook -i inventory.ini playbook-k3s-uninstall.yml --limit nolan
```

On a worker, the playbook only removes the agent (it never touches the control plane).

## 4. Remove it from Incus

From the leader (`invincible`). `ssh` gets in with [SSO access](acceso-ssh.md) (`opkssh login` first):

```bash
ssh devops@invincible.homelab.local sudo incus cluster remove nolan
```

## 5. Inventory and DNS

1. Delete the node's line in `inventory.ini` (architecture group and
   `k3s_agent`) and its `host_vars/nolan.yml` file.
2. If it was in `reboot_schedule` (`group_vars/incus_cluster/k3s_install.yml`),
   remove it from there.
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

In Longhorn, the volumes must end up *Healthy* (no replicas on
`nolan`).

## If it fails

| Symptom | Check |
|---|---|
| `drain` keeps waiting | A pod with a PodDisruptionBudget or without a controller; check with `kubectl get pods -A -o wide \| grep nolan` |
| Longhorn volumes *Degraded* | You did not wait for the replica eviction (step 1); add the disk back or wait for Longhorn to rebuild |
| `incus cluster remove` refuses | There are instances left on the node: repeat `incus cluster evacuate nolan` |
| The node no longer powers on | Skip the steps that require connecting to it and use `sudo incus cluster remove --force nolan` |
