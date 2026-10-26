# Add a disk to a node

Formats a free disk on a node, mounts it and hands it to **Longhorn**
(replicated Kubernetes storage) or to **Incus** (a new pool for
instances).

!!! danger "Destructive"
    The playbook **formats** the disk: it erases any data on it. Confirm
    the exact device before running it. The playbook has a safety
    pause and does not reformat a disk that already has a filesystem.

In the examples: disk `/dev/nvme0n1` on node **`deborah`**.

## 1. Identify the disk

Run the node discovery and read the *Recomendaciones de
almacenamiento* section of `reports/<nodo>.md`:

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-discovery.yml --limit deborah
```

Also confirm it on the node (`lsblk -f`): the disk must be empty and
unmounted.

## 2. Choose who gets it

| Consumer | When | What the playbook does |
|---|---|---|
| `longhorn` | Kubernetes volumes with replicas across nodes | Mounts the disk and annotates the node so Longhorn uses it |
| `incus` | More space for Incus containers and VMs (virtual machines) | Mounts the disk and creates a new storage pool, separate from the `local` pool |

## 3. Declare it in `host_vars`

In `host_vars/deborah.yml`:

```yaml
storage_provision_disks:
  - device: /dev/nvme0n1
    consumer: longhorn            # o incus
    mount_path: /var/lib/longhorn-nvme0n1
    filesystem: ext4
    # solo si consumer: incus
    # incus_pool_name: nvme-pool
```

Without this variable, the playbook does nothing on that node.

## 4. Apply

```bash
ansible-playbook -i inventory.ini playbook-storage-provision.yml --limit deborah
```

Confirm at the safety pause when the device shown is the
right one.

## Verify

`ssh` gets in with [SSO access](acceso-ssh.md) (`opkssh login` first):

```bash
# montado, con la entrada en /etc/fstab
ssh devops@deborah.homelab.local findmnt /var/lib/longhorn-nvme0n1
```

- **Longhorn:** in the UI (user interface), *Node → deborah* shows the new disk with
  *Schedulable* enabled.
- **Incus:** `sudo incus storage list` shows the new pool.

## If it fails

| Symptom | Check |
|---|---|
| The playbook does nothing | `storage_provision_disks` is missing from the node's `host_vars`, or `--limit` points to another node |
| "Already has a filesystem" and it does not format | On purpose: the disk is not empty. Check what it holds before wiping it by hand |
| Longhorn does not show the disk | Wait a minute and check the node annotation: `kubectl get node deborah -o yaml \| grep longhorn` |

More detail on the role: [`storage_provision`](https://github.com/maceosoft/homelab/blob/main/ansible/roles/storage_provision/README.md).
