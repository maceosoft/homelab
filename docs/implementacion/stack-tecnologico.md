# Stack tecnológico

Inventario de tecnologías del HomeLab: **diagrama por capas** + lista con
enlaces oficiales en el nombre de cada producto.

Parte de la [guía de implementación](index.md). Vista C4 (modelo C4) complementaria:
[Arquitectura](../architecture/overview.md) · [Nivel 3 — Componentes](../architecture/nivel-3-componentes.md) · [Nivel 4 — Despliegue](../architecture/nivel-4-despliegue.md).

## Diagrama por capas

```mermaid
flowchart TB
  subgraph capa0 [Capa 0 — Hardware y SO]
    HW[Nodos_fisicos_Debian]
    Netplan[Netplan_br0]
    Ansible[Ansible]
  end
  subgraph capa1 [Capa 1 — Virtualizacion]
    Incus[Incus_cluster]
    IncusUI[Incus_UI]
  end
  subgraph capa2 [Capa 2 — Orquestacion base]
    K3s[K3s]
    KubeVip[kube_vip_opcional]
  end
  subgraph capa3 [Capa 3 — GitOps y red de servicios]
    ArgoCD[Argo_CD]
    Dex[Dex]
    GitHub[GitHub_OAuth]
    MetalLB[MetalLB]
    Gateway[Gateway_API_Kong]
  end
  subgraph capa4 [Capa 4 — Datos y secretos]
    OpenEBS[OpenEBS]
    Longhorn[Longhorn]
    SealedSecrets[Sealed_Secrets]
    OnePassword[1Password_SDK]
  end
  subgraph capa5 [Capa 5 — Plataforma y workloads opcionales]
    VCluster[vCluster_Platform]
    CAPI[Cluster_API]
    CAPN[CAPN]
    SUC[system_upgrade_controller]
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
```

## Capa 0 — Bootstrap

- **[Ansible](https://docs.ansible.com/)** — Automatización idempotente de SO, red, Incus y K3s (distribución ligera de Kubernetes); Fases 0–3.
- **[Netplan](https://netplan.io/)** — IP estática en `br0`; Fase 1; identidad de nodo para Incus/K3s/CAPN.
- **[Debian](https://www.debian.org/)** — SO base en los 3 nodos; prerequisito global.

## Capa 1 — Virtualización

- **[Incus](https://linuxcontainers.org/incus/docs/main/)** — Clúster LXC/VM con quorum; Fase 2; sustrato para CAPN (Cluster API Provider for Incus) e instancias.
- **[Incus UI](https://linuxcontainers.org/incus/docs/main/howto/server_expose/#web-ui)** — Administración web del clúster Incus; Fase 2 (cert) + Fase 4 (OIDC Dex).
- **[Zabbly Incus stable](https://github.com/zabbly/incus-stable)** — Repo de paquetes; Fase 2.

## Capa 2 — Kubernetes management

- **[K3s](https://docs.k3s.io/)** — Management cluster bare-metal; Fase 3.
- **[kube-vip](https://kube-vip.io/)** — VIP (IP virtual) opcional del API (Application Programming Interface) `:6443`; Fase 3 (fork).
- **CNI (elegir uno)** — Fase 3:
  - **[Flannel](https://github.com/flannel-io/flannel)** — default embebido en K3s (`vxlan` en `br0`)
  - **[Canal](https://docs.tigera.io/calico/latest/getting-started/kubernetes/flannel/flannel)** — Flannel + políticas Calico
  - **[Calico](https://docs.tigera.io/calico/latest/about/)** — NetworkPolicy, BGP (Border Gateway Protocol) opcional
  - **[Cilium](https://docs.cilium.io/)** — eBPF, Hubble, políticas L3–L7

<div class="card">
  <div class="card-kicker">CNI</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">Flannel</div>
      <div class="text-muted">Cero pasos extra en K3s</div>
      <div class="text-muted">Sin NetworkPolicy nativa</div>
    </div>
    <div class="card-col">
      <div class="card-title">Canal</div>
      <div class="text-muted">Políticas sobre overlay conocido</div>
      <div class="text-muted">Legacy; dos stacks</div>
    </div>
    <div class="card-col">
      <div class="card-title">Calico</div>
      <div class="text-muted">Madurez y BGP en L2</div>
      <div class="text-muted">Más pods/RAM</div>
    </div>
    <div class="card-col">
      <div class="card-title">Cilium</div>
      <div class="text-muted">Observabilidad eBPF</div>
      <div class="text-muted">CPU/kernel; validar ARM64</div>
    </div>
  </div>
</div>

## Capa 3 — GitOps, red y acceso

- **[Argo CD](https://argo-cd.readthedocs.io/)** — ApplicationSet de bootstrap (`homelab-root`) desde GitHub, por olas; Fase 4.
- **[Dex](https://dexidp.io/docs/)** — IdP OIDC (OpenID Connect) embebido en ArgoCD; SSO (inicio de sesión único) para ArgoCD, vCluster Platform e Incus UI (interfaz de usuario); Fase 4.
- **[GitHub](https://docs.github.com/en/apps/oauth-apps)** — Connector OAuth + repos GitOps; Fase 4.
- **[MetalLB](https://metallb.universe.tf/)** — LoadBalancer en LAN (red local); Fase 4 wave 0–1.
- **[Gateway API](https://gateway-api.sigs.k8s.io/)** con **[Kong Ingress Controller](https://developer.konghq.com/kubernetes-ingress-controller/)** — HTTP(S) hacia ArgoCD y vCluster; Fase 4 wave 1 (alternativas: Traefik, NGINX Gateway Fabric).
- **[1Password Python SDK](https://github.com/1Password/onepassword-sdk-python)** — Secretos OAuth desde la app local; Fase 4.
- **[VictoriaMetrics](https://docs.victoriametrics.com/)** (con **[Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)**) — Métricas y alertas de nodos y plataforma, más ligero que Prometheus; Fase 4 (4.13, opcional).
- **[Grafana](https://grafana.com/docs/grafana/latest/)** — Paneles de temperatura, memoria y disco en `grafana.homelab.local`; Fase 4 (4.13, opcional).
- **[Discord](https://discord.com/developers/docs/resources/webhook)** y **[healthchecks.io](https://healthchecks.io/docs/)** — Destino de las alertas (webhooks) y vigilante externo (*dead man's switch*) que recibe un ping de Alertmanager, por si cae todo el clúster; Fase 4 (4.13, opcional).

## Capa 4 — Storage y secretos en clúster

- **[OpenEBS](https://openebs.io/docs)** — LocalPV default; Fase 4 wave 0.
- **[Longhorn](https://longhorn.io/docs/)** — Storage replicado cross-arch; Fase 4 wave 1.
- **[Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)** — Secretos cifrados en git; Fase 4 y 6.
- **[SOPS](https://github.com/getsops/sops)** — Cifrado pre-bootstrap; profundización [Secretos](../secrets/index.md).

## Capa 5 — Opcionales y operaciones

- **[vCluster Platform](https://www.vcluster.com/docs/platform/)** — Clústeres virtuales + kubeconfig web (host K3s y vclusters); Fase 5.
- **[Cluster API](https://cluster-api.sigs.k8s.io/)** — API declarativa de clusters; Fase 6.
- **[CAPN](https://capn.linuxcontainers.org/)** — Provider Incus para CAPI (Cluster API); Fase 6.
- **[clusterctl](https://cluster-api.sigs.k8s.io/user/quick-start.html)** — CLI (interfaz de línea de comandos) bootstrap CAPI; Fase 6.
- **[system-upgrade-controller](https://github.com/rancher/system-upgrade-controller)** — Upgrades K3s escalonados; Fase 4 wave 3.
