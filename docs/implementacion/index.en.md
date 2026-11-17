# Implementation — step-by-step guide

This section is the **main walkthrough** of the HomeLab: from bare-metal nodes to full GitOps. Each phase is executable, verifiable, and links to the [tech stack](stack-tecnologico.md) and deep-dive pages.

!!! tip "How to use this guide"
    Follow the phases in order the first time. In subsequent deployments you can jump to the phase you need if prerequisites are already met. Where there is **more than one alternative**, each phase includes a brief **trade-off analysis** (benefit vs cost/risk).

## Phase timeline

```mermaid
flowchart LR
  F0[Fase_0_Preparacion] --> F1[Fase_1_Red]
  F1 --> F2[Fase_2_Incus]
  F2 --> F3[Fase_3_K3s]
  F3 --> F4[Fase_4_GitOps]
  F4 --> F5[Fase_5_vCluster]
  F4 --> F6[Fase_6_CAPN]
```

<div class="stepper">
  <div class="stepper-item">
    <div class="stepper-dot-col">
      <div class="stepper-dot">0</div>
      <div class="stepper-line"></div>
    </div>
    <div class="card stepper-card">
      <div class="card-title"><a href="fase-0-preparacion/">Preparation</a> <span class="tag tag-accent">Completed</span></div>
      <div class="card-body">Repo, Ansible, inventory, optional discovery.</div>
      <div class="card-meta"><code>playbook-discovery.yml</code></div>
    </div>
  </div>
  <div class="stepper-item">
    <div class="stepper-dot-col">
      <div class="stepper-dot">1</div>
      <div class="stepper-line"></div>
    </div>
    <div class="card stepper-card">
      <div class="card-title"><a href="fase-1-red/">Network</a> <span class="tag tag-accent">Completed</span></div>
      <div class="card-body">Static IP on <code>br0</code> on all 4 nodes.</div>
      <div class="card-meta"><code>playbook-set-static-ip.yml</code></div>
    </div>
  </div>
  <div class="stepper-item">
    <div class="stepper-dot-col">
      <div class="stepper-dot">2</div>
      <div class="stepper-line"></div>
    </div>
    <div class="card stepper-card">
      <div class="card-title"><a href="fase-2-incus/">Incus</a> <span class="tag tag-accent">Completed</span></div>
      <div class="card-body">HA Incus cluster + cluster groups + UI.</div>
      <div class="card-meta"><code>playbook-bootstrap.yml</code> + <code>playbook-incus-cluster.yml</code></div>
    </div>
  </div>
  <div class="stepper-item">
    <div class="stepper-dot-col">
      <div class="stepper-dot">3</div>
      <div class="stepper-line"></div>
    </div>
    <div class="card stepper-card">
      <div class="card-title"><a href="fase-3-k3s/">K3s</a> <span class="tag tag-accent">Completed</span></div>
      <div class="card-body">Management cluster + Argo CD controller.</div>
      <div class="card-meta"><code>playbook-k3s.yml</code></div>
    </div>
  </div>
  <div class="stepper-item">
    <div class="stepper-dot-col">
      <div class="stepper-dot">4</div>
      <div class="stepper-line"></div>
    </div>
    <div class="card stepper-card">
      <div class="card-title"><a href="fase-4-gitops/">GitOps</a> <span class="tag tag-accent">Completed</span></div>
      <div class="card-body">MetalLB, Gateway API, storage, Dex, waves.</div>
      <div class="card-meta">Argo CD + <code>gitops</code></div>
    </div>
  </div>
  <div class="stepper-item">
    <div class="stepper-dot-col">
      <div class="stepper-dot stepper-dot--neutral">5</div>
      <div class="stepper-line"></div>
    </div>
    <div class="card stepper-card">
      <div class="card-title"><a href="fase-5-vcluster/">vCluster</a> <span class="tag tag-neutral">Optional</span></div>
      <div class="card-body">Virtual clusters + web kubeconfig.</div>
      <div class="card-meta">Manual Application</div>
    </div>
  </div>
  <div class="stepper-item">
    <div class="stepper-dot-col">
      <div class="stepper-dot stepper-dot--neutral">6</div>
    </div>
    <div class="card stepper-card">
      <div class="card-title"><a href="fase-6-capn/">CAPN</a> <span class="tag tag-neutral">Optional</span></div>
      <div class="card-body">Workload clusters on Incus.</div>
      <div class="card-meta"><code>clusterctl</code> + Manual Application</div>
    </div>
  </div>
</div>

**End of guide:** **[HomeLab Summary](resumen-homelab.md)** — global checklist, URLs, `/etc/hosts`, nodes and verification.

## Two repos, two responsibilities

| Repo | What it installs | Tool |
|---|---|---|
| [`homelab`](https://github.com/maceosoft/homelab) | OS networking, Incus, K3s, kube-vip, Argo CD controller | [Ansible](https://docs.ansible.com/) |
| [`gitops`](https://github.com/maceosoft/gitops) | MetalLB, Gateway API, storage, vCluster, CAPN, … | [Argo CD](https://argo-cd.readthedocs.io/) |

## Tech stack

Layer diagram, product list with official links and role in the HomeLab:

**[View full tech stack →](stack-tecnologico.md)**

Complementary architectural view: [C4 Architecture](../architecture/overview.md).

## Decision map (forks)

| Decision | Option A (default HomeLab) | Option B |
|---|---|---|
| Stable K3s API | Name `k3s.homelab.local` to control plane (`deborah`, `192.168.20.5`) | [kube-vip](https://kube-vip.io/) (`kube_vip.enabled: true` on `k3s_install.yml`) |
| Install K3s | `playbook-k3s.yml` | Manual curl ([reference](../k3s/index.md)) |
| **CNI** | [Calico](https://docs.tigera.io/calico/latest/about/) (`k3s_cni: calico`) | [Flannel](https://github.com/flannel-io/flannel) embedded (`vxlan`), [Canal](https://docs.tigera.io/calico/latest/getting-started/kubernetes/flannel/flannel), [Cilium](https://docs.cilium.io/) |
| OAuth Secrets | [1Password SDK](https://github.com/1Password/onepassword-sdk-python) — personal account, vault `HomeLab` | Company account or other vault via env vars |
| vCluster / CAPN | In `gitops/bootstrap/components/apagadas/` | Move them to `bootstrap/components/` when ready |
| HA Storage | [Longhorn](https://longhorn.io/docs/) on invincible+deborah | Only [OpenEBS](https://openebs.io/docs) |

<div class="card">
  <div class="card-kicker">Trade-off analysis</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">Fixed IP vs kube-vip</div>
      <div class="text-muted">Fixed IP: zero extra components</div>
      <div class="text-muted">kube-vip: stable VIP <code>192.168.20.4</code> if CP changes node</div>
    </div>
    <div class="card-col">
      <div class="card-title">kube-vip</div>
      <div class="text-muted">API on dedicated IP; agents don't depend on hostname</div>
      <div class="text-muted">One more daemon; doesn't replace MetalLB</div>
    </div>
    <div class="card-col">
      <div class="card-title">Ansible vs curl K3s</div>
      <div class="text-muted">Idempotent, flags in <code>group_vars</code></div>
      <div class="text-muted">Manual only for one-off debugging</div>
    </div>
    <div class="card-col">
      <div class="card-title">Flannel</div>
      <div class="text-muted">Embedded in K3s; low overhead</div>
      <div class="text-muted">No native NetworkPolicy</div>
    </div>
    <div class="card-col">
      <div class="card-title">Calico <span class="tag tag-accent">chosen</span> · Canal / Cilium</div>
      <div class="text-muted">Network policies (Canal/Calico) or eBPF (Cilium)</div>
      <div class="text-muted"><code>--flannel-backend=none</code>; more RAM/CPU; choose <strong>before</strong> bootstrap</div>
    </div>
    <div class="card-col">
      <div class="card-title">1Password SDK</div>
      <div class="text-muted">Secrets out of Git; local DesktopAuth</div>
      <div class="text-muted">Requires unlocked 1Password app on workstation</div>
    </div>
    <div class="card-col">
      <div class="card-title">env vars / <code>kubectl patch</code></div>
      <div class="text-muted">No 1Password</div>
      <div class="text-muted">Secrets in shell/history; not idempotent</div>
    </div>
    <div class="card-col">
      <div class="card-title">Manual vCluster/CAPN sync</div>
      <div class="text-muted">Prevents accidental deletion of ephemeral clusters</div>
      <div class="text-muted">Extra step in Argo CD UI</div>
    </div>
    <div class="card-col">
      <div class="card-title">Longhorn</div>
      <div class="text-muted">x86↔arm64 replication</div>
      <div class="text-muted">Designed for 2 nodes; more pods than OpenEBS</div>
    </div>
    <div class="card-col">
      <div class="card-title">OpenEBS only</div>
      <div class="text-muted">LocalPV on all nodes; simple</div>
      <div class="text-muted">No HA across nodes</div>
    </div>
  </div>
</div>

CNI (Container Network Interface) detail: [Phase 3 — K3s](fase-3-k3s.md#options) · [playbook-options](../k3s/playbook-options.md#cni).

K3s flags detail (lightweight Kubernetes distribution): [Playbook options](../k3s/playbook-options.md).

Ansible roles catalog: [Ansible — roles](../ansible/index.md).

## After the phases

With the platform running, the **local AI assistant** (Ollama on multiple nodes behind a router, with Open WebUI and Open Terminal), **centralized logs** with AI-powered weekly reports, and **security** layers (host firewall, per-service tokens, staged NetworkPolicy) are added. They are in [Operations](../operacion/index.md): [Local AI Assistant](../operacion/ia-ollama.md), [Logs](../operacion/logs.md), and [Authentication Model](../security/modelo-de-autenticacion.md). If you ever need to change the control plane node, the procedure is in [Move the control plane](../operacion/mover-control-plane.md).

## Start here

**[→ Phase 0 — Preparation](fase-0-preparacion.md)**

Appendix outside the normal path: [Uninstall K3s](apendice-desinstalar.md).
