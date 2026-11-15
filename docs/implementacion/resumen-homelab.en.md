# HomeLab Summary

Wrap-up of the [implementation guide](index.md): checklist of what was deployed,
URLs, `/etc/hosts`, nodes, secrets, and global verification. Check this page
when you finish Phase 4 at the very least; phases 5 and 6 are optional.

## Completed walkthrough (by phase)

| Phase | What is ready | Tool |
|---|---|---|
| [0 — Preparation](fase-0-preparacion.md) | Repo, Ansible, `inventory.ini`, optional discovery | `playbook-discovery.yml` |
| [1 — Network](fase-1-red.md) | Static IP on `br0` (`192.168.20.5`, `.6`, `.7`) | `playbook-set-static-ip.yml` |
| [2 — Incus](fase-2-incus.md) | HA cluster, groups, UI, `dir` storage | `playbook-bootstrap.yml` + `playbook-incus-cluster.yml` |
| [3 — K3s](fase-3-k3s.md) | Management cluster + Argo CD controller; **Calico** CNI | `playbook-k3s.yml` |
| [4 — GitOps](fase-4-gitops.md) | MetalLB, Gateway API, storage, Dex/GitHub SSO | Argo CD + `playbook-dex-oauth-secrets.yml` |
| [5 — vCluster](fase-5-vcluster.md) *(opt.)* | Platform, web kubeconfig (connected cluster) | Argo CD Application |
| [6 — CAPN](fase-6-capn.md) *(opt.)* | Workload clusters on Incus | `clusterctl` + `capn-demo.yaml` |

## URLs and web access

| Service | URL | Auth | Phase |
|---|---|---|---|
| **Argo CD** | [`https://argocd.homelab.local`](https://argocd.homelab.local) | GitHub SSO via Dex | 4 |
| **Dex** (issuer) | `https://argocd.homelab.local/api/dex` | — | 4 |
| **vCluster Platform** | [`https://vcluster.homelab.local`](https://vcluster.homelab.local) | Dex → GitHub SSO | 5 |
| **Incus UI** | [`https://incus.homelab.local:8443`](https://incus.homelab.local:8443) | Dex SSO (or client cert before Phase 4) | 2 / 4 |
| **Grafana** *(optional)* | [`https://grafana.homelab.local`](https://grafana.homelab.local) | GitHub SSO via Dex (fallback: `admin` from the `grafana-admin` item) | 4 ([4.13](fase-4-gitops.md#413-monitoring-and-alerts-optional)) |
| **Open WebUI** (AI assistant) | [`https://open-webui.homelab.local`](https://open-webui.homelab.local) | GitHub SSO via Dex (team `devops`) | [Local AI](../operacion/ia-ollama.md) |
| **Ollama** (router) | `https://ollama.homelab.local` | Per-client Bearer token (not for people) | [Local AI](../operacion/ia-ollama.md) |
| **K3s API** | `https://k3s.homelab.local:6443` (currently points to `deborah`, `192.168.20.5`) | kubeconfig | 3 |

### Kubeconfig

| Cluster | How to get it |
|---|---|
| Management K3s | vCluster Platform (connected cluster) or `playbook-k3s.yml` with `fetch_kubeconfig` |
| vClusters | [vCluster Platform](fase-5-vcluster.md) UI |
| CAPN workload | `clusterctl get kubeconfig` (Phase 6) |

## DNS on your workstation

Use `192.168.20.5` (BIND on `deborah`) as your DNS server: `argocd`, `vcluster`, `api`, `grafana`, `open-webui`, and `ollama` (`.homelab.local`) point to the Gateway
(`192.168.23.200`, static IP) and `incus.homelab.local` to invincible
([Phase 4 — 4.8](fase-4-gitops.md#48-homelablocal-dns)). If you can't, the fallback
is `/etc/hosts`:

```
192.168.23.200  argocd.homelab.local vcluster.homelab.local api.homelab.local grafana.homelab.local open-webui.homelab.local ollama.homelab.local
192.168.20.6    incus.homelab.local
```

Verification:

```bash
curl -kI https://argocd.homelab.local
curl -kI https://vcluster.homelab.local
# solo si instalaste el monitoreo (4.13)
curl -kI https://grafana.homelab.local
curl -kI https://incus.homelab.local:8443
```

## HomeLab nodes

| Hostname | IP `br0` | Incus | K3s | Notes |
|---|---|---|---|---|
| invincible | 192.168.20.6 | Leader + UI | agent | 15.5 GB; Longhorn disk; Ollama node |
| oliver | 192.168.20.7 | Quorum, manual scheduler | agent | 7.7 GB: tight on RAM; no automatic instances; Ollama node |
| deborah | 192.168.20.5 | arm64-nodes | **server** (CP) | 31 GB RAM; DNS (BIND); Ollama node |
| eve | 192.168.20.8 | Database standby (`database-standby`) | agent | 31 GB; MacBook Pro with T2 chip; `br0` over USB adapter; Ollama node |

The control plane is on `deborah`. If you ever need to move it to another node, the procedure is in
[Move the control plane](../operacion/mover-control-plane.md).

Incus storage: pool `local`, driver `dir`, profile `default` → NIC (network interface card) `br0`.

Hardware details: [Inventory](../hardware/inventory.md).

## Cluster network (CNI)

| Decision | HomeLab default | Alternative |
|---|---|---|
| CNI | **Calico** (`k3s_cni: calico`; then Argo CD adopts it with `calico-operator` and `calico-config`) | Flannel `vxlan` (embedded in K3s), Canal, or Cilium |

Ansible variable: `k3s_install.core.cni` in [`group_vars/incus_cluster/k3s_install.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/group_vars/incus_cluster/k3s_install.yml).
Details and trade-offs: [Phase 3 — CNI](fase-3-k3s.md#cni) · [playbook-options](../k3s/playbook-options.md#cni).

Verification:

```bash
kubectl get pods -n calico-system -l k8s-app=calico-node
# o flannel / canal / cilium si elegiste otro CNI
```

## Secrets and SSO (1Password)

| 1Password field | Use |
|---|---|
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | Dex → GitHub OAuth (manual in GitHub + 1Password) |
| `VCLUSTER_CLIENT_SECRET` | Dex + Helm Platform (Ansible generates it if missing) |

**Personal** account, **`HomeLab`** vault (configurable via env vars).
Playbook: `playbook-dex-oauth-secrets.yml`.

!!! important "Default permissions"
    In vCluster Platform, SSO (single sign-on) users **can't see anything** until they are granted
    access. In Incus, anyone who signs in via SSO has full access: the control is that Dex only lets
    through the `devops` team of `maceosoft`. See [Phase 4](fase-4-gitops.md) and [Phase 5](fase-5-vcluster.md).

Documentation: [OAuth secrets](https://github.com/maceosoft/gitops/blob/main/argocd/secrets/1password.md)

## GitOps (Argo CD)

Typical apps in `Healthy` after Phase 4:

- `argocd`, `argocd-route`, `metallb`, `homelab-storage`, `kong`, …
- Optional (manual sync): `vcluster-platform`, `capn-demo`
- CNI: `calico-operator` + `calico-config` (manual sync); `canal` or `cilium` as alternatives — **one** at a time
- AI and logs: `ollama-router`, `open-webui`, `open-terminal`, `ai-tools`, `alert-triage`, `log-report`, `victoria-logs`, `vector`; `k8sgpt` is staged

Repo: [`gitops`](https://github.com/maceosoft/gitops) · [`bootstrap/root-appset.yaml`](https://github.com/maceosoft/gitops/blob/main/bootstrap/root-appset.yaml)

## After the phases: AI, logs, and security

On top of the Phase 4 platform, you can add the following (each with its own guide):

- **Local AI**: Ollama on all four nodes (and, optionally, a separate Mac) behind a router with automatic registration; Open WebUI
  with Dex and Open Terminal. [Local AI assistant](../operacion/ia-ollama.md) ·
  [Add an Ollama node](../operacion/agregar-nodo-ollama.md).
- **Logs and reports**: Vector → VictoriaLogs → Grafana, with a daily summary and a weekly AI-generated report in the Discord
  `#ia` channel. [Centralized logs](../operacion/logs.md).
- **Security**: people → Dex; machines → token and network restriction; host firewall on every node. The
  `default-deny` NetworkPolicies and K8sGPT are **yet to be enabled**. [Authentication model](../security/modelo-de-autenticacion.md).

## Global Verification

```bash
# Incus
incus cluster list
incus cluster group list

# K3s
kubectl get nodes
kubectl get applications -n argocd

# SSO — login GitHub en ArgoCD, Grafana, Open WebUI, vCluster e Incus UI

# CAPN (si Fase 6)
kubectl get clusters,machines
```

## Official Stack Links

- [Incus](https://linuxcontainers.org/incus/docs/main/) · [K3s](https://docs.k3s.io/) · [Argo CD](https://argo-cd.readthedocs.io/)
- [vCluster Platform](https://www.vcluster.com/docs/platform/) · [Cluster API](https://cluster-api.sigs.k8s.io/) · [CAPN](https://capn.linuxcontainers.org/)
- [1Password SDK](https://github.com/1Password/onepassword-sdk-python)

## Maintenance and Further Reading

- [Technology Stack](stack-tecnologico.md)
- [Ansible Catalog](../ansible/index.md)
- [GitOps](../gitops/index.md)
- [Incus Backup (optional)](../incus/cluster-setup.md#backup-and-snapshots-optional)
- [Uninstall K3s](apendice-desinstalar.md)
