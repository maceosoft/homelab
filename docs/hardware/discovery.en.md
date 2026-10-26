# Hardware discovery (Ansible)

Playbook that scans the 3 nodes and produces one Markdown sheet per node, to
confirm (or contradict) with measured data the roles assigned in the
[Hardware inventory](inventory.md) — in particular, whether `deborah`
is still the best candidate for the K3s (lightweight Kubernetes distribution) control plane.

Code: [`ansible/playbook-discovery.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-discovery.yml)
(two plays in the same file: per-node scan + summary).

## Usage

```bash
cd ansible/
ansible-playbook -i inventory.ini playbook-discovery.yml
```

The second play (summary) reads the facts collected by the first one
from `hostvars`, which are only available in memory during the same
`ansible-playbook` invocation -- that is why they live in the same file
instead of in a separate playbook you would have to remember to pass along with the other one.

## What it collects per node

- **CPU** — architecture, model, physical/logical cores.
- **Memory** — total RAM and swap.
- **Storage** — each disk (rotational or not, size, model) +
  a 4k write benchmark (`fio`, or `dd` as a fallback) to estimate
  suitability for etcd.
- **Network** — interfaces with their negotiated speed.
- **Operating system** — distro, kernel, uptime, temperature (`vcgencmd`
  sensor on an SBC (Single Board Computer) or generic `thermal_zone0`).
- **Installed stack** — whether `/dev/kvm` is available, Incus and
  K3s versions.
- **Key packages** — version (or "no instalado") of docker, containerd,
  python3, git, qemu-img, virsh.
- **Incus instances** — name/type/state of each container or VM (virtual machine).
- **K3s** — `kubectl get nodes` and `get pods -A` (if the node has access to the
  API server).
- **Loose containers** — `crictl ps -a` / `docker ps -a`, to detect
  drift outside K3s/Incus.
- **systemd services** — active/enabled state of k3s, k3s-agent, incus,
  docker, containerd.
- **Listening ports** (`ss -tlnp`), **disk usage per filesystem**
  (`df -h`), **kernel modules** (overlay/br_netfilter/veth) and **firewall
  state** (ufw or nftables, whichever exists).

## Output

```
ansible/reports/            (gitignored -- datos de un escaneo en vivo)
├── invincible.md
├── oliver.md
├── deborah.md
└── summary.md
```

`summary.md` puts the 3 nodes side by side and lists the 4 criteria used
to decide the control plane role:

1. Lowest write latency (fsync) — the decisive factor for etcd.
2. Stable power supply (NVMe + dedicated power, not USB).
3. RAM headroom above normal cluster usage (not the
   decisive factor on its own).
4. Temperature under sustained load — thermal throttling on an SBC.

## How to read a sheet

This is a **real** excerpt of the `invincible` sheet, trimmed to the hardware
part. The full sheet also lists ports, services and containers, which is why it is not published.

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

| Field | What it means and what it is for |
|---|---|
| **Physical and logical cores** | Logical cores count threads (hyper-threading): 6 physical give 12 logical. Kubernetes and Incus schedule by logical cores. |
| **Total RAM** | Given in GB that are GiB (15834 MB ÷ 1024 = 15.5). With 0 MB of swap, if RAM runs out the kernel kills processes. |
| **Type** | `HDD (rotacional)` is a mechanical disk: much slower and unsuitable for etcd. It also tells apart `SSD`, `NVMe`, `eMMC/SD` (the memory of ARM boards), `flash SPI` and `zram` (compressed RAM, which is not a disk). There are no mechanical disks here. |
| **4k write benchmark** | Writes 40 MB in 4 KB blocks **directly to the disk**. It is for comparing nodes with each other, not an absolute figure. |

!!! warning "The benchmark is not the fsync latency"
    What matters for etcd is the **fsync latency** (how long each write takes to be confirmed), measured with
    `fio --fsync=1`. The 4k `dd` gives an idea of the order of magnitude: 59.5 MB/s on `deborah`'s eMMC versus 78.4 MB/s
    on `invincible`'s SSD. A figure very different from another run is almost always a badly done test (a cache
    in between), not a faster disk.

If any result contradicts the role assigned in the
[Hardware inventory](inventory.md), that document is the one that gets
updated — the reports in `ansible/reports/` are not versioned.
