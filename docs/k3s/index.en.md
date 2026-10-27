# K3s — Manual Installation (Reference)

!!! info "Recommended Path"
    Use **[Phase 3 — K3s](../implementacion/fase-3-k3s.md)** with
    `playbook-k3s.yml`. This page documents manual steps (curl) as
    an alternative legacy approach.

K3s (lightweight Kubernetes distribution) hybrid cluster across the 3 nodes of the Homelab.

> The Homelab hostnames follow the *Invincible* series — see
> [characters](https://invincible.fandom.com/es/wiki/Categor%C3%ADa:Personajes).

## Cluster Nodes

| Node | IP | K3s Role |
|---|---|---|
| deborah | 192.168.20.5 | server (control plane) |
| invincible | 192.168.20.6 | agent (worker) |
| oliver | 192.168.20.7 | agent (worker) |

Verification from a node with API (Application Programming Interface) server access:

```bash
kubectl get nodes -o wide
kubectl get pods -A
```

!!! warning "Residual Traefik"
    The cluster was installed with `--disable traefik`, but residual pods
    `svclb-traefik-*` (K3s ServiceLB) persist. Remove them with the role
    `k3s_cleanup_traefik` or `ansible-playbook playbook-k3s.yml --tags traefik`.

!!! warning "Control-plane after reboot"
    If `deborah` does not expose `:6443` after reboot, verify:
    `sudo systemctl enable --now k3s && sudo journalctl -u k3s -n 50`

## 1. Prerequisites (all 3 nodes)

```bash
# Deshabilitar swap (requerido por K3s)
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# Módulos de red y sysctl para el CNI (Flannel/VXLAN por defecto)
cat <<EOF | sudo tee /etc/modules-load.d/k3s.conf
br_netfilter
overlay
EOF
sudo modprobe br_netfilter overlay

cat <<EOF | sudo tee /etc/sysctl.d/k3s.conf
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sudo sysctl --system
```

Disable swap (K3s requires this for predictable scheduling), load
the kernel modules needed by the CNI (Container Network Interface) to route traffic between pods,
and enable IP forwarding so each node can act as a pod router.

!!! note "Network"
    If these nodes run Incus cluster instances (see
    [Incus Cluster](../incus/cluster-setup.md)), use the same bridge/cluster
    group already defined — no need for an additional bridge just for K3s.

Automatable with: `ansible-playbook -i inventory.ini playbook-k3s.yml --tags prereqs`

Bootstrap options (kube-vip, Argo CD controller, labels, …):
[`playbook-options.md`](playbook-options.md). GitOps:
[`Fase 4 — GitOps`](../implementacion/fase-4-gitops.md).

## 2. Control Plane Installation (deborah)

```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.36.5+k3s1 \
  INSTALL_K3S_EXEC="server \
  --disable traefik \
  --disable servicelb \
  --write-kubeconfig-mode 600 \
  --node-ip 192.168.20.5 \
  --tls-san 192.168.20.5 \
  --tls-san deborah" sh -
```

- `--disable traefik/servicelb`: installed later (or replaced by a Gateway API controller + MetalLB) to avoid losing control
  over versions.
- `--write-kubeconfig-mode 600`: kubeconfig readable only by root (hardened
  vs 644).
- `--tls-san`: adds the fixed IP to the API server certificate, avoiding
  TLS (Transport Layer Security) errors if accessed by IP instead of hostname.

Token to join workers:

```bash
sudo cat /var/lib/rancher/k3s/server/node-token
```

Automatable with: `ansible-playbook -i inventory.ini playbook-k3s.yml --limit k3s_server`

## 3. Joining Workers

**invincible (15.5 GB — also runs CAPN as management cluster):**

```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.36.5+k3s1 \
  K3S_URL=https://192.168.20.5:6443 \
  K3S_TOKEN=<TOKEN> \
  INSTALL_K3S_EXEC="agent --node-ip 192.168.20.6" sh -
```

**oliver (7.7 GB — lightweight profile, same criteria as its `scheduler.instance manual` in Incus):**

```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.36.5+k3s1 \
  K3S_URL=https://192.168.20.5:6443 \
  K3S_TOKEN=<TOKEN> \
  INSTALL_K3S_EXEC="agent --node-ip 192.168.20.7 --kubelet-arg=max-pods=110" sh -
```

Automatable with: `ansible-playbook -i inventory.ini playbook-k3s.yml --limit k3s_agent`

## 4. Verification

```bash
kubectl get nodes -o wide
kubectl get pods -A
```

Label the nodes by architecture and capacity to use
`nodeSelector`/`nodeAffinity` in manifests:

```bash
kubectl label node oliver workload-tier=light
kubectl label node deborah workload-tier=heavy kubernetes.io/arch=arm64
kubectl label node invincible node.longhorn.io/create-default-disk=true
kubectl label node deborah node.longhorn.io/create-default-disk=true
kubectl label node oliver node.longhorn.io/create-default-disk=false
```

!!! warning "Multi-arch"
    Any container image must support `arm64/v8`
    (`docker manifest inspect <imagen>`) before scheduling it without
    `nodeSelector`, or it will fail on `deborah`.

## 5. Storage

See [Storage](../storage/index.md) for the details of replicated OpenEBS/Longhorn
x86↔arm64. GitOps manifests in [`gitops/storage/`](https://github.com/maceosoft/gitops/tree/main/storage).

## 6. Automated Update Plan

Versioned manifests in [`gitops/k3s-upgrade/`](https://github.com/maceosoft/gitops/tree/main/k3s-upgrade).

### 6.1 K3s (server + agents) — `system-upgrade-controller`

```bash
kubectl apply -f https://github.com/rancher/system-upgrade-controller/releases/latest/download/system-upgrade-controller.yaml
kubectl apply -f https://github.com/rancher/system-upgrade-controller/releases/latest/download/crd.yaml
kubectl apply -f gitops/k3s-upgrade/
```

`concurrency: 1` is intentional in a 3-node cluster: it never leaves the
cluster without full failover capacity. The controller checks the
`stable` channel periodically and, upon detecting a new version, cordons and
drains one node at a time — `deborah` (control plane) first, then
`invincible`/`oliver`.

### 6.2 Base Operating System (all 3 nodes)

In this Homelab, Debian updates **do not install automatically**: each node publishes how many are pending and
monitoring alerts via Discord. The procedure is in [Patching the Nodes](../operacion/parchear-nodos.md).

### 6.3 Incus

Follows the package cycle from the Zabbly repo:

```bash
sudo apt update && sudo apt upgrade -y incus incus-client
```

If Incus clustering is active, verify that the 3 major versions match before updating — a version mismatch between
Incus cluster members can break quorum.

### 6.4 Summary of Cadence

| Component | Mechanism | Frequency | Window |
|---|---|---|---|
| K3s (server/agents) | system-upgrade-controller, stable channel | Automatic upon detecting release | Continuous, one node at a time, control plane first |
| Base OS | Metric alert + [Patching the Nodes](../operacion/parchear-nodos.md) | Upon receiving the alert | One node at a time |
| Incus | Manual apt or monthly cron | Monthly | Scheduled maintenance |

## 7. Post-Installation Checklist

- [x] K3s v1.36.5+k3s1 installed (stable channel)
- [x] Workers invincible/oliver joined to API at `192.168.20.5:6443`
- [x] overlay/br_netfilter modules loaded on workers
- [x] Argo CD deployed (application-controller on invincible)
- [ ] `kubectl get nodes` shows 3 nodes in `Ready` (verify CP after reboot)
- [ ] Architecture, tier, and Longhorn labels applied
- [ ] Traefik svclb removed
- [ ] `system-upgrade-controller` deployed with both `Plan` applied
- [ ] Patch metrics active ([`playbook-apt-metrics.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-apt-metrics.yml))
- [ ] kubeconfig backed up outside the cluster (never committed — see `.gitignore`)
