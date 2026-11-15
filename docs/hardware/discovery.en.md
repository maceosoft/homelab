# Hardware Discovery (Ansible)

Playbook that scans all nodes and generates a Markdown sheet per node to
confirm (or contradict) with measured data the roles assigned in the
[Hardware Inventory](inventory.md) — in particular, if `deborah`
remains the best candidate for the K3s control plane (lightweight Kubernetes distribution).

Code: [`ansible/playbook-discovery.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-discovery.yml)
(two plays in a single file: node scan + consolidation).

## Usage

```bash
cd ansible/
ansible-playbook -i inventory.ini playbook-discovery.yml
```

The second play (consolidation) reads the facts collected by the first
from `hostvars`, which are only available in memory during the same
invocation of `ansible-playbook` -- that's why they live in the same file instead of
in a separate playbook that would have to be remembered to pass along with the other.

## What it collects per node

- **CPU** — architecture, model, physical/logical cores.
- **Memory** — total RAM and swap.
- **Storage** — each disk (rotational or not, size, model) +
  4k write benchmark (`fio`, or `dd` as fallback) to estimate
  suitability for etcd.
- **Network** — interfaces with negotiated speed.
- **Operating System** — distro, kernel, uptime, temperature (sensor
  `vcgencmd` on SBC (Single Board Computer) or `thermal_zone0` generic).
- **Installed Stack** — if `/dev/kvm` is available, Incus and K3s versions.
- **Key Packages** — version (or "not installed") of docker, containerd,
  python3, git, qemu-img, virsh.
- **Incus Instances** — name/type/status of each container or VM (virtual machine).
- **K3s** — `kubectl get nodes` and `get pods -A` (if the node has access to the
  API server).
- **Orphan Containers** — `crictl ps -a` / `docker ps -a`, to detect drift outside of K3s/Incus.
- **Systemd Services** — active/enabled status of k3s, k3s-agent, incus,
  docker, containerd.
- **Listening Ports** (`ss -tlnp`), **disk usage by filesystem**
  (`df -h`), **kernel modules** (overlay/br_netfilter/veth) and **firewall status**
  (ufw or nftables, whichever exists).

## Output

```
ansible/reports/            (gitignored -- datos de un escaneo en vivo)
├── invincible.md
├── oliver.md
├── deborah.md
├── eve.md
└── summary.md
```

`summary.md` puts all nodes side by side and lists the 4 criteria used
to decide the control plane role:

1. Lowest write latency (fsync) — the decisive factor for etcd.
2. Stable power supply (NVMe + dedicated power, not USB).
3. RAM margin above normal cluster usage (not a decisive factor on its own).
4. Temperature under sustained load — thermal throttling on an SBC.

## How to read a sheet

This is a **real** excerpt from the sheet of `invincible`, trimmed to just
hardware. The full sheet also lists ports, services, and containers, and is not published.

```text
## CPU
Arquitectura     x86_64
Modelo           Intel(R) Core(TM) i7-8700T CPU @ 2.40GHz
Núcleos físicos  6          Núcleos lógicos  12

## Memoria
RAM total        15.5 GB (15834 MB)          Swap total  0 MB

## Almacenamiento
sda   SSD   223.6GB   KINGSTON SA400S3   En uso
Benchmark I/O (escritura 4k): 40960000 bytes (41 MB) copied, 0.52 s, 78.4 MB/s
```

| Field | What it means and what it's for |
|---|---|
| **Physical and Logical Cores** | Logical cores count threads (hyper-threading): 6 physical cores give 12 logical cores. Kubernetes and Incus schedule by logical cores. |
| **Total RAM** | Given in GB which are GiB (15834 MB ÷ 1024 = 15.5). With 0 MB of swap, if RAM runs out the kernel kills processes. |
| **Type** | `HDD (rotacional)` is a mechanical disk: much slower and not suitable for etcd. Also distinguishes `SSD`, `NVMe`, `eMMC/SD` (memory on ARM boards), `flash SPI` and `zram` (compressed RAM, which is not a disk). Here there are no mechanical disks. |
| **4k Write Benchmark** | Writes 40 MB in 4 KB blocks **directly to disk**. Useful for comparing nodes, not as an absolute figure. |

!!! warning "The benchmark is not fsync latency"
    For etcd what matters is the **fsync latency** (how long it takes to confirm each write), which is measured with
    `fio --fsync=1`. The `dd` of 4k gives an idea of the order of magnitude: 59.5 MB/s on the eMMC of `deborah` versus 78.4 MB/s
    on the SSD of `invincible`. A very different figure from another run is usually a poorly conducted test (cache in the middle), not a faster disk.

If any result contradicts the role assigned in
[Hardware Inventory](inventory.md), that document is the one that gets
updated — the reports of `ansible/reports/` are not versioned.
