# Incus Cluster

!!! info "Part of the implementation guide"
    Follow **[Phase 2 — Incus](../implementacion/fase-2-incus.md)** for the complete
    order. **Ansible** runs bootstrap, join, cluster groups, scheduler, and UI (user interface)
    via [`playbook-incus-cluster.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-incus-cluster.yml).
    The manual blocks below are reference.

## Automation (Ansible)

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-bootstrap.yml
ansible-playbook -i inventory.ini playbook-incus-cluster.yml
```

Roles: [`incus_cluster`](https://github.com/maceosoft/homelab/blob/main/ansible/roles/incus_cluster/README.md),
[`incus_ui`](https://github.com/maceosoft/homelab/blob/main/ansible/roles/incus_ui/README.md).

## Storage

Default HomeLab: driver **`dir`**, pool **`local`**, path
`/var/lib/incus/storage-pools/local`. Ansible validates ≥ **20 GB** free before
init (`incus_storage_min_free_gb` in
[`group_vars/incus_cluster/vars.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/group_vars/incus_cluster/vars.yml)).

| Aspect | Default |
|---|---|
| Driver | `dir` |
| Pool | `local` (one per member) |
| Path | `/var/lib/incus/storage-pools/local` |
| Profile `default` | root on `local`, NIC bridged to `br0` |

### Per node

| Node | Note |
|---|---|
| invincible | 224 GB SSD; leader + UI |
| oliver | 120 GB SSD; local pool required; manual scheduler |
| deborah | eMMC boot; optional override to NVMe: `incus_storage_path: /srv/incus/storage-pools/local` |

### `dir` limitations

- No pool-level CoW; instance snapshots and export tarball work.
- VMs (virtual machines) slower than with `zfs`/`btrfs`.
- Each member has a local pool; no Ceph by default.

### Alternatives

| Driver | When | Variable |
|---|---|---|
| `dir` | **Default** HomeLab | `incus_storage_driver: dir` |
| `btrfs` | Efficient snapshots | `incus_storage_driver: btrfs` + disk/subvolume |
| `zfs` | VMs + advanced snapshots | `incus_storage_driver: zfs` |
| `lvm` | Thin LVM for VMs | `incus_storage_driver: lvm` |

<div class="card">
  <div class="card-kicker">Trade-off analysis</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">Ansible (<code>playbook-incus-cluster.yml</code>)</div>
      <div class="text-muted">Idempotent bootstrap/join/UI</div>
      <div class="text-muted">Requires prior playbook (<code>incus_install</code>)</div>
    </div>
    <div class="card-col">
      <div class="card-title">Manual</div>
      <div class="text-muted">Per-node debugging</div>
      <div class="text-muted">Single-use tokens</div>
    </div>
    <div class="card-col">
      <div class="card-title"><code>dir</code></div>
      <div class="text-muted">No dedicated disk</div>
      <div class="text-muted">Slow VMs; no pool CoW</div>
    </div>
    <div class="card-col">
      <div class="card-title"><code>btrfs</code> / <code>zfs</code></div>
      <div class="text-muted">Efficient snapshots</div>
      <div class="text-muted">Disk/loop; migration if already clustered</div>
    </div>
    <div class="card-col">
      <div class="card-title">UI via Ansible</div>
      <div class="text-muted">Same playbook as cluster</div>
      <div class="text-muted">Only on invincible (native daemon)</div>
    </div>
  </div>
</div>

!!! warning "Cluster already initialized"
    Changing driver requires manual migration; choose before the first playbook.

Docs: [Storage pools](https://linuxcontainers.org/incus/docs/main/explanation/storage/)

## Bootstrap (invincible) — manual

```bash
curl https://pkgs.zabbly.com/get/incus-stable | sudo bash -x
sudo incus admin init
# clustering=yes, no te unes (bootstrap), storage backend dir
```

## Join (oliver and deborah) — manual

```bash
# ejecutar en invincible; genera token de un solo uso
incus cluster add oliver
# otro token distinto
incus cluster add deborah
```
On each node: install Incus and `incus admin init`, answering yes to join, with the corresponding token.

## Cluster groups (architecture)

```bash
incus cluster group create x86-nodes
incus cluster group create arm64-nodes

incus cluster group assign invincible x86-nodes,default
incus cluster group assign oliver x86-nodes,default
incus cluster group assign deborah arm64-nodes,default
```

## Protect oliver RAM (manual scheduler)

oliver has 7.7 GB measured, so it stays as a light node for Incus quorum
without automatic instances:

```bash
incus cluster set oliver scheduler.instance manual
```
Excludes `oliver` from automatic scheduling; it only receives instances if
explicitly targeted with `--target=oliver`. Still counts as a quorum vote.

## Virtual machines (VM)

### Which nodes can run VMs

A VM needs KVM (Kernel-based Virtual Machine, hardware virtualization by the kernel), the kernel module `vhost_vsock` and the Incus driver `qemu`. How each node stands:

| Node | Architecture | Runs VMs? | Reason |
|---|---|---|---|
| invincible | x86_64 | Yes | Driver `lxc` + `qemu`, `vhost_vsock` available |
| oliver | x86_64 | Yes | Same as invincible |
| deborah | ARM64 | **No** | Its vendor kernel (5.10, Rockchip) was built without `vhost_vsock`, and its Incus driver is only `lxc` |

If a VM is created targeting `Auto` and the scheduler picks deborah, it fails with
`Instance type "virtual-machine" is not supported on this server: vhost_vsock kernel module not loaded`.
Always specify the node:

```bash
incus launch images:debian/12 mi-vm --vm --target invincible
```

In the UI, on the creation form, choose the image first (until then **Instance type**, **Target**, and
**Profiles** are disabled), then **Virtual machine** and in **Target** an x86 node (invincible or oliver).

### `cloud` images and the agent disk

Incus VMs are controlled from outside via `incus-agent`, a program that runs inside the VM and enables
`incus exec`, console, file copy, IP viewing, and clean VM shutdown. Incus delivers it to the VM as a
read-only virtual disk called `agent:config`, which carries the binary, its certificates, and the service that starts it.

With a normal image (e.g., `almalinux/8`) Incus adds it automatically. The `cloud` variants (e.g., `almalinux/8/cloud`,
designed for cloud-init, which configures user, SSH keys, and network on boot) require adding it manually. If missing, the VM
won't boot:

```text
Error: This virtual machine image requires an agent:config disk be added
```

The `default` profile doesn't include it (nor should it: it's shared by containers and `agent:config` only applies to VMs).
Add it to the VM:

```bash
incus config device add mi-vm agent disk source=agent:config
incus start mi-vm
```

Or, if you use `cloud` images often, create a separate profile and apply it on launch:

```bash
incus profile create vm-agent
incus profile device add vm-agent agent disk source=agent:config
incus launch images:almalinux/8/cloud mi-vm --vm -p default -p vm-agent --target invincible
```

From the UI: **Instances → (the VM) → Configuration → YAML configuration**, and inside `devices:` add

```yaml
devices:
  agent:
    type: disk
    source: agent:config
```

Save with **Save changes** and click **Start**.

## Admin UI

Incus exposes a **native web interface** (`incus-ui-canonical`) to manage
instances, profiles, networks, and the cluster. It doesn't use kubeconfig; initial authentication
is by **client certificate** and, after Phase 4, by **OIDC (OpenID Connect)** (Dex → GitHub).

### Installation (Ansible or manual)

Ansible installs the UI on **invincible** (`incus_ui`, tag `ui`). The UI is **not** a container: it is served by the Incus daemon at `core.https_address`.

=== "Ansible (recommended)"

    Included in `playbook-incus-cluster.yml` (tag `ui`).

=== "Manual"

    On **invincible**:

    ```bash
    sudo apt install incus-ui-canonical
    sudo incus config set core.https_address=:8443
    ```

`/etc/hosts` on your workstation — full block in [HomeLab Overview](../implementacion/resumen-homelab.md#dns-on-your-workstation):

Initial access: [`https://incus.homelab.local:8443`](https://incus.homelab.local:8443) → client certificate.

<div class="card">
  <div class="card-kicker">UI</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">Ansible (tag <code>ui</code>)</div>
      <div class="text-muted">Included in <code>playbook-incus-cluster.yml</code></div>
      <div class="text-muted">Only on invincible</div>
    </div>
    <div class="card-col">
      <div class="card-title">Manual (<code>apt</code> + <code>config set</code>)</div>
      <div class="text-muted">Without Ansible</div>
      <div class="text-muted">Easy to drift from the rest of the cluster</div>
    </div>
  </div>
</div>

### OIDC via Dex (Phase 4)

With OIDC configured, the UI login screen offers **Login with SSO** (single sign-on) (GitHub via Dex) and **Login with TLS** (Transport Layer Security) (client certificate):

??? note "View screenshot: Incus UI access"
    ![Incus UI login screen with "Login with SSO" and "Login with TLS" options](../assets/screenshots/incus-ui-login.jpg){ loading=lazy }

After [Phase 4 — Incus UI OIDC](../implementacion/fase-4-gitops.md#incus-ui-oidc), with the HomeLab CA (certificate authority) already installed on the node (see the warning below):

```bash
incus config set oidc.issuer=https://argocd.homelab.local/api/dex
incus config set oidc.client.id=incus-ui
```

Incus (7.x) only knows five OIDC keys: `oidc.issuer`, `oidc.client.id`, `oidc.audience`, `oidc.claim`, and `oidc.scopes`. There are no `oidc.client.secret` or `oidc.groups.claim`: Incus does not send a secret, so in Dex the client `incus-ui` is **public** (PKCE —Proof Key for Code Exchange—, `public: true`).

!!! warning "Incus must trust the HomeLab CA"
    The Dex certificate is signed by the HomeLab's own CA (cert-manager). If the node doesn't know it, Incus cannot validate the identity provider and login fails. The playbook (`--tags incus`, or just `--tags incus_ca`) installs it in `invincible` and restarts `incus`. Manually, on the node:

    ```bash
    kubectl -n cert-manager get secret homelab-ca -o jsonpath='{.data.ca\.crt}' | base64 -d \
      | sudo tee /usr/local/share/ca-certificates/homelab-ca.crt > /dev/null
    sudo update-ca-certificates
    sudo systemctl restart incus
    ```

    Verify with `curl -s -o /dev/null -w "%{http_code} ssl_verify=%{ssl_verify_result}\n" https://argocd.homelab.local/api/dex/.well-known/openid-configuration` (must return `200 ssl_verify=0`). Details in [Phase 4](../implementacion/fase-4-gitops.md#incus-ui-oidc).

### OIDC user permissions

Incus 7.x does **not** include `incus auth` (groups and `identity-provider-group` are from LXD —the project Incus forked from—). With OIDC:

| Scenario | Result |
|---|---|
| Member of the `devops` team in the `maceosoft` org | Dex allows access and, with Incus default configuration, has **full access** |
| Account not in that team | Dex rejects login: never reaches Incus |

Access control is therefore membership in the `devops` team (filter `orgs`/`teams` of the GitHub connector in `dex.config`). For granular permissions (per project, read-only) Incus uses [OpenFGA](https://linuxcontainers.org/incus/docs/main/authentication/), which is not configured in the HomeLab.

References:

- [Incus OIDC](https://linuxcontainers.org/incus/docs/main/authentication/#openid-connect-oidc-authentication)

## Load balancing and OVN

Incus has network load balancers (`incus network load-balancer`) and port forwards (`incus network forward`), but **network load balancers only exist on OVN networks** (Open Virtual Network, software-defined virtual network). The HomeLab deploys **OVN** (see [Deploy OVN and segments](#deploy-ovn-and-the-segments)): `br0` remains an unmanaged bridge for existing instances, and the uplink network `UPLINK` and OVN network `ovn-lan` are created, making network load balancers available.

!!! note "`lb01` is not the Incus load balancer"
    The `lb01` instance appearing in `incus list` is an `nginx` OCI container (for testing). The HomeLab's actual load balancing is at other layers:

| What is balanced | Who does it | Where |
|---|---|---|
| Kubernetes applications (Services `LoadBalancer`) | **MetalLB**, with the `192.168.23.200–.220` IPs (Kong Gateway uses `.200`) | [GitOps Catalog](../gitops/index.md) |
| Cluster API cluster control planes | **CAPN**, with its own load balancer (`LOAD_BALANCER='lxc: {}'`, a container inside Incus) | [Phase 6 — CAPN](../implementacion/fase-6-capn.md) |
| K3s API | Control plane IP (`kube-vip` is optional and disabled) | [Phase 3 — K3s](../implementacion/fase-3-k3s.md) |

### Should you enable OVN?

What OVN requires and what it implies for the HomeLab. The segments and deployment are in [Deploy OVN and the segments](#deploy-ovn-and-the-segments).

| OVN Requirement | Status in the HomeLab |
|---|---|
| Packages `ovn-central` (3 nodes, highly available database), `ovn-host` and `openvswitch-switch` | They are on Debian on all three nodes, with OVN 25.03 and Open vSwitch 3.5 on Debian 13 (`invincible`, `oliver`); `deborah` remains on Debian 12 until [updating it](../operacion/actualizar-debian-deborah.md), and until then its versions do not match |
| Shared layer 2 network between nodes | Yes: all three are on the same LAN via `br0` |
| Uplink: an unmanaged bridge or an unused NIC | `br0` works; no need to redo it |
| Reserved IP range outside DHCP for the OVN router and virtual IPs | Defined: `192.168.23.224/28` (LB) and `192.168.23.240–.249` (external OVN), outside DHCP and MetalLB. See [Deploy OVN and the segments](#deploy-ovn-and-the-segments) |
| Instances inside an OVN network | Instances hanging off `br0` (such as `lb01`, `test` and `vm01`) have LAN IPs: to use OVN they must be connected to `ovn-lan` |
| Memory per node (OVS, `ovn-controller` and the central database) | `oliver` has 7.7 GB: it's worth measuring OVN consumption there |

| Pros | Cons |
|---|---|
| Native load balancers and forwards in Incus | Three new components per node and a distributed database to operate |
| Isolated virtual networks per project or cluster, with ACLs | Must reserve a new IP range and move instances that want to use them |
| `LOAD_BALANCER: ovn` in CAPN for Phase 6 clusters | Only benefits instances that move to an OVN network; K3s runs on the hosts and does not benefit |

### Deploy OVN and the segments

The role [`incus_ovn`](https://github.com/maceosoft/homelab/blob/main/ansible/roles/incus_ovn/README.md), within [`playbook-incus-cluster.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-incus-cluster.yml), installs OVN on the three nodes (the highly available database, with `invincible` creating it and the others joining), configures Incus, and creates the *uplink* network over `br0` and an OVN network. It is **safe by default**: without `-e incus_ovn_confirm=true` it only runs the preflight (Incus version, packages, free memory, that `br0` exists and that the reserved IPs do not respond) and installs nothing. With `incus_ovn_enabled: false` (the default value) the cluster playbook doesn't even touch it.

| Segment | Value | Where configured | Variable |
|---|---|---|---|
| **LB** (IP of load balancers and forwards) | `192.168.23.224/28` | `ipv4.routes` of the uplink | `incus_ovn_lb_routes` |
| **External OVN** (one IP per virtual router) | `192.168.23.240–192.168.23.249` | `ipv4.ovn.ranges` of the uplink | `incus_ovn_external_ranges` |
| **Internal OVN** (private subnet, with NAT) | `192.168.19.1/24` | `ipv4.address` of the `ovn-lan` network | `incus_ovn_internal_cidr` |

The first two are from the LAN (`192.168.20.0/22`) and must be **outside the router's DHCP** (`192.168.20.31–192.168.23.191`) and the MetalLB pool (`192.168.23.200–.220`). The allocation of the high free zone of the LAN:

| Range | Use |
|---|---|
| `192.168.23.192–.199` | Free |
| `192.168.23.200–.220` | **MetalLB** (21 IPs; the Kong Gateway uses `.200`) |
| `192.168.23.221–.223` | Free |
| `192.168.23.224/28` (`.224–.239`) | **Incus LB** (16 IPs) |
| `192.168.23.240–.249` | **External OVN** (10 IPs, one virtual router per OVN network) |
| `192.168.23.250–.255` | Free (`.255` is the broadcast of the `/22`, not used) |

The preflight **fails if the segments overlap** with DHCP, with MetalLB, with each other, or with the broadcast. The internal one is private and does not touch the LAN: it also does not overlap with the K3s ranges (`10.42.0.0/16` and `10.43.0.0/16`). Current instances (`lb01`, `test`, `vm01`) remain on `br0`: only those you connect to `ovn-lan` use OVN.

```bash
cd ansible && source ../.venv/bin/activate
# preflight
ansible-playbook -i inventory.ini playbook-incus-cluster.yml --tags ovn --skip-tags always -e incus_ovn_enabled=true
# instala
ansible-playbook -i inventory.ini playbook-incus-cluster.yml --tags ovn --skip-tags always -e incus_ovn_enabled=true -e incus_ovn_confirm=true
```

Then, a network load balancer is created with `incus network load-balancer create ovn-lan 192.168.23.225` and its configuration. The listen address must be in the `ipv4.routes` of the uplink and not overlap with another network in use.

**Verify the deployment:** `ovn-central`, `ovn-controller` and Open vSwitch active on all three nodes; the Northbound database clustered with leader (`ovn-appctl -t /var/run/ovn/ovnnb_db.ctl cluster/status OVN_Northbound`); one Geneve *chassis* per node (`ovn-sbctl show`); and `UPLINK` and `ovn-lan` in `Created` state (`incus network list`).

!!! warning "The OVN database is not encrypted"
    Following the Incus guide, the playbook exposes the OVN databases via `tcp` without SSL (Secure Sockets Layer) on the nodes' LAN. This is acceptable in a lab; for production you would need to enable SSL in OVN.

**Alternatives without OVN:** MetalLB for applications, the CAPN (Cluster API Provider for Incus) load balancer for new clusters, and a container with HAProxy or nginx plus `keepalived` if a virtual IP is needed for instances.

## Update or uninstall Incus

Both playbooks are **safe by default**: without the confirmation variable they only show what they would do.

| What | Playbook | Confirmation | Effect |
|---|---|---|---|
| Update Incus to the latest repository version | [`playbook-upgrade-incus.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-upgrade-incus.yml) | `-e incus_upgrade_confirm=true` | Updates the `incus*` packages node by node and waits for the three members to be `ONLINE`. Does not delete instances |
| Uninstall the cluster (to rebuild it) | [`playbook-uninstall-incus.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-uninstall-incus.yml) | `-e incus_uninstall_confirm=true` | **Destructive:** deletes instances, images, managed networks, the pool, and the packages. Does not touch `br0`, K3s, or BIND |

The cluster requires **the same Incus version on all members**: while they differ, the API is blocked on the already-updated ones until the others catch up. That's why the update playbook runs through the three nodes sequentially and verifies at the end. To rebuild the cluster after uninstalling: `playbook-bootstrap.yml` and `playbook-incus-cluster.yml`.

## Backup and snapshots (optional)

They are not part of the default bootstrap. Enable them when you want to protect
instances or cluster state. The step-by-step is in [Incus Backups](../operacion/backups-incus.md).

| Method | Scope | When to use |
|---|---|---|
| **Instance snapshots** | One instance, same storage pool | Quick rollback; does not replace offsite backup |
| **Export tarball** | Portable instance or volume | Restorable copy to another pool or server |
| **DB dump** | Incus metadata (networks, profiles) | Lightweight cron addition |
| **Tar of `/var/lib/incus`** | Full server | Bootstrap node DR |

### Scheduled snapshots (per instance)

```bash
# Diario a las 06:00; expira a los 7 días
incus config set <instancia> snapshots.schedule="0 6 * * *"
incus config set <instancia> snapshots.expiry=7d
incus config set <instancia> snapshots.pattern="{{ creation_date|date:'2006-01-02' }}"
```

Manual snapshot: `incus snapshot create <instancia> <nombre>`

### Export and metadata dump

```bash
incus export <instancia> /backup/<instancia>.tar.gz
incus admin sql local .dump > /backup/incus-local.sql
incus admin sql global .dump > /backup/incus-global.sql
```

### Limitations

- Snapshots live in the **same storage pool** as the instance; if you lose
  the disk, you lose snapshots and data.
- In a cluster, schedule backups on the node hosting the instance or use
  `incus copy --refresh` to another Incus server for offsite copies.
- For CAPN/critical workloads, combine snapshots with periodic export or replication.

Official docs: [Instance backup](https://linuxcontainers.org/incus/docs/main/howto/instances_backup/),
[Server backup](https://linuxcontainers.org/incus/docs/main/backup/).
