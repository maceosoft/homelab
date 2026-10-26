# C4 Level 4 — Deployment

**Physical** map of the platform: the 3 nodes on the LAN (local network), Debian OS with
`br0`, the Incus daemon and the K3s (lightweight Kubernetes distribution) role on each one. It complements the logical zoom of
[Level 3 — Components](nivel-3-componentes.md).

Back to [Overview (Level 1–2)](overview.md).

## Nodes and roles

| Node | Hardware | RAM | `br0` IP | Incus | K3s |
|---|---|---|---|---|---|
| `invincible` | Lenovo M920q x86_64 | 15.5 GB | 192.168.20.6 | Leader + UI `:8443` | agent; Longhorn disk |
| `oliver` | Lenovo M700 x86_64 | 7.7 GB | 192.168.20.7 | Quorum; **manual** scheduler | agent |
| `deborah` | Orange Pi 5 Plus ARM64 | 31 GB | 192.168.20.5 | `arm64-nodes` member | **server** (CP) `:6443` |

All three nodes also run on-demand Ollama (`llm_nodes` group, see [Local AI](../operacion/ia-ollama.md)), and
`deborah` serves the LAN DNS (BIND, `homelab.local` zone).

!!! note "RAM budget"
    `oliver` has a manual scheduler because it must not host Incus instances
    automatically (it saves RAM for the management cluster). `deborah` is the
    control plane because of its available RAM (31 GB), even though it is ARM64 (64-bit ARM architecture) — validate the CNI (Container Network Interface)
    and workloads before heavy production use.

Hardware details: [Inventory](../hardware/inventory.md).

## Deployment diagram

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


## Previous

**[← Level 3 — Components](nivel-3-componentes.md)**
