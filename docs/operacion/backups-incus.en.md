# Incus backups and snapshots

How to back up Incus instances (containers and VMs) and how to recover them.
There are three levels, from fastest to safest:

| Level | What it protects | Where it ends up | Useful if the disk is lost |
|---|---|---|---|
| **Snapshot** | One instance, to roll back | In the same storage pool | No |
| **Export** | A complete instance, restorable on another node | A `.tar.gz` file | Yes, if you keep it off the node |
| **Database dump** | Incus cluster configuration (networks, profiles) | `.sql` files | Yes, if you keep it off the node |

Commands run on the node that hosts the instance, with `sudo`.

## Manual snapshot (before a risky change)

```bash
sudo incus snapshot create <instancia> antes-de-cambio
# ... haces el cambio ...
# si salió mal
sudo incus snapshot restore <instancia> antes-de-cambio
```

## Scheduled snapshots

A daily snapshot at 06:00 that deletes itself after 7 days:

```bash
sudo incus config set <instancia> snapshots.schedule="0 6 * * *"
sudo incus config set <instancia> snapshots.expiry=7d
sudo incus config set <instancia> snapshots.pattern="{{ creation_date|date:'2006-01-02' }}"
```

Check the existing ones with `sudo incus snapshot list <instancia>`.

## Export (backup off the node)

```bash
sudo incus export <instancia> /backup/<instancia>.tar.gz
```

Copy the file to another machine or disk: an export that stays on the same
node is useless if the node is lost. To restore, on any node of the
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

- `sudo incus snapshot list <instancia>` shows the scheduled snapshots
  with a recent date.
- Every now and then, test an `incus import` of an export on another node: a
  backup that was never restored is not tested.

More detail and official links:
[Incus — Backup and snapshots](../incus/cluster-setup.md#backup-y-snapshots-opcional).
