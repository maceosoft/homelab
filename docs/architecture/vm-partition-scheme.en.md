# Partitioning scheme for workload VMs (CAPN)

Convention for the VMs (virtual machines) that CAPN (Cluster API Provider for Incus) provisions as workload
clusters (for example `demo`, see [Workload Clusters](nivel-3-componentes.md#33-workload-clusters)). It is a
template for the base image of those VMs, not a measured state.

It comes from the partition review of the 3 bare-metal nodes (the
[`playbook-discovery.yml`](../hardware/discovery.md) report, section "Recomendaciones — esquema de partición del SO"):
no node has `/var` separate from `/`, and the swap of each one was sized with a different criterion (between 13 % and
94 % off from `min(RAM/2, 8GB)`). On an already installed node this cannot be fixed without repartitioning the
mounted root; on a new VM it is defined from the first boot.

## Scheme

| Partition | Size | Filesystem | Notes |
|---|---|---|---|
| `/boot` (or `/boot/efi` with UEFI) | 1 GB | vfat/ext4 | Same as the 3 bare-metal nodes |
| swap | `min(RAM/2, 8GB)` | swap | Fixed formula, the same on every VM |
| `/var` | ≥20 % of the disk, or 20 GB minimum | ext4 | Separate from `/`: runaway growth of logs, containerd images or local volumes does not fill the root |
| `/` | Rest of the disk | ext4 | Base system |

## Why separate `/var`

K3s workloads (containerd, logs, image cache, `local-path-provisioner`/OpenEBS if used inside the VM) all write
under `/var`. Without a separate partition, if that grows out of control it can fill `/` and bring down the whole
node, not just the workload. On already installed bare metal, separating `/var` requires reinstalling; on a new
CAPN VM it costs nothing to define it in the template from day one.

## Applying it

The scheme belongs in the base image or template that CAPN uses to provision the VMs, not in Ansible after
installation. This repo does not have that template yet.
