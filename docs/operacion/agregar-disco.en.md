# Add a disk to a node

Format a free disk on a node, mount it, and deliver it to **Longhorn**
(replicated storage for Kubernetes) or to **Incus** (a new pool for
containers and VMs).

!!! danger "Destructive"
    The playbook **formats** the disk: it deletes any data on it. Confirm the
    exact device before running it. The playbook has a safety pause and does not
    reformat a disk that already has a file system.

In the examples: disk `/dev/nvme0n1` on the node **`deborah`**.

## 1. Identify the disk

Run the node discovery and read the *Storage Recommendations* section of
`reports/<nodo>.md`:

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-discovery.yml --limit deborah
```

Confirm it also on the node (`lsblk -f`): the disk must be empty and unmounted.

## 2. Choose who to deliver to

| Consumer | When | What the playbook does |
|---|---|---|
| `longhorn` | For Kubernetes volumes with node-to-node replication | Mounts the disk and marks the node so Longhorn can use it |
| `incus` | For more space for Incus containers and VMs | Mounts the disk and creates a new storage pool, separate from the pool `local` |

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

Confirm in the safety pause when the device shown is correct.

## Verify

The `ssh` logs in with [single sign-on](acceso-ssh.md) (`opkssh login` before):

```bash
# montado, con la entrada en /etc/fstab
ssh devops@deborah.homelab.local findmnt /var/lib/longhorn-nvme0n1
```

- **Longhorn:**

    === "🖱️ From the UI"

        In the UI, *Node → deborah* shows the new disk with *Schedulable* enabled.

    === "⌨️ From the console"

        The disks on the node are in the resource `nodes.longhorn.io`; the new disk should appear with the condition
        `Schedulable` in `True`:

        ```bash
        kubectl -n longhorn-system get nodes.longhorn.io deborah -o jsonpath='{.status.diskStatus}'
        ```

- **Incus:** `sudo incus storage list` shows the new pool.

## If it fails

| Symptom | Check |
|---|---|
| The playbook does nothing | Missing `storage_provision_disks` in `host_vars` of the node, or `--limit` points to another node |
| "Already has filesystem" and does not format | By design: the disk is not empty. Check what it contains before manually deleting it |
| Longhorn does not show the disk | Wait a minute and check the node annotation: `kubectl get node deborah -o yaml \| grep longhorn` |

More details about the role: [`storage_provision`](https://github.com/maceosoft/homelab/blob/main/ansible/roles/storage_provision/README.md).
