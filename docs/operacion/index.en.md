# Operations — routine procedures

The [implementation guide](../implementacion/index.md) (Phases 0 to 6) builds
the HomeLab **once**. This section collects what you do **afterwards**, every
time it is needed: adding pieces, maintaining them and rotating credentials.

Each procedure says when to use it, what must be ready beforehand, the
steps in order, how to verify and what to check if something fails.

| Procedure | When | Where it runs |
|---|---|---|
| [Product URLs and access](urls-y-accesos.md) | Know where each tool lives, how to sign in and whether it responds | Browser, `kubectl` |
| [SSH into the servers](acceso-ssh.md) | Sign in to `invincible`, `oliver` or `deborah` with your GitHub account | Your workstation (`opkssh`, `ssh`) |
| [Monitoring and alerts](monitoreo.md) | Check node temperatures and usage, understand a Discord notice, silence an alert | Grafana, `kubectl` |
| [Add a repo](agregar-repo.md) | Every new project in the `maceosoft` org | 1Password + PR in `infra` |
| [Add a node](agregar-nodo.md) | Add a machine to the Incus and K3s cluster | Ansible (`homelab`) |
| [Remove or replace a node](sacar-nodo.md) | Retire a machine or swap it for another | `kubectl`, Incus and Ansible |
| [Add a disk to a node](agregar-disco.md) | More storage for Longhorn or Incus | Ansible (`homelab`) |
| [Incus backups and snapshots](backups-incus.md) | Schedule backups or recover an instance | Incus |
| [Upgrade K3s](actualizar-k3s.md) | Review the automatic upgrades or pin a version | GitOps + Ansible |
| [Patch the nodes](parchear-nodos.md) | Install Debian security patches when monitoring warns you | Ansible + `apt` |
| [Upgrade Argo CD](actualizar-argocd.md) | It upgrades itself to the latest version; first upgrade, pinning a version, what to do if it fails | GitOps + Ansible |
| [Change the Gateway controller](cambiar-gateway.md) | Switch between Kong, Traefik and NGINX; TLS for `*.homelab.local` | GitOps + `kubectl` |
| [Upgrade Debian on deborah (12 → 13)](actualizar-debian-deborah.md) | Move the control plane to Debian 13, with a backup and a boot gate | Ansible (`homelab`) |
| [Calico (CNI) with Argo CD](actualizar-calico.md) | How Argo CD manages and upgrades the pod network | GitOps + `kubectl` |
| [Runner cache (ARC)](cache-arc.md) | What is cached between jobs, how to check it, prune it or empty it | `kubectl` + GitOps |
| [Disk and DNS health](salud-de-discos.md) | What to do when a SMART, eMMC wear or BIND alert fires | Ansible (`homelab`) + nodes |
| [Incus metrics certificate](certificado-metricas-incus.md) | What the read-only client certificate used by monitoring is and how to register it in Incus | `kubectl` + Ansible (`homelab`) |
| [New version notices (Renovate)](actualizaciones-de-productos.md) | Which products have a new version, Discord notices and how to handle each PR | GitHub + Discord + GitOps |
| [Rotate credentials](rotar-credenciales.md) | Periodically, or if a credential leaked | 1Password + playbooks |
| [gitops pipeline](pipeline-gitops.md) | What each `gitops` PR validates; enable the Argo CD diff (once) | GitHub Actions + 1Password |

!!! note "Where the commands run"
    Unless the procedure says otherwise, Ansible commands run from the
    `ansible/` folder of the `homelab` repo, and `kubectl` commands use
    the HomeLab kubeconfig (`~/.kube/homelab-k3s.yaml`).
