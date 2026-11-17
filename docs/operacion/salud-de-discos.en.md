# Disk and DNS Health

What is monitored on node hardware that previously had no alerts, and what to do when each one fires. Notifications arrive via Discord just like the other monitoring alerts.

| What | Where | How it is read |
|---|---|---|
| SMART (Self-Monitoring, Analysis and Reporting Technology) self-test, bad sectors, temperature, and remaining life of SSDs | `invincible`, `oliver` (SATA SSD, Serial ATA) | `smartctl` (`smartmontools` package) |
| Same on NVMe (PCIe SSD), plus all its temperature sensors, the thresholds declared by the drive itself, its critical warning, and data errors | `deborah` (SK hynix BC501) | `smartctl` (NVMe health log) |
| Temperature of Apple NVMe (behind T2 chip, `smartctl` does not read it) | `eve` | Kernel hwmon (`/sys/class/nvme/nvme0/hwmon*`) |
| Wear and end-of-life warning of eMMC (embedded MultiMediaCard) | `deborah` | `/sys/block/mmcblk*/device/` files |
| BIND (Berkeley Internet Name Domain, the LAN DNS) up and responding | `deborah` | One test query per minute |

The eMMC on `deborah` **has no SMART**: `smartctl` replies "Unable to detect device type". What the controller does do is track its wear, and the kernel exposes it in `life_time` and `pre_eol_info`. These are standard JEDEC (Joint Electron Device Engineering Council) fields, so they apply to any eMMC.

## How Metrics Are Collected

On each node, a systemd timer runs a script that writes a `.prom` file to `/var/lib/node_exporter/textfile`. node-exporter reads it with its *textfile collector* and VictoriaMetrics stores it. It is **read-only**: nothing is written to the disks, no SMART self-tests are launched, and BIND is not touched. The SMART self-test is run manually, with Ansible (see [SMART Self-Test](#smart-self-test)).

| Component | Where |
|---|---|
| Disk roles | [`ansible/roles/node_smart_metrics`](https://github.com/maceosoft/homelab/tree/main/ansible/roles/node_smart_metrics) and [`playbook-smart-metrics.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-smart-metrics.yml) |
| BIND role | [`ansible/roles/node_bind_metrics`](https://github.com/maceosoft/homelab/tree/main/ansible/roles/node_bind_metrics) and [`playbook-bind-metrics.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-bind-metrics.yml) |
| Alerts | [`gitops/addons/monitoring/config/rules/homelab-hardware.yaml`](https://github.com/maceosoft/gitops/blob/main/addons/monitoring/config/rules/homelab-hardware.yaml) |
| Alert tests | [`gitops/addons/monitoring/tests/rules-test.yaml`](https://github.com/maceosoft/gitops/blob/main/addons/monitoring/tests/rules-test.yaml) |

!!! note "Requirement: textfile collector"
    node-exporter must mount `/var/lib/node_exporter/textfile` (configured in [`gitops/addons/monitoring/values/values-vm-stack.yaml`](https://github.com/maceosoft/gitops/blob/main/addons/monitoring/values/values-vm-stack.yaml)).
    Without that the files are written but nobody reads them, and after 24 h `SinDatosDeDiscos` fires.

### Why a Script and Not `smartctl_exporter`

`prometheus-smartctl-exporter` is not packaged in Debian 13: you would have to maintain a separate binary or image, and in Kubernetes it would run as a privileged DaemonSet with access to `/dev`. Besides, it would not cover the eMMC, which is the node's most important disk. The script uses only `smartctl` (Debian package) and `/sys`, runs as `root` for a few seconds every 30 minutes, and node-exporter needs no privileges.

### Why a Probe and Not `bind_exporter`

BIND does not have `statistics-channels` enabled, so `prometheus-bind-exporter` would have nothing to read. Enabling it means editing BIND's configuration and restarting it, and the entire LAN DNS depends on that restart. To know if DNS works it is enough to **ask it**: the probe resolves a custom name (`deborah.mco.local`) every minute.

## Alerts and What to Do

**Imminent failure** alerts (`critical`) require action the same day; `warning` require planning.

### SATA Disks (SSD)

| Alert | When it fires | What to do |
|---|---|---|
| `DiscoSmartFalla` (critical) | SMART self-test says FAILED for 5 min | The drive predicts it will fail. Verify backups, copy data, and replace it. Detail: `sudo smartctl -a /dev/sdX` |
| `DiscoAtributoSmartEnFallo` | A SMART attribute is below its threshold (`FAILING_NOW`) for 1 h | Check which one with `sudo smartctl -A /dev/sdX`; almost always precedes `DiscoSmartFalla` |
| `DiscoSectoresInestables` | Pending or uncorrectable sectors greater than 0 for 1 h | The drive cannot reliably read some areas. Verify backups and plan replacement |
| `DiscoSectoresReasignadosCreciendo` | Reallocated sectors increased over the last 3 days | A static value is not a problem; growth is. Plan replacement and watch the trend |
| `SsdVidaBaja` | Remaining life below 20 % for 1 h | Buy the replacement before it hits 0 |
| `DiscoTemperaturaAlta` | A SATA SSD at 60 °C or higher for 15 min | Typical SATA SSD max is 70 °C. Check node ventilation and dust |

### NVMe

NVMe (PCIe SSDs) run hotter than SATA, so they have their own alerts and the hottest sensor is watched (the one on `deborah` has three: composite temperature and two sensors). On 8 Nov 2026 the NVMe on `deborah`, without a heatsink, dropped off the PCIe bus under sustained writes ([Add a Disk](agregar-disco.md#move-data-to-another-disk)).

| Alert | When it fires | What to do |
|---|---|---|
| `NvmeTemperaturaAlta` | Hottest sensor at 75 °C or higher for 10 min | Drain writes (evict its Longhorn disk) and check heatsink or ventilation. `ansible/scripts/temperaturas.sh <nodo>` shows all sensors |
| `NvmeTemperaturaCritica` (critical) | Within 3 °C of the critical threshold declared by the drive (79 °C on `deborah`), or 80 °C if undeclared, for 2 min | Stop writes now: near that point the drive throttles or drops off the bus |
| `NvmeAvisoCritico` (critical) | Drive publishes a critical warning (`Critical Warning` not equal to 0) | `sudo smartctl -a /dev/nvme0` tells which one (spare low, temperature, reliability, read-only). Back up data |
| `NvmeErroresDeDatos` | Uncorrectable data errors appear or grow over 3 days | The drive is degrading: verify backups and plan replacement |
| `DiscoDesaparecido` (critical) | A drive seen in the last 24 h no longer appears, with the node alive | If it is an NVMe, it almost certainly dropped off the bus: `dmesg` on the node; only comes back after power cycle |

### `deborah` eMMC

The `life_time` field has two areas (A and B) and the value rises from 1 to 11 based on wear:

| Value | Meaning |
|---|---|
| 1 to 10 | Between 0-10% and 90-100% of estimated life used (each step, 10%) |
| 11 | Exceeded estimated life |

And `pre_eol_info` (end-of-life warning, EOL) is 1 if normal, 2 if 80% of spare blocks consumed, and 3 if 90% consumed.

| Alert | When it triggers | What to do |
|---|---|---|
| `EmmcDesgastada` (warning) | Level 9 or higher (more than 80% used) for 1 h | Back up (the K3s control plane lives there) and plan replacement |
| `EmmcDesgastada` (critical) | Level 11: exceeded estimated life | May fail at any moment: back up now and replace it |
| `EmmcFinDeVida` (warning) | `pre_eol_info` = 2 | Plan backup and replacement |
| `EmmcFinDeVida` (critical) | `pre_eol_info` = 3 | Back up now and replace it |

To view values manually: `cat /sys/block/mmcblk1/device/life_time /sys/block/mmcblk1/device/pre_eol_info`.

!!! tip "How to reduce eMMC wear"
    This is the usual cause of reaching end of life prematurely: many small writes (logs, etcd, K3s database). If the level rises quickly, move those workloads to another disk.

### Don't lose monitoring

| Alert | When it triggers | What to do |
|---|---|---|
| `DiscoSmartNoLegible` | `smartctl` cannot read a disk's SMART status for 2 h | Try `sudo smartctl -a /dev/sdX`. SMART may be off (`smartctl -s on`), `smartmontools` may be missing, or the disk may not respond |
| `DatosDeDiscosViejos` | The metrics file hasn't been updated for more than 2 h | `systemctl status node-smart-metrics.timer node-smart-metrics.service` and `journalctl -u node-smart-metrics` |
| `SinDatosDeDiscos` | node-exporter responds but no disk metrics for 1 day | `playbook-smart-metrics.yml` not applied on that node, or node-exporter isn't mounting the textfile collector folder |

### BIND (DNS)

| Alert | When it triggers | What to do |
|---|---|---|
| `BindCaido` (critical) | `named` not active for 2 min | On `deborah`: `systemctl status named` and `journalctl -u named -e`. Check syntax with `named-checkconf` before restarting. Without DNS, internal LAN names don't resolve |
| `DnsSinRespuesta` (critical) | `named` is active but test query fails or errors for 3 min | `dig @<IP del DNS> deborah.mco.local`. Check `rndc status`, disk space, and `named` logs |
| `DnsLento` | Query takes longer than 0.5 s for 10 min | Normally takes milliseconds. Check node load and forwarders |
| `MetricasDeBindViejas` | Probe hasn't run for more than 10 min | `systemctl status node-bind-metrics.timer`. Meanwhile, DNS responsiveness is unknown |
| `SinDatosDeBind` | `deborah` node-exporter doesn't publish the probe for 1 h | `playbook-bind-metrics.yml` not applied, or textfile collector not mounted |

!!! note "What the local probe doesn't cover"
    Runs on the `deborah` itself: alerts if BIND goes down or doesn't answer, but not if the network between pods and DNS fails. That's what an external probe is for (blackbox-exporter's `dns` module pointing at the LAN DNS).

## Apply the playbooks

From the `ansible/` folder of the `homelab` repo, and **after** `gitops` mounts the textfile collector:

```bash
ansible-playbook -i inventory.ini playbook-smart-metrics.yml --check --diff
ansible-playbook -i inventory.ini playbook-smart-metrics.yml
ansible-playbook -i inventory.ini playbook-bind-metrics.yml --check --diff
ansible-playbook -i inventory.ini playbook-bind-metrics.yml
```

They install `smartmontools` only where there are SATA or NVMe disks (`invincible`, `oliver`, and `deborah`; on `eve` it's disabled in `host_vars` because its Apple SSD is read via hwmon), create the folder and timers, and don't restart anything. Verify on each node with `cat /var/lib/node_exporter/textfile/smart.prom` (or `bind.prom` on `deborah`).

!!! warning "SSD remaining life"
    Each manufacturer publishes wear in a different SMART attribute. After the first run, check that `node_smart_ssd_life_remaining_percent` exists in `smart.prom`; if missing, that model uses another attribute and the script's filter must be adjusted (see the role's README). While it's missing, `SsdVidaBaja` cannot alert.

## SMART self-test

A self-test asks the disk to scan its surface and electronics. It doesn't erase or write data: the disk does it in the background and the node keeps working (may run a bit slower while it lasts). Useful to confirm an alert like `DiscoSectoresInestables` or to check a disk occasionally. Only applies to SATA SSDs (`invincible`, `oliver`); the `deborah` eMMC has no SMART.

From `ansible/`, the simulation shows which disks would be targeted; the second command launches it:

```bash
ansible-playbook -i inventory.ini playbook-smart-metrics.yml --tags smart_selftest --check
ansible-playbook -i inventory.ini playbook-smart-metrics.yml --tags smart_selftest
```

The output says how many minutes it takes (a long SSD self-test usually takes minutes to an hour). After that time:

```bash
ansible-playbook -i inventory.ini playbook-smart-metrics.yml --tags smart_selftest_result
```

These tasks don't run in a normal playbook run. For another disk or a short self-test: `-e '{"node_smart_metrics_selftest_devices": ["sda"], "node_smart_metrics_selftest_type": "short"}'`.

### How to read the result

In `autotests` the disk's log appears, most recent first (`# 1`):

| `Status` | Meaning |
|---|---|
| `Completed without error` | Disk found no problems |
| `Self-test routine in progress` | Not finished yet: read again later |
| `Aborted by host` or `Interrupted` | Interrupted (reboot or power-off); run again |
| `Completed: read failure` (or other `failure`) | Unreadable areas; the `LBA_of_first_error` column says where. Back up and plan replacement |

In `atributos` four counters are shown; look at the last column (`RAW_VALUE`):

| ID | Attribute | Indicates |
|---|---|---|
| 5 | `Reallocated_Sector_Ct` | Sectors the disk has already replaced from spare pool |
| 187 | `Reported_Uncorrect` | Errors the disk couldn't correct |
| 197 | `Current_Pending_Sector` | Suspect sectors, pending reallocation |
| 198 | `Offline_Uncorrectable` | Sectors unreadable during disk's internal scans |

Normal is 0 in all four. A fixed non-zero value isn't urgent, but an increase between two readings is: back up and plan replacement, as with the SATA disk alert table.
