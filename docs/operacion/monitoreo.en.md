# Monitoring and alerts

What is watched in the HomeLab, where to look, and what to do when a notice arrives in Discord. If you are the one **installing** it,
go to [4.13 — Monitoring and alerts](../implementacion/fase-4-gitops.md#413-monitoring-and-alerts-optional).

!!! info "In one line"
    Every 60 seconds, metrics are read from the four nodes and the platform. If something exceeds a threshold for a while,
    a message arrives in Discord: **🔴 critical** in `alertas-criticas` (reaches your phone) and **🟡 warnings** in `alertas-avisos`.
    When it resolves, a **✅** arrives.

**This decision in other environments**

=== "🏠 At home"

    VictoriaMetrics stores the metrics, vmagent collects them, vmalert evaluates the rules, Alertmanager notifies Discord, and
    Grafana displays them. It is **lightweight on purpose**: it reads every 60 seconds and fits in the limited memory of four nodes.

=== "🏢 In a company"

    - **Benefits:** you learn about a problem **before the user** and can measure whether you meet what was promised with
      [SLO](https://sre.google/sre-book/service-level-objectives/) (service level objectives), instead of
      arguing based on feelings.
    - **On-call:** alerts don't go to a chat channel, but to a tool that calls or messages whoever is on duty and escalates if no one responds, like [PagerDuty](https://www.pagerduty.com/),
      [Grafana Cloud IRM](https://grafana.com/products/cloud/irm/) or
      [Jira Service Management](https://www.atlassian.com/software/jira/service-management) (Atlassian is
      migrating Opsgenie customers there).
    - **Retention and scale:** months or years of metrics are kept to compare and plan capacity, with high availability of the monitoring itself.
    - **Commercial support:** it is common to pay for [Grafana Cloud](https://grafana.com/products/cloud/) or
      [Grafana Enterprise](https://grafana.com/products/grafana-enterprise/), or a full platform like
      [Datadog](https://www.datadoghq.com/), in exchange for not operating the monitoring yourself.
    - **When the HomeLab approach makes sense:** when you want the data in your infrastructure, a predictable cost, or
      to monitor sites with poor connectivity; the same open source stack scales quite a bit before needing something else.

=== "☁️ In the cloud"

    | Cloud | Equivalent service |
    |---|---|
    | GCP | [Google Cloud Managed Service for Prometheus](https://docs.cloud.google.com/stackdriver/docs/managed-prometheus) |
    | AWS | [Amazon Managed Service for Prometheus](https://aws.amazon.com/prometheus/) + [Amazon Managed Grafana](https://aws.amazon.com/grafana/) |
    | Azure | [Azure Monitor managed service for Prometheus](https://learn.microsoft.com/en-us/azure/azure-monitor/metrics/prometheus-metrics-overview) + [Azure Managed Grafana](https://learn.microsoft.com/en-us/azure/managed-grafana/overview) |
    | Oracle Cloud (OCI) | [OCI Monitoring](https://docs.oracle.com/en-us/iaas/Content/Monitoring/home.htm) |

    You gain managed storage and queries, with high availability, scale, and SLA, without tending the metrics database. You lose control over configuration, pay per stored and queried metric, and become more locked into that provider.

## General status: what to look at first

If you only look at one dashboard, make it **HomeLab / General status**: it summarizes on one screen whether the HomeLab is healthy. It is designed for
beginners: each box (*tile*) paints **green** if all is well, **amber** if it warrants a look, and **red** if action is needed, and
**each one links to the detail dashboard** for that topic. Read top to bottom:

| Row | What it shows |
|---|---|
| **Summary** | The green/amber/red tiles for each area: the first thing you check |
| **Active alerts** | The alerts firing right now, with their severity |
| **Nodes** | CPU, memory, disk, and temperature of each node; pending security patches and whether any node needs a reboot |
| **Kubernetes** | Pods with issues, recent restarts, workloads with fewer replicas than requested, and unbound volumes (PVC) |
| **Storage (Longhorn)** | Status of Longhorn volumes. A **detached** volume (no app using it) appears as `unknown`: this is normal, not a failure |
| **Platform** | ArgoCD (healthy and synced apps), certificates, web probes, Kong 5xx errors, and Incus |
| **AI and logs** | The Ollama router (live nodes, requests) and log ingestion. Their tiles show **"no data"** in neutral color until you deploy the router and Vector: this is not an error |

The problem tables (pods, workloads, alerts…) that appear **empty, with the text "No issues"**, are expected: it means
there is nothing to attend to. A red tile **links to its detail dashboard**: click it to see what is failing. At the top, the
**HomeLab Panels** menu leads to all dashboards with the tag `homelab`.

What to do if a tile turns red:

| Red tile | Where to continue |
|---|---|
| Node down or no metrics | [SSH in](acceso-ssh.md) and the alert row below; if the node doesn't come back, [Remove or replace a node](sacar-nodo.md) |
| Temperature | Check what is loading it (`kubectl top pods -A`) and ventilation; see the alert table below |
| Disk or DNS | [Disk and DNS health](salud-de-discos.md) |
| Pending patches or reboot | [Patch the nodes](parchear-nodos.md) |
| Pods or workloads with issues | `kubectl get pods -A`, and the tile's detail dashboard |
| Longhorn degraded or failed | The Longhorn UI ([URLs and access](urls-y-accesos.md)) and [Add a disk](agregar-disco.md) if it fills up |
| ArgoCD | `kubectl get applications -n argocd` and the ArgoCD UI; to update it, [Update ArgoCD](actualizar-argocd.md) |
| Certificates | `kubectl describe certificate -A`; if it is an expired credential, [Rotate credentials](rotar-credenciales.md) |
| Calico | [Calico (CNI) with ArgoCD](actualizar-calico.md) |
| Kong 5xx or unreachable webs | The service and Kong logs, and [URLs and access](urls-y-accesos.md) |
| AI (router without nodes) | [Local AI assistant](ia-ollama.md) and [Add an Ollama node](agregar-nodo-ollama.md) |
| No log ingestion | [Centralized logs and AI reports](logs.md) |

This is the **home dashboard** in Grafana: it is pinned by the repo `gitops` (`default_home_dashboard_path` in
[`values-vm-stack.yaml`](https://github.com/maceosoft/gitops/blob/main/monitoring/values-vm-stack.yaml)), so it opens on entry.
If you want a different home just for your user, choose it in *Profile → Preferences → Home Dashboard*.

## View temperatures and usage

Go to [`https://grafana.homelab.local`](https://grafana.homelab.local) (local network only) and click
**Sign in with SSO (GitHub)**: it's the same login as Argo CD, and only members of the `devops` team in the
`maceosoft` organization get in, receiving the **Admin** role. Anyone else is rejected. The node and Kubernetes dashboards come preloaded.

??? note "If SSO doesn't work: log in with the local user"
    The local admin remains active as a fallback, because SSO depends on Dex, which lives in Argo CD, and on the cluster
    resolving DNS. Log in with user `admin` and the password from item `grafana-admin` in 1Password (in the form on the
    same screen, without clicking the SSO button). If the button fails with *Failed to get token from provider*, check the Grafana log:
    `kubectl -n monitoring logs deploy/vm-grafana -c grafana | grep oauth`.

For a one-off query use *Explore* with these expressions:

| What | Query |
|---|---|
| Temperature per node | `max by (nodename) (node_thermal_zone_temp)` |
| Available memory (%) | `100 * node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes` |
| Root disk used (%) | `100 * (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})` |
| CPU usage (%) | `100 * (1 - avg by (nodename) (rate(node_cpu_seconds_total{mode="idle"}[5m])))` |

## Grafana dashboards

There are **13** custom or community dashboards (those tagged **`homelab`**), versioned as code in
[`monitoring/config/dashboards`](https://github.com/maceosoft/gitops/tree/main/monitoring/config/dashboards) of repo `gitops`: they are
not edited manually in Grafana. Those from grafana.com are saved with the revision pinned.

| Dashboard | Purpose | Source |
|---|---|---|
| **HomeLab / General status** | The landing screen: the summary from [above](#estado-general-que-mirar-primero) | custom |
| **HomeLab / Temperatures** | Temperature of `deborah` and the two Intel nodes, now and over 24 hours, with alert thresholds | custom |
| **HomeLab / Sealed Secrets** | The Sealed Secrets controller: decryptions, errors, CPU and memory | custom (none on grafana.com) |
| **HomeLab / Logs** | Log volume by level, errors by service and by node, restarts ([Logs](logs.md)) | custom |
| **HomeLab / Ollama** | Ollama router: nodes with heartbeat, in-flight requests, 5xx errors, tokens and latency by model and node ([Local AI](ia-ollama.md)) | custom |
| **ArgoCD** | App sync and health, sync operations, repo-server usage | grafana.com 14584 |
| **Kong (official)** | Requests, HTTP codes and latency by service and route | grafana.com 7424 |
| **Longhorn Example v1.1.0** | Volumes, replicas, usage and disk health | grafana.com 13032 |
| **Calico: Felix** | The Calico agent on each node: applied rules, timings and dataplane errors | grafana.com 12175 |
| **Cert-manager-Kubernetes** | Certificates, their expiry and status | grafana.com 20842 |
| **Metallb** | MetalLB speakers, L2 advertisements and IP pool usage | grafana.com 20162 |
| **Incus** | CPU, memory, disk and network per project and instance (without the Loki log row, which isn't used) | grafana.com 19727 |
| **GitHub Actions ARC - Runner Scale Set** | CI runners: queued, busy, jobs and timings | grafana.com 25015 |

Additionally, the VictoriaMetrics chart brings **41** built-in dashboards: *Node Exporter Full* (CPU, memory, disk and network per node),
*Kubernetes / Views* (global, namespaces, pods, nodes), *Alertmanager / Overview* and VictoriaMetrics' own (single node,
vmagent, vmalert, operator), among others.

!!! tip "If a panel shows empty"
    Check in *Explore* whether the base metric exists (for example `argocd_app_info`, `longhorn_volume_robustness`,
    `kong_http_requests_total` or `certmanager_certificate_expiration_timestamp_seconds`): the scrape may be missing or the labels may not match. The Longhorn one is built for version 1.1 and with the current one some panels come up empty. The AI and logs panels show "no data" until the router and Vector are deployed.

Reference temperatures, read from the hardware itself: `deborah` (SoC, system on chip, the chip that integrates CPU and graphics)
throttles at 75 °C and again at 85 °C; `invincible` and `oliver` have a manufacturer limit of 100 °C.

## What you might receive

| Alert | What it means | What to do |
|---|---|---|
| 🟡 `TemperaturaAlta` | Processor exceeded 80 °C (75 °C on `deborah`) for several minutes | Check what's loading it (`kubectl top pods -A`) and the machine's ventilation |
| 🔴 `TemperaturaCritica` | Exceeded 90 °C (85 °C on `deborah`) | Check ventilation and load now; if it keeps rising, shut down heavy workloads (e.g., ARC runners) |
| 🔴 `NodoNoListo` | A node is not `Ready` in Kubernetes | Verify it's powered on and on the network, access with `ssh` ([access](acceso-ssh.md)) and check `systemctl status k3s` or `k3s-agent` |
| 🔴 `ServicioBaseSinReplicas` | ArgoCD, Kong, or cert-manager with no replicas | `kubectl -n <namespace> get pods`; without them there's no GitOps, Gateway, or certificates |
| 🟡/🔴 `CertificadoPorVencer` | A certificate expires in less than 14 / 3 days | `kubectl describe certificate -A`; cert-manager should renew it automatically, so if it doesn't, investigate why |
| 🟡 `CertificadoNoListo` | A certificate failed to be issued | `kubectl describe certificate -A` and cert-manager logs |
| 🔴 `LonghornVolumenDegradado` | A volume lost a replica: only one copy remains | Open Longhorn UI (see [URLs and access](urls-y-accesos.md)) and verify both disks are healthy |
| 🔴 `LonghornVolumenFallido` | A volume with no usable replicas | Urgent: the app using it doesn't work; check Longhorn and the nodes |
| 🟡 `LonghornDiscoLlenandose` | Longhorn disk passed 80 % | Delete unused volumes or snapshots, or add a disk ([add disk](agregar-disco.md)) |
| 🟡 `ArgoCDAppNoSana` / `Desincronizada` | An app has been out of `Healthy` / `Synced` for more than 15 / 30 min | `kubectl get applications -n argocd` and the ArgoCD UI |
| 🟡 `NodosSinMetricas` | Some node isn't sending metrics | `kubectl -n monitoring get pods -o wide` (missing a `node-exporter`?) |
| 🟡 `SensoresTemperaturaSinDatos` | Metrics are received from a node, but no temperature | That node's temperature alerts won't work: check `node-exporter` |
| 🔴 `WebInaccesible` | ArgoCD, Dex, or Grafana don't respond `200` via their URL (what the user sees, even if pods are fine) | Open the URL; `kubectl -n kong get pods`, the Gateway, and the route (`kubectl get httproute -A`) |
| 🟡 `RedirectHttpRoto` / `DnsInternoFalla` / `CertificadoWebPorVencer` | The `http://` doesn't redirect to `https://`; a name doesn't resolve inside the cluster (CoreDNS or BIND); a Gateway certificate expires soon | Check the Gateway, `deborah`'s BIND, and certificates (`kubectl describe certificate -A`) |
| 🔴/🟡 `KongErrores5xx` | More than 5 % of a service's requests return 5xx (critical if ArgoCD, Grafana, or Dex and exceeds 25 %) | Check the service logs and Kong |
| 🟡 `KongConfiguracionNoSeAplica` / `KongRecursosInvalidos` | Kong controller fails to apply a route or there are broken resources | `kubectl -n kong logs deploy/kong-controller` and the affected `HTTPRoute` |
| 🔴 `CalicoNodoCaido` | A node lacks the Calico pod: its pods are left without network | `kubectl -n calico-system get pods -o wide` |
| 🟡 Calico, MetalLB, Sealed Secrets, ARC, and ArgoCD (`CalicoFelix…`, `MetalLB…`, `SealedSecretsError…`, `ARC…`, `ArgoCDApplicationSetConErrores`) | A platform component fails, has no replicas, or has no metrics | The alert name says which; `kubectl -n <namespace> get pods` and its logs |
| 🔴/🟡 Disks and BIND (`DiscoSmartFalla`, `EmmcDesgastada`, `BindCaido`…) | SMART failure, worn SSD or eMMC, or LAN DNS not responding | [Disk and DNS health](salud-de-discos.md) |
| 🟡 `ParchesDeSeguridadPendientes` | A node has had pending security patches for more than 3 days | Follow [Patch the nodes](parchear-nodos.md) |
| 🟡 `ReinicioPendiente` | An installed update requires a node reboot, pending for more than 7 days | Reboot the node with the same procedure |
| 🟡 `ListasDePaquetesViejas` | apt lists haven't been updated for more than 7 days: patch notices may not be real | Check `systemctl status node-apt-metrics.timer` on the node |
| 🟡 `SinDatosDePaquetes` | `node-exporter` responds but doesn't publish pending packages | Missing `playbook-apt-metrics.yml` apply on that node |
| 🟡 `KongLatenciaUpstreamAlta` / `KongLatenciaPropiaAlta` / `KongControladorConErrores` | A service responds slowly, Kong adds too much latency, or its controller accumulates errors | *Kong (official)* dashboard and `kubectl -n kong logs deploy/kong-controller` |
| 🟡 `PlataformaMetricasCaidas` / `PlataformaComponenteSinReplicas` | A platform component stopped publishing metrics or ran out of replicas | `kubectl -n <namespace> get pods` of the component named in the alert |
| 🟡 `ActualizacionK3sFallida` | A K3s upgrade job from SUC (*System Upgrade Controller*) failed | [Upgrade K3s](actualizar-k3s.md) |
| 🟡 `SondasSinDatos` | No metrics from external probes: the web could be broken without anything warning | `kubectl -n monitoring get pods` (blackbox-exporter) |
| 🟡 `RafagaDeErroresEnLogs` | A namespace logged more than 200 errors in 5 minutes | *HomeLab / Logs* dashboard; example query in [Logs](logs.md) |
| 🟡 `OOMKillerEnNodo` | Kernel killed processes due to out of memory | Node kernel logs ([Logs](logs.md)) and what's consuming memory (`kubectl top pods -A`); if it's Ollama, lower its `MemoryMax` |
| 🟡 `LogsSinIngestaEnNodo` / `VectorCaido` | Vector isn't sending logs from a node, or its metrics aren't being read | `kubectl -n monitoring get pods -o wide` (that node's Vector pod) and [Logs](logs.md) |
| 🟡 `OllamaRouterCaido` / `OllamaRouterSinNodos` | Ollama router not responding, or no node with heartbeat | `kubectl -n ai get pods` and [Local AI Assistant](ia-ollama.md); for nodes, [Add an Ollama node](agregar-nodo-ollama.md) |

You also get the standard Kubernetes and node alerts that come with the chart (disk filling up, high memory, clock not synced via NTP or Network Time Protocol, pods restarting endlessly or with fewer replicas). Their description appears in the message itself. After the first deployment, the full list is in Grafana's *Alerting* tab.

Messages include the node name and a summary, **no IP addresses**, because the channel may be viewed by more people. A critical alert repeats every 4 hours while active; a warning, every 12 hours.

## What reaches the deployments channel

Besides alerts, ArgoCD writes to your `despliegues` channel every time an app finishes a successful sync
([4.14](../implementacion/fase-4-gitops.md#414-argocd-notifications-to-discord-optional)):

- **🚀 `<app>` deployed**: with the revision, status, and images the app uses. If ArgoCD, Longhorn, or another product
  updated itself, the new version appears in those images (for example `quay.io/argoproj/argocd:v3.5.6`).
- **🟡 `<app>`: sync failed**: arrives at `alertas-avisos` with the error message. Check `kubectl describe application -n argocd <app>`.

This is a **record of what happened**, not something to act on: no need to respond to a 🚀.

## Silencing an alert

To stop an alert from firing for a while (for example during maintenance), create a silence in Alertmanager:

=== "🖱️ From the UI"

    ```bash
    kubectl -n monitoring port-forward svc/vmalertmanager-vm-victoria-metrics-k8s-stack 9093:9093
    ```

    Open [`http://localhost:9093`](http://localhost:9093), click **Silences → New Silence**, enter `alertname` and the alert
    name (plus `nodename` if it's for a single node) and choose the duration. If the Service isn't named that,
    look up its name with `kubectl -n monitoring get svc | grep alertmanager`.

=== "⌨️ From the console"

    The Alertmanager image ships with [`amtool`](https://github.com/prometheus/alertmanager#amtool), so you can create the
    silence from inside the pod, no port-forward needed. Change the alert name, node, and duration:

    ```bash
    kubectl -n monitoring exec statefulset/vmalertmanager-vm-victoria-metrics-k8s-stack -c alertmanager -- \
      amtool silence add alertname=TemperaturaAlta nodename=oliver \
      --duration=2h --author=devops --comment="mantenimiento" \
      --alertmanager.url=http://localhost:9093
    ```

    Remove `nodename=…` if the alert isn't for a single node. With `amtool silence query` (same connection flags) you see
    active silences and with `amtool silence expire <id>` you end one early. If the StatefulSet isn't named that,
    look it up with `kubectl -n monitoring get statefulset | grep alertmanager`.

A silence must never be left without an end date.

## If alerts stop arriving

Monitoring lives inside the cluster, so a severe failure could leave it mute. That's why there's a **dead man's switch**: every 5 minutes
Alertmanager sends a ping to [healthchecks.io](https://healthchecks.io/), and if it stops arriving, that tool notifies via Discord in
`alertas-criticas` that the check `homelab-monitoreo` (or whatever name you gave it) is down. When you receive it:

1. Check if the cluster responds: `kubectl get nodes`.
2. If it responds, check the monitoring pods: `kubectl -n monitoring get pods`.
3. If it doesn't respond, check the control plane node (today `deborah`, which is also the DNS) and emergency key access, because SSO via Dex also lives in the cluster.

## What's still not covered

- What each login in Dex does (only publishes gRPC telemetry), failed deliveries of ArgoCD notifications, and the status of K3s upgrade plans.
- OpenEBS, which doesn't publish useful metrics; only replica alerts cover it.
- Silencing alerts or querying status from Discord (today done with `kubectl` and the Alertmanager UI).
