# Updates

What has been added to the HomeLab, from most recent to oldest. The last three also appear on the
[home page](index.md).

<!--
To add an update: write it at the top, inside the "recientes" block, and move the oldest one from that block
just below the closing marker. The home page (index.md) includes only what is inside the block, using
pymdownx.snippets. One line with date and bold title, two or three sentences, and a link to the page that explains it.
-->

<!-- --8<-- [start:recientes] -->
- **Nov 15, 2026 · AI moves to Claude and NVIDIA.** Ollama was paused on all nodes because it overheated them.
  Now every alert reaches Discord with a Claude summary, and Open WebUI converses with Claude and with NVIDIA's
  open models. The keys live in 1Password, like the rest of the secrets.
  [AI Assistant](operacion/ia-ollama.md).
- **Nov 10, 2026 · Temperatures and NVMe monitored.** The NVMe (PCIe SSD) of `deborah`, without a heatsink,
  dropped off the bus due to heat when copying data to it: it was out of use until getting a heatsink, and now
  there are alerts for NVMe temperature and missing disk. A script shows all sensors for each node.
  [Disk Health](operacion/salud-de-discos.md#nvme).
- **Nov 8, 2026 · A fourth node: `eve`.** A 2019 16" MacBook Pro with T2 chip (Apple's security coprocessor)
  joins the cluster as an Incus member, Kubernetes node, and Ollama node. It connects via a TP-Link gigabit
  network adapter; if the cable is unplugged, the backup WiFi now takes over, and the prompt warns whether it's
  on charger or battery. [See in inventory](hardware/inventory.md#eve-macbook-pro-with-t2-chip).
<!-- --8<-- [end:recientes] -->
- **Nov 8, 2026 · Monitoring ready for four nodes.** Calico alerts compare against the actual node count instead of a
  fixed number, Incus metrics include `eve`, and a conflict between Argo CD and the VictoriaMetrics
  operator that desynced logs every five minutes was fixed. By the way: Open WebUI 0.13, VictoriaMetrics 0.97,
  and runner patches. [Monitoring and Alerts](operacion/monitoreo.md).
- **Nov 7, 2026 · Tools up to date.** Ansible playbooks install opkssh v0.19.2, Ollama 0.40.15, the current version of
  the Incus web UI, and kube-vip v1.3.1. [Local AI Assistant](operacion/ia-ollama.md).
- **Nov 2, 2026 · Docker in GitHub Actions runners.** ARC (Actions Runner Controller) runners can now build images
  with Docker, and the new scale set `arc-php-84` brings PHP (web programming language) 8.4 and Composer with
  shared cache. [Runner Cache](operacion/cache-arc.md).
- **Nov 1, 2026 · Automatic updates.** Dependabot checks Python, GitHub Actions, and OpenTofu dependencies, and opens
  a PR (pull request) when a new version is released.
- **Oct 26, 2026 · The guide in three perspectives.** For important decisions, you can read how it's done at home,
  what would change in a company, and what the cloud equivalent is; steps are shown from the UI or the CLI, as
  you prefer. Also, a [glossary](glosario.md) with all acronyms.
