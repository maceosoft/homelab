# Technology Stack

Inventory of HomeLab technologies: **layer diagram** + list with
official links in each product name.

Part of the [implementation guide](index.md). Complementary C4 view (C4 model):
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
    VCluster[vCluster]
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
  K3s --> VCluster
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

## Layer 0 — Hardware, OS and Bootstrap

- **[Ansible](https://docs.ansible.com/)** — Idempotent automation of OS, network, Incus and K3s (lightweight Kubernetes distribution); Phases 0–3.
- **[Netplan](https://netplan.io/)** — Static IP on `br0`; Phase 1; node identity for Incus/K3s/CAPN (Cluster API Provider for Incus).
- **[Debian](https://www.debian.org/)** — Base OS on the 4 nodes; global prerequisite.

## Layer 1 — Virtualization

- **[Incus](https://linuxcontainers.org/incus/docs/main/)** — LXC cluster (Linux system containers)/VM with quorum; Phase 2; substrate for CAPN and instances.
- **[Incus UI](https://linuxcontainers.org/incus/docs/main/howto/server_expose/#web-ui)** — Web administration of the Incus cluster; Phase 2 (cert) + Phase 4 (OIDC —OpenID Connect— with Dex).
- **[Zabbly Incus stable](https://github.com/zabbly/incus)** — Package repository; Phase 2.

## Layer 2 — Kubernetes Management

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
      <div class="text-muted">Policies on known overlay</div>
      <div class="text-muted">Legacy; two stacks</div>
    </div>
    <div class="card-col">
      <div class="card-title">Calico</div>
      <div class="text-muted">Maturity and BGP on L2</div>
      <div class="text-muted">More pods/RAM</div>
    </div>
    <div class="card-col">
      <div class="card-title">Cilium</div>
      <div class="text-muted">eBPF observability</div>
      <div class="text-muted">CPU/kernel; validate ARM64</div>
    </div>
  </div>
</div>

## Layer 3 — GitOps, Networking and Access

- **[Argo CD](https://argo-cd.readthedocs.io/)** — ApplicationSet `homelab` (one Application per `bootstrap/components/` file, in waves with RollingSync), managed by the `homelab-bootstrap` Application; Phase 4.
- **[Dex](https://dexidp.io/docs/)** — Embedded OIDC IdP (Identity Provider) in Argo CD; SSO (Single Sign-On) for Argo CD, Grafana, Open WebUI, Incus UI and `kubectl`; Phase 4.
- **[GitHub](https://docs.github.com/en/apps/oauth-apps)** — OAuth (Open Authorization) Connector + GitOps repos; Phase 4.
- **[MetalLB](https://metallb.universe.tf/)** — LoadBalancer on LAN (Local Area Network); Phase 4 wave 0–1.
- **[Gateway API](https://gateway-api.sigs.k8s.io/)** with **[Kong Ingress Controller](https://developer.konghq.com/kubernetes-ingress-controller/)** — HTTP(S) to Argo CD, Grafana, Open WebUI and the Ollama router; Phase 4 wave 1 (alternatives: Traefik, NGINX Gateway Fabric).
- **[1Password Python SDK](https://github.com/1Password/onepassword-sdk-python)** — OAuth secrets from the local app; Phase 4.
- **[VictoriaMetrics](https://docs.victoriametrics.com/)** (with **[Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)**) — Node and platform metrics and alerts, lighter than Prometheus; Phase 4 (4.13, optional).
- **[Grafana](https://grafana.com/docs/grafana/latest/)** — Temperature, memory, disk, logs and Ollama dashboards on `grafana.homelab.local`; Phase 4 (4.13, optional).
- **[Discord](https://discord.com/developers/docs/resources/webhook)** and **[healthchecks.io](https://healthchecks.io/docs/)** — Alert destination (webhooks) and external watchdog (*dead man's switch*) that receives a ping from Alertmanager, in case the entire cluster goes down; Phase 4 (4.13, optional).

## Layer 4 — Storage and Secrets

- **[OpenEBS](https://openebs.io/docs)** — Default LocalPV; Phase 4 wave 0.
- **[Longhorn](https://longhorn.io/docs/)** — Cross-arch replicated storage; Phase 4 wave 1.
- **[Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)** — Encrypted secrets in Git; Phase 4 and 6.
- **[SOPS (Secrets OPerationS)](https://github.com/getsops/sops)** — Pre-bootstrap encryption; deep dive [Secrets](../secrets/index.md).

## Layer 5 — Optionals and Operations

- **[vCluster](https://www.vcluster.com/docs/vcluster/)** (open source) — Virtual clusters inside K3s; created with the `vcluster` CLI and accessed with `vcluster connect` and the GitHub kubeconfig; Phase 5.
- **[Cluster API](https://cluster-api.sigs.k8s.io/)** — Declarative cluster API; Phase 6.
- **[CAPN](https://capn.linuxcontainers.org/)** — Incus provider for CAPI (Cluster API); Phase 6.
- **[clusterctl](https://cluster-api.sigs.k8s.io/user/quick-start.html)** — CAPI bootstrap CLI (Command Line Interface); Phase 6.
- **[system-upgrade-controller](https://github.com/rancher/system-upgrade-controller)** — Staggered K3s upgrades; Phase 4 wave 3.

## Layer 6 — Local AI, logs and security

- **[Ollama](https://ollama.com/)** — Language models (LLM, *Large Language Model*) on CPU (central processing unit), on demand in
  `deborah`, `invincible` and `oliver`, and on machines that join as nodes. [Guide](../operacion/ia-ollama.md) · [add a node](../operacion/agregar-nodo-ollama.md).
- **Ollama Router** (`ollama-router`, custom) — Single entry point (`ollama.homelab.local`): automatic node
  registration, model-based selection, per-client token, and per-model and per-node metrics.
- **[Open WebUI](https://docs.openwebui.com/)** — Chat with the assistant, with Dex login; **[Open Terminal](https://docs.openwebui.com/features/open-terminal)**
  as an isolated terminal (sandbox) for the assistant to execute code.
- **K8sGPT** — Cluster analysis with Ollama; **staged** (its operator requests cluster-wide permissions).
- **[Vector](https://vector.dev/)** → **[VictoriaLogs](https://docs.victoriametrics.com/victorialogs/)** → Grafana —
  Centralized logs (30 days) and daily and weekly AI-powered reports in the `#ia` Discord channel ([guide](../operacion/logs.md)).
- **[nftables](https://wiki.nftables.org/)** — Host firewall on each node (role `host_firewall`), with automatic rollback.
- **NetworkPolicy** `default-deny` per namespace and **`oauth2-proxy`** — ready and **to be enabled** in stages
  ([Authentication Model](../security/modelo-de-autenticacion.md)).

## Each layer in the enterprise and in the cloud

The same stack, viewed through each lens. The detail of each row (trade-offs, benefits, and official links) is in the
"Decision in other environments" block of the linked page.

=== "🏠 At home"

    Everything runs on four machines, almost entirely with free software: the stack from the layers above. Almost no licenses and full control;
    in exchange, operations, updates, and backups are yours.

=== "🏢 In a company"

    | Layer | What changes in an enterprise | Detail |
    |---|---|---|
    | Virtualization | Supported platform (vSphere, Proxmox VE, Nutanix, OpenStack) | [Phase 2](fase-2-incus.md) |
    | Kubernetes | 3 control planes with etcd and a supported distribution (RKE2, OpenShift) | [Phase 3](fase-3-k3s.md) |
    | GitOps | Argo CD with commercial support; every change audited in Git | [Phase 4](fase-4-gitops.md) |
    | Network & ingress | Dedicated load balancers or MetalLB in BGP; supported gateway | [Network](../networking/index.md) |
    | Storage | SAN/NAS or supported storage with off-cluster backups | [Storage](../storage/index.md) |
    | Secrets | Central vault with rotation and auditing (Vault, 1Password Business) | [Secrets](../secrets/index.md) |
    | Identity | Corporate IdP with MFA (Entra ID, Okta, Google Workspace) | [Authentication](../security/modelo-de-autenticacion.md) |
    | Monitoring | On-call, escalation, and long retention | [Monitoring](../operacion/monitoreo.md) |
    | Logs | Compliance retention and SIEM | [Logs](../operacion/logs.md) |
    | AI | Local inference with GPU when data cannot leave | [Local AI](../operacion/ia-ollama.md) |
    | Multi-tenancy | One virtual cluster per team or customer | [Phase 5](fase-5-vcluster.md) |
    | Cluster fleet | Cluster API or provider fleet console | [Phase 6](fase-6-capn.md) |
    | Backups | 3-2-1 rule with tested RPO/RTO | [Backups](../operacion/backups-incus.md) |

=== "☁️ In the cloud"

    | Layer | GCP | AWS | Azure | Oracle Cloud (OCI) |
    |---|---|---|---|---|
    | Virtualization | Compute Engine | EC2 | Azure Virtual Machines | OCI Compute |
    | Kubernetes | GKE | EKS | AKS | OKE |
    | Network & ingress | Cloud Load Balancing and GKE Gateway | ELB and AWS Load Balancer Controller | Application Gateway for Containers | OCI Load Balancer and Native Ingress (Ingress only) |
    | GitOps | Config Sync | EKS Capability for Argo CD | GitOps Extensions (Flux and Argo CD) | Argo CD installed on OKE |
    | Storage | Persistent Disk, Hyperdisk, and Filestore | EBS and EFS | Azure Disk and Azure Files | Block Volume and File Storage |
    | Secrets | Secret Manager | Secrets Manager | Key Vault | OCI Vault |
    | Identity | Workforce Identity Federation | IAM Identity Center | Microsoft Entra ID | IAM Identity Domains |
    | Metrics | Managed Service for Prometheus | Managed Prometheus and Managed Grafana | Azure Monitor and Managed Grafana | OCI Monitoring |
    | Logs | Cloud Logging | CloudWatch Logs | Azure Monitor Logs | OCI Logging |
    | AI | Gemini Enterprise Agent Platform | Bedrock | Microsoft Foundry | OCI Generative AI |
    | Backups | Backup and DR and Backup for GKE | AWS Backup | Azure Backup | Block Volume Backups |

    In general you gain managed operations, SLAs, and scale; you lose control, pay per use, and become more locked in to each
    provider.
