# Monitoring and alerts

What is watched in the HomeLab, where to look, and what to do when a notice arrives in Discord. If you are the one **installing** it,
go to [4.13 — Monitoring and alerts](../implementacion/fase-4-gitops.md#413-monitoring-and-alerts-optional).

!!! info "In one line"
    Every 60 seconds metrics are scraped from the three nodes and the platform. If something crosses a threshold for a while,
    a message lands in Discord: **🔴 critical** in `alertas-criticas` (reaches your phone) and **🟡 warnings** in `alertas-avisos`.
    When it resolves, a **✅** arrives.

## General status: what to look at first

If you only check one dashboard, make it **HomeLab / General status**: it summarizes on one screen whether the HomeLab is healthy. It is designed
for beginners: each box (*tile*) paints **green** if all is well, **amber** if it deserves a look, and **red** if action is needed, and
**each one links to the detail dashboard** for that topic. Read top to bottom:

| Row | What it shows |
|---|---|
| **Summary** | The green/amber/red tiles for each area: the first thing you check |
| **Active alerts** | Alerts firing right now, with their severity |
| **Nodes** | CPU, memory, disk, and temperature per node; pending security patches and whether any node needs a reboot |
| **Kubernetes** | Pods with issues, recent restarts, workloads with fewer replicas than requested, and unbound volumes (PVC) |
| **Storage (Longhorn)** | Status of Longhorn volumes. A **detached** volume (no app using it) shows as `unknown`: this is normal, not a failure |
| **Platform** | ArgoCD (healthy and synced apps), certificates, web probes, Kong 5xx errors, and Incus |
| **AI and logs** | The Ollama router (live nodes, requests) and log ingestion. Their tiles show **"no data"** in neutral color until you deploy the router and Vector: not an error |

Problem tables (pods, workloads, alerts…) that appear **empty, with the text "No issues"**, are expected: it means
there is nothing to attend to. A red tile **links to its detail dashboard**: click it to see what is failing. At the top, the
**HomeLab Panels** menu leads to all dashboards tagged `homelab`.

What to do if a tile turns red:

| Red tile | Where to continue |
|---|---|
| Node down or no metrics | [SSH in](acceso-ssh.md) and the alert row; if the node does not come back, [Remove or replace a node](sacar-nodo.md) |
| Temperature | Check what is loading it (`kubectl top pods -A`) and ventilation; see the alert table below |
| Disk or DNS | [Disk and DNS health](salud-de-discos.md) |
| Pending patches or reboot | [Patch the nodes](parchear-nodos.md) |
| Pods or workloads with issues | `kubectl get pods -A`, and the tile's detail dashboard |
| Longhorn degraded or failed | Longhorn UI ([URLs and access](urls-y-accesos.md)) and [Add a disk](agregar-disco.md) if it fills up |
| ArgoCD | `kubectl get applications -n argocd` and the ArgoCD UI; to update it, [Update ArgoCD](actualizar-argocd.md) |
| Certificates | `kubectl describe certificate -A`; if it is an expired credential, [Rotate credentials](rotar-credenciales.md) |
| Calico | [Calico (CNI) with ArgoCD](actualizar-calico.md) |
| Kong 5xx or unreachable webs | Service and Kong logs, and [URLs and access](urls-y-accesos.md) |
| AI (router without nodes) | [Local AI assistant](ia-ollama.md) and [Add an Ollama node](agregar-nodo-ollama.md) |
| No log ingestion | [Centralized logs and AI reports](logs.md) |

This is the **Grafana home dashboard**: it is pinned by the repo `gitops` (`default_home_dashboard_path` in
[`values-vm-stack.yaml`](https://github.com/maceosoft/gitops/blob/main/monitoring/values-vm-stack.yaml)), so it opens on entry.
If you want a different home just for your user, pick it in *Profile → Preferences → Home Dashboard*.

## View temperatures and usage

Go to [`https://grafana.homelab.local`](https://grafana.homelab.local) (local network only) and click
**Sign in with SSO (GitHub)**: it is the same login as Argo CD, and only members of the `devops` team in the
`maceosoft` organization get in, receiving the **Admin** role. Anyone else is rejected. Node and Kubernetes panels
come preloaded.

??? note "If SSO fails: log in with the local user"
    The local admin remains active as a fallback, because SSO depends on Dex, which lives in Argo CD, and on the cluster
    resolving DNS. Log in with user `admin` and the password from item `grafana-admin` in 1Password (on the same screen's form,
    without pressing the SSO button). If the button fails with *Failed to get token from provider*, check the Grafana log:
    `kubectl -n monitoring logs deploy/vm-grafana -c grafana | grep oauth`.

For a one-off query use *Explore* with these expressions:

| What | Query |
|---|---|
| Temperature per node | `max by (nodename) (node_thermal_zone_temp)` |
| Available memory (%) | `100 * node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes` |
| Root disk used (%) | `100 * (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})` |
| CPU usage (%) | `100 * (1 - avg by (nodename) (rate(node_cpu_seconds_total{mode="idle"}[5m])))` |

## Grafana Dashboards

There are **13 dashboards**, own or from the community (those with the tag **`homelab`**), versioned as code in
[`monitoring/config/dashboards`](https://github.com/maceosoft/gitops/tree/main/monitoring/config/dashboards) of repo `gitops`: they are not
edited manually in Grafana. Those from grafana.com are saved with the revision pinned.

| Dashboard | Purpose | Source |
|---|---|---|
| **HomeLab / General Status** | The home screen: the summary from [above](#general-status-what-to-look-at-first) | own |
| **HomeLab / Temperatures** | Temperature of `deborah` and the two Intels, now and over 24 hours, with alert thresholds | own |
| **HomeLab / Sealed Secrets** | The Sealed Secrets controller: decryptions, errors, CPU and memory | own (none on grafana.com) |
| **HomeLab / Logs** | Log volume by level, errors by service and by node, restarts ([Logs](logs.md)) | own |
| **HomeLab / Ollama** | Ollama Router: nodes with heartbeat, in-flight requests, 5xx errors, tokens and latency by model and node ([Local AI](ia-ollama.md)) | own |
| **ArgoCD** | Sync and health of apps, sync operations, repo-server usage | grafana.com 14584 |
| **Kong (official)** | Requests, HTTP codes and latency by service and route | grafana.com 7424 |
| **Longhorn Example v1.1.0** | Volumes, replicas, usage and disk health | grafana.com 13032 |
| **Calico: Felix** | The Calico agent on each node: applied rules, times and dataplane errors | grafana.com 12175 |
| **Cert-manager-Kubernetes** | Certificates, their expiration and their status | grafana.com 20842 |
| **Metallb** | MetalLB Speakers, L2 advertisements and IP pool usage | grafana.com 20162 |
| **Incus** | CPU, memory, disk and network of each project and instance (without the Loki logs row, which is not used) | grafana.com 19727 |
| **GitHub Actions ARC - Runner Scale Set** | CI Runners: queued, busy, jobs and times | grafana.com 25015 |

Additionally, the VictoriaMetrics chart brings **41 own dashboards**: *Node Exporter Full* (CPU, memory, disk and network of each node),
*Kubernetes / Views* (global, namespaces, pods, nodes), *Alertmanager / Overview* and VictoriaMetrics' own (single node,
vmagent, vmalert, operator), among others.

!!! tip "If a panel comes up empty"
    Check in *Explore* if the base metric exists (for example `argocd_app_info`, `longhorn_volume_robustness`,
    `kong_http_requests_total` or `certmanager_certificate_expiration_timestamp_seconds`): the scrape may be missing or the labels may
    not match. The Longhorn one is made for version 1.1 and with the current one some panels come up empty. The AI and logs ones show «no data» until deploying the router and Vector.

The reference temperatures, read from the hardware itself: `deborah` (SoC, system on chip, the chip that integrates CPU and graphics) throttles at 75 °C and again at 85 °C; `invincible` and `oliver` have a manufacturer limit of 100 °C.

## What you might receive

| Alert | Meaning | Action |
|---|---|---|
| 🟡 `TemperaturaAlta` | CPU exceeded 80 °C (75 °C on `deborah`) for several minutes | Check what's loading it (`kubectl top pods -A`) and the machine's ventilation |
| 🔴 `TemperaturaCritica` | Exceeded 90 °C (85 °C on `deborah`) | Check ventilation and load immediately; if it keeps rising, shut down heavy workloads (e.g., ARC runners) |
| 🔴 `NodoNoListo` | A node is not `Ready` in Kubernetes | Verify it's powered on and on the network, access via `ssh` ([access](acceso-ssh.md)) and check `systemctl status k3s` or `k3s-agent` |
| 🔴 `ServicioBaseSinReplicas` | ArgoCD, Kong, or cert-manager with zero replicas | `kubectl -n <namespace> get pods`; without them there's no GitOps, Gateway, or certificates |
| 🟡/🔴 `CertificadoPorVencer` | A certificate expires in less than 14 / 3 days | `kubectl describe certificate -A`; cert-manager should renew it automatically, so if it doesn't, investigate why |
| 🟡 `CertificadoNoListo` | A certificate failed to be issued | `kubectl describe certificate -A` and cert-manager logs |
| 🔴 `LonghornVolumenDegradado` | A volume lost a replica: only one copy remains | Open the Longhorn UI (see [URLs and access](urls-y-accesos.md)) and verify both disks are healthy |
| 🔴 `LonghornVolumenFallido` | A volume with no usable replicas | Urgent: the app using it isn't working; check Longhorn and the nodes |
| 🟡 `LonghornDiscoLlenandose` | Longhorn disk exceeded 80 % | Delete unused volumes or snapshots, or add a disk ([add disk](agregar-disco.md)) |
| 🟡 `ArgoCDAppNoSana` / `Desincronizada` | An app has been out of `Healthy` / `Synced` for more than 15 / 30 min | `kubectl get applications -n argocd` and the ArgoCD UI |
| 🟡 `NodosSinMetricas` | Some node isn't sending metrics | `kubectl -n monitoring get pods -o wide` (missing a `node-exporter`?) |
| 🟡 `SensoresTemperaturaSinDatos` | Metrics are received from a node, but no temperature | Temperature alerts for that node won't work: check `node-exporter` |
| 🔴 `WebInaccesible` | ArgoCD, Dex, or Grafana don't respond `200` via their URL (what the user sees, even if pods are healthy) | Open the URL; `kubectl -n kong get pods`, the Gateway, and the route (`kubectl get httproute -A`) |
| 🟡 `RedirectHttpRoto` / `DnsInternoFalla` / `CertificadoWebPorVencer` | The `http://` doesn't redirect to `https://`; a name doesn't resolve inside the cluster (CoreDNS or BIND); a Gateway certificate expires soon | Check the Gateway, `deborah`'s BIND, and certificates (`kubectl describe certificate -A`) |
| 🔴/🟡 `KongErrores5xx` | More than 5 % of a service's requests return 5xx (critical if ArgoCD, Grafana, or Dex and exceeds 25 %) | Check the service logs and Kong |
| 🟡 `KongConfiguracionNoSeAplica` / `KongRecursosInvalidos` | Kong controller fails to apply a route or there are broken resources | `kubectl -n kong logs deploy/kong-controller` and the affected `HTTPRoute` |
| 🔴 `CalicoNodoCaido` | A node lacks the Calico pod: its pods are left without network | `kubectl -n calico-system get pods -o wide` |
| 🟡 Calico, MetalLB, Sealed Secrets, ARC, and ArgoCD (`CalicoFelix…`, `MetalLB…`, `SealedSecretsError…`, `ARC…`, `ArgoCDApplicationSetConErrores`) | A platform component fails, has no replicas, or has no metrics | The alert name tells which one; `kubectl -n <namespace> get pods` and its logs |
| 🔴/🟡 Disks and BIND (`DiscoSmartFalla`, `EmmcDesgastada`, `BindCaido`…) | SMART failure, worn SSD or eMMC, or LAN DNS not responding | [Disk and DNS health](salud-de-discos.md) |
| 🟡 `ParchesDeSeguridadPendientes` | A node has gone more than 3 days with uninstalled security patches | Follow [Patch the nodes](parchear-nodos.md) |
| 🟡 `ReinicioPendiente` | An installed update requires a node reboot, pending for more than 7 days | Reboot the node using the same procedure |
| 🟡 `ListasDePaquetesViejas` | apt lists haven't been updated for more than 7 days: patch notices may not be real | Check `systemctl status node-apt-metrics.timer` on the node |
| 🟡 `SinDatosDePaquetes` | `node-exporter` responds but doesn't publish pending packages | Missing `playbook-apt-metrics.yml` apply on that node |
| 🟡 `KongLatenciaUpstreamAlta` / `KongLatenciaPropiaAlta` / `KongControladorConErrores` | A service responds slowly, Kong adds too much latency, or its controller accumulates errors | *Kong (official)* dashboard and `kubectl -n kong logs deploy/kong-controller` |
| 🟡 `PlataformaMetricasCaidas` / `PlataformaComponenteSinReplicas` | A platform component stopped publishing metrics or ran out of replicas | `kubectl -n <namespace> get pods` of the component named in the alert |
| 🟡 `ActualizacionK3sFallida` | A K3s upgrade job from SUC (*System Upgrade Controller*) failed | [Upgrade K3s](actualizar-k3s.md) |
| 🟡 `SondasSinDatos` | No metrics from external probes: the web could be broken without any warning | `kubectl -n monitoring get pods` (blackbox-exporter) |
| 🟡 `RafagaDeErroresEnLogs` | A namespace logged more than 200 errors in 5 minutes | *HomeLab / Logs* dashboard; example query in [Logs](logs.md) |
| 🟡 `OOMKillerEnNodo` | Kernel killed processes due to OOM | Node kernel logs ([Logs](logs.md)) and what's consuming memory (`kubectl top pods -A`); if it's Ollama, lower its `MemoryMax` |
| 🟡 `LogsSinIngestaEnNodo` / `VectorCaido` | Vector isn't shipping logs from a node, or its metrics aren't being scraped | `kubectl -n monitoring get pods -o wide` (that node's Vector pod) and [Logs](logs.md) |
| 🟡 `OllamaRouterCaido` / `OllamaRouterSinNodos` | Ollama router doesn't respond, or has no nodes with heartbeat | `kubectl -n ai get pods` and [Local AI Assistant](ia-ollama.md); for nodes, [Add an Ollama node](agregar-nodo-ollama.md) |

You also get the standard Kubernetes and node alerts that come with the chart (disk filling up, high memory, clock not synced via NTP or Network Time Protocol, pods restarting endlessly or with missing replicas). Their description appears in the message itself. After the first deployment, the full list is in Grafana's *Alerting* tab.

Messages include the node name and a summary, **no IP addresses**, because the channel may be viewed by more people. A critical alert repeats every 4 hours while active; a warning, every 12 hours.

## What reaches the deployments channel

Besides alerts, ArgoCD writes to your `despliegues` channel every time an app finishes a successful sync ([4.14](../implementacion/fase-4-gitops.md#414-notificaciones-de-argocd-a-discord-opcional)):

- **🚀 `<app>` deployed**: with the revision, status, and images the app uses. If ArgoCD, Longhorn, or another product updated itself, the new version appears in those images (for example `quay.io/argoproj/argocd:v3.5.6`).
- **🟡 `<app>`: sync failed**: arrives at `alertas-avisos` with the error message. Check `kubectl describe application -n argocd <app>`.

This is a **record of what happened**, not something to act on: no need to reply to a 🚀.

## Silence an alert

To stop an alert from firing for a while (e.g., during maintenance), create a silence in Alertmanager:

```bash
kubectl -n monitoring port-forward svc/vmalertmanager-vm-victoria-metrics-k8s-stack 9093:9093
```

Open [`http://localhost:9093`](http://localhost:9093), click **Silences → New Silence**, enter `alertname` and the alert name (plus `nodename` if it's for a single node), and choose the duration. If the Service isn't named that, look up its name with `kubectl -n monitoring get svc | grep alertmanager`. A silence must never be left without an end date.

## If alerts stop arriving

Monitoring lives inside the cluster, so a severe failure could leave it mute. That's why there's a **dead man's switch**: every 5 minutes Alertmanager sends a ping to [healthchecks.io](https://healthchecks.io/), and if it stops arriving, that tool notifies via Discord in `alertas-criticas` that the check `homelab-monitoreo` (or whatever name you gave it) is down. When you receive it:

1. Check if the cluster responds: `kubectl get nodes`.
2. If it responds, check the monitoring pods: `kubectl -n monitoring get pods`.
3. If it doesn't respond, check the control plane node (currently `deborah`, which is also the DNS) and emergency key access, because Dex SSO also lives in the cluster.

## What still isn't covered

- What each login in Dex does (it only publishes gRPC telemetry), failed ArgoCD notification deliveries, and the status of K3s upgrade plans.
- OpenEBS, which doesn't publish useful metrics; only replica alerts cover it.
- Silencing alerts or checking status from Discord (currently done with `kubectl` and the Alertmanager UI).
