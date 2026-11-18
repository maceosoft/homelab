# HomeLab — K8s + Incus

<span class="tag tag-status">Under active construction</span>

Hi! Welcome to my **HomeLab**. Here I walk you through, step by step, how I built a small cloud at home
so you can also learn to **build and operate modern infrastructure**. I use four computers (two small Lenovos,
an Orange Pi board, and a 2019 MacBook Pro turned into a server) that work together as a
Kubernetes (K8s) cluster. What you practice here are **the same patterns used by enterprises and major clouds**; only the scale changes.

**You don't need four machines like mine.** You can practice at whatever scale you have: on your own computer (for example, with kind, which spins up a Kubernetes cluster inside Docker containers), on a server or a virtual machine, or on a managed cluster in the cloud. The guide follows my HomeLab and doesn't include a step-by-step for every case, but the concepts are the same and almost everything installed on Kubernetes works the same way. What changes is how you create the cluster and the pieces tied to hardware, like Incus, which needs Linux on the host. In
[Phase 0](implementacion/fase-0-preparacion.md) I explain which phases you can follow depending on what you have, and the
**☁️ In the cloud** tab of [Choose how to read the guide](#elige-como-leer-la-guia) shows the equivalent of each piece in
major providers.

- **What you'll learn:** how to split one computer into several smaller ones (virtualization with Incus), how to make several computers work as one (Kubernetes), how to describe everything in text files so the system adjusts itself (GitOps), how to keep copies of your data on more than one machine (replicated storage), how to access all services with your GitHub account (single sign-on), how to see what's happening on each machine (logging and monitoring), and how to have artificial intelligence (AI) running in your own home.
- **How you'll learn it:** each step explains what is done, why it's done that way, and how to verify it worked. Installations are automated with Ansible, so you can repeat them as many times as you need.
- **With what:** almost everything is free and open-source software, no licenses to pay. The exceptions are few:
  1Password, the password manager (paid) where I store secrets and which you'll use from Phase 0, and Open
  WebUI, free but with its own license.
- **With a free tutor:** next to the title of each guide step there's a **Learn with AI** button. Choose
  *Explain it to me*, *Quiz me*, or *Something's broken*: the button copies a question with that step's context and opens a
  NotebookLM notebook that answers using only this documentation. [How to use it](aprende.md).

[Start with Phase 0 →](implementacion/fase-0-preparacion.md){ .md-button .md-button--primary }
[I know the basics: choose your path](#choose-your-path){ .md-button }

!!! tip "What's new"

    --8<-- "docs/novedades.md:recientes"

    [See all updates](novedades.md)

## What is this?

I'll explain it two ways; pick whichever suits you (and if you want, read both):

=== "In simple terms"

    Imagine a small four-story building. Each floor is a computer. A program called **Incus** divides each
    floor into apartments (virtual machines and containers). On top works a **manager**, Kubernetes (in its lightweight
    version, K3s), which decides which application goes in which apartment and replaces any that fail. Everything installed
    is written in a **blueprint stored in Git**; another program, Argo CD, compares the building with the blueprint and
    corrects any difference. And each installation is done with automated task lists (Ansible), so it can be repeated
    exactly as many times as you want.

    The building also has its own **artificial intelligence assistant**, which lives at home and costs nothing:
    several computers run the models, you can add more whenever you want, and a single "reception" routes
    each question to the one that has the requested model. A **central file** collects
    the logs from all floors, and every Friday the assistant writes a weekly summary. To access anything, people identify with their GitHub account and programs, with their own key.

=== "In technical detail"

    Hybrid K3s cluster (ARM64 control plane —64-bit ARM architecture—, x86_64 workers) over a four-member Incus cluster (quorum with dqlite, cluster groups by architecture). Pod network with Calico (VXLAN —Virtual Extensible LAN— across subnets), `LoadBalancer` with MetalLB in L2 (layer 2) and HTTPS ingress (secure HTTP) via Gateway API (Kong) with TLS (Transport Layer Security) from a custom CA (cert-manager). Storage with OpenEBS LocalPV and Longhorn. The platform deploys via GitOps: an Argo CD ApplicationSet activates apps in waves from the `maceosoft/gitops` repository, with secrets in 1Password (never in Git) and SSO (single sign-on) with Dex and GitHub. Ansible bootstraps the nodes, OpenTofu manages GitHub repositories and ARC (Actions Runner Controller) runs pipelines in the cluster itself. Cluster API (with CAPN, Cluster API Provider for Incus) creates ephemeral clusters on Incus.

    Local AI with Ollama on multiple nodes behind a custom router (`ollama-router`): each node announces itself only to the router and tells it every minute that it's still available and which models it has; the router sends each question to a node that has the requested model. More machines can be added as nodes. Open WebUI with Dex and Open Terminal as a code execution sandbox. Logs with Vector → VictoriaLogs → Grafana and daily and weekly AI reports in Discord (`#ia`). Security: people → Dex, machines → token + network restriction, host firewall with `nftables`; NetworkPolicy `default-deny` enabled in stages. Documentation translates itself to English with the same Ollama.

## The HomeLab at a glance

These are the pieces you'll be assembling, each with its analogy so you don't lose the thread:

| Piece | In simple terms | What it does technically |
|---|---|---|
| Nodes | The building's four «floors» | Lenovo M920q, M700, Orange Pi 5 Plus and MacBook Pro 16" 2019 (x86_64 and ARM64) |
| **Incus** | The one that divides each floor into apartments | Manages containers and VMs in a four-member cluster |
| **K3s** | The manager that distributes the work | Lightweight Kubernetes: control plane on `deborah`, workers on the other three |
| **Calico** | The hallways between departments | CNI: provides networking and addresses to pods |
| **MetalLB** | The building's landline number | Assigns LAN IPs to Services `LoadBalancer` |
| **Gateway (Kong)** | The main door with a doorman | Receives HTTPS traffic and routes it to each application |
| **cert-manager** | The office that issues badges | Issues TLS certificates with a HomeLab's own CA |
| **Longhorn and OpenEBS** | Warehouses: one fast, one with backup | Local and replicated storage across nodes |
| **Argo CD (GitOps)** | The inspector that compares the building to the blueprint | Syncs the cluster with what Git declares |
| **Dex** | The identification desk | SSO: sign in with GitHub on Argo CD, Grafana, Open WebUI, Incus, K3s, and SSH |
| **Ollama + router** | The assistant and their reception | Local language models on multiple nodes; a token-based router picks the node based on the model |
| **Open WebUI and Open Terminal** | The consultation room and the workshop | Chat with the assistant (entry via Dex) and an isolated terminal where the assistant runs code |
| **Vector, VictoriaLogs, and Grafana** | The central archive and its screens | Collects node and pod logs, stores them for 30 days, and displays them; AI-powered reports in Discord |
| **Host firewall** | The locks on each floor | `nftables` on each node, with automatic rollback if something goes wrong when applying it |
| **ARC** | Workers that build and test | GitHub Actions runners inside the cluster |
| **CAPN** | A 3D printer for clusters | Cluster API to create clusters from a manifest |

## Choose your path

Choose based on what you already know:

<div class="card">
  <div class="card-kicker">Where do I start?</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">I'm just starting</div>
      <div class="text-muted">Follow the phases in order, no rush. Each includes a «Learn this phase» block with analogies, a hands-on challenge, and review questions.</div>
      <div class="text-muted"><a href="implementacion/fase-0-preparacion/">Phase 0</a> · <a href="implementacion/fase-1-red/">Phase 1</a> · <a href="implementacion/fase-2-incus/">Phase 2</a> · <a href="implementacion/fase-3-k3s/">Phase 3</a> · <a href="glosario/">Glossary</a></div>
    </div>
    <div class="card-col">
      <div class="card-title">I already know Linux and Kubernetes</div>
      <div class="text-muted">Go straight to the decisions: the platform's GitOps, architecture, and trade-off analyses for each phase.</div>
      <div class="text-muted"><a href="implementacion/fase-4-gitops/">Phase 4 — GitOps</a> · <a href="architecture/overview/">Architecture</a> · <a href="gitops/">GitOps Catalog</a></div>
    </div>
    <div class="card-col">
      <div class="card-title">I'm here to operate</div>
      <div class="text-muted">Routine procedures: add a node (including to the Ollama cluster), rotate credentials, update K3s and Argo CD, review logs.</div>
      <div class="text-muted"><a href="operacion/">Operations</a> · <a href="operacion/ia-ollama/">AI Assistant</a> · <a href="operacion/logs/">Logs</a> · <a href="security/modelo-de-autenticacion/">Security</a> · <a href="secrets/">Secrets</a></div>
    </div>
  </div>
</div>

## Choose how to read the guide

Not everyone arrives with the same question, so in key decisions you'll find three tabs.
Pick the one that suits you here and the guide will remember it across all pages:

=== "🏠 At home"

    The guide exactly as I built it: four machines and almost all free software, no licenses to pay. Ideal for learning
    by doing and making mistakes without fear. If you practice on your computer or in a VM, this is also your
    tab: it changes how you create the cluster, not what you learn.

=== "🏢 In a company"

    Besides how it's done here, you see what a company gains with each pattern and what would change: high availability,
    commercial support, compliance, and backups.

=== "☁️ In the cloud"

    You see the equivalent service in Google Cloud, AWS, Azure, and Oracle Cloud, and what you gain and lose by using it instead
    of building it yourself. It's the perspective you need if you practice on a managed cloud cluster.

The same goes for steps that can be done two ways: choose **🖱️ From the UI** or **⌨️ From the CLI**
once and the guide will always show your preferred one.

## Learn with AI, free

Here you don't study alone. At every step of the guide there's a **Learn with AI** button: it prepares a tutor prompt with that section's context and takes you to a study notebook that **answers only with this documentation**, with quizzes and audio summaries. Pick your level, hit the button, and paste the prompt into the chat.

- [**How to use it and what free tools are available**](aprende.md)
- [Open the NotebookLM notebook](https://notebooklm.google/){ data-notebook-link="1" } (requires a Google account)
- If you use another assistant: [`llms-full.txt`](https://homelab.maceo.cl/llms-full.txt) brings the whole guide in plain text.

## Hardware

I use four distinct machines: two small Lenovos, an ARM64 board, and a MacBook Pro that now lives plugged in as a server. Here's how they divide the work:

| Node | Model | CPU | RAM (measured) | IP (`br0`) | Role |
|---|---|---|---|---|---|
| `invincible` | Lenovo M920q | i7-8700T x86_64 | 15.5 GB | 192.168.20.6 | Incus (now database leader) · K3s worker · Ollama |
| `oliver` | Lenovo M700 | i3-6100T x86_64 | 7.7 GB | 192.168.20.7 | Incus quorum · K3s worker · Ollama |
| `deborah` | Orange Pi 5 Plus | RK3588 ARM64 | 31 GB | 192.168.20.5 | K3s control plane · Incus ARM64 · DNS · Ollama |
| `eve` | MacBook Pro 16" 2019 | i9-9980HK x86_64 | 31 GB | 192.168.20.8 | Incus (database reserve) · K3s worker · Ollama |

The measured detail of each machine and how much RAM (working memory) each piece uses are in the [Hardware inventory](hardware/inventory.md). If you're interested in how a MacBook with a T2 chip (Apple's security coprocessor) ended up as a cluster node, it's told in [eve: MacBook Pro with T2 chip](hardware/inventory.md#eve-macbook-pro-with-t2-chip). If you ever need to change the control plane node, the procedure is documented in [Move the control plane](operacion/mover-control-plane.md). And if you want to add more machines as Ollama nodes, here's the [guide](operacion/agregar-nodo-ollama.md).

> Node names come from the *Invincible* series — see [characters](https://invincible.fandom.com/es/wiki/Categor%C3%ADa:Personajes).

## Deep dive

When you want to go beyond a specific phase:

**Main guide — step-by-step implementation:**

- **[Implementation — overview](implementacion/index.md)** — phases 0 through 6 in order and a map of the decisions you make in each.
- **[Tech stack](implementacion/stack-tecnologico.md)** — a layered diagram with every product used.

Architecture and background topics:

- [Architecture (C4 model, from general to detailed)](architecture/overview.md) · [Components](architecture/nivel-3-componentes.md) · [Deployment](architecture/nivel-4-despliegue.md)
- [Hardware inventory](hardware/inventory.md)
- [GitOps catalog](gitops/index.md) · [Storage](storage/index.md) · [Secrets](secrets/index.md)
- [Local AI assistant](operacion/ia-ollama.md) · [Logs and reports with AI](operacion/logs.md) · [Authentication model](security/modelo-de-autenticacion.md)
- [Cinc/Chef Lab](labs/cinc/index.md)

!!! note "Repository"
    The Ansible, OpenTofu, and Ollama node agent code lives in this same repo (`maceosoft/homelab`), outside `docs/`; the Kubernetes manifests are in [`maceosoft/gitops`](https://github.com/maceosoft/gitops).
    This site explains the why; the code that actually runs is in the repositories.
    Spanish is the original: the English version is automatically translated by the HomeLab's Ollama.
