# Arquitectura

Vista de diseño del HomeLab. Para el **stack tecnológico** con diagrama por
capas y enlaces a documentación oficial de cada producto, ver
**[Stack tecnológico](../implementacion/stack-tecnologico.md)**.

Guía ejecutable: **[Implementación](../implementacion/index.md)**.

## Capas

1. **Hardware** — 3 nodos físicos (2x x86_64, 1x ARM64). Ver [inventario](../hardware/inventory.md).
2. **Incus Cluster** — sustrato de virtualización, 3 miembros con quorum dqlite.
   Cluster groups `x86-nodes` / `arm64-nodes` para dirigir dónde corre cada instancia.
3. **K3s (distribución ligera de Kubernetes) Management** — el clúster K3s bare-metal existente, que aloja:
    - Cluster API (Application Programming Interface) core + controller de CAPN (Cluster API Provider for Incus)
    - ArgoCD (GitOps)
    - Sealed Secrets controller
4. **Workload Clusters** — clusters kubeadm efímeros provisionados por CAPN
   como instancias Incus (LXC o VM), para dev/test/aislamiento.
5. **Storage** — OpenEBS LocalPV (default, en los 3 nodos) + Longhorn v1
   (replicado entre `invincible` y `deborah`, excluyendo `oliver` por RAM).

## Decisión de diseño clave

No se migra el K3s de producción a nested-K8s. El K3s existente se mantiene
como *management cluster* de Cluster API; CAPN provisiona clusters adicionales
bajo demanda sobre el mismo hardware, sin tocar producción.

## Diagramas C4

### Nivel 1 — Contexto

Vista de más alto nivel: la **Plataforma HomeLab** como una sola caja negra y
los actores/sistemas externos con los que interactúa (operador, Git, registro
de imágenes, Omnitruck, la LAN y los servicios de avisos Discord y
healthchecks.io). Útil para entender *qué entra y sale* del
sistema sin detalle interno.

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

### Nivel 2 — Contenedores

Abre la caja de la plataforma y muestra los **contenedores lógicos** (K3s
Management, Incus Cluster, Workload Clusters, Storage, Monitoreo y Cinc Lab) con sus
tecnologías y cómo se relacionan entre sí y con los sistemas externos.

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

    classDef person fill:#08427B,stroke:#073B6F,color:#fff
    classDef system fill:#1168BD,stroke:#0B4884,color:#fff
    classDef container fill:#438DD5,stroke:#3C7FC0,color:#fff
    classDef component fill:#85BBF0,stroke:#78A8D8,color:#000
    classDef external fill:#999999,stroke:#8A8A8A,color:#fff
    class operador person
    class k3s_mgmt,incus,workload,storage,monitoreo,cinclab container
    class git,registro,discord,healthchecks external
    style homelab fill:none,stroke:#888,stroke-dasharray:6 4
```

## Profundizar en C4

| Nivel | Página | Qué muestra |
|---|---|---|
| 1–2 | *(esta página)* | Contexto + contenedores lógicos |
| 3 | **[Componentes](nivel-3-componentes.md)** | Zoom por contenedor (K3s, Incus, workload, storage, monitoreo, Cinc) |
| 4 | **[Despliegue](nivel-4-despliegue.md)** | 3 nodos físicos en la LAN |

