# Technology Stack

Inventory of HomeLab technologies: **layer diagram** + list with
official links in the name of each product.

Part of the [implementation guide](index.md). Complementary C4 (C4 model) view:
[Architecture](../architecture/overview.md) · [Level 3 — Components](../architecture/nivel-3-componentes.md) · [Level 4 — Deployment](../architecture/nivel-4-despliegue.md).

## Layer Diagram

```mermaid
flowchart TB
  subgraph capa0 [Capa 0 — Hardware, SO y bootstrap]
    HW[Nodos_fisicos_Debian]
    Netplan[Netplan_br0]
    Ansible[Ansible]
  end
  subgraph capa1 [Capa 1 — Virtualización]
    Incus[Incus_cluster]
    IncusUI[Incus_UI]
  end
  subgraph capa2 [Capa 2 — Kubernetes management]
    K3s[K3s]
    KubeVip[kube_vip_opcional]
  end
  subgraph capa3 [Capa 3 — GitOps, red y acceso]
    ArgoCD[Argo_CD]
    Dex[Dex]
    GitHub[GitHub_OAuth]
    MetalLB[MetalLB]
    Gateway[Gateway_API_Kong]
  end
  subgraph capa4 [Capa 4 — Storage y secretos]
    OpenEBS[OpenEBS]
    Longhorn[Longhorn]
    SealedSecrets[Sealed_Secrets]
    OnePassword[1Password_SDK]
  end
  subgraph capa5 [Capa 5 — Opcionales y operaciones]
    VCluster[vCluster_Platform]
    CAPI[Cluster_API]
    CAPN[CAPN]
    SUC[system_upgrade_controller]
  end
  subgraph capa6 [Capa 6 — IA local, logs y seguridad]
    Ollama[Ollama_en_nodos_y_Mac]
    Router[ollama_router]
    OpenWebUI[Open_WebUI_y_Open_Terminal]
    Vector[Vector]
    VLogs[VictoriaLogs]
    Firewall[nftables_por_nodo]
  end
  HW --> Netplan --> Incus
  Incus --> IncusUI
  Dex --> IncusUI
  Netplan --> K3s
  K3s --> KubeVip
  K3s --> ArgoCD
  ArgoCD --> Dex
  Dex --> GitHub
  ArgoCD --> MetalLB --> Gateway
  ArgoCD --> OpenEBS
  ArgoCD --> Longhorn
  ArgoCD --> SealedSecrets
  Dex --> VCluster
  K3s --> CAPI --> CAPN
  Incus --> CAPN
  ArgoCD --> SUC
  ArgoCD --> Router --> Ollama
  OpenWebUI --> Router
  Dex --> OpenWebUI
  Vector --> VLogs
  Ansible --> Firewall
  Ansible --> Ollama
```

## Layer 0 — Hardware, OS, and bootstrap

- **[Ansible](https://docs.ansible.com/)** — Idempotent OS, network, Incus, and K3s (lightweight Kubernetes distribution) automation; Phases 0–3.
- **[Netplan](https://netplan.io/)** — Static IP on `br0`; Phase 1; node identity for Incus/K3s/CAPN (Cluster API Provider for Incus).
- **[Debian](https://www.debian.org/)** — Base OS on the 3 nodes; global prerequisite.

## Layer 1 — Virtualization

- **[Incus](https://linuxcontainers.org/incus/docs/main/)** — LXC (Linux container) cluster/VM with quorum; Phase 2; substrate for CAPN and instances.
- **[Incus UI](https://linuxcontainers.org/incus/docs/main/howto/server_expose/#web-ui)** — Web management of the Incus cluster; Phase 2 (cert) + Phase 4 (OIDC —OpenID Connect— with Dex).
- **[Zabbly Incus stable](https://github.com/zabbly/incus-stable)** — Package repo; Phase 2.

## Layer 2 — Kubernetes management

- **[K3s](https://docs.k3s.io/)** — Bare-metal management cluster; Phase 3.
- **[kube-vip](https://kube-vip.io/)** — Optional API (Application Programming Interface) VIP (Virtual IP) `:6443`; Phase 3 (fork).
- **CNI (choose one; in this HomeLab, Calico)** — Phase 3:
  - **[Flannel](https://github.com/flannel-io/flannel)** — Default embedded in K3s (`vxlan` in `br0`)
  - **[Canal](https://docs.tigera.io/calico/latest/getting-started/kubernetes/flannel/flannel)** — Flannel + Calico policies
  - **[Calico](https://docs.tigera.io/calico/latest/about/)** — NetworkPolicy, optional BGP (Border Gateway Protocol)
  - **[Cilium](https://docs.cilium.io/)** — eBPF (extended Berkeley Packet Filter), Hubble, L3–L7 policies

<div class="card">
  <div class="card-kicker">CNI</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">Flannel</div>
      <div class="text-muted">Zero extra steps in K3s</div>
      <div class="text-muted">No native NetworkPolicy</div>
    </div>
    <div class="card-col">
      <div class="card-title">Canal</div>
      <div class="text-muted">Policies over known overlay</div>
      <div class="text-muted">Legacy; two stacks</div>
    </div>
    <div class="card-col">
      <div class="card-title">Calico</div>
      <div class="text-muted">Maturity and BGP at L2</div>
      <div class="text-muted">More pods/RAM</div>
    </div>
    <div class="card-col">
      <div class="card-title">Cilium</div>
      <div class="text-muted">eBPF observability</div>
      <div class="text-muted">CPU/kernel; validate ARM64</div>
    </div>
  </div>
</div>

## Layer 3 — GitOps, network, and access

- **[Argo CD](https://argo-cd.readthedocs.io/)** — Bootstrap ApplicationSet (`homelab-root`) from GitHub, by waves; Phase 4.
- **[Dex](https://dexidp.io/docs/)** — Embedded OIDC (OpenID Connect) IdP (identity provider) in Argo CD; SSO (single sign-on) for Argo CD, Grafana, Open WebUI, vCluster Platform, and Incus UI (user interface); Phase 4.
- **[GitHub](https://docs.github.com/en/apps/oauth-apps)** — OAuth (Open Authorization) connector + GitOps repos; Phase 4.
- **[MetalLB](https://metallb.universe.tf/)** — LoadBalancer in LAN (local network); Phase 4 wave 0–1.
- **[Gateway API](https://gateway-api.sigs.k8s.io/)** with **[Kong Ingress Controller](https://developer.konghq.com/kubernetes-ingress-controller/)** — HTTP(S) to Argo CD, Grafana, Open WebUI, Ollama router, and vCluster; Phase 4 wave 1 (alternatives: Traefik, NGINX Gateway Fabric).
- **[1Password Python SDK](https://github.com/1Password/onepassword-sdk-python)** — OAuth secrets from local app; Phase 4.
- **[VictoriaMetrics](https://docs.victoriametrics.com/)** (with **[Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)**) — Node and platform metrics and alerts, lighter than Prometheus; Phase 4 (4.13, optional).
- **[Grafana](https://grafana.com/docs/grafana/latest/)** — Temperature, memory, disk, logs, and Ollama panels in `grafana.homelab.local`; Phase 4 (4.13, optional).
- **[Discord](https://discord.com/developers/docs/resources/webhook)** and **[healthchecks.io](https://healthchecks.io/docs/)** — Alert destination (webhooks) and external watchdog (*dead man's switch*) that receives a ping from Alertmanager, in case the entire cluster goes down; Phase 4 (4.13, optional).

## Layer 4 — Storage and secrets

- **[OpenEBS](https://openebs.io/docs)** — Default LocalPV; Phase 4 wave 0.
- **[Longhorn](https://longhorn.io/docs/)** — Cross-arch replicated storage; Phase 4 wave 1.
- **[Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)** — Encrypted secrets in Git; Phase 4 and 6.
- **[SOPS (Secrets OPerationS)](https://github.com/getsops/sops)** — Pre-bootstrap encryption; dive deeper into [secrets](../secrets/index.md).

## Layer 5 — Optional and operations

- **[vCluster Platform](https://www.vcluster.com/docs/platform/)** — Virtual clusters + web kubeconfig (host K3s and vClusters); Phase 5.
- **[Cluster API](https://cluster-api.sigs.k8s.io/)** — Declarative cluster API; Phase 6.
- **[CAPN](https://capn.linuxcontainers.org/)** — Incus provider for CAPI (Cluster API); Phase 6.
- **[clusterctl](https://cluster-api.sigs.k8s.io/user/quick-start.html)** — CAPI bootstrap CLI (command-line interface); Phase 6.
- **[system-upgrade-controller](https://github.com/rancher/system-upgrade-controller)** — Staged K3s upgrades; Phase 4 wave 3.

## Layer 6 — Local AI, logs, and security

- **[Ollama](https://ollama.com/)** — Language models (LLM, *Large Language Model*) on CPU (central processing unit), on-demand in
  `deborah`, `invincible` and `oliver`, and on an optional Mac that is manually powered on (`ollama-node on|off`, socket of
  `launchd`). [Guide](../operacion/ia-ollama.md) · [add a node](../operacion/agregar-nodo-ollama.md).
- **Ollama Router** (`ollama-router`, custom) — Single entry point (`ollama.homelab.local`): automatic node registration, model selection, client token, and model and node metrics.
- **[Open WebUI](https://docs.openwebui.com/)** — Chat with the assistant, with Dex login; **[Open Terminal](https://docs.openwebui.com/features/open-terminal)**
  as a sandbox terminal for the assistant to run code.
- **K8sGPT** — Cluster analysis with Ollama; **staged** (its operator requests cluster-wide permissions).
- **[Vector](https://vector.dev/)** → **[VictoriaLogs](https://docs.victoriametrics.com/victorialogs/)** → Grafana —
  Centralized logs (30 days) and daily and weekly reports with AI in the `#ia` Discord channel ([guide](../operacion/logs.md)).
- **[nftables](https://wiki.nftables.org/)** — Host firewall on each node (role `host_firewall`), with automatic rollback.
- **NetworkPolicy** `default-deny` by namespace and **`oauth2-proxy`** — prepared and **to be activated** in stages
  ([Authentication Model](../security/modelo-de-autenticacion.md)).
