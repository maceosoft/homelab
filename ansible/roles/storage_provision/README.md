# storage_provision

Formatea y monta un disco libre, y lo wirea a Longhorn (disco dedicado) o a
un pool nuevo de Incus, según se decida leyendo el reporte de discovery
(`reports/<host>.md`, sección "Recomendaciones de almacenamiento").

**DESTRUCTIVO** — `mkfs` borra cualquier dato existente en el disco. No
correr sin confirmar antes qué disco y qué consumidor usar.

## Playbook

[`playbook-storage-provision.yml`](../../playbook-storage-provision.yml).

## Variables (host_vars)

```yaml
storage_provision_disks:
  - device: /dev/nvme0n1
    consumer: longhorn   # "incus" o "local"
    mount_path: /var/lib/longhorn-nvme0n1
    filesystem: ext4
    mount_opts: noatime  # opcional (default: defaults)
    wipe: true           # opcional: borra particiones y firmas previas (p. ej. un disco que vino con Windows)
    # solo si consumer == incus:
    incus_pool_name: nvme-pool
    # opcionales para Longhorn (con consumer: local, longhorn_disk_path usa solo una carpeta del disco):
    longhorn_disk_path: /srv/nvme/longhorn
    longhorn_disk_name: nvme
    longhorn_storage_reserved_gib: 80
```

- `consumer: local`: solo formatea y monta. Sirve para repartir el disco entre varios usos: una carpeta para
  Longhorn (`longhorn_disk_path`) y otras para mover datos con el rol `data_relocation`.

Sin esta variable definida en el host, `playbook-storage-provision.yml` no hace nada en ese host (ver el `when` a nivel de role en el playbook).

## Qué hace

1. Pausa de seguridad (igual que `netplan_bridge`) — confirma antes de tocar el disco.
2. Con `wipe: true`, `wipefs -a` si el disco tiene particiones y no está montado. Sin `wipe`, un disco con tabla de
   particiones no se formatea y el role falla al no encontrar UUID.
3. `blkid` para chequear si ya tiene filesystem (idempotente — no reformatea si ya tiene uno).
4. Formatea con `community.general.filesystem` si hace falta.
5. Monta y persiste en `/etc/fstab` por UUID (`ansible.posix.mount`).
6. Según `consumer`:
   - `longhorn` (o `longhorn_disk_path`): agrega el disco a `nodes.longhorn.io` con `kubectl patch`. Antes anotaba
     el nodo (`default-disks-config`), pero Longhorn solo lee esa anotación al crear el nodo y con
     `createDefaultDiskLabeledNodes=true`: en un nodo existente no hacía nada.
   - `incus`: crea un storage pool nuevo (`incus storage create ... dir source=...`), separado del pool `local` del bootstrap — no toca `preseed-bootstrap.yml.j2`.

## Ejecutar

```bash
ansible-playbook -i inventory.ini playbook-storage-provision.yml --limit deborah
```

## Verificar

```bash
ansible deborah -m command -a "df -h /var/lib/longhorn-nvme0n1"
ansible deborah -m command -a "k3s kubectl -n longhorn-system get nodes.longhorn.io deborah -o jsonpath='{.spec.disks}'"  # Longhorn
ansible deborah -m command -a "incus storage list"  # si consumer=incus
```
