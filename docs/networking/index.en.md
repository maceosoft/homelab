# Network

!!! info "Part of the implementation guide"
    Run this phase with **[Phase 1 — Network](../implementacion/fase-1-red.md)** and
    `playbook-set-static-ip.yml`.

## L2 Bridge to the Physical LAN

The **3 nodes** use a Linux bridge (`br0`) over the physical interface,
so that Incus instances receive IP directly from the LAN (local network) and are
reachable between hosts without needing OVN (Open Virtual Network).

| Node | Physical Interface | IP on br0 (static) |
|---|---|---|
| invincible | `eno2` | 192.168.20.6 |
| oliver | `eno1` | 192.168.20.7 |
| deborah | `enP4p65s0` | 192.168.20.5 |

> Confirm with `ip -br link` on the node before applying — the name of the
> physical interface may differ from this table after an OS update.

Example netplan — invincible:

```yaml
# /etc/netplan/br0.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eno2:
      dhcp4: no
  bridges:
    br0:
      interfaces: [eno2]
      addresses: [192.168.20.6/22]
      routes:
        - to: default
          via: 192.168.20.1
      nameservers:
        addresses: [192.168.20.5, 192.168.20.1]
```

Example netplan — deborah (same subnet, different interface and last octet):

```yaml
# /etc/netplan/br0.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enP4p65s0:
      dhcp4: no
  bridges:
    br0:
      interfaces: [enP4p65s0]
      addresses: [192.168.20.5/22]
      routes:
        - to: default
          via: 192.168.20.1
      nameservers:
        addresses: [192.168.20.5, 192.168.20.1]
```

```bash
ip -br link
# Debian no lo trae instalado por defecto
sudo apt install -y netplan.io
# corta SSH si cambias de IP
sudo netplan apply
```

The Ansible playbook installs `netplan.io`, enables `systemd-networkd` and migrates
the NIC (network interface card) out of ifupdown before writing `/etc/netplan/br0.yaml`.

```bash
ansible-playbook -i inventory.ini playbook-set-static-ip.yml --limit deborah
```

Incus profile to use the bridge in the instances:

```bash
incus profile device add default eth0 nic nictype=bridged parent=br0
```

## Fixed IP — why it is mandatory here

1. **Incus cluster**: `cluster.https_address` is recorded by IP when joining.
2. **K3s (lightweight Kubernetes distribution)**: kubelet uses the node IP as identity.
3. **CAPN (Cluster API Provider for Incus)**: the `Secret` `lxc-secret` points to `https://<IP>:8443` as a fixed string.

## IP Scheme

| Node | Current IP (DHCP/pre-bridge) | IP on br0 |
|---|---|---|
| invincible | 192.168.23.162 | 192.168.20.6 |
| oliver | 192.168.20.87 | 192.168.20.7 |
| deborah | 192.168.21.211 | 192.168.20.5 |

> The LAN is a `/22` (`192.168.20.0`–`192.168.23.255`), not a `/24` — the
> "current" IPs in this table are DHCP leases within that same range
> (not different subnets). The source of truth at all times is
> `ansible_host` in `inventory.ini`.

### LAN Addressing (`192.168.20.0/22`, gateway `192.168.20.1`)

The router's DHCP hands out **`192.168.20.31` to `192.168.23.191`**. Everything static lives **outside** that range:

| Range | Use | Where Configured |
|---|---|---|
| `192.168.20.1` | Gateway (router) | Router |
| `192.168.20.4` | K3s API VIP (kube-vip, optional) | `kube_vip.address` in `k3s_install.yml` |
| `192.168.20.5`, `.6`, `.7` | deborah, invincible, oliver | `static_ip` in `inventory.ini` |
| `192.168.20.31 – 192.168.23.191` | **Router's DHCP** | Router |
| `192.168.23.192 – .199` | Available | — |
| `192.168.23.200 – .220` | **MetalLB** (`LoadBalancer`, Gateway; the Gateway of Kong uses `.200`) | [`gitops/metallb/ipaddresspool.yaml`](https://github.com/maceosoft/gitops/blob/main/metallb/ipaddresspool.yaml) |
| `192.168.23.221 – .223` | Available | — |
| `192.168.23.224/28` (`.224–.239`) | **Incus LB** (OVN), `ipv4.routes` of the uplink | `incus_ovn_lb_routes` in `group_vars/incus_cluster/ovn.yml` |
| `192.168.23.240 – .249` | **External OVN**, `ipv4.ovn.ranges` (a virtual router per OVN network) | `incus_ovn_external_ranges` in the same file |
| `192.168.23.250 – .255` | Available (`.255` is the broadcast of the `/22`) | — |

Outside the LAN, private networks that cannot overlap with it or each other:

| Network | Use |
|---|---|
| `10.42.0.0/16` and `10.43.0.0/16` | K3s Pods and Services |
| `192.168.19.0/24` | Internal OVN network (`ovn-lan`, with NAT) |

!!! warning "Outside the DHCP"
    Fixed IPs, the MetalLB pool, and OVN segments must remain **outside the DHCP range**
    (`192.168.20.31–192.168.23.191`). If not, the router may hand them out to another device and conflict. The preflight of the role
    `incus_ovn` fails if its segments overlap with DHCP or MetalLB.

After `playbook-set-static-ip.yml`, update `ansible_host` in
[`inventory.ini`](https://github.com/maceosoft/homelab/blob/main/ansible/inventory.ini)
to the value of `static_ip` if the connection IP changed.

### Ollama: router and nodes

The AI assistant has **one entry point**: the router `ollama-router` (namespace `ai`). Internal clients use the Service `http://ollama-router.ai.svc`; external clients, `https://ollama.homelab.local` (Kong, HTTPS only; the name is in the `homelab.local` zone of BIND). The router requires a Bearer token.

Each Ollama node (`deborah` `192.168.20.5`, `invincible` `192.168.20.6`, `oliver` `192.168.20.7`, and when powered on, the Mac) has a **socket on port `11434`** that wakes up Ollama; internally Ollama listens only
on `127.0.0.1:11435`. The socket listens **only on the node IP** (variable `ollama_ondemand_listen`) and the
node firewall allows the port from K3s nodes and from pods (the router may be on the same node). The Ollama node does not authenticate: inference protection is the router token plus NetworkPolicy in the namespace `ai` (which are activated in stages). Details in
[Local AI Assistant](../operacion/ia-ollama.md) and [Add a node to the Ollama cluster](../operacion/agregar-nodo-ollama.md).

### K3s API Names

Agents, kubeconfig, and certificates use the name `k3s.homelab.local` for the API (port `6443`) instead of a specific node IP. This way the control plane can move without touching clients
([procedure](../operacion/mover-control-plane.md)).

## Exposed Ports and Host Firewall

Each node has a host firewall with `nftables` (role `host_firewall`): its own table, evaluated before
kube-proxy and not modifying Calico chains. The policy is `accept` with explicit denials (to avoid cutting off K3s, Calico, Longhorn, and MetalLB if they change their ports), and traffic between nodes is trusted. The following is restricted:

- SSH (`22`) from the LAN, with authentication via Dex.
- The K3s API (`6443`), the kubelet (`10250`), BGP traffic (`179`), FRR traffic (`2623`), and MetalLB traffic (`7946`), and Typha
  (`5473`): only between nodes and the pod range.
- Metrics (`9100`, `9120`, `9140`, `9141`): only to the collector and nodes.
- Incus (`8443`): nodes, pods, and operator. Ollama (`11434`): K3s nodes, pods, and machines added to `host_firewall_ollama_extra_cidrs` (the Mac).
- DNS (`53`) from the LAN.

The list of what remains without its own authentication, along with the reason and the network control that replaces it, is in
[Authentication Model](../security/modelo-de-autenticacion.md#network-controlled-exceptions). The rules are applied with a self-reversing safety mechanism (see [Post-Incident Hardening](../security/hardening-post-incidente.md)).
