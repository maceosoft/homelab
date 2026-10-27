# Homelab Summary

Completion of the [implementation guide](index.md): checklist of what was deployed,
URLs, `/etc/hosts`, nodes, secrets, and global verification. Check this page
upon finishing Phase 4 at a minimum; Phases 5 and 6 are optional.

## Completed Walkthrough (by phase)

| Phase | What is Ready | Tool |
|---|---|---|
| [0 — Preparation](fase-0-preparacion.md) | Repo, Ansible, `inventory.ini`, optional discovery | `playbook-discovery.yml` |
| [1 — Network](fase-1-red.md) | Fixed IP on `br0` (`192.168.20.5`, `.6`, `.7`) | `playbook-set-static-ip.yml` |
| [2 — Incus](fase-2-incus.md) | HA cluster, groups, UI, storage `dir` | `playbook-bootstrap.yml` + `playbook-incus-cluster.yml` |
| [3 — K3s](fase-3-k3s.md) | Management cluster + Argo CD controller; CNI **Calico** | `playbook-k3s.yml` |
| [4 — GitOps](fase-4-gitops.md) | MetalLB, Gateway API, storage, Dex/GitHub SSO | Argo CD + `playbook-dex-oauth-secrets.yml` |
| [5 — vCluster](fase-5-vcluster.md) *(optional)* | Platform, kubeconfig web (connected cluster) | Application Argo CD |
| [6 — CAPN](fase-6-capn.md) *(optional)* | Workload clusters on Incus | `clusterctl` + `capn-demo.yaml` |

## URLs and Web Access

| Service | URL | Auth | Phase |
|---|---|---|---|
| **Argo CD** | [`https://argocd.homelab.local`](https://argocd.homelab.local) | GitHub SSO via Dex | 4 |
| **Dex** (issuer) | `https://argocd.homelab.local/api/dex` | — | 4 |
| **vCluster Platform** | [`https://vcluster.homelab.local`](https://vcluster.homelab.local) | SSO Dex → GitHub | 5 |
| **Incus UI** | [`https://incus.homelab.local:8443`](https://incus.homelab.local:8443) | SSO Dex (or client cert before Phase 4) | 2 / 4 |
| **Grafana** *(optional)* | [`https://grafana.homelab.local`](https://grafana.homelab.local) | GitHub SSO via Dex (backup: `admin` of item `grafana-admin`) | 4 ([4.13](fase-4-gitops.md#413-monitoring-and-alerts-optional)) |
| **Open WebUI** (AI assistant) | [`https://open-webui.homelab.local`](https://open-webui.homelab.local) | GitHub SSO via Dex (team `devops`) | [local AI](../operacion/ia-ollama.md) |
| **Ollama** (router) | `https://ollama.homelab.local` | Bearer token by client (not for people) | [local AI](../operacion/ia-ollama.md) |
| **K3s API** | `https://k3s.homelab.local:6443` (currently points to `deborah`, `192.168.20.5`) | kubeconfig | 3 |

### Kubeconfig

| Cluster | How to Obtain It |
|---|---|
| Management K3s | vCluster Platform (connected cluster) or `playbook-k3s.yml` with `fetch_kubeconfig` |
| vClusters | UI [vCluster Platform](fase-5-vcluster.md) |
| Workload CAPN | `clusterctl get kubeconfig` (Phase 6) |

## DNS on Your Workstation

Use `192.168.20.5` (BIND on `deborah`) as DNS: `argocd`, `vcluster`, `api`, `grafana`, `open-webui`, and `ollama` (`.homelab.local`) point to the Gateway
(`192.168.23.200`, fixed IP) and `incus.homelab.local` to invincible
([Phase 4 — 4.8](fase-4-gitops.md#48-homelablocal-dns)). If you cannot, the backup
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

## Homelab Nodes

| Hostname | IP `br0` | Incus | K3s | Notes |
|---|---|---|---|---|
| invincible | 192.168.20.6 | Leader + UI | agent | 15.5 GB; Longhorn disk; Ollama node |
| oliver | 192.168.20.7 | Quorum, manual scheduler | agent | 7.7 GB: RAM adjusted; no automatic instances; Ollama node |
| deborah | 192.168.20.5 | arm64-nodes | **server** (CP) | 31 GB RAM; DNS (BIND); Ollama node |

The control plane is on `deborah`. If it ever needed to move to another node, the procedure is in
[Moving the Control Plane](../operacion/mover-control-plane.md).

Incus storage: pool `local`, driver `dir`, profile `default` → NIC (network card) `br0`.

Hardware details: [Inventory](../hardware/inventory.md).

## Cluster Network (CNI)

| Decision | Default Homelab | Alternative |
|---|---|---|
| CNI | **Calico** (`k3s_cni: calico`; later adopted by Argo CD with `calico-operator` and `calico-config`) | Flannel `vxlan` (embedded in K3s), Canal or Cilium |

Ansible variable: `k3s_install.core.cni` in [`group_vars/incus_cluster/k3s_install.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/group_vars/incus_cluster/k3s_install.yml).
Details and trade-offs: [Phase 3 — CNI](fase-3-k3s.md#cni) · [playbook-options](../k3s/playbook-options.md#cni).

Verification:

```bash
kubectl get pods -n calico-system -l k8s-app=calico-node
# o flannel / canal / cilium si elegiste otro CNI
```

## Secrets and SSO (1Password)

| 1Password Field | Usage |
|---|---|
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | Dex → GitHub OAuth (manual in GitHub + 1Password) |
| `VCLUSTER_CLIENT_SECRET` | Dex + Helm Platform (Ansible generates if missing) |

Personal account, vault **`HomeLab`** (configurable via env vars).
Playbook: `playbook-dex-oauth-secrets.yml`.

!!! important "Default Permissions"
    In vCluster Platform, SSO users (single sign-on) **see nothing** until access is assigned.
    In Incus, anyone who logs in via SSO has full access: the control is that Dex only allows
    the team `devops` of `maceosoft`. See [Phase 4](fase-4-gitops.md) and [Phase 5](fase-5-vcluster.md).

Documentation: [OAuth Secrets](https://github.com/maceosoft/gitops/blob/main/argocd/secrets/1password.md)

## GitOps (Argo CD)

Typical apps in `Healthy` after Phase 4:

- `argocd`, `argocd-route`, `metallb`, `homelab-storage`, `kong`, …
- Optional (manual sync): `vcluster-platform`, `capn-demo`
- CNI: `calico-operator` + `calico-config` (manual sync); `canal` or `cilium` as alternatives — **one** at a time
- AI and logs: `ollama-router`, `open-webui`, `open-terminal`, `ai-tools`, `alert-triage`, `log-report`, `victoria-logs`, `vector`; `k8sgpt` is staged

Repo: [`gitops`](https://github.com/maceosoft/gitops) · [`bootstrap/root-appset.yaml`](https://github.com/maceosoft/gitops/blob/main/bootstrap/root-appset.yaml)

## After Phases: AI, logs, and security

On top of the Phase 4 platform, the following are added (each with its guide):

- **Local AI**: Ollama on the three nodes (and an optional Mac) behind a router with automatic registration; Open WebUI
  with Dex and Open Terminal. [Local AI Assistant](../operacion/ia-ollama.md) ·
  [Add an Ollama Node](../operacion/agregar-nodo-ollama.md).
- **Logs and reports**: Vector → VictoriaLogs → Grafana, with a daily summary and a weekly report with AI in the Discord channel
  `#ia`. [Centralized Logs](../operacion/logs.md).
- **Security**: people → Dex; machines → token and network restriction; host firewall on each node. The
  NetworkPolicy `default-deny` and K8sGPT are **to be activated**. [Authentication Model](../security/modelo-de-autenticacion.md).

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

## Official stack links

- [Incus](https://linuxcontainers.org/incus/docs/main/) · [K3s](https://docs.k3s.io/) · [Argo CD](https://argo-cd.readthedocs.io/)
- [vCluster Platform](https://www.vcluster.com/docs/platform/) · [Cluster API](https://cluster-api.sigs.k8s.io/) · [CAPN](https://capn.linuxcontainers.org/)
- [1Password SDK](https://github.com/1Password/onepassword-sdk-python)

## Maintenance and deepening

- [Technology stack](stack-tecnologico.md)
- [Ansible Catalog](../ansible/index.md)
- [GitOps](../gitops/index.md)
- [Backup Incus (optional)](../incus/cluster-setup.md#backup-and-snapshots-optional)
- [Uninstall K3s](apendice-desinstalar.md)
