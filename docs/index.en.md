# Homelab — K3s + Incus + CAPN

<span class="tag tag-status">Under active construction</span>

A lab to **learn and operate modern infrastructure** with equipment that anyone can have at home: three small computers that turn into a "mini cloud" with Kubernetes. The documentation explains each step, why it's done, and how to check that it worked, and **accompanies you with artificial intelligence (AI) as you study**.

## What is this?

=== "In simple terms"

    Imagine a small building with three floors. Each floor is a computer. A program called **Incus** divides each floor into departments (virtual machines and containers). On top works a **manager**, Kubernetes (in its lightweight version, K3s), which decides which application goes in which department and replaces the one that fails. Everything that is installed is written in a **plan stored in Git**; another program, Argo CD, compares the building with the plan and corrects any differences. And each installation is done with automated task lists (Ansible), so it can be repeated as many times as you want.

    The building also has its own **AI assistant**, which lives in the house and costs nothing: several computers can run the models (even a Mac, which only turns on manually when you want to lend it) and a single "reception" distributes each question to the node with the requested model. A **central file** gathers the logs of all floors, and every Friday the assistant writes a summary of the week. To access anything, people identify with their GitHub account and programs with their own key.

=== "In technical terms"

    Hybrid K3s cluster (control plane ARM64 —64-bit ARM architecture—, workers x86_64) on a three-member Incus cluster (quorum with dqlite, cluster groups by architecture). Pod network with Calico (VXLAN —Virtual Extensible LAN— between subnets), `LoadBalancer` with MetalLB in L2 (Layer 2) and HTTPS ingress via Gateway API (Kong) with TLS (Transport Layer Security) from a self-managed CA (certificate authority) (cert-manager). Storage with OpenEBS LocalPV and Longhorn. The platform is deployed via GitOps: an Argo CD ApplicationSet activates apps in waves from the repository `maceosoft/gitops`, with secrets in 1Password (never in Git) and SSO (single sign-on) with Dex and GitHub. Ansible does the bootstrap of the nodes, OpenTofu manages the GitHub repositories and ARC (Actions Runner Controller) runs the pipelines in the cluster itself. Cluster API (with CAPN, Cluster API Provider for Incus) creates ephemeral clusters on Incus.

    Local AI with Ollama on several nodes behind a custom router (`ollama-router`): the nodes register themselves (heartbeat every 60 s) and the router chooses the node by model; the Mac is an optional node activated by socket of `launchd` with `ollama-node on|off`. Open WebUI with Dex and Open Terminal as a sandbox for code execution. Logs with Vector → VictoriaLogs → Grafana and daily and weekly reports with AI in Discord (`#ia`). Security: people → Dex, machines → token + network restriction, host firewall with `nftables`; NetworkPolicy `default-deny` are activated in stages. The documentation is automatically translated to English with the same Ollama.

## The Homelab at a glance

| Piece | In simple terms | What it does technically |
|---|---|---|
| Nodes | The three "floors" of the building | Lenovo M920q, M700 and Orange Pi 5 Plus (x86_64 and ARM64) |
| **Incus** | The one that divides each floor into departments | Manages containers and VMs in a three-member cluster |
| **K3s** | The manager that distributes the work | Lightweight Kubernetes: control plane today on `deborah` (will move to `oliver`), workers on the other two |
| **Calico** | The hallways between departments | CNI: provides network and addresses to pods |
| **MetalLB** | The building's fixed phone number | Assigns LAN IP to Services `LoadBalancer` |
| **Gateway (Kong)** | The main door with a doorman | Receives HTTPS traffic and sends it to each application |
| **cert-manager** | The office that issues the cards | Issues TLS certificates with a self-managed CA of the Homelab |
| **Longhorn and OpenEBS** | Warehouses: one fast and one with backup | Local and replicated storage between nodes |
| **Argo CD (GitOps)** | The inspector that compares the building with the plan | Synchronizes the cluster with what Git declares |
| **Dex** | The identification counter | SSO: logs in with GitHub in Argo CD, Grafana, Open WebUI, vCluster, Incus and SSH |
| **Ollama + router** | The assistant and its reception | Local language models on several nodes; a router with token chooses the node by model |
| **Open WebUI and Open Terminal** | The consultation room and the workshop | Chat with the assistant (entry with Dex) and an isolated terminal where the assistant runs code |
| **Vector, VictoriaLogs and Grafana** | The central file and its screens | Collects logs from nodes and pods, stores them for 30 days and displays them; reports with AI in Discord |
| **Host firewall** | The locks on each floor | `nftables` on each node, with automatic rollback if something goes wrong when applying it |
| **ARC** | Workers that build and test | GitHub Actions runners inside the cluster |
| **CAPN** | A 3D printer for clusters | Cluster API to create clusters from a manifest |

## Choose Your Path

<div class="card">
  <div class="card-kicker">Where to Start?</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">I'm Starting Out</div>
      <div class="text-muted">Follow the phases in order. Each phase includes a "Learn This Phase" block with analogies, a practical challenge, and review questions.</div>
      <div class="text-muted"><a href="implementacion/fase-0-preparacion/">Phase 0</a> · <a href="implementacion/fase-1-red/">Phase 1</a> · <a href="implementacion/fase-2-incus/">Phase 2</a> · <a href="implementacion/fase-3-k3s/">Phase 3</a> · <a href="glosario/">Glossary</a></div>
    </div>
    <div class="card-col">
      <div class="card-title">I Already Know Linux and Kubernetes</div>
      <div class="text-muted">Go straight to the decisions: the platform's GitOps, the architecture, and the trade-off analysis for each phase.</div>
      <div class="text-muted"><a href="implementacion/fase-4-gitops/">Phase 4 — GitOps</a> · <a href="architecture/overview/">Architecture</a> · <a href="gitops/">GitOps Catalog</a></div>
    </div>
    <div class="card-col">
      <div class="card-title">I'm Here to Operate</div>
      <div class="text-muted">Routine procedures: add a node (also to the Ollama cluster), rotate credentials, update K3s and Argo CD, check logs.</div>
      <div class="text-muted"><a href="operacion/">Operations</a> · <a href="operacion/ia-ollama/">AI Assistant</a> · <a href="operacion/logs/">Logs</a> · <a href="security/modelo-de-autenticacion/">Security</a> · <a href="secrets/">Secrets</a></div>
    </div>
  </div>
</div>

## Learn with AI, Free

At each step of the guide, there is a button **Learn with AI**: prepare a tutor question with the context of that section
and it takes you to a study notebook that **responds only with this documentation**, with quizzes and audio summaries. Choose your level, click the button, and paste the question in the chat.

- [**How to use and what free tools are available**](aprende.md)
- [Open the NotebookLM Notebook](https://notebooklm.google/){ data-notebook-link="1" } (you need a Google account)
- If you use another assistant: [`llms-full.txt`](https://homelab.maceo.cl/llms-full.txt) brings the entire guide in plain text.

## Hardware

| Node | Model | CPU | RAM (measurement) | IP (`br0`) | Role |
|---|---|---|---|---|---|
| `invincible` | Lenovo M920q | i7-8700T x86_64 | 15.5 GB | 192.168.20.6 | Incus leader · K3s worker · Ollama |
| `oliver` | Lenovo M700 | i3-6100T x86_64 | 7.7 GB | 192.168.20.7 | Incus quorum · K3s worker (future control plane) · Ollama |
| `deborah` | Orange Pi 5 Plus | RK3588 ARM64 | 31 GB | 192.168.20.5 | K3s control plane (will become worker) · Incus ARM64 · DNS · Ollama |

Measured details and RAM budget: [Hardware Inventory](hardware/inventory.md). The control plane will move from
`deborah` to `oliver` with a guided procedure that has not yet been executed:
[Move the Control Plane](operacion/mover-control-plane.md). A Mac can be added as an optional Ollama node
([guide](operacion/agregar-nodo-ollama.md)).

> Hostnames from the *Invincible* series — see
> [characters](https://invincible.fandom.com/es/wiki/Categor%C3%ADa:Personajes).

## Start Here

**Main Guide — step-by-step implementation:**

- **[Implementation — Overview](implementacion/index.md)** — Phases 0→6, timeline, forks.
- **[Technology Stack](implementacion/stack-tecnologico.md)** — layered diagram + products.

Context and deeper dive:

- [Architecture (C4 Level 1–4)](architecture/overview.md) · [Components](architecture/nivel-3-componentes.md) · [Deployment](architecture/nivel-4-despliegue.md)
- [Hardware Inventory](hardware/inventory.md)
- [GitOps Catalog](gitops/index.md) · [Storage](storage/index.md) · [Secrets](secrets/index.md)
- [Local AI Assistant](operacion/ia-ollama.md) · [Logs and Reports with AI](operacion/logs.md) · [Authentication Model](security/modelo-de-autenticacion.md)
- [Lab Cinc/Chef](labs/cinc/index.md)

!!! note "Repository"
    The Ansible, OpenTofu, and Ollama node agent code lives in this
    same repo (`maceosoft/homelab`), outside of `docs/`; Kubernetes manifests, in [`maceosoft/gitops`](https://github.com/maceosoft/gitops).
    This site is the human-readable documentation; the repos are the executable source.
    Spanish is the original: the English version is automatically translated by the Ollama of the HomeLab.
