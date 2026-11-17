# Updates

What has been added to the HomeLab, from most recent to oldest. The last three also appear on the
[home page](index.md).

<!--
To add an update: write it at the very top, inside the "recientes" block, and move the oldest one from that block just below the closing marker. The home page (index.md) includes only what's inside the block, via pymdownx.snippets. One line with date and bold title, two or three sentences, and a link to the page that explains it.
-->

<!-- --8<-- [start:recientes] -->
- **17 Nov 2026 · PostgreSQL backups in Incus.** The platform's shared PostgreSQL will have its backups
  in an Incus bucket at `invincible`, exposed via S3 (Simple Storage Service) with a certificate from the HomeLab's own
  CA. A proxy in front avoids changing the Incus API certificate, and passwords and keys come from
  1Password. [PostgreSQL and backups in Incus](storage/postgres.md).
- **17 Nov 2026 · New repo structure `gitops`.** Each Argo CD app is now a file in
  `bootstrap/components/`: enabling or disabling it means moving the file to `apagadas/`, without reapplying anything. The
  ApplicationSet `homelab` deploys them in waves (each wave waits for the previous one to be healthy) and an app can
  be paused without a PR. Manifests moved to `addons/<área>/` (network, security, monitoring, AI…).
  [GitOps Catalog](gitops/index.md).
- **17 Nov 2026 · Runners without credentials in their environment.** The GitHub Actions runners from `maceosoft` no longer
  load the OpenTofu App, FTP credentials, or the Argo CD token: any job, including one from a PR, could read them.
  The diff token from `gitops` now arrives as a GitHub Actions secret only to the step that uses it, and expires
  in 90 days. [GitOps pipeline](operacion/pipeline-gitops.md#activar-el-diff-contra-el-cluster-una-vez).
<!-- --8<-- [end:recientes] -->
- **15 Nov 2026 · AI moves to Claude and NVIDIA.** Ollama was paused on all nodes because it overheated
  them. Now every alert reaches Discord with a Claude summary, and Open WebUI converses with Claude and with NVIDIA's
  open models. The keys live in 1Password, like the rest of the secrets.
  [AI Assistant](operacion/ia-ollama.md).
- **10 Nov 2026 · Temperatures and NVMe monitored.** The NVMe (PCIe SSD) of `deborah`, without a heatsink,
  dropped off the bus due to heat when copying data to it: it was out of use until getting a heatsink, and now there
  are alerts for NVMe temperature and missing disk. A script shows all sensors from each node.
  [Disk Health](operacion/salud-de-discos.md#nvme).
- **8 Nov 2026 · A fourth node: `eve`.** A 2019 16" MacBook Pro with T2 chip (Apple's security
  coprocessor) joins the cluster as an Incus member, Kubernetes node, and Ollama node. It connects via a TP-Link
  gigabit network adapter; if the cable is unplugged, the backup WiFi now takes over, and the prompt warns whether it's
  on charger or battery. [View in inventory](hardware/inventory.md#eve-macbook-pro-with-t2-chip).
- **8 Nov 2026 · Monitoring ready for four nodes.** Calico alerts compare against the actual node count
  instead of a fixed number, Incus metrics include `eve`, and a conflict between Argo CD and the
  VictoriaMetrics operator that desynced logs every five minutes was fixed. By the way: Open WebUI 0.13, VictoriaMetrics
  0.97, and runner patches. [Monitoring and Alerts](operacion/monitoreo.md).
- **7 Nov 2026 · Tools up to date.** Ansible playbooks install opkssh v0.19.2, Ollama 0.40.15, the current
  version of the Incus web UI, and kube-vip v1.3.1. [Local AI Assistant](operacion/ia-ollama.md).
- **2 Nov 2026 · Docker in GitHub Actions runners.** ARC (Actions Runner Controller) runners can build
  images with Docker, and the new scale set `arc-php-84` brings PHP (web programming language) 8.4 and Composer with
  shared cache. [Runner Cache](operacion/cache-arc.md).
- **1 Nov 2026 · Automatic updates.** Dependabot checks Python, GitHub Actions, and OpenTofu dependencies,
  and opens a PR (pull request) when a new version is released.
- **26 Oct 2026 · The guide in three views.** In important decisions you can read how it's done at home,
  what would change in a company, and what the cloud equivalent is; steps are shown from the UI or the CLI, as you
  prefer. Also, a [glossary](glosario.md) with all acronyms.
