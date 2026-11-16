# Hardware Inventory

> Hostnames follow the *Invincible* series — see
> [character category](https://invincible.fandom.com/es/wiki/Categor%C3%ADa:Personajes).
> `deborah` was previously `orangepi5plus`.

**Measured** data with [`playbook-discovery.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-discovery.yml).
Where the nominal value differs from the measured one, the *Measured*
column is the source of truth for planning.

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
  <div class="card">
    <div class="card-title"><code>eve</code> <span class="tag tag-neutral">x86_64</span></div>
    <div class="text-muted">MacBook Pro 16" 2019 · i9-9980HK 8c/16t</div>
    <div class="hr"></div>
    <div class="card-body">RAM: <span class="card-highlight">31 GB</span></div>
    <div class="card-body">Static IP: <span class="card-highlight">192.168.20.8</span></div>
    <div class="card-meta">Incus: Member (x86 group) · K3s: Worker (agent)</div>
  </div>
</div>

!!! note "Nominal vs measured specs"
    Measured on the nodes themselves with `playbook-discovery.yml` (and verified with `lscpu`, `free`, `dmidecode`, and `lsblk`); RAM is given in GiB, as reported by discovery:
    **invincible** is the M920q with i7-8700T and 15.5 GB, and **oliver** is the M700 with i3-6100T and 7.7 GB.

## IP Scheme

| Concept | invincible | oliver | deborah | eve |
|---|---|---|---|---|
| SSH IP today (`ansible_host`) | `192.168.20.6` | `192.168.20.7` | `192.168.20.5` | `192.168.20.8` |
| Static IP in `br0` | `192.168.20.6` | `192.168.20.7` | `192.168.20.5` | `192.168.20.8` |
| Physical interface → bridge | `eno2` | `eno1` | `enP4p65s0` | `enx9c69d3a4be6a` (TP-Link USB adapter) |
| Backup WiFi (`wifi_ip`) | `192.168.20.10` | — | `192.168.20.9` | `192.168.20.11` |

After `playbook-set-static-ip.yml`, update `ansible_host` in
[`inventory.ini`](https://github.com/maceosoft/homelab/blob/main/ansible/inventory.ini)
if the connection IP changed.

## Storage & I/O

| Node | Primary Disk | 4k Write (dd/fio) |
|---|---|---|
| invincible | Kingston SA400 224GB | **78.4 MB/s** |
| oliver | TECLAST 120GB SSD | 73.9 MB/s |
| deborah | eMMC `mmcblk1` 233GB (root) | 59.5 MB/s |

Test: `dd` of 40 MB in 4k blocks with direct write (`oflag=direct`). The `deborah` measurement in this
table is from the eMMC.

`deborah` also has an NVMe SK hynix BC501 256 GB (`nvme0n1`), which replaced the 250 GB WDC whose
PCIe link wouldn't come up (`rk-pcie … PCIe Link Fail`). It is formatted and mounted at `/srv/nvme` (with `nofail`) as a
Longhorn disk, but **unused until a heatsink is added**: idle it reads 71 °C (79 °C on its second sensor) and its
critical temperature is 82 °C. Copying 40 GB continuously made it stop responding and drop off the PCIe bus
(`controller is down`, `D3cold`), and it only came back after power cycling. That's why only data that can tolerate
losing the disk goes on it: the K3s database and containerd images remain on the eMMC (see
[Add a disk to a node](../operacion/agregar-disco.md)).

### Temperatures

[`ansible/scripts/temperaturas.sh`](https://github.com/maceosoft/homelab/blob/main/ansible/scripts/temperaturas.sh)
shows, per node, each temperature sensor with its name (CPU and cores, board, GPU, NVMe, battery, and on `eve`,
the Mac's SMC sensors) and marks with `!` those exceeding 75 °C (`AVISO_C`). The NVMe on `deborah` does not appear
in `hwmon` (hence it doesn't reach metrics either): the script reads it with `smartctl`.

```bash
ansible/scripts/temperaturas.sh            # todos los nodos
ansible/scripts/temperaturas.sh deborah    # uno solo
```

`deborah`'s RK3588 starts throttling above 85 °C. Due to temperature, `deborah` no longer runs Ollama:
it is the control plane and DNS.

## eve: MacBook Pro with T2 chip

`eve` is a 16" 2019 MacBook Pro (`MacBookPro16,1`) running Debian 13. It has the T2 chip (Apple security coprocessor): the internal keyboard, trackpad, Touch Bar, and audio go through it, and the Debian kernel doesn't see them. [`playbook-t2-mac.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-t2-mac.yml) installs the `linux-t2` kernel from [t2linux](https://wiki.t2linux.org/), fan control (`t2fanrd`), and gets it ready to run as a server (lid closed, no suspend, Intel GPU as primary, screen turns off when lid closes and after 5 minutes alone, boot without graphical mode, AMD GPU off, trackpad in console (`gpm`), `thermald`, and battery limited to 80% charge because it lives plugged in). Details in the [role README](https://github.com/maceosoft/homelab/blob/main/ansible/roles/t2_mac/README.md).

- **WiFi (BCM4364):** firmware only ships with macOS. Since macOS was wiped, it's downloaded once manually with `sudo get-apple-firmware` from an Apple **Sonoma** recovery image (the script recommends Monterey, Ventura, or Sonoma; Tahoe may leave incomplete files). If the download hangs, firmware from another Mac with macOS works: that's how it was done with `eve`. Steps in the [role README](https://github.com/maceosoft/homelab/blob/main/ansible/roles/t2_mac/README.md#firmware-wifi-paso-manual).
- **Touch ID:** doesn't work. Linux only uses fingerprints enrolled from macOS.
- **Network:** no Ethernet port. The `br0` runs over a USB adapter (`bridge_iface` on `inventory.ini`); when swapping adapters the interface name changes, `bridge_iface` is updated and `playbook-set-static-ip.yml` is rerun. The static IP (`192.168.20.8`) doesn't change, so Incus and K3s don't notice. WiFi stays as backup (`playbook-wifi-failover.yml`): if the cable is unplugged, `br0` goes down and you SSH into `eve-wifi` (`192.168.20.11`).
- **Current adapter:** TP-Link with ASIX AX88179B chip (`enx9c69d3a4be6a`), plugged straight into a Thunderbolt port so it runs on USB 3. Linux handles it with the generic `cdc_ncm` driver and it delivers ~940 Mb/s on `iperf3` against `oliver`, no errors. Hot-plugged, eve didn't detect it: it only appeared after a reboot. A USB 2.0 hub limits any adapter to ~300 Mb/s even if the link says 1000 Mb/s.
- **Battery:** the bash prompt starts with `[AC 80%]` (green) if on charger or `[BAT 74%]` (yellow, red below 20%) if on battery. If it says `BAT` without you unplugging it on purpose, plug it in: on battery the node shuts down when depleted.
- **Screen:** turns off when lid closes and after 5 minutes without keyboard (`consoleblank=300`); never suspends. With lid open, a key wakes it. If it stays black and a key doesn't wake it:

    1. Wake it from another machine (happens if turned off manually with `setterm --blank force`):

        ```bash
        ssh 192.168.20.8 'sudo sh -c "TERM=linux setterm --blank poke </dev/tty1 >/dev/tty1"'
        ```

    2. If still black, the console ended up on the empty device (`dummy`). Check with `cat /sys/class/vtconsole/vtcon*/name`: the one in use has `(S)` and must be `frame buffer device`. Happens if the AMD GPU (`amdgpu`) loads after the Intel one (`i915`) and steals the console; the role prevents this with `softdep i915 pre: amdgpu` in `/etc/modprobe.d/t2-mac-gpu-order.conf`. To recover without rebooting:

        ```bash
        ssh 192.168.20.8 'echo 1 | sudo tee /sys/class/vtconsole/vtcon1/bind'
        ```

## RAM budget (recalculated)

- **invincible (15.5 GB)**: K3s (lightweight Kubernetes distribution) agent + Argo CD controller + Incus leader. It's the x86 node with the most headroom and the fastest disk: supports CAPN (Cluster API Provider for Incus) management and Longhorn simultaneously.
- **oliver (7.7 GB)**: K3s agent (CoreDNS, metrics-server) + Incus in `scheduler.instance manual`. RAM constrained: that's why it stays as a light node and, by design, out of Longhorn (see [Longhorn v1](../storage/index.md#longhorn-v1-selective-ha-cross-arch)).
- **eve (31 GB)**: K3s agent + Incus member + Ollama on demand (preferred node for 7B models: it's the fastest x86). Contributes disk to Longhorn like the others, because `createDefaultDiskLabeledNodes` is on `false` (see [Longhorn](../storage/index.md)).
- **deborah (31 GB)**: K3s control plane + BIND (role `bind_dns`) + Ollama on demand (role `ollama_ondemand`, group `llm_nodes`, alongside `invincible`, `oliver`, and `eve`): only uses RAM while responding and releases it ~5 minutes after (see [Local AI Assistant](../operacion/ia-ollama.md)). Root on eMMC; has an NVMe (SSD over PCIe) of 256 GB not used yet (see [Storage & I/O](#storage-io)).

## Decision: control plane on deborah

!!! info "Moving the control plane is just an option"
    The control plane stays on `deborah`. If it ever makes sense to move it to another node (for example, to `oliver`), the
    procedure is in [Move the control plane](../operacion/mover-control-plane.md); not planned for today.

**Status:** the API (Application Programming Interface) server responds on `192.168.20.5:6443` (deborah).
Workers on invincible (`192.168.20.6`), oliver (`192.168.20.7`), and eve (`192.168.20.8`). Installed with
**K3s v1.37.2+k3s1** (`k3s_install.core.version`); then the SUC (System Upgrade Controller) updates it automatically
([Update K3s](../operacion/actualizar-k3s.md)). Actual version: `kubectl get nodes`.

<div class="card">
  <div class="card-kicker">Trade-off analysis</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">A: deborah <span class="tag tag-accent">chosen</span></div>
      <div class="text-muted">31 GB RAM, ARM64 (root on eMMC; 256 GB NVMe not used yet)</div>
      <div class="text-muted">SBC; thermal throttling; extra services on the same node</div>
    </div>
    <div class="card-col">
      <div class="card-title">B: invincible</div>
      <div class="text-muted">I/O 78.4 MB/s (best measured); 15.5 GB RAM; i7-8700T</div>
      <div class="text-muted">It is the Incus leader; CP migration costly</div>
    </div>
    <div class="card-col">
      <div class="card-title">C: oliver</div>
      <div class="text-muted">Lightweight node already reserved for quorum</div>
      <div class="text-muted">Only 7.7 GB RAM; I/O 73.9 MB/s</div>
    </div>
  </div>
</div>

**Discovery note:** measured before having NVMe, `deborah` measures the lowest I/O of the three (59.5 MB/s on eMMC) and `invincible` the highest (78.4 MB/s); the report itself suggests considering `invincible` as control plane. The decision for `deborah` stands until measuring fsync latency (`fio`), which is what matters for etcd.

!!! warning "deborah after reboot"
    If after a reboot `deborah` has the `k3s` binary but not the active service nor port `:6443`, check
    `sudo systemctl enable --now k3s` and the logs (`sudo journalctl -u k3s -n 50`).

## See also

- [Hardware discovery (Ansible)](discovery.md)
- [K3s — installation and deployment](../k3s/index.md)
