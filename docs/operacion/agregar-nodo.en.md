# Add a Node

Add a new machine to the HomeLab as a member of the Incus cluster and as a
**K3s worker (lightweight Kubernetes distribution)**. It's the same sequence as the initial setup
([Stages 0 to 3](../implementacion/index.md)), but limited to a single node with
`--limit`, without touching the ones that are already running.

!!! info "Before you start"
    - Debian installed on the new machine, with your admin user created
      during installation (see [which user gets `sudo`](../implementacion/fase-0-preparacion.md#day-0-freshly-installed-nodes-only-the-first-time-per-node)),
      and connected to the LAN (local network).
    - A free IP address in `192.168.20.0/22` for the node.
    - The current cluster running: Incus and K3s with the 3 healthy nodes.
    - A name for the node (the current ones follow the series *Invincible*:
      `invincible`, `oliver`, `deborah`). In the examples: **`nolan`**.

All commands are run from `ansible/`.

## Day 0: python3, sudo, and your SSH key

A freshly installed Debian doesn't have what Ansible needs. Add the current IP
address of the node (the one assigned by DHCP) to `bootstrap/inventory.ini`, in the
group `servidores_debian`, and run:

```bash
ansible-playbook -i bootstrap/inventory.ini bootstrap/setup_sudo.yml --ask-pass --limit <ip-actual>
ssh-copy-id <usuario-admin>@<ip-actual>
```

Details: [Stage 0 — Day 0](../implementacion/fase-0-preparacion.md#day-0-freshly-installed-nodes-only-the-first-time-per-node).

## Node Inventory and Variables

In `inventory.ini`, add the node to its architecture group
(`x86_nodes` or `arm64_nodes`) and to the group `k3s_agent`:

```ini
[x86_nodes]
# ... nodos existentes ...
nolan ansible_host=<ip-actual> static_ip=192.168.20.8 ip_static=false bridge_iface=eno1 ram_gb=16 cpu_model="..." k3s_role=agent

[k3s_agent]
invincible
oliver
nolan
```

`bridge_iface` is the physical network interface: confirm it on the node with
`ip -br link`. The groups `incus_cluster` and the K3s groups are separated on purpose: a new node is **agent**, never control plane, unless you add it to `k3s_server` intentionally.

Create `host_vars/nolan.yml` (copy an existing one as a base):

```yaml
---
incus_role: "Miembro"
incus_cluster_role: member
incus_cluster_groups: [x86-nodes, default]   # arm64-nodes si es ARM64
k3s_role: agent
ip_static: true
k3s_node_labels:
  node.longhorn.io/create-default-disk: "false"   # "true" si aporta disco a Longhorn
ansible_python_interpreter: /usr/bin/python3
```

!!! tip "No playbook edits"
    The *join* to Incus, the cluster groups, the manual scheduler, the K3s labels, and the DNS are calculated from `inventory.ini` and `host_vars/`. No playbook edits are needed for a new node.

If you use automatic OS updates (`k3s_install.os_hardening`), also add its reboot schedule in `group_vars/incus_cluster/k3s_install.yml`
(`reboot_schedule`), different from the others.

## Discovery (optional, recommended)

Measure the real hardware of the node (RAM, disks, network, temperature) before
deciding its role:

```bash
ansible-playbook -i inventory.ini playbook-discovery.yml --limit nolan
```

The report is saved in `reports/nolan.md`.

## Fixed IP Address

First review what will change and then apply it. The playbook has a safety pause
because it can cut the SSH connection:

```bash
ansible-playbook -i inventory.ini playbook-set-static-ip.yml --limit nolan --check --diff
ansible-playbook -i inventory.ini playbook-set-static-ip.yml --limit nolan
```

After that, in `inventory.ini`, change `ansible_host` to the fixed IP address and
`ip_static=true`.

## Incus Package and Hardening

```bash
ansible-playbook -i inventory.ini playbook-bootstrap.yml --limit nolan
ansible-playbook -i inventory.ini playbook-hardening.yml --limit nolan --check --diff
ansible-playbook -i inventory.ini playbook-hardening.yml --limit nolan
```

The hardening disables password login via SSH: if step 1 didn't load your key, the role stops before leaving you out.

## Join the Node to the Incus Cluster

Include `invincible` in the `--limit`: it's the *leader* that generates the join token and assigns the cluster groups.

```bash
ansible-playbook -i inventory.ini playbook-incus-cluster.yml --limit invincible,nolan
```

## Join the Node to K3s

Include the control plane node (today `deborah`; `oliver` after the [move](mover-control-plane.md)) in the `--limit`: from there comes the token
with which the agent joins. With only `--limit nolan` fails with *Missing k3s_token*.

!!! warning "K3s Version"
    The [SUC (System Upgrade Controller)](actualizar-k3s.md) updates the
    cluster only, but Ansible installs the fixed version of
    `k3s_install.core.version` (`group_vars/incus_cluster/k3s_install.yml`).
    Before this step, put there the version the nodes have today
    (`kubectl get nodes` → column `VERSION`); if not, the new node joins
    with an older version.

```bash
# el primero es el control plane
ansible-playbook -i inventory.ini playbook-k3s.yml --limit deborah,nolan
```

The same playbook applies the `k3s_node_labels` labels.

## DNS and Extras

Add the `nolan.mco.local` record to DNS (the zones are generated from the inventory):

```bash
ansible-playbook -i inventory.ini playbook-bind-dns.yml
```

If the node has WiFi (`has_wifi: true` and `wifi_iface` in its `host_vars`),
configure the WiFi backup:

```bash
ansible-playbook -i inventory.ini playbook-wifi-failover.yml --limit nolan
```

## Verify

The `ssh` log in with [SSO access](acceso-ssh.md): run `opkssh login` first (requires step
[4.12](../implementacion/fase-4-gitops.md#412-ssh-to-hosts-with-dex-optional)).

```bash
# nolan en Ready, misma VERSION que el resto
kubectl get nodes -o wide
# etiquetas de k3s_node_labels
kubectl get node nolan --show-labels
# nolan ONLINE
ssh devops@deborah.homelab.local sudo incus cluster list
ssh devops@deborah.homelab.local sudo incus cluster group show x86-nodes
# 192.168.20.8
dig +short nolan.mco.local @192.168.20.5
```

## If It Fails

| Symptom | Check |
|---|---|
| `setup_sudo.yml` doesn't connect | Current IP in `bootstrap/inventory.ini`; that Debian still allows root login via SSH with password |
| Lose SSH after fixed IP | Connect with the new IP; check `bridge_iface` with `ip -br link` on the machine console |
| Join to Incus fails | `--limit` without `invincible`; free space (≥ 20 GB) on the node |
| K3s: *Missing k3s_token* | `--limit` without the control plane node (`deborah` today, `oliver` after the move) |
| The node joins with a different K3s version | `k3s_install.core.version` outdated (see the warning in step 7) |
