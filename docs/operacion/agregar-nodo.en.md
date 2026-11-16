# Add a node

Add a new machine to the HomeLab as an Incus cluster member and as a **K3s worker (agent) (lightweight Kubernetes distribution)**. It is the same sequence as the initial build ([Phases 0 to 3](../implementacion/index.md)), but limited to a single node with `--limit`, so as not to touch the ones already working.

!!! info "Before you start"
    - Debian installed on the new machine, with your admin user created during installation (see [which user receives `sudo`](../implementacion/fase-0-preparacion.md#dia-0-nodos-recien-instalados-solo-la-primera-vez-por-nodo)), and connected to the LAN (local network).
    - A free static IP in `192.168.20.0/22` for the node.
    - The current cluster working: Incus and K3s with all nodes healthy.
    - A name for the node (current ones follow the *Invincible* series: `invincible`, `oliver`, `deborah`, `eve`). In examples: **`nolan`**.

All commands are run from `ansible/`.

## 1. Day 0: python3, sudo and your SSH key

A freshly installed Debian lacks what Ansible needs. Add the node's current IP (the one DHCP gave it) to `bootstrap/inventory.ini`, in the `servidores_debian` group, and run:

```bash
ansible-playbook -i bootstrap/inventory.ini bootstrap/setup_sudo.yml --ask-pass --limit <ip-actual>
ssh-copy-id <usuario-admin>@<ip-actual>
```

Details: [Phase 0 — Day 0](../implementacion/fase-0-preparacion.md#dia-0-nodos-recien-instalados-solo-la-primera-vez-por-nodo).

## 2. Inventory and node variables

In `inventory.ini`, add the node to its architecture group (`x86_nodes` or `arm64_nodes`) and to the `k3s_agent` group:

```ini
[x86_nodes]
# ... nodos existentes ...
nolan ansible_host=<ip-actual> static_ip=192.168.20.12 ip_static=false bridge_iface=eno1 ram_gb=16 cpu_model="..." k3s_role=agent

[k3s_agent]
invincible
oliver
nolan
```

`bridge_iface` is the physical network interface: confirm it on the node with `ip -br link`. The `incus_cluster` groups and the K3s groups are separated on purpose: a new node is an **agent**, never a control plane, unless you add it to `k3s_server` on purpose.

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

!!! tip "Without touching playbooks"
    The Incus *join*, cluster groups, manual scheduler, K3s labels, and DNS are computed from `inventory.ini` and `host_vars/`. No playbook needs to be edited for a new node.

If you use automatic OS updates (`k3s_install.os_hardening`), also add its reboot schedule in `group_vars/incus_cluster/k3s_install.yml` (`reboot_schedule`), different from the other nodes'.

## 3. Discovery (optional, recommended)

Measure the node's actual hardware (RAM, disks, network, temperature) before deciding its role:

```bash
ansible-playbook -i inventory.ini playbook-discovery.yml --limit nolan
```

The report ends up in `reports/nolan.md`.

## 4. Static IP

First review what will change, then apply. The playbook has a safety pause, because it may cut the SSH (Secure Shell) connection:

```bash
ansible-playbook -i inventory.ini playbook-set-static-ip.yml --limit nolan --check --diff
ansible-playbook -i inventory.ini playbook-set-static-ip.yml --limit nolan
```

Then, in `inventory.ini`, change `ansible_host` to the static IP and `ip_static=true`.

## 5. Incus package and hardening

```bash
ansible-playbook -i inventory.ini playbook-bootstrap.yml --limit nolan
ansible-playbook -i inventory.ini playbook-hardening.yml --limit nolan --check --diff
ansible-playbook -i inventory.ini playbook-hardening.yml --limit nolan
```

Hardening disables password login via SSH: if step 1 didn't load your key, the role stops on its own before locking you out.

## 6. Join the node to the Incus cluster

Include `invincible` in the `--limit`: it is the *leader* that generates the join token and assigns the cluster groups.

```bash
ansible-playbook -i inventory.ini playbook-incus-cluster.yml --limit invincible,nolan
```

## 7. Join the node to K3s

Include the control plane node (`deborah`) in the `--limit`: that's where the token the agent joins with comes from. With only `--limit nolan` it fails with *Missing k3s_token*.

!!! warning "K3s version"
    The [SUC (System Upgrade Controller)](actualizar-k3s.md) updates the cluster on its own, but Ansible installs the fixed version from `k3s_install.core.version` (`group_vars/incus_cluster/k3s_install.yml`). Before this step, put there the version the nodes have today (`kubectl get nodes` → column `VERSION`); otherwise, the new node joins with an older version.

```bash
# el primero es el control plane
ansible-playbook -i inventory.ini playbook-k3s.yml --limit deborah,nolan
```

The same playbook applies the labels from `k3s_node_labels`.

## 8. DNS and extras

Add the `nolan.mco.local` record to DNS (zones are generated from inventory):

```bash
ansible-playbook -i inventory.ini playbook-bind-dns.yml
```

If the node has WiFi (`has_wifi: true` and `wifi_iface` in its `host_vars`), configure the backup WiFi:

```bash
ansible-playbook -i inventory.ini playbook-wifi-failover.yml --limit nolan
```

## SSO access and node metrics

Without this step the node works, but no one can log in with `ssh devops@…` (it lacks opkssh and the `devops` user) and monitoring alerts with `SinDatosDeServiciosDelHost` and `SinDatosDeDiscos`. It happened to `eve`.

```bash
# SSH con la identidad de Dex: opkssh, el usuario devops y la CA del HomeLab.
# Lee la CA de cert-manager con kubectl desde tu equipo: necesita KUBECONFIG.
export KUBECONFIG=~/.kube/homelab-k3s.yaml
ansible-playbook -i inventory.ini playbook-opkssh.yml --limit nolan --check --diff
ansible-playbook -i inventory.ini playbook-opkssh.yml --limit nolan
# Métricas del nodo para el monitoreo: paquetes pendientes, servicios del host y salud de los discos
ansible-playbook -i inventory.ini playbook-apt-metrics.yml --limit nolan
ansible-playbook -i inventory.ini playbook-units-metrics.yml --limit nolan
ansible-playbook -i inventory.ini playbook-smart-metrics.yml --limit nolan
```

## Verify

The `ssh` log in via [SSO access](acceso-ssh.md): run `opkssh login` first (requires step [4.12](../implementacion/fase-4-gitops.md#412-ssh-to-hosts-with-dex-optional)).

```bash
# nolan en Ready, misma VERSION que el resto
kubectl get nodes -o wide
# etiquetas de k3s_node_labels
kubectl get node nolan --show-labels
# nolan ONLINE
ssh devops@deborah.homelab.local sudo incus cluster list
ssh devops@deborah.homelab.local sudo incus cluster group show x86-nodes
# 192.168.20.12
dig +short nolan.mco.local @192.168.20.5
```

## If it fails

| Symptom | Check |
|---|---|
| `setup_sudo.yml` doesn't connect | Current IP in `bootstrap/inventory.ini`; that Debian still allows root via SSH with password |
| You lose SSH after static IP | Connect via the new IP; check `bridge_iface` with `ip -br link` on the machine's console |
| Incus *join* fails | `--limit` without `invincible`; free space (≥ 20 GB) on the node |
| K3s: *Missing k3s_token* | `--limit` without the control plane node (`deborah`) |
| Node joins with a different K3s version | `k3s_install.core.version` outdated (see step 7 warning) |
