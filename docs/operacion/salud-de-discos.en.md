# Disk and DNS Health

What is monitored on the hardware of nodes that previously had no alerts, and what to do when each one triggers. The notifications
come through Discord just like the rest of the monitoring.

| What | Where | How to Read |
|---|---|---|
| Self-Monitoring, Analysis and Reporting Technology (SMART) diagnostics, damaged sectors, temperature, and remaining life of SSDs | `invincible`, `oliver` (SSD SATA, Serial ATA) | `smartctl` (package `smartmontools`) |
| Wear and end-of-life warning for the eMMC (embedded MultiMediaCard) | `deborah` | Files in `/sys/block/mmcblk*/device/` |
| Active and responding BIND (Berkeley Internet Name Domain, LAN DNS) | `deborah` | A test query every minute |

The eMMC of `deborah` **does not have SMART**: `smartctl` responds with "Unable to detect device type". What the driver
does do is keep track of its wear, and the kernel publishes it in `life_time` and `pre_eol_info`. These are JEDEC (Joint Electron Device Engineering Council) standard fields, so they apply to any eMMC.

## How Metrics Are Collected

On each node, a systemd timer runs a script that writes a file `.prom` in
`/var/lib/node_exporter/textfile`. node-exporter reads it with its *textfile collector* and VictoriaMetrics stores it. It is only
**read**: no data is written to disks, no SMART autotests are launched, and BIND is not touched. The SMART autotest is launched
manually, with Ansible (see [SMART Autotest](#autotest-smart)).

| Component | Where |
|---|---|
| Disk role | [`ansible/roles/node_smart_metrics`](https://github.com/maceosoft/homelab/tree/main/ansible/roles/node_smart_metrics) and [`playbook-smart-metrics.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-smart-metrics.yml) |
| BIND role | [`ansible/roles/node_bind_metrics`](https://github.com/maceosoft/homelab/tree/main/ansible/roles/node_bind_metrics) and [`playbook-bind-metrics.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-bind-metrics.yml) |
| Alerts | [`gitops/monitoring/config/rules/homelab-hardware.yaml`](https://github.com/maceosoft/gitops/blob/main/monitoring/config/rules/homelab-hardware.yaml) |
| Alert tests | [`gitops/monitoring/tests/rules-test.yaml`](https://github.com/maceosoft/gitops/blob/main/monitoring/tests/rules-test.yaml) |

!!! note "Requirement: textfile collector"
    node-exporter must mount `/var/lib/node_exporter/textfile` (configuration in
    [`gitops/monitoring/values-vm-stack.yaml`](https://github.com/maceosoft/gitops/blob/main/monitoring/values-vm-stack.yaml)).
    Without this, the files are written but no one reads them, and after 24 hours `SinDatosDeDiscos` triggers.

### Why a Script and Not `smartctl_exporter`

`prometheus-smartctl-exporter` is not packaged in Debian 13: it would require maintaining a separate binary or image, and in
Kubernetes it would run as a privileged DaemonSet with access to `/dev`. Additionally, it would not cover the eMMC, which is the most important node disk. The script uses only `smartctl` (Debian package) and `/sys`, runs as `root` for a few seconds every 30
minutes, and node-exporter does not need elevated privileges.

### Why a Probe and Not `bind_exporter`

BIND does not have `statistics-channels` enabled, so `prometheus-bind-exporter` would have nothing to read. Enabling it would require
editing BIND's configuration and restarting it, and the LAN DNS depends on that restart. To check if DNS is working, it is
enough to **ask it**: the probe resolves a specific name (`deborah.mco.local`) every minute.

## Alerts and What to Do

**Imminent failure** alerts (`critical`) require action the same day; **warnings** (`warning`) require planning.

### SATA SSDs

| Alert | When It Triggers | What to Do |
|---|---|---|
| `DiscoSmartFalla` (critical) | The SMART diagnostics report FAILED for 5 minutes | The disk predicts it will fail. Verify backups, copy data, and replace it. Details: `sudo smartctl -a /dev/sdX` |
| `DiscoAtributoSmartEnFallo` | A SMART attribute is below its threshold (`FAILING_NOW`) for 1 hour | Check which one with `sudo smartctl -A /dev/sdX`; it usually precedes `DiscoSmartFalla` |
| `DiscoSectoresInestables` | Unrecoverable or pending sectors greater than 0 for 1 hour | The disk cannot reliably read some areas. Check backups and plan replacement |
| `DiscoSectoresReasignadosCreciendo` | Reallocated sectors increased in the last 3 days | A fixed value is not a problem; an increase is. Plan replacement and monitor the trend |
| `SsdVidaBaja` | Remaining life less than 20% for 1 hour | Buy a replacement before it reaches 0 |
| `DiscoTemperaturaAlta` | 60 °C or higher for 15 minutes | The typical maximum for a SATA SSD is 70 °C. Check ventilation and dust on the node |

### eMMC of `deborah`

The field `life_time` has two areas (A and B) and the value ranges from 1 to 11 based on wear:

| Value | Meaning |
|---|---|
| 1 to 10 | Between 0-10% and 90-100% of estimated life used (each step is 10%) |
| 11 | Exceeded estimated life |

And `pre_eol_info` (end-of-life warning, EOL) is 1 if normal, 2 if 80% of the reserved blocks are used, and 3 if 90% are used.

| Alert | When It Triggers | What to Do |
|---|---|---|
| `EmmcDesgastada` (warning) | Level 9 or higher (more than 80% used) for 1 hour | Back up (K3s control plane lives there) and plan replacement |
| `EmmcDesgastada` (critical) | Level 11: exceeded estimated life | It may fail at any moment: back up immediately and replace it |
| `EmmcFinDeVida` (warning) | `pre_eol_info` = 2 | Plan backup and replacement |
| `EmmcFinDeVida` (critical) | `pre_eol_info` = 3 | Back up immediately and replace it |

To check the values manually: `cat /sys/block/mmcblk1/device/life_time /sys/block/mmcblk1/device/pre_eol_info`.

!!! tip "How to Reduce eMMC Wear"
    This is the usual cause of reaching end-of-life prematurely: many small writes (logs, etcd, K3s database). If the level rises quickly, move those loads to another disk.

### Do Not Lose Monitoring

| Alert | When It Triggers | What to Do |
|---|---|---|
| `DiscoSmartNoLegible` | `smartctl` cannot read the SMART status of a disk for 2 hours | Test `sudo smartctl -a /dev/sdX`. SMART may be off (`smartctl -s on`), the file may be missing (`smartmontools`), or the disk may not respond |
| `DatosDeDiscosViejos` | The metrics file has not been updated for more than 2 hours | `systemctl status node-smart-metrics.timer node-smart-metrics.service` and `journalctl -u node-smart-metrics` |
| `SinDatosDeDiscos` | node-exporter responds but there are no disk metrics for 1 day | The role `playbook-smart-metrics.yml` is missing on that node, or node-exporter does not mount the textfile collector directory |

### BIND (DNS)

| Alert | When triggered | What to do |
|---|---|---|
| `BindCaido` (critical) | `named` is not active for 2 min | In `deborah`: `systemctl status named` and `journalctl -u named -e`. Check syntax with `named-checkconf` before restarting. Without DNS, internal LAN names won't resolve |
| `DnsSinRespuesta` (critical) | `named` is active but the test query fails or errors for 3 min | `dig @<IP del DNS> deborah.mco.local`. Check `rndc status`, disk space, and `named` logs |
| `DnsLento` | The query takes more than 0.5 s for 10 min | Normally takes milliseconds. Check node load and forwarders (*forwarders*) |
| `MetricasDeBindViejas` | The probe has not run for more than 10 min | `systemctl status node-bind-metrics.timer`. Until then, it's unknown if DNS is responding |
| `SinDatosDeBind` | node-exporter of `deborah` does not publish the probe for 1 h | Missing `playbook-bind-metrics.yml` or the textfile collector is not mounted |

!!! note "What it does not cover"
    Runs locally on the `deborah`: warns if BIND falls or does not respond, but not if the network between pods and DNS fails. For that, an external probe (blackbox-exporter module `dns` pointing to the LAN DNS) is needed.

## Apply the playbooks

From the `ansible/` folder of the `homelab` repo, and **after** `gitops` mounts the textfile collector:

```bash
ansible-playbook -i inventory.ini playbook-smart-metrics.yml --check --diff
ansible-playbook -i inventory.ini playbook-smart-metrics.yml
ansible-playbook -i inventory.ini playbook-bind-metrics.yml --check --diff
ansible-playbook -i inventory.ini playbook-bind-metrics.yml
```

Installs `smartmontools` only where SATA disks are present (`invincible` and `oliver`), creates the directory and timers, and does not restart anything. Verify on each node with `cat /var/lib/node_exporter/textfile/smart.prom` (or `bind.prom` in `deborah`).

!!! warning "Remaining SSD life"
    Each manufacturer publishes wear in a different SMART attribute. After the first run, check that `node_smart_ssd_life_remaining_percent` exists in `smart.prom`; if it's missing, that model uses another attribute and the script filter needs adjustment (see the role's README). Until it's fixed, `SsdVidaBaja` cannot warn.

## Autotest SMART

An autotest asks the disk itself to check its surface and electronics. It does not erase or write data: the disk does it in the background while the node continues to operate (it may slow down during the test). It confirms a warning like `DiscoSectoresInestables` or checks a disk occasionally. Only applies to SATA SSDs (`invincible`, `oliver`); the eMMC of `deborah` does not have SMART.

From `ansible/`, the simulation shows which disks would be tested; the second command runs it:

```bash
ansible-playbook -i inventory.ini playbook-smart-metrics.yml --tags smart_selftest --check
ansible-playbook -i inventory.ini playbook-smart-metrics.yml --tags smart_selftest
```

The output shows how many minutes it takes (a long SMART test on an SSD usually takes from minutes to an hour). After that time:

```bash
ansible-playbook -i inventory.ini playbook-smart-metrics.yml --tags smart_selftest_result
```

These tasks do not run in a normal playbook execution. For another disk or a short autotest:
`-e '{"node_smart_metrics_selftest_devices": ["sda"], "node_smart_metrics_selftest_type": "short"}'`.

### How to read the result

In `autotests`, the disk log appears, most recent first (`# 1`):

| `Status` | What it means |
|---|---|
| `Completed without error` | The disk did not find any issues |
| `Self-test routine in progress` | Still running: check it later |
| `Aborted by host` or `Interrupted` | Interrupted (reboot or shutdown); run it again |
| `Completed: read failure` (or another `failure`) | There are unreadable sectors; the column `LBA_of_first_error` shows where. Backup and plan replacement |

In `atributos`, four counters are shown; look at the last column (`RAW_VALUE`):

| ID | Attribute | What it indicates |
|---|---|---|
| 5 | `Reallocated_Sector_Ct` | Sectors the disk has already replaced with reserve |
| 187 | `Reported_Uncorrect` | Errors the disk could not correct |
| 197 | `Current_Pending_Sector` | Suspect sectors, pending reassignment |
| 198 | `Offline_Uncorrectable` | Sectors that could not be read during disk checks |

Normal is 0 in all four. A fixed value different from 0 is not urgent, but an increase between readings is: backup and plan replacement, as with the SATA disk alerts.
