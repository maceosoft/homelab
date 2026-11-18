# Implementation — step-by-step guide

This section is the **main walkthrough** of the HomeLab: from bare-metal nodes to full GitOps. Each phase is executable, verifiable, and links to the [tech stack](stack-tecnologico.md) and deep-dive pages.

!!! tip "How to use this guide"
    Follow the phases in order the first time. In subsequent deployments you can jump to the phase you need if the prerequisites are already met. Where there is **more than one alternative**, each phase includes a brief **trade-off analysis** (benefit vs cost/risk).

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
      <div class="card-body">Open-source virtual clusters with the <code>vcluster</code> CLI.</div>
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

**End of guide:** **[HomeLab Summary](resumen-homelab.md)** — global checklist, URLs, `/etc/hosts`, nodes, and verification.

## Two repos, two responsibilities

| Repo | What it installs | Tool |
|---|---|---|
| [`homelab`](https://github.com/maceosoft/homelab) | OS networking, Incus, K3s, kube-vip, Argo CD controller | [Ansible](https://docs.ansible.com/) |
| [`gitops`](https://github.com/maceosoft/gitops) | MetalLB, Gateway API, storage, vCluster, CAPN, … | [Argo CD](https://argo-cd.readthedocs.io/) |

## Tech stack

Layered diagram, product list with official links and role in the HomeLab:

**[View full tech stack →](stack-tecnologico.md)**

Complementary architectural view: [C4 Architecture](../architecture/overview.md).

## Mapa de decisiones (forks)

| Decisión | Opción A (default HomeLab) | Opción B |
|---|---|---|
| API K3s estable | Nombre `k3s.homelab.local` hacia el control plane (`deborah`, `192.168.20.5`) | [kube-vip](https://kube-vip.io/) (`kube_vip.enabled: true` en `k3s_install.yml`) |
| Instalar K3s | `playbook-k3s.yml` | curl manual ([referencia](../k3s/index.md)) |
| **CNI** | [Calico](https://docs.tigera.io/calico/latest/about/) (`k3s_cni: calico`) | [Flannel](https://github.com/flannel-io/flannel) embebido (`vxlan`), [Canal](https://docs.tigera.io/calico/latest/getting-started/kubernetes/flannel/flannel), [Cilium](https://docs.cilium.io/) |
| Secretos OAuth | [1Password SDK](https://github.com/1Password/onepassword-sdk-python) — cuenta personal, bóveda `HomeLab` | Cuenta empresa u otra bóveda vía env vars |
| vCluster / CAPN | En `gitops/bootstrap/components/apagadas/` | Moverlas a `bootstrap/components/` cuando estés listo |
| Storage HA | [Longhorn](https://longhorn.io/docs/) en invincible+deborah | Solo [OpenEBS](https://openebs.io/docs) |

<div class="card">
  <div class="card-kicker">Análisis de trade-offs</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">IP fija vs kube-vip</div>
      <div class="text-muted">IP fija: cero componentes extra</div>
      <div class="text-muted">kube-vip: VIP <code>192.168.20.4</code> estable si el CP cambia de nodo</div>
    </div>
    <div class="card-col">
      <div class="card-title">kube-vip</div>
      <div class="text-muted">API en IP dedicada; agents no dependen de hostname</div>
      <div class="text-muted">Un daemon más; no sustituye MetalLB</div>
    </div>
    <div class="card-col">
      <div class="card-title">Ansible vs curl K3s</div>
      <div class="text-muted">Idempotente, flags en <code>group_vars</code></div>
      <div class="text-muted">Manual solo para depuración puntual</div>
    </div>
    <div class="card-col">
      <div class="card-title">Flannel</div>
      <div class="text-muted">Embebido en K3s; bajo consumo</div>
      <div class="text-muted">Sin NetworkPolicy nativa</div>
    </div>
    <div class="card-col">
      <div class="card-title">Calico <span class="tag tag-accent">elegida</span> · Canal / Cilium</div>
      <div class="text-muted">Políticas de red (Canal/Calico) o eBPF (Cilium)</div>
      <div class="text-muted"><code>--flannel-backend=none</code>; más RAM/CPU; elegir <strong>antes</strong> del bootstrap</div>
    </div>
    <div class="card-col">
      <div class="card-title">1Password SDK</div>
      <div class="text-muted">Secretos fuera de Git; DesktopAuth local</div>
      <div class="text-muted">Requiere app 1Password desbloqueada en la estación</div>
    </div>
    <div class="card-col">
      <div class="card-title">env vars / <code>kubectl patch</code></div>
      <div class="text-muted">Sin 1Password</div>
      <div class="text-muted">Secretos en shell/historial; no idempotente</div>
    </div>
    <div class="card-col">
      <div class="card-title">Sync manual vCluster/CAPN</div>
      <div class="text-muted">Evita borrados accidentales de clústeres efímeros</div>
      <div class="text-muted">Paso extra en Argo CD UI</div>
    </div>
    <div class="card-col">
      <div class="card-title">Longhorn</div>
      <div class="text-muted">Replicación x86↔arm64</div>
      <div class="text-muted">Pensado para 2 nodos; más pods que OpenEBS</div>
    </div>
    <div class="card-col">
      <div class="card-title">Solo OpenEBS</div>
      <div class="text-muted">LocalPV en todos los nodos; simple</div>
      <div class="text-muted">Sin HA entre nodos</div>
    </div>
  </div>
</div>

Detalle CNI (Container Network Interface): [Fase 3 — K3s](fase-3-k3s.md#options) · [playbook-options](../k3s/playbook-options.md#cni).

Detalle de flags K3s (distribución ligera de Kubernetes): [Opciones del playbook](../k3s/playbook-options.md).

Catálogo de roles Ansible: [Ansible — roles](../ansible/index.md).

## Después de las fases

Con la plataforma en marcha se agregan el **asistente de IA local** (Ollama en varios nodos detrás de un router, con
Open WebUI y Open Terminal), los **logs centralizados** con reportes semanales con IA y las capas de **seguridad**
(firewall de host, tokens por servicio, NetworkPolicy por etapas). Están en
[Operación](../operacion/index.md): [Asistente de IA local](../operacion/ia-ollama.md),
[Logs](../operacion/logs.md) y [Modelo de autenticación](../security/modelo-de-autenticacion.md). Si algún día
hiciera falta cambiar el nodo del control plane, el procedimiento está en
[Mover el control plane](../operacion/mover-control-plane.md).

## Empieza aquí

**[→ Fase 0 — Preparación](fase-0-preparacion.md)**

Apéndice fuera del recorrido normal: [Desinstalar K3s](apendice-desinstalar.md).
