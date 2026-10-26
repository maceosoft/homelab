# C4 Nivel 4 — Despliegue

Mapa **físico** de la plataforma: los 3 nodos en la LAN (red local), SO Debian con
`br0`, daemon Incus y rol K3s (distribución ligera de Kubernetes) en cada uno. Complementa el zoom lógico del
[Nivel 3 — Componentes](nivel-3-componentes.md).

Volver a [Overview (Nivel 1–2)](overview.md).

## Nodos y roles

| Nodo | Hardware | RAM | IP `br0` | Incus | K3s |
|---|---|---|---|---|---|
| `invincible` | Lenovo M920q x86_64 | 15.5 GB | 192.168.20.6 | Leader + UI `:8443` | agent; disco Longhorn |
| `oliver` | Lenovo M700 x86_64 | 7.7 GB | 192.168.20.7 | Quorum; scheduler **manual** | agent |
| `deborah` | Orange Pi 5 Plus ARM64 | 31 GB | 192.168.20.5 | Miembro `arm64-nodes` | **server** (CP) `:6443` |

Los tres nodos ejecutan además Ollama bajo demanda (grupo `llm_nodes`, ver [IA local](../operacion/ia-ollama.md)) y
`deborah` sirve el DNS de la LAN (BIND, zona `homelab.local`).

!!! note "Presupuesto RAM"
    `oliver` tiene scheduler manual porque no debe alojar instancias Incus de
    forma automática (preserva RAM para el management cluster). `deborah` es
    control plane por RAM disponible (31 GB), aunque sea ARM64 (arquitectura ARM de 64 bits) — validar CNI (Container Network Interface)
    y cargas antes de producción intensiva.

Detalle hardware: [Inventario](../hardware/inventory.md).

## Diagrama de despliegue

```mermaid
---
title: Despliegue (C4 Nivel 4) - Plataforma HomeLab
config:
  flowchart:
    wrappingWidth: 280
---
flowchart TB
    subgraph lan["Red LAN &nbsp;[192.168.20.0/22 · br0] · Debian + netplan en los 3 nodos"]
        direction TB
        subgraph deborah["deborah · Orange Pi 5 Plus ARM64 · 31 GB · .5"]
            direction LR
            k3s_deb["<span style='color:#fff'><b>K3s</b><br/><small>[Container]</small><br/>server control-plane :6443</span>"]
            incus_deb["<span style='color:#fff'><b>Incus</b><br/><small>[Container]</small><br/>arm64-nodes member</span>"]
            bind_deb["<span style='color:#fff'><b>BIND</b><br/><small>[Container]</small><br/>DNS homelab.local :53</span>"]
            oll_deb["<span style='color:#fff'><b>Ollama</b><br/><small>[Container]</small><br/>bajo demanda :11434</span>"]
        end
        subgraph invincible["invincible · M920q x86_64 · 15.5 GB · .6"]
            direction LR
            k3s_inv["<span style='color:#fff'><b>K3s</b><br/><small>[Container]</small><br/>agent + Longhorn disk</span>"]
            incus_inv["<span style='color:#fff'><b>Incus</b><br/><small>[Container]</small><br/>leader + UI :8443</span>"]
            oll_inv["<span style='color:#fff'><b>Ollama</b><br/><small>[Container]</small><br/>bajo demanda :11434</span>"]
        end
        subgraph oliver["oliver · M700 x86_64 · 7.7 GB · .7"]
            direction LR
            incus_nol["<span style='color:#fff'><b>Incus</b><br/><small>[Container]</small><br/>quorum, scheduler manual</span>"]
            k3s_nol["<span style='color:#fff'><b>K3s</b><br/><small>[Container]</small><br/>agent</span>"]
            oll_nol["<span style='color:#fff'><b>Ollama</b><br/><small>[Container]</small><br/>bajo demanda :11434</span>"]
        end
    end

    k3s_deb -->|"Cluster<br/><small>[K3s agent]</small>"| k3s_inv
    k3s_deb -->|"Cluster<br/><small>[K3s agent]</small>"| k3s_nol
    incus_deb <-.->|"Quorum<br/><small>[dqlite]</small>"| incus_inv
    incus_deb <-.->|"Quorum<br/><small>[dqlite]</small>"| incus_nol
    incus_inv <-.->|"Quorum<br/><small>[dqlite]</small>"| incus_nol

    classDef person fill:#08427B,stroke:#073B6F,color:#fff
    classDef system fill:#1168BD,stroke:#0B4884,color:#fff
    classDef container fill:#438DD5,stroke:#3C7FC0,color:#fff
    classDef component fill:#85BBF0,stroke:#78A8D8,color:#000
    classDef external fill:#999999,stroke:#8A8A8A,color:#fff
    class incus_inv,k3s_inv,k3s_deb,incus_deb,incus_nol,k3s_nol,bind_deb,oll_deb,oll_inv,oll_nol container
    style lan fill:none,stroke:#888,stroke-dasharray:6 4
    style invincible fill:none,stroke:#888,stroke-dasharray:6 4
    style deborah fill:none,stroke:#888,stroke-dasharray:6 4
    style oliver fill:none,stroke:#888,stroke-dasharray:6 4
```


## Anterior

**[← Nivel 3 — Componentes](nivel-3-componentes.md)**
