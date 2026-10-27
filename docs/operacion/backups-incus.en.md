# Backups and snapshots in Incus

How to back up Incus instances (containers and VMs) and how to restore them.
There are three levels, from fastest to safest:

| Level | What it protects | Where it stays | Works if the disk is lost |
|---|---|---|---|
| **Snapshot** | An instance, to roll back | In the same storage pool | No |
| **Export** | A complete instance, restorable on another node | A file `.tar.gz` | Yes, if you save it outside the node |
| **Database dump** | Incus cluster configuration (networks, profiles) | Files `.sql` | Yes, if you save it outside the node |

The commands go on the node hosting the instance, with `sudo`.

**This decision in other environments**

=== "🏠 At home"

    Scheduled Incus snapshots for quick rollbacks, and `incus export` to a file that you copy outside the node.
    No licenses or backup server: enough for a few instances, as long as you test restoring.

=== "🏢 In a company"

    - **Benefits:** a centralized backup system schedules, encrypts, and verifies copies of all machines,
      alerts if a failure occurs, and allows restoring a VM or a single file without depending on who created it.
    - **Rule 3-2-1:** three copies of the data, on two different media and one off-site; many companies add
      an immutable or disconnected copy against ransomware.
    - **RPO and RTO defined:** how much data can be lost (RPO) and how quickly recovery must occur (RTO) for each
      system; from there comes how often backups are made and restoration is tested, with evidence for auditing.
    - **Products with support:** [Veeam Backup & Replication](https://www.veeam.com/products/veeam-data-platform/backup-recovery.html)
      for VMs on supported hypervisors, and for Kubernetes
      [Veeam Kasten](https://www.veeam.com/products/cloud/kubernetes-data-protection.html) or
      [Velero](https://velero.io/) (open source). Incus does not integrate with these products, so backups are made
      with its own commands or by files.
    - **When the same applies:** in small or disconnected sites, with few instances, where a script with
      snapshots and exports to another disk covers the requested RPO.

=== "☁️ In the cloud"

    | Cloud | Equivalent service |
    |---|---|
    | GCP | [Backup and DR Service](https://cloud.google.com/backup-disaster-recovery) (VMs) and [Backup for GKE](https://docs.cloud.google.com/kubernetes-engine/docs/add-on/backup-for-gke/concepts/backup-for-gke) |
    | AWS | [AWS Backup](https://aws.amazon.com/backup/) (EC2, EBS, EKS, and more) |
    | Azure | [Azure Backup](https://learn.microsoft.com/en-us/azure/backup/backup-overview) (VMs, disks, and AKS) |
    | Oracle Cloud (OCI) | [Block Volume Backups](https://docs.oracle.com/en-us/iaas/Content/Block/Concepts/blockvolumebackups.htm), with [scheduled policies](https://docs.oracle.com/en-us/iaas/Content/Block/Tasks/schedulingvolumebackups.htm) |

    Gain managed backup policies, copies in another region, and configurable retention or immutability without
    managing a backup server. Lose portability (each cloud restores only in its own) and pay for each GB
    stored and for restorations between regions.

## Manual snapshot (before a risky change)

```bash
sudo incus snapshot create <instancia> antes-de-cambio
# ... haces el cambio ...
# si salió mal
sudo incus snapshot restore <instancia> antes-de-cambio
```

## Scheduled snapshots

A daily snapshot at 06:00, which is deleted after 7 days:

```bash
sudo incus config set <instancia> snapshots.schedule="0 6 * * *"
sudo incus config set <instancia> snapshots.expiry=7d
sudo incus config set <instancia> snapshots.pattern="{{ creation_date|date:'2006-01-02' }}"
```

Check the existing ones with `sudo incus snapshot list <instancia>`.

## Export (backup outside the node)

```bash
sudo incus export <instancia> /backup/<instancia>.tar.gz
```

Copy the file to another machine or disk: an export that stays on the same
node does not work if the node is lost. To restore, on any node in the
cluster:

```bash
sudo incus import /backup/<instancia>.tar.gz
```

## Cluster configuration

```bash
sudo incus admin sql local .dump > /backup/incus-local.sql
sudo incus admin sql global .dump > /backup/incus-global.sql
```

## Verify

- `sudo incus snapshot list <instancia>` shows scheduled snapshots
  with a recent date.
- Occasionally test a `incus import` of an export on another node: a
  backup that has never been restored is not tested.

More detail and official links:
[Incus — Backup and snapshots](../incus/cluster-setup.md#backup-and-snapshots-optional).
