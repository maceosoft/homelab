# Add a disk to a node

Formats a free disk on a node, mounts it, and hands it off to **Longhorn** (Kubernetes replicated storage) or to **Incus** (a new pool for instances).

!!! danger "Destructive"
    The playbook **formats** the disk: it erases any data on it. Confirm the exact device before running it. The playbook has a safety pause and will not reformat a disk that already has a filesystem.

In the examples: disk `/dev/nvme0n1` on node **`deborah`**.

## 1. Identify the disk

Run the node discovery and read the *Storage Recommendations* section of `reports/<nodo>.md`:

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-discovery.yml --limit deborah
```

Also confirm on the node (`lsblk -f`): the disk must be empty and unmounted.

## 2. Choose who receives it

| Consumer | When | What the playbook does |
|---|---|---|
| `longhorn` | Kubernetes volumes with replicas across nodes | Mounts the disk and registers the node so Longhorn can use it |
| `incus` | More space for Incus containers and VMs (virtual machines) | Mounts the disk and creates a new storage pool, separate from the `local` pool |
| `local` | Split the disk across multiple uses | Only mounts it. With `longhorn_disk_path`, one folder goes to Longhorn; others are used to [move data](#move-data-to-another-disk) |

## 3. Declare it in `host_vars`

In `host_vars/deborah.yml`:

```yaml
storage_provision_disks:
  - device: /dev/nvme0n1
    consumer: longhorn            # o incus
    mount_path: /var/lib/longhorn-nvme0n1
    filesystem: ext4
    # wipe: true                  # si el disco trae particiones (p. ej. de Windows): las borra
    # solo si consumer: incus
    # incus_pool_name: nvme-pool
```

If the disk has partitions from another system, add `wipe: true`: without it the playbook will not format it. `wipe` never acts on a mounted disk.

`deborah` uses the `local` variant: a single disk for Longhorn, K3s, and Ollama (see its `host_vars`):

```yaml
storage_provision_disks:
  - device: /dev/nvme0n1
    consumer: local
    wipe: true
    mount_path: /srv/nvme
    mount_opts: noatime
    filesystem: ext4
    longhorn_disk_path: /srv/nvme/longhorn   # esta carpeta va a Longhorn
    longhorn_disk_name: nvme
    longhorn_storage_reserved_gib: 80        # lo que queda para K3s y Ollama
```

Without this variable, the playbook does nothing on that node.

## 4. Apply

```bash
ansible-playbook -i inventory.ini playbook-storage-provision.yml --limit deborah
```

Confirm at the safety pause when the shown device is the correct one.

## Verify

Access `ssh` via [SSO access](acceso-ssh.md) (`opkssh login` before):

```bash
# montado, con la entrada en /etc/fstab
ssh devops@deborah.homelab.local findmnt /var/lib/longhorn-nvme0n1
```

- **Longhorn:**

    === "🖱️ From the UI"

        In the UI (user interface), *Node → deborah* shows the new disk with *Schedulable* enabled.

    === "⌨️ From the console"

        The node's disks are in the `nodes.longhorn.io` resource; the new disk should appear with the condition `Schedulable` in `True`:

        ```bash
        kubectl -n longhorn-system get nodes.longhorn.io deborah -o jsonpath='{.status.diskStatus}'
        ```

- **Incus:** `sudo incus storage list` shows the new pool.

## If it fails

| Symptom | Check |
|---|---|
| The playbook does nothing | Missing `storage_provision_disks` in the node's `host_vars`, or `--limit` points to another node |
| "Already has filesystem" and does not format | Intentional: the disk is not empty. Check what it has; if it can be wiped, add `wipe: true` |
| Fails at "Get disk UUID" | The disk has a partition table (e.g., from Windows) and `wipe: true` is missing |
| Longhorn does not show the disk | Check `kubectl -n longhorn-system get nodes.longhorn.io deborah -o jsonpath='{.spec.disks}'`: the playbook adds it there |

## Remove the old disk from Longhorn

If the new disk replaces another on the same node (in `deborah`, the eMMC), Longhorn moves replicas without interrupting volumes:

1. Verify that all volumes are `healthy`:
   `kubectl -n longhorn-system get volumes.longhorn.io`.
2. Stop scheduling on the old disk and request its eviction (the disk name comes from `.spec.disks`):

    ```bash
    kubectl -n longhorn-system patch nodes.longhorn.io deborah --type merge \
      -p '{"spec":{"disks":{"<disco-viejo>":{"allowScheduling":false,"evictionRequested":true}}}}'
    ```

3. Wait for the old disk to have no replicas and for volumes to return to `healthy`:
   `kubectl -n longhorn-system get replicas.longhorn.io -o wide`.
4. Remove it from the node (in the UI: *Node → deborah → Edit node and disks → Remove*). The old disk's folder (`/var/lib/longhorn/`) is deleted manually afterwards.

## Move data to another disk

With the disk mounted at `local`, [`playbook-data-relocation.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-data-relocation.yml)
moves folders to the new disk **without changing their paths**: it copies the folder, renames the original (for rollback)
and bind-mounts the copy on top at `/etc/fstab`. Today **no node uses it**: see the warning below.

!!! danger "What happened in `deborah` (Nov 8, 2026)"
    Copying container images (`/var/lib/rancher/k3s/agent/containerd`, about 43 GB) to the NVMe, sustained writes
    heated it until it stopped responding and dropped off the PCIe bus (`controller is down`); it only came back
    after power-cycling the node. The cutover hadn't started yet, so K3s kept running. The NVMe (no heatsink)
    reads 71 °C at idle and 80 °C on one of its sensors, with critical at 82 °C.

    That's why in `deborah` only data that can be lost without consequences goes to the NVMe: **Longhorn** (each volume has
    another replica on another node). The K3s database and images stay on the eMMC: with the safeguard below,
    an NVMe that doesn't appear would leave K3s unable to start, and `deborah` is the only control plane. Until it gets
    a heatsink, not even Longhorn: its disk `nvme` is on `allowScheduling: false`. Alerts
    `NvmeTemperaturaAlta`, `NvmeTemperaturaCritica` and `DiscoDesaparecido` warn if it happens again
    ([Monitoring](monitoreo.md)).

!!! info "Before moving anything, measure"
    An NVMe isn't always faster than the disk it replaces. The one in `deborah` (SK hynix BC501, no DRAM cache)
    measured with `fio` against its eMMC: double in random 4k writes (41,300 vs 20,600 IOPS), but half
    in sequential writes (125 vs 250 MB/s) and significantly worse in writes with `fsync` (775 vs 1,329 IOPS).
    And check temperature under sustained writes (`ansible/scripts/temperaturas.sh`) before trusting it with anything.

!!! warning "Services are drained"
    Before each cutover there is a pause. If what's being moved lives inside k3s (containerd), the playbook cordons
    the node (`drain`), stops k3s and its containers (`k3s-killall.sh`), does the final copy and restarts. On a
    control-plane node, the cluster API doesn't respond while the final copy runs.

Items are declared in `data_relocation_items` of the node's `host_vars` (examples in the
[role README](https://github.com/maceosoft/homelab/blob/main/ansible/roles/data_relocation/README.md)):

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-data-relocation.yml --limit <nodo> --check
ansible-playbook -i inventory.ini playbook-data-relocation.yml --limit <nodo>
```

The safeguard is the drop-in `RequiresMountsFor` that the playbook adds to each service: if the disk doesn't mount, the service
**does not start**, instead of starting with an empty folder. If the K3s database
(`/var/lib/rancher/k3s/server`) is ever moved, that safeguard is mandatory: without it, K3s would create a new cluster. And that's exactly
the reason not to do it on a disk that can disappear.

Original folders remain as `*.emmc-old` (or the configured suffix). Delete them after everything has been
stable for a couple of days. Details and rollback in the role README.

More role details: [`storage_provision`](https://github.com/maceosoft/homelab/blob/main/ansible/roles/storage_provision/README.md).
