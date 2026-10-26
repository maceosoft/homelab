# Architecture

Design view of the HomeLab. For the **technology stack** with a layered diagram
and links to official documentation of each product, see **[Technology Stack](../implementacion/stack-tecnologico.md)**.

Executable guide: **[Implementation](../implementacion/index.md)**.

## Layers

1. **Hardware** — 3 physical nodes (2x x86_64, 1x ARM64). See [inventory](../hardware/inventory.md).
2. **Incus Cluster** — virtualization substrate, 3 members with dqlite quorum.
   Cluster groups `x86-nodes` / `arm64-nodes` to direct where each instance runs.
3. **K3s (lightweight Kubernetes distribution) Management** — the existing bare-metal K3s cluster, hosting:
    - Cluster API core + CAPN controller (Cluster API Provider for Incus)
    - Argo CD (GitOps)
    - Sealed Secrets controller
4. **Workload Clusters** — ephemeral kubeadm clusters provisioned by CAPN as Incus (LXC or VM) instances for dev/test/isolation.
5. **Storage** — OpenEBS LocalPV (default, on all 3 nodes) + Longhorn v1
   (replicated between `invincible` and `deborah`; `oliver` stays out due to RAM if `createDefaultDiskLabeledNodes` is activated, see [Longhorn v1](../storage/index.md#longhorn-v1-selective-ha-cross-arch)).

## Key Design Decision

The production K3s is not migrated to nested-K8s. The existing K3s cluster is
kept as the *management cluster* for Cluster API; CAPN provisions additional
clusters on demand over the same hardware without touching production.

## C4 Diagrams

### Level 1 — Context

High-level view: the **HomeLab Platform** as a single black box and the external
actors/systems it interacts with (operator, Git, image registry, Omnitruck, LAN,
and Discord and healthchecks.io alert services). Useful for understanding *what
goes in and out* of the system without internal details.

```mermaid
---
title: Diagrama de Contexto (C4 Nivel 1) - Plataforma HomeLab
config:
  flowchart:
    wrappingWidth: 280
---
flowchart TB
    operador(["<span style='color:#fff'><b>Operador HomeLab</b><br/><small>[Person]</small><br/>Administra el clúster vía kubectl, SSH y la UI de ArgoCD</span>"])
    plataforma["<span style='color:#fff'><b>Plataforma HomeLab</b><br/><small>[Software System]</small><br/>K3s + Incus + CAPN — sistema en alcance</span>"]
    git["<span style='color:#fff'><b>Git remoto</b><br/><small>[Software System]</small><br/>GitHub / GitLab: fuente de verdad de los manifiestos</span>"]
    registro["<span style='color:#fff'><b>Registro de imágenes</b><br/><small>[Software System]</small><br/>images.linuxcontainers.org (simplestreams Incus/CAPN)</span>"]
    omnitruck["<span style='color:#fff'><b>Omnitruck Cinc/Chef</b><br/><small>[Software System]</small><br/>Distribuye los paquetes de cinc-client/cinc-auditor</span>"]
    lan["<span style='color:#fff'><b>Red LAN / Router</b><br/><small>[Software System]</small><br/>DHCP y asignación de IPs fijas para los 3 nodos</span>"]
    discord["<span style='color:#fff'><b>Discord</b><br/><small>[Software System]</small><br/>Canales de alertas críticas, avisos y despliegues</span>"]
    healthchecks["<span style='color:#fff'><b>healthchecks.io</b><br/><small>[Software System]</small><br/>Dead man's switch: avisa si el monitoreo deja de pingear</span>"]

    operador -->|"Administra<br/><small>[kubectl / SSH / ArgoCD UI]</small>"| plataforma
    plataforma -->|"Sincroniza manifiestos<br/><small>[GitOps (ArgoCD)]</small>"| git
    plataforma -->|"Descarga imágenes<br/><small>[kubeadm / ubuntu]</small>"| registro
    plataforma -->|"Instala paquetes<br/><small>[HTTPS]</small>"| omnitruck
    plataforma <-->|"Bridge L2, IP fija<br/><small>[netplan]</small>"| lan
    plataforma -->|"Envía alertas y avisos<br/><small>[webhook HTTPS]</small>"| discord
    plataforma -->|"Ping cada 5 min<br/><small>[HTTPS]</small>"| healthchecks
    healthchecks -.->|"Avisa si el ping se corta<br/><small>[integración Discord]</small>"| discord
    discord -.->|"Notifica<br/><small>[móvil / escritorio]</small>"| operador

    classDef person fill:#08427B,stroke:#073B6F,color:#fff
    classDef system fill:#1168BD,stroke:#0B4884,color:#fff
    classDef container fill:#438DD5,stroke:#3C7FC0,color:#fff
    classDef component fill:#85BBF0,stroke:#78A8D8,color:#000
    classDef external fill:#999999,stroke:#8A8A8A,color:#fff
    class operador person
    class plataforma system
    class git,registro,omnitruck,lan,discord,healthchecks external
```

### Level 2 — Containers

Open the box of the platform and show the **logical containers** (K3s Management,
Incus Cluster, Workload Clusters, Storage, Monitoring, Logs, Local AI, Gateway
and SSO, DNS, and Cinc Lab) with their technologies and how they relate to each
other and to external systems.

```mermaid
---
title: Diagrama de Contenedores (C4 Nivel 2) - Plataforma HomeLab
config:
  flowchart:
    wrappingWidth: 280
---
flowchart TB
    operador(["<span style='color:#fff'><b>Operador HomeLab</b><br/><small>[Person]</small><br/>kubectl / SSH / ArgoCD UI</span>"])
    subgraph homelab["Plataforma HomeLab"]
        k3s_mgmt["<span style='color:#fff'><b>K3s Management</b><br/><small>[Container: Kubernetes bare-metal]</small><br/>Cluster API + CAPN controller + ArgoCD + Sealed Secrets</span>"]
        incus["<span style='color:#fff'><b>Incus Cluster</b><br/><small>[Container: Incus, dqlite HA]</small><br/>3 miembros: grupo x86 (M920q+M700) y grupo arm64 (Orange Pi)</span>"]
        workload["<span style='color:#fff'><b>Workload Clusters</b><br/><small>[Container: kubeadm sobre LXCMachine]</small><br/>Clusters K8s efímeros provisionados por CAPN (LXC o VM)</span>"]
        storage["<span style='color:#fff'><b>Storage</b><br/><small>[Container: OpenEBS LocalPV + Longhorn v1]</small><br/>Persistencia local y replicada entre x86/arm64</span>"]
        monitoreo["<span style='color:#fff'><b>Monitoreo</b><br/><small>[Container: VictoriaMetrics + Grafana]</small><br/>Métricas, sondas, alertas y paneles (namespace monitoring)</span>"]
        cinclab["<span style='color:#fff'><b>Cinc Lab VMs</b><br/><small>[Container: Incus VM (Ubuntu 24.04)]</small><br/>Sandbox para probar cookbooks de Cinc/Chef</span>"]
        acceso["<span style='color:#fff'><b>Gateway y SSO</b><br/><small>[Container: Kong Gateway + Dex]</small><br/>Entrada HTTPS de *.homelab.local y login con GitHub (team devops)</span>"]
        ia["<span style='color:#fff'><b>IA local</b><br/><small>[Container: Ollama router + Open WebUI]</small><br/>Chat y API de modelos; Ollama bajo demanda en los 3 nodos</span>"]
        logs["<span style='color:#fff'><b>Logs</b><br/><small>[Container: VictoriaLogs + Vector]</small><br/>Logs de pods y nodos (namespace monitoring)</span>"]
        dns["<span style='color:#fff'><b>DNS</b><br/><small>[Container: BIND en deborah]</small><br/>Zona homelab.local y reenvío al router</span>"]
    end
    git["<span style='color:#fff'><b>Git remoto</b><br/><small>[Software System]</small><br/>GitHub / GitLab</span>"]
    registro["<span style='color:#fff'><b>Registro de imágenes</b><br/><small>[Software System]</small><br/>images.linuxcontainers.org</span>"]
    discord["<span style='color:#fff'><b>Discord</b><br/><small>[Software System]</small><br/>Canales de alertas y despliegues</span>"]
    healthchecks["<span style='color:#fff'><b>healthchecks.io</b><br/><small>[Software System]</small><br/>Dead man's switch</span>"]

    operador -->|"Administra<br/><small>[kubectl / ArgoCD UI]</small>"| k3s_mgmt
    git -->|"Sincroniza manifiestos<br/><small>[GitOps]</small>"| k3s_mgmt
    k3s_mgmt -->|"Provisiona instancias<br/><small>[API REST Incus (LXCMachine)]</small>"| incus
    registro -->|"Sirve imágenes<br/><small>[simplestreams]</small>"| incus
    incus -->|"Aloja<br/><small>[cluster group @x86 / @arm64]</small>"| workload
    incus -->|"Aloja<br/><small>[target manual]</small>"| cinclab
    workload -->|"Monta volúmenes<br/><small>[PVC]</small>"| storage
    k3s_mgmt -->|"Despliega por GitOps<br/><small>[Argo CD]</small>"| monitoreo
    monitoreo -->|"Lee métricas de los nodos<br/><small>[HTTPS :8443, certificado metrics]</small>"| incus
    monitoreo -->|"Guarda métricas<br/><small>[PVC Longhorn]</small>"| storage
    monitoreo -->|"Alertas<br/><small>[webhook HTTPS]</small>"| discord
    monitoreo -->|"Ping cada 5 min<br/><small>[HTTPS]</small>"| healthchecks
    operador -->|"Consulta paneles<br/><small>[Grafana, SSO]</small>"| monitoreo
    operador -->|"Resuelve nombres<br/><small>[DNS :53]</small>"| dns
    operador -->|"Entra a las UIs<br/><small>[HTTPS + SSO]</small>"| acceso
    acceso -->|"Enruta<br/><small>[HTTPRoute]</small>"| ia
    acceso -->|"Enruta Grafana y Argo CD<br/><small>[HTTPRoute]</small>"| monitoreo
    logs -->|"Guarda logs<br/><small>[PVC Longhorn]</small>"| storage
    monitoreo -->|"Resume alertas<br/><small>[token Bearer]</small>"| ia

    classDef person fill:#08427B,stroke:#073B6F,color:#fff
    classDef system fill:#1168BD,stroke:#0B4884,color:#fff
    classDef container fill:#438DD5,stroke:#3C7FC0,color:#fff
    classDef component fill:#85BBF0,stroke:#78A8D8,color:#000
    classDef external fill:#999999,stroke:#8A8A8A,color:#fff
    class operador person
    class k3s_mgmt,incus,workload,storage,monitoreo,cinclab,acceso,ia,logs,dns container
    class git,registro,discord,healthchecks external
    style homelab fill:none,stroke:#888,stroke-dasharray:6 4
```

## Dive Deeper into C4

| Level | Page | What it shows |
|---|---|---|
| 1–2 | *(this page)* | Context + logical containers |
| 3 | **[Components](nivel-3-componentes.md)** | Zoom into container (K3s, Incus, workload, storage, monitoring, Cinc); AI, logs, and access in [Local AI](../operacion/ia-ollama.md), [Logs](../operacion/logs.md), and [Authentication Model](../security/modelo-de-autenticacion.md) |
| 4 | **[Deployment](nivel-4-despliegue.md)** | 3 physical nodes on the LAN |

