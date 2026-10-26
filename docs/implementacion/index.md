# Implementación — guía paso a paso

Esta sección es el **recorrido principal** del HomeLab: desde nodos bare-metal
hasta GitOps completo. Cada fase es ejecutable, verificable y enlaza al
[stack tecnológico](stack-tecnologico.md) y a páginas de profundización.

!!! tip "Cómo usar esta guía"
    Sigue las fases en orden la primera vez. En despliegues posteriores puedes
    saltar a la fase que necesites si los prerrequisitos ya están cumplidos.
    Donde haya **más de una alternativa**, cada fase incluye un breve
    **Análisis de trade-offs** (ventaja vs coste/riesgo).

## Timeline de fases

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
      <div class="card-title"><a href="fase-0-preparacion/">Preparación</a> <span class="tag tag-accent">Completada</span></div>
      <div class="card-body">Repo, Ansible, inventario, discovery opcional.</div>
      <div class="card-meta"><code>playbook-discovery.yml</code></div>
    </div>
  </div>
  <div class="stepper-item">
    <div class="stepper-dot-col">
      <div class="stepper-dot">1</div>
      <div class="stepper-line"></div>
    </div>
    <div class="card stepper-card">
      <div class="card-title"><a href="fase-1-red/">Red</a> <span class="tag tag-accent">Completada</span></div>
      <div class="card-body">IP fija en <code>br0</code> en los 3 nodos.</div>
      <div class="card-meta"><code>playbook-set-static-ip.yml</code></div>
    </div>
  </div>
  <div class="stepper-item">
    <div class="stepper-dot-col">
      <div class="stepper-dot">2</div>
      <div class="stepper-line"></div>
    </div>
    <div class="card stepper-card">
      <div class="card-title"><a href="fase-2-incus/">Incus</a> <span class="tag tag-accent">Completada</span></div>
      <div class="card-body">Clúster Incus HA + cluster groups + UI.</div>
      <div class="card-meta"><code>playbook-bootstrap.yml</code> + <code>playbook-incus-cluster.yml</code></div>
    </div>
  </div>
  <div class="stepper-item">
    <div class="stepper-dot-col">
      <div class="stepper-dot">3</div>
      <div class="stepper-line"></div>
    </div>
    <div class="card stepper-card">
      <div class="card-title"><a href="fase-3-k3s/">K3s</a> <span class="tag tag-accent">Completada</span></div>
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
      <div class="card-title"><a href="fase-4-gitops/">GitOps</a> <span class="tag tag-accent">Completada</span></div>
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
      <div class="card-title"><a href="fase-5-vcluster/">vCluster</a> <span class="tag tag-neutral">Opcional</span></div>
      <div class="card-body">Clústeres virtuales + kubeconfig web.</div>
      <div class="card-meta">Application manual</div>
    </div>
  </div>
  <div class="stepper-item">
    <div class="stepper-dot-col">
      <div class="stepper-dot stepper-dot--neutral">6</div>
    </div>
    <div class="card stepper-card">
      <div class="card-title"><a href="fase-6-capn/">CAPN</a> <span class="tag tag-neutral">Opcional</span></div>
      <div class="card-body">Workload clusters sobre Incus.</div>
      <div class="card-meta"><code>clusterctl</code> + Application manual</div>
    </div>
  </div>
</div>

**Cierre de la guía:** **[Resumen del HomeLab](resumen-homelab.md)** — checklist global,
URLs, `/etc/hosts`, nodos y verificación.

## Dos repos, dos responsabilidades

| Repo | Qué instala | Herramienta |
|---|---|---|
| [`homelab`](https://github.com/maceosoft/homelab) | Red SO, Incus, K3s, kube-vip, controller Argo CD | [Ansible](https://docs.ansible.com/) |
| [`gitops`](https://github.com/maceosoft/gitops) | MetalLB, Gateway API, storage, vCluster, CAPN, … | [Argo CD](https://argo-cd.readthedocs.io/) |

## Stack tecnológico

Diagrama por capas, lista de productos con enlaces oficiales y rol en el HomeLab:

**[Ver stack tecnológico completo →](stack-tecnologico.md)**

Vista arquitectónica complementaria: [Arquitectura C4](../architecture/overview.md).

## Mapa de decisiones (forks)

| Decisión | Opción A (default HomeLab) | Opción B |
|---|---|---|
| API K3s estable | Nombre `k3s.homelab.local` hacia el control plane (hoy `deborah`, `192.168.20.5`; se mudará a `oliver`) | [kube-vip](https://kube-vip.io/) (`kube_vip.enabled: true` en `k3s_install.yml`) |
| Instalar K3s | `playbook-k3s.yml` | curl manual ([referencia](../k3s/index.md)) |
| **CNI** | [Calico](https://docs.tigera.io/calico/latest/about/) (`k3s_cni: calico`) | [Flannel](https://github.com/flannel-io/flannel) embebido (`vxlan`), [Canal](https://docs.tigera.io/calico/latest/getting-started/kubernetes/flannel/flannel), [Cilium](https://docs.cilium.io/) |
| Secretos OAuth | [1Password SDK](https://github.com/1Password/onepassword-sdk-python) — cuenta personal, bóveda `HomeLab` | Cuenta empresa u otra bóveda vía env vars |
| vCluster / CAPN | Comentadas en `homelab-root` | Descomentar en `root-appset.yaml` cuando estés listo |
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
      <div class="text-muted">LocalPV en 3 nodos; simple</div>
      <div class="text-muted">Sin HA entre nodos</div>
    </div>
  </div>
</div>

Detalle CNI (Container Network Interface): [Fase 3 — K3s](fase-3-k3s.md#opciones) · [playbook-options](../k3s/playbook-options.md#cni).

Detalle de flags K3s (distribución ligera de Kubernetes): [Opciones del playbook](../k3s/playbook-options.md).

Catálogo de roles Ansible: [Ansible — roles](../ansible/index.md).

## Después de las fases

Con la plataforma en marcha se agregan el **asistente de IA local** (Ollama en varios nodos detrás de un router, con
Open WebUI y Open Terminal), los **logs centralizados** con reportes semanales con IA y las capas de **seguridad**
(firewall de host, tokens por servicio, NetworkPolicy por etapas). Están en
[Operación](../operacion/index.md): [Asistente de IA local](../operacion/ia-ollama.md),
[Logs](../operacion/logs.md) y [Modelo de autenticación](../security/modelo-de-autenticacion.md). La mudanza del
control plane de `deborah` a `oliver` está documentada en [Mover el control plane](../operacion/mover-control-plane.md)
y todavía no se ha hecho.

## Empieza aquí

**[→ Fase 0 — Preparación](fase-0-preparacion.md)**

Apéndice fuera del recorrido normal: [Desinstalar K3s](apendice-desinstalar.md).
