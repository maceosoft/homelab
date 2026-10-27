# Hardware Inventory

> The hostnames follow the *Invincible* series — see
> [character category](https://invincible.fandom.com/es/wiki/Categor%C3%ADa:Personajes).
> `deborah` was previously `orangepi5plus`.

Data **measured** with [`playbook-discovery.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-discovery.yml).
Where the nominal value differs from the measured, the *Measured* column is the source of truth for planning.

<div class="option-grid">
  <div class="card">
    <div class="card-title"><code>invincible</code> <span class="tag tag-neutral">x86_64</span></div>
    <div class="text-muted">Lenovo M920q · i7-8700T 6c/12t</div>
    <div class="hr"></div>
    <div class="card-body">RAM: <span class="card-highlight">15.5 GB</span></div>
    <div class="card-body">Static IP: <span class="card-highlight">192.168.20.6</span></div>
    <div class="card-meta">Incus: leader · K3s: Worker (agent)</div>
  </div>
  <div class="card">
    <div class="card-title"><code>oliver</code> <span class="tag tag-neutral">x86_64</span></div>
    <div class="text-muted">Lenovo M700 · i3-6100T 2c/4t</div>
    <div class="hr"></div>
    <div class="card-body">RAM: <span class="card-highlight">7.7 GB</span></div>
    <div class="card-body">Static IP: <span class="card-highlight">192.168.20.7</span></div>
    <div class="card-meta">Incus: Member (manual scheduler) · K3s: Worker (agent)</div>
  </div>
  <div class="card">
    <div class="card-title"><code>deborah</code> <span class="tag tag-accent">ARM64</span></div>
    <div class="text-muted">Orange Pi 5 Plus · RK3588 8c</div>
    <div class="hr"></div>
    <div class="card-body">RAM: <span class="card-highlight">31.0 GB</span></div>
    <div class="card-body">Static IP: <span class="card-highlight">192.168.20.5</span></div>
    <div class="card-meta">Incus: Member (arm64 group) · K3s: Control-plane (server)</div>
  </div>
</div>

!!! note "Nominal specs vs measured"
    Measured on the nodes themselves with `playbook-discovery.yml` (and verified with `lscpu`, `free`, `dmidecode`, and `lsblk`); RAM is given in GiB, as reported by discovery:
    **invincible** is the M920q with i7-8700T and 15.5 GB, and **oliver** is the M700 with i3-6100T and 7.7 GB.

## IP Scheme

| Concept | invincible | oliver | deborah |
|---|---|---|---|
| SSH IP today (`ansible_host`) | `192.168.20.6` | `192.168.20.7` | `192.168.20.5` |
| Static IP in `br0` | `192.168.20.6` | `192.168.20.7` | `192.168.20.5` |
| Physical interface → bridge | `eno2` | `eno1` | `enP4p65s0` |

After `playbook-set-static-ip.yml`, update `ansible_host` in
[`inventory.ini`](https://github.com/maceosoft/homelab/blob/main/ansible/inventory.ini)
if the connection IP changed.

## Storage and I/O

| Node | Main Disk | 4k Write (dd/fio) |
|---|---|---|
| invincible | Kingston SA400 224GB | **78.4 MB/s** |
| oliver | TECLAST 120GB SSD | 73.9 MB/s |
| deborah | eMMC `mmcblk1` 233GB (root) | 59.5 MB/s |

Test: `dd` of 40 MB in 4k blocks with direct write (`oflag=direct`). The NVMe WDC 250GB (`nvme0n1`) of `deborah` **is not detected**: `lsblk` and `lspci` do not see it and `dmesg` says `rk-pcie … PCIe Link Fail` (the slot link does not come up).

## RAM Budget (recalculated)

- **invincible (15.5 GB)**: K3s (lightweight Kubernetes distribution) agent + Argo CD controller + Incus leader. It is the x86 node with the most margin and the fastest disk: it supports CAPN (Cluster API Provider for Incus) management and Longhorn simultaneously.
- **oliver (7.7 GB)**: K3s agent (CoreDNS, metrics-server) + Incus in `scheduler.instance manual`. RAM adjusted: that's why it remains a light node and, in the design, outside of Longhorn (see [Longhorn v1](../storage/index.md#longhorn-v1-selective-ha-cross-arch)).
- **deborah (31 GB)**: K3s control plane + BIND (role `bind_dns`) + Ollama on demand (role `ollama_ondemand`, group `llm_nodes`, alongside `invincible` and `oliver`): it only uses RAM while responding and releases it about 5 minutes later (see [Local AI Assistant](../operacion/ia-ollama.md)). Root on eMMC; the NVMe (SSD via PCIe) is not detected (see [Storage and I/O](#storage-and-io)).

## Decision: control plane on deborah

!!! info "Moving the control plane is only an option"
    The control plane stays on `deborah`. If it ever makes sense to move it to another node (for example, to `oliver`),
    the procedure is in [Moving the control plane](../operacion/mover-control-plane.md); it is not planned today.

**Status:** the API server responds on `192.168.20.5:6443` (deborah).
Workers on invincible (`192.168.20.6`) and oliver (`192.168.20.7`). Installed with
**K3s v1.36.5+k3s1** (`k3s_install.core.version`); afterwards the SUC (System Upgrade Controller) updates it automatically
([Updating K3s](../operacion/actualizar-k3s.md)). Actual version: `kubectl get nodes`.

<div class="card">
  <div class="card-kicker">Trade-off Analysis</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">A: deborah <span class="tag tag-accent">chosen</span></div>
      <div class="text-muted">31 GB RAM, ARM64 (root on eMMC; NVMe not detected)</div>
      <div class="text-muted">SBC; thermal throttling; extra services on the same node</div>
    </div>
    <div class="card-col">
      <div class="card-title">B: invincible</div>
      <div class="text-muted">I/O 78.4 MB/s (the best measured); 15.5 GB RAM; i7-8700T</div>
      <div class="text-muted">It is the Incus leader; costly control plane migration</div>
    </div>
    <div class="card-col">
      <div class="card-title">C: oliver</div>
      <div class="text-muted">Node already reserved for quorum</div>
      <div class="text-muted">Only 7.7 GB RAM; I/O 73.9 MB/s</div>
    </div>
  </div>
</div>

**Discovery note:** without NVMe, `deborah` measures the lowest I/O (59.5 MB/s on eMMC) and `invincible` the highest (78.4 MB/s); the report itself suggests considering `invincible` as the control plane. The decision to keep `deborah` is maintained until fsync latency (`fio`) is measured, which is what matters for etcd.

!!! warning "deborah after reboot"
    If after a reboot `deborah` has the `k3s` binary but no active service or port `:6443`, check
    `sudo systemctl enable --now k3s` and the logs (`sudo journalctl -u k3s -n 50`).

## See also

- [Hardware discovery (Ansible)](discovery.md)
- [K3s — installation and deployment](../k3s/index.md)
