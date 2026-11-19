# What's New

What has been added to the HomeLab, from most recent to oldest. The last three also appear on the
[home page](index.md).

<!--
To add a news item: write it at the very top, inside the "recientes" block, and move the oldest item from that block
just below the closing marker. The home page (index.md) includes only what is inside the block, via
pymdownx.snippets. One line with date and bold title, two or three sentences, and a link to the page that explains it.
-->

<!-- --8<-- [start:recientes] -->
- **Nov 18, 2026 · CAPN works.** Kubernetes clusters with Incus nodes (Cluster API) now boot in the
  HomeLab: the API sits on a fixed IP with `kube-vip` instead of the IPv6 that left it unreachable. They are created
  manually, in about 2 minutes, and the operations guide (create, scale, upgrade, delete) was tested command by command.
  [Frequent CAPN operations](operacion/capn.md).
- **Nov 18, 2026 · Automatic DNS.** Everything created registers itself in DNS: apps published in Kubernetes
  (ExternalDNS), Incus instances on `ovn-lan` (`<instancia>.ovn.homelab.local`), and inventory nodes
  (Ansible). Each writes with its own key, and BIND prevents one from overwriting another's names.
  [Automatic DNS](networking/dns-automatico.md).
- **Nov 18, 2026 · vCluster open source instead of vCluster Platform.** The vCluster web UI doesn't work without paying:
  its free plan doesn't include GitHub login. Virtual clusters are now created with the `vcluster` CLI or with an
  Argo CD Application, and you sign in with the same GitHub account as the rest of the cluster.
  [Frequent vCluster operations](operacion/vcluster.md).
<!-- --8<-- [end:recientes] -->
- **Nov 17, 2026 · Kubernetes with GitHub login and encrypted Secrets.** The K3s API now accepts GitHub login
  via Dex: `kubectl` opens the browser and the `devops` team gets full access, without copying the
  admin certificate. Cluster Secrets are now encrypted at rest, and the API certificate accepts the
  `k3s.homelab.local` name.
  [Access Kubernetes with GitHub](operacion/acceso-kubernetes.md).
- **Nov 17, 2026 · PostgreSQL backups in Incus.** The platform's shared PostgreSQL will have its backups
  in an Incus bucket on `invincible`, exposed via S3 (Simple Storage Service) with a certificate from the HomeLab's
  own CA. A proxy in front avoids changing the Incus API certificate, and passwords and keys come from
  1Password. [PostgreSQL and backups in Incus](storage/postgres.md).
- **Nov 17, 2026 · New `gitops` repo structure.** Each Argo CD app is now a file in
  `bootstrap/components/`: enabling or disabling it means moving the file to `apagadas/`, without reapplying anything. The
  ApplicationSet `homelab` deploys them in waves (each wave waits for the previous one to be healthy) and an app
  can be paused without a PR. Manifests moved to `addons/<área>/` (network, security, monitoring, AI…).
  [GitOps Catalog](gitops/index.md).
- **Nov 17, 2026 · Runners without credentials in their environment.** The `maceosoft` GitHub Actions runners no longer
  load the OpenTofu App, FTP credentials, or the Argo CD token: any job, including one from a PR, could read them.
  The `gitops` diff token now arrives as a GitHub Actions secret only to the step that uses it, and expires in 90
  days. [GitOps pipeline](operacion/pipeline-gitops.md#activar-el-diff-contra-el-cluster-una-vez).
- **Nov 15, 2026 · AI moves to Claude and NVIDIA.** Ollama was paused on all nodes because it overheated them
  too much. Now every alert reaches Discord with a Claude summary, and Open WebUI converses with Claude and with open
  models from NVIDIA. The keys live in 1Password, like the rest of the secrets.
  [AI Assistant](operacion/ia-ollama.md).
- **Nov 10, 2026 · Temperatures and NVMe monitored.** The NVMe (PCIe SSD) of `deborah`, without a heatsink, dropped off the bus due to heat while
  copying data to it: it was unusable until a heatsink was added, and now there are alerts for NVMe temperature and
  missing disk. A script shows all sensors on each node.
  [Disk Health](operacion/salud-de-discos.md#nvme).
- **Nov 8, 2026 · A fourth node: `eve`.** A 2019 16" MacBook Pro with a T2 chip (Apple's security coprocessor)
  joins the cluster as an Incus member, Kubernetes node, and Ollama node. It connects via a TP-Link gigabit network
  adapter; if the cable is unplugged, the backup WiFi now actually takes over, and the prompt warns whether it's on
  charger or battery. [View in inventory](hardware/inventory.md#eve-macbook-pro-with-t2-chip).
- **Nov 8, 2026 · Monitoring ready for four nodes.** Calico alerts compare against the actual number of nodes instead of a
  fixed number, Incus metrics include `eve`, and a clash between Argo CD and the VictoriaMetrics operator that
  desynced logs every five minutes was fixed. By the way: Open WebUI 0.13, VictoriaMetrics 0.97, and runner patches.
  [Monitoring and Alerts](operacion/monitoreo.md).
- **Nov 7, 2026 · Tools up to date.** Ansible playbooks install opkssh v0.19.2, Ollama 0.40.15, the current version of the
  Incus web UI, and kube-vip v1.3.1. [Local AI Assistant](operacion/ia-ollama.md).
- **Nov 2, 2026 · Docker in GitHub Actions runners.** The ARC (Actions Runner Controller) runners can now build
  images with Docker, and the new scale set `arc-php-84` brings PHP (web programming language) 8.4 and Composer with
  shared cache. [Runner Cache](operacion/cache-arc.md).
- **Nov 1, 2026 · Automatic updates.** Dependabot checks Python, GitHub Actions, and OpenTofu dependencies, and opens a PR
  (pull request) when a new version is released.
- **Oct 26, 2026 · The guide in three views.** In key decisions you can read how it's done at home, what would change in a
  company, and what the cloud equivalent is; steps are shown from the UI or the CLI, as you prefer. Plus, a
  [glossary](glosario.md) with all the acronyms.
