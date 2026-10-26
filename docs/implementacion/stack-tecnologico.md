# Stack tecnológico

Inventario de tecnologías del HomeLab: **diagrama por capas** + lista con
enlaces oficiales en el nombre de cada producto.

Parte de la [guía de implementación](index.md). Vista C4 (modelo C4) complementaria:
[Arquitectura](../architecture/overview.md) · [Nivel 3 — Componentes](../architecture/nivel-3-componentes.md) · [Nivel 4 — Despliegue](../architecture/nivel-4-despliegue.md).

## Diagrama por capas

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

## Capa 0 — Hardware, SO y bootstrap

- **[Ansible](https://docs.ansible.com/)** — Automatización idempotente de SO, red, Incus y K3s (distribución ligera de Kubernetes); Fases 0–3.
- **[Netplan](https://netplan.io/)** — IP estática en `br0`; Fase 1; identidad de nodo para Incus/K3s/CAPN (Cluster API Provider for Incus).
- **[Debian](https://www.debian.org/)** — SO base en los 3 nodos; prerrequisito global.

## Capa 1 — Virtualización

- **[Incus](https://linuxcontainers.org/incus/docs/main/)** — Clúster LXC (contenedores de sistema de Linux)/VM con quórum; Fase 2; sustrato para CAPN e instancias.
- **[Incus UI](https://linuxcontainers.org/incus/docs/main/howto/server_expose/#web-ui)** — Administración web del clúster Incus; Fase 2 (cert) + Fase 4 (OIDC —OpenID Connect— con Dex).
- **[Zabbly Incus stable](https://github.com/zabbly/incus-stable)** — Repo de paquetes; Fase 2.

## Capa 2 — Kubernetes management

- **[K3s](https://docs.k3s.io/)** — Management cluster bare-metal; Fase 3.
- **[kube-vip](https://kube-vip.io/)** — VIP (IP virtual) opcional del API (Application Programming Interface) `:6443`; Fase 3 (fork).
- **CNI (elegir uno; en este HomeLab, Calico)** — Fase 3:
  - **[Flannel](https://github.com/flannel-io/flannel)** — default embebido en K3s (`vxlan` en `br0`)
  - **[Canal](https://docs.tigera.io/calico/latest/getting-started/kubernetes/flannel/flannel)** — Flannel + políticas Calico
  - **[Calico](https://docs.tigera.io/calico/latest/about/)** — NetworkPolicy, BGP (Border Gateway Protocol) opcional
  - **[Cilium](https://docs.cilium.io/)** — eBPF (extended Berkeley Packet Filter), Hubble, políticas L3–L7

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
- **[Dex](https://dexidp.io/docs/)** — IdP (proveedor de identidad) OIDC embebido en Argo CD; SSO (inicio de sesión único) para Argo CD, Grafana, Open WebUI, vCluster Platform e Incus UI (interfaz de usuario); Fase 4.
- **[GitHub](https://docs.github.com/en/apps/oauth-apps)** — Connector OAuth (Open Authorization) + repos GitOps; Fase 4.
- **[MetalLB](https://metallb.universe.tf/)** — LoadBalancer en LAN (red local); Fase 4 wave 0–1.
- **[Gateway API](https://gateway-api.sigs.k8s.io/)** con **[Kong Ingress Controller](https://developer.konghq.com/kubernetes-ingress-controller/)** — HTTP(S) hacia Argo CD, Grafana, Open WebUI, el router de Ollama y vCluster; Fase 4 wave 1 (alternativas: Traefik, NGINX Gateway Fabric).
- **[1Password Python SDK](https://github.com/1Password/onepassword-sdk-python)** — Secretos OAuth desde la app local; Fase 4.
- **[VictoriaMetrics](https://docs.victoriametrics.com/)** (con **[Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)**) — Métricas y alertas de nodos y plataforma, más ligero que Prometheus; Fase 4 (4.13, opcional).
- **[Grafana](https://grafana.com/docs/grafana/latest/)** — Paneles de temperatura, memoria, disco, logs y Ollama en `grafana.homelab.local`; Fase 4 (4.13, opcional).
- **[Discord](https://discord.com/developers/docs/resources/webhook)** y **[healthchecks.io](https://healthchecks.io/docs/)** — Destino de las alertas (webhooks) y vigilante externo (*dead man's switch*) que recibe un ping de Alertmanager, por si cae todo el clúster; Fase 4 (4.13, opcional).

## Capa 4 — Storage y secretos

- **[OpenEBS](https://openebs.io/docs)** — LocalPV default; Fase 4 wave 0.
- **[Longhorn](https://longhorn.io/docs/)** — Storage replicado cross-arch; Fase 4 wave 1.
- **[Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)** — Secretos cifrados en Git; Fase 4 y 6.
- **[SOPS (Secrets OPerationS)](https://github.com/getsops/sops)** — Cifrado pre-bootstrap; profundización [Secretos](../secrets/index.md).

## Capa 5 — Opcionales y operaciones

- **[vCluster Platform](https://www.vcluster.com/docs/platform/)** — Clústeres virtuales + kubeconfig web (host K3s y vClusters); Fase 5.
- **[Cluster API](https://cluster-api.sigs.k8s.io/)** — API declarativa de clústeres; Fase 6.
- **[CAPN](https://capn.linuxcontainers.org/)** — Provider Incus para CAPI (Cluster API); Fase 6.
- **[clusterctl](https://cluster-api.sigs.k8s.io/user/quick-start.html)** — CLI (interfaz de línea de comandos) bootstrap CAPI; Fase 6.
- **[system-upgrade-controller](https://github.com/rancher/system-upgrade-controller)** — Upgrades K3s escalonados; Fase 4 wave 3.

## Capa 6 — IA local, logs y seguridad

- **[Ollama](https://ollama.com/)** — Modelos de lenguaje (LLM, *Large Language Model*) en CPU (unidad central de procesamiento), bajo demanda en
  `deborah`, `invincible` y `oliver`, y en un Mac opcional que se enciende a mano (`ollama-node on|off`, socket de
  `launchd`). [Guía](../operacion/ia-ollama.md) · [agregar un nodo](../operacion/agregar-nodo-ollama.md).
- **Router de Ollama** (`ollama-router`, propio) — Única entrada (`ollama.homelab.local`): registro automático de
  nodos, elección por modelo, token por cliente y métricas por modelo y nodo.
- **[Open WebUI](https://docs.openwebui.com/)** — Chat con el asistente, con login por Dex; **[Open Terminal](https://docs.openwebui.com/features/open-terminal)**
  como terminal aislado (sandbox) para que el asistente ejecute código.
- **K8sGPT** — Análisis del clúster con Ollama; **etapado** (su operador pide permisos de todo el clúster).
- **[Vector](https://vector.dev/)** → **[VictoriaLogs](https://docs.victoriametrics.com/victorialogs/)** → Grafana —
  Logs centralizados (30 días) y reportes diario y semanal con IA en el canal `#ia` de Discord ([guía](../operacion/logs.md)).
- **[nftables](https://wiki.nftables.org/)** — Firewall de host en cada nodo (rol `host_firewall`), con reversión automática.
- **NetworkPolicy** `default-deny` por namespace y **`oauth2-proxy`** — preparados y **por activar** por etapas
  ([Modelo de autenticación](../security/modelo-de-autenticacion.md)).
