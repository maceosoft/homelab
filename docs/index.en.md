# HomeLab — K3s + Incus + CAPN

<span class="tag tag-status">Under active construction</span>

A lab to **learn and operate modern infrastructure** with equipment that anyone can have at home: three small computers that become a "mini cloud" with Kubernetes. What you learn here are **the same patterns that companies and large clouds use** (GitOps, replicated storage, single sign-on, monitoring, private AI); what changes is the scale. The documentation explains each step, why it's done, and how to check that it worked, and **accompanies you with artificial intelligence (AI) while you study**.

## Choose How to Read the Guide

At important decision points, you will find three tabs. Choose one here and the guide will remember it on all pages:

=== "🏠 At home"

    The guide as it is built: three machines, free software with no licenses to pay. Ideal for learning by doing and making mistakes without fear.

=== "🏢 In a company"

    In addition to how it's done here, you see what a company gains with each pattern and what would change: high availability, commercial support, compliance, and backups.

=== "☁️ In the cloud"

    You see the equivalent service in Google Cloud, AWS, Azure, and Oracle Cloud, and what you gain and lose by using it instead of setting it up yourself.

The same happens with steps that can be done in two ways: choose **🖱️ From the Interface** or **⌨️ From the Console** once and the guide will always show you that.

## What Is This?

=== "In simple terms"

    Imagine a small building with three floors. Each floor is a computer. A program called **Incus** divides each floor into departments (virtual machines and containers). On top, a **manager**, Kubernetes (in its lightweight version, K3s), decides which application goes in which department and replaces the one that fails. Everything that is installed is written in a **plan stored in Git**; another program, Argo CD, compares the building with the plan and corrects any differences. And each installation is done with automated task lists (Ansible), so it can be repeated as many times as you want.

    The building also has its own **AI assistant**, which lives in the house and costs nothing: several computers run the models, more can be added when you want, and a single "reception" distributes each question to the one with the requested model. A **central file** gathers the logs (records) from all floors, and every Friday the assistant writes a summary of the week. To access anything, people identify themselves with their GitHub account and programs, with their own key.

=== "In technical terms"

    Hybrid K3s cluster (control plane ARM64 —64-bit ARM architecture—, workers x86_64) on a three-member Incus cluster (quorum with dqlite, cluster groups by architecture). Pod network with Calico (VXLAN —Virtual Extensible LAN— between subnets), `LoadBalancer` with MetalLB in L2 (Layer 2) and HTTPS ingress via Gateway API (Kong) with TLS (Transport Layer Security) from a self-managed CA (certificate authority) (cert-manager). Storage with OpenEBS LocalPV and Longhorn. The platform is deployed via GitOps: an Argo CD ApplicationSet activates apps in waves from the repository `maceosoft/gitops`, with secrets in 1Password (never in Git) and SSO (single sign-on) with Dex and GitHub. Ansible does the bootstrap of the nodes, OpenTofu manages the GitHub repositories and ARC (Actions Runner Controller) runs the pipelines in the cluster itself. Cluster API (with CAPN, Cluster API Provider for Incus) creates ephemeral clusters on Incus.

    Local AI with Ollama on several nodes behind a custom router (`ollama-router`): each node announces itself only to the router and informs it every minute that it is still available and which models it has; the router sends each question to a node that has the requested model. More machines can be added as nodes. Open WebUI with Dex and Open Terminal as a code execution sandbox. Logs with Vector → VictoriaLogs → Grafana and daily and weekly reports with AI in Discord (`#ia`). Security: people → Dex, machines → token + network restriction, host firewall with `nftables`; the NetworkPolicy `default-deny` are activated in stages. The documentation translates itself to English with the same Ollama.

## A Homelab Overview

| Piece | In Simple Terms | What It Does Technically |
|---|---|---|
| Nodes | The three "floors" of the building | Lenovo M920q, M700 and Orange Pi 5 Plus (x86_64 and ARM64) |
| **Incus** | The one that divides each floor into departments | Manages containers and VMs in a three-member cluster |
| **K3s** | The manager that distributes the work | Lightweight Kubernetes: control plane on `deborah`, workers on the other two |
| **Calico** | The hallways between departments | CNI: provides network and addresses to pods |
| **MetalLB** | The building's fixed phone number | Assigns LAN IP to Services `LoadBalancer` |
| **Gateway (Kong)** | The main door with a doorman | Receives HTTPS traffic and routes it to each application |
| **cert-manager** | The office that issues badges | Issues TLS certificates with a self-signed CA |
| **Longhorn and OpenEBS** | Warehouses: one fast and one with backup | Local and replicated storage between nodes |
| **Argo CD (GitOps)** | The inspector that compares the building with the blueprint | Syncs the cluster with what is declared in Git |
| **Dex** | The identification counter | SSO: logs in with GitHub in Argo CD, Grafana, Open WebUI, vCluster, Incus and SSH |
| **Ollama + router** | The assistant and its reception | Local language models on multiple nodes; a router with a token chooses the node based on the model |
| **Open WebUI and Open Terminal** | The consultation room and workshop | Chat with the assistant (login with Dex) and an isolated terminal where the assistant runs code |
| **Vector, VictoriaLogs and Grafana** | The central archive and its screens | Collects logs from nodes and pods, stores them for 30 days and displays them; reports with AI in Discord |
| **Host firewall** | The locks on each floor | `nftables` on each node, with automatic rollback if something goes wrong when applying it |
| **ARC** | Cluster builders and testers | GitHub Actions runners inside the cluster |
| **CAPN** | A cluster 3D printer | Cluster API for creating clusters from a manifest |

## Choose Your Path

<div class="card">
  <div class="card-kicker">Where to start?</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">I'm Starting</div>
      <div class="text-muted">Follow the phases in order. Each one brings a "Learn this phase" block with analogies, a practical challenge, and review questions.</div>
      <div class="text-muted"><a href="implementacion/fase-0-preparacion/">Phase 0</a> · <a href="implementacion/fase-1-red/">Phase 1</a> · <a href="implementacion/fase-2-incus/">Phase 2</a> · <a href="implementacion/fase-3-k3s/">Phase 3</a> · <a href="glosario/">Glossary</a></div>
    </div>
    <div class="card-col">
      <div class="card-title">I Already Know Linux and Kubernetes</div>
      <div class="text-muted">Go straight to the decisions: the platform's GitOps, the architecture, and the trade-offs analysis of each phase.</div>
      <div class="text-muted"><a href="implementacion/fase-4-gitops/">Phase 4 — GitOps</a> · <a href="architecture/overview/">Architecture</a> · <a href="gitops/">GitOps Catalog</a></div>
    </div>
    <div class="card-col">
      <div class="card-title">I'm Here to Operate</div>
      <div class="text-muted">Routine procedures: add a node (also to the Ollama cluster), rotate credentials, update K3s and Argo CD, review logs.</div>
      <div class="text-muted"><a href="operacion/">Operation</a> · <a href="operacion/ia-ollama/">AI Assistant</a> · <a href="operacion/logs/">Logs</a> · <a href="security/modelo-de-autenticacion/">Security</a> · <a href="secrets/">Secrets</a></div>
    </div>
  </div>
</div>

## Learn with AI, Free

In each step of the guide, there is a button **Learn with AI**: prepares a tutor question with the context of that section
and takes you to a study notebook that **responds only with this documentation**, with quizzes and audio summaries.
Choose your level, press the button, and paste the question in the chat.

- [**How to use and what free tools are available**](aprende.md)
- [Open the NotebookLM Notebook](https://notebooklm.google/){ data-notebook-link="1" } (you need a Google account)
- If you use another assistant: [`llms-full.txt`](https://homelab.maceo.cl/llms-full.txt) brings the entire guide in plain text.

## Hardware

| Node | Model | CPU | RAM (measured) | IP (`br0`) | Role |
|---|---|---|---|---|---|
| `invincible` | Lenovo M920q | i7-8700T x86_64 | 15.5 GB | 192.168.20.6 | Incus leader · K3s worker · Ollama |
| `oliver` | Lenovo M700 | i3-6100T x86_64 | 7.7 GB | 192.168.20.7 | Incus quorum · K3s worker · Ollama |
| `deborah` | Orange Pi 5 Plus | RK3588 ARM64 | 31 GB | 192.168.20.5 | K3s control plane · Incus ARM64 · DNS · Ollama |

Measured details and RAM budget: [Hardware Inventory](hardware/inventory.md). If the control plane node ever needs to be changed, the procedure is documented in
[Move the Control Plane](operacion/mover-control-plane.md). Additional equipment can be added as Ollama nodes
([guide](operacion/agregar-nodo-ollama.md)).

> Hostnames from the *Invincible* series — see
> [characters](https://invincible.fandom.com/es/wiki/Categor%C3%ADa:Personajes).

## Start Here

**Main Guide — Step-by-Step Implementation:**

- **[Implementation — Overview](implementacion/index.md)** — Phases 0→6, timeline, forks.
- **[Tech Stack](implementacion/stack-tecnologico.md)** — Layer diagram + products.

Context and Deep Dive:

- [Architecture (C4 Level 1–4)](architecture/overview.md) · [Components](architecture/nivel-3-componentes.md) · [Deployment](architecture/nivel-4-despliegue.md)
- [Hardware Inventory](hardware/inventory.md)
- [GitOps Catalog](gitops/index.md) · [Storage](storage/index.md) · [Secrets](secrets/index.md)
- [Local AI Assistant](operacion/ia-ollama.md) · [Logs and Reports with AI](operacion/logs.md) · [Authentication Model](security/modelo-de-autenticacion.md)
- [Lab Cinc/Chef](labs/cinc/index.md)

!!! note "Repository"
    The Ansible code, OpenTofu, and Ollama node agent live in this
    same repo (`maceosoft/homelab`), outside of `docs/`; Kubernetes manifests
    are in [`maceosoft/gitops`](https://github.com/maceosoft/gitops).
    This site is the human-readable documentation; the repos are the executable
    source. Spanish is the original: the English version is automatically
    translated by the HomeLab Ollama.
