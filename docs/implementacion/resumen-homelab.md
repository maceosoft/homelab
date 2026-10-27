# Resumen del HomeLab

Cierre de la [guía de implementación](index.md): checklist de lo desplegado,
URLs, `/etc/hosts`, nodos, secretos y verificación global. Consulta esta página
al terminar la Fase 4 como mínimo; las fases 5 y 6 son opcionales.

## Recorrido completado (por fase)

| Fase | Qué quedó listo | Herramienta |
|---|---|---|
| [0 — Preparación](fase-0-preparacion.md) | Repo, Ansible, `inventory.ini`, discovery opcional | `playbook-discovery.yml` |
| [1 — Red](fase-1-red.md) | IP fija en `br0` (`192.168.20.5`, `.6`, `.7`) | `playbook-set-static-ip.yml` |
| [2 — Incus](fase-2-incus.md) | Clúster HA, groups, UI, storage `dir` | `playbook-bootstrap.yml` + `playbook-incus-cluster.yml` |
| [3 — K3s](fase-3-k3s.md) | Management cluster + Argo CD controller; CNI **Calico** | `playbook-k3s.yml` |
| [4 — GitOps](fase-4-gitops.md) | MetalLB, Gateway API, storage, Dex/GitHub SSO | Argo CD + `playbook-dex-oauth-secrets.yml` |
| [5 — vCluster](fase-5-vcluster.md) *(opc.)* | Platform, kubeconfig web (connected cluster) | Application Argo CD |
| [6 — CAPN](fase-6-capn.md) *(opc.)* | Workload clusters sobre Incus | `clusterctl` + `capn-demo.yaml` |

## URLs y accesos web

| Servicio | URL | Auth | Fase |
|---|---|---|---|
| **Argo CD** | [`https://argocd.homelab.local`](https://argocd.homelab.local) | SSO GitHub vía Dex | 4 |
| **Dex** (issuer) | `https://argocd.homelab.local/api/dex` | — | 4 |
| **vCluster Platform** | [`https://vcluster.homelab.local`](https://vcluster.homelab.local) | SSO Dex → GitHub | 5 |
| **Incus UI** | [`https://incus.homelab.local:8443`](https://incus.homelab.local:8443) | SSO Dex (o cert cliente antes Fase 4) | 2 / 4 |
| **Grafana** *(opcional)* | [`https://grafana.homelab.local`](https://grafana.homelab.local) | SSO GitHub vía Dex (respaldo: `admin` del item `grafana-admin`) | 4 ([4.13](fase-4-gitops.md#413-monitoreo-y-alertas-opcional)) |
| **Open WebUI** (asistente de IA) | [`https://open-webui.homelab.local`](https://open-webui.homelab.local) | SSO GitHub vía Dex (team `devops`) | [IA local](../operacion/ia-ollama.md) |
| **Ollama** (router) | `https://ollama.homelab.local` | Token Bearer por cliente (no es para personas) | [IA local](../operacion/ia-ollama.md) |
| **K3s API** | `https://k3s.homelab.local:6443` (hoy apunta a `deborah`, `192.168.20.5`) | kubeconfig | 3 |

### Kubeconfig

| Clúster | Cómo obtenerlo |
|---|---|
| Management K3s | vCluster Platform (connected cluster) o `playbook-k3s.yml` con `fetch_kubeconfig` |
| vClusters | UI [vCluster Platform](fase-5-vcluster.md) |
| Workload CAPN | `clusterctl get kubeconfig` (Fase 6) |

## DNS en tu estación de trabajo

Usa `192.168.20.5` (BIND en `deborah`) como DNS: `argocd`, `vcluster`, `api`, `grafana`, `open-webui` y `ollama` (`.homelab.local`) apuntan al Gateway
(`192.168.23.200`, IP fija) e `incus.homelab.local` a invincible
([Fase 4 — 4.8](fase-4-gitops.md#48-dns-de-homelablocal)). Si no puedes, el respaldo
es `/etc/hosts`:

```
192.168.23.200  argocd.homelab.local vcluster.homelab.local api.homelab.local grafana.homelab.local open-webui.homelab.local ollama.homelab.local
192.168.20.6    incus.homelab.local
```

Verificación:

```bash
curl -kI https://argocd.homelab.local
curl -kI https://vcluster.homelab.local
# solo si instalaste el monitoreo (4.13)
curl -kI https://grafana.homelab.local
curl -kI https://incus.homelab.local:8443
```

## Nodos del HomeLab

| Hostname | IP `br0` | Incus | K3s | Notas |
|---|---|---|---|---|
| invincible | 192.168.20.6 | Leader + UI | agent | 15.5 GB; Longhorn disk; nodo de Ollama |
| oliver | 192.168.20.7 | Quorum, scheduler manual | agent | 7.7 GB: RAM ajustada; sin instancias automáticas; nodo de Ollama |
| deborah | 192.168.20.5 | arm64-nodes | **server** (CP) | 31 GB RAM; DNS (BIND); nodo de Ollama |

El control plane está en `deborah`. Si algún día hiciera falta pasarlo a otro nodo, el procedimiento está en
[Mover el control plane](../operacion/mover-control-plane.md).

Storage Incus: pool `local`, driver `dir`, perfil `default` → NIC (tarjeta de red) `br0`.

Detalle hardware: [Inventario](../hardware/inventory.md).

## Red del clúster (CNI)

| Decisión | Default HomeLab | Alternativa |
|---|---|---|
| CNI | **Calico** (`k3s_cni: calico`; luego lo adopta Argo CD con `calico-operator` y `calico-config`) | Flannel `vxlan` (embebido en K3s), Canal o Cilium |

Variable Ansible: `k3s_install.core.cni` en [`group_vars/incus_cluster/k3s_install.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/group_vars/incus_cluster/k3s_install.yml).
Detalle y trade-offs: [Fase 3 — CNI](fase-3-k3s.md#cni) · [playbook-options](../k3s/playbook-options.md#cni).

Verificación:

```bash
kubectl get pods -n calico-system -l k8s-app=calico-node
# o flannel / canal / cilium si elegiste otro CNI
```

## Secretos y SSO (1Password)

| Campo 1Password | Uso |
|---|---|
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | Dex → GitHub OAuth (manual en GitHub + 1Password) |
| `VCLUSTER_CLIENT_SECRET` | Dex + Helm Platform (Ansible genera si falta) |

Cuenta **Personal**, bóveda **`HomeLab`** (configurable vía env vars).
Playbook: `playbook-dex-oauth-secrets.yml`.

!!! important "Permisos por defecto"
    En vCluster Platform, los usuarios SSO (inicio de sesión único) **no ven nada** hasta asignarles
    acceso. En Incus, quien entra por SSO tiene acceso completo: el control es que Dex solo deja
    pasar al team `devops` de `maceosoft`. Ver [Fase 4](fase-4-gitops.md) y [Fase 5](fase-5-vcluster.md).

Documentación: [Secretos OAuth](https://github.com/maceosoft/gitops/blob/main/argocd/secrets/1password.md)

## GitOps (Argo CD)

Apps típicas en `Healthy` tras Fase 4:

- `argocd`, `argocd-route`, `metallb`, `homelab-storage`, `kong`, …
- Opcionales (sync manual): `vcluster-platform`, `capn-demo`
- CNI: `calico-operator` + `calico-config` (sync manual); `canal` o `cilium` como alternativas — **una** a la vez
- IA y logs: `ollama-router`, `open-webui`, `open-terminal`, `ai-tools`, `alert-triage`, `log-report`, `victoria-logs`, `vector`; `k8sgpt` está etapado

Repo: [`gitops`](https://github.com/maceosoft/gitops) · [`bootstrap/root-appset.yaml`](https://github.com/maceosoft/gitops/blob/main/bootstrap/root-appset.yaml)

## Después de las fases: IA, logs y seguridad

Sobre la plataforma de la Fase 4 se agregan (cada uno con su guía):

- **IA local**: Ollama en los tres nodos (y un Mac opcional) detrás de un router con registro automático; Open WebUI
  con Dex y Open Terminal. [Asistente de IA local](../operacion/ia-ollama.md) ·
  [Agregar un nodo de Ollama](../operacion/agregar-nodo-ollama.md).
- **Logs y reportes**: Vector → VictoriaLogs → Grafana, con un resumen diario y un reporte semanal con IA en el canal
  `#ia` de Discord. [Logs centralizados](../operacion/logs.md).
- **Seguridad**: personas → Dex; máquinas → token y restricción de red; firewall de host en cada nodo. Las
  NetworkPolicy `default-deny` y K8sGPT están **por activar**. [Modelo de autenticación](../security/modelo-de-autenticacion.md).

## Verificación global

```bash
# Incus
incus cluster list
incus cluster group list

# K3s
kubectl get nodes
kubectl get applications -n argocd

# SSO — login GitHub en ArgoCD, Grafana, Open WebUI, vCluster e Incus UI

# CAPN (si Fase 6)
kubectl get clusters,machines
```

## Enlaces oficiales del stack

- [Incus](https://linuxcontainers.org/incus/docs/main/) · [K3s](https://docs.k3s.io/) · [Argo CD](https://argo-cd.readthedocs.io/)
- [vCluster Platform](https://www.vcluster.com/docs/platform/) · [Cluster API](https://cluster-api.sigs.k8s.io/) · [CAPN](https://capn.linuxcontainers.org/)
- [1Password SDK](https://github.com/1Password/onepassword-sdk-python)

## Mantenimiento y profundización

- [Stack tecnológico](stack-tecnologico.md)
- [Catálogo Ansible](../ansible/index.md)
- [GitOps](../gitops/index.md)
- [Backup Incus (opcional)](../incus/cluster-setup.md#backup-y-snapshots-opcional)
- [Desinstalar K3s](apendice-desinstalar.md)
