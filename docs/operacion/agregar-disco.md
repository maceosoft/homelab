# Agregar un disco a un nodo

Formatea un disco libre de un nodo, lo monta y lo entrega a **Longhorn**
(almacenamiento replicado de Kubernetes) o a **Incus** (un pool nuevo para
instancias).

!!! danger "Destructivo"
    El playbook **formatea** el disco: borra cualquier dato que tenga. Confirma
    el dispositivo exacto antes de correrlo. El playbook tiene una pausa de
    seguridad y no reformatea un disco que ya tiene sistema de archivos.

En los ejemplos: disco `/dev/nvme0n1` en el nodo **`deborah`**.

## 1. Identificar el disco

Corre el discovery del nodo y lee la sección *Recomendaciones de
almacenamiento* de `reports/<nodo>.md`:

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-discovery.yml --limit deborah
```

Confírmalo también en el nodo (`lsblk -f`): el disco tiene que estar vacío y
sin montar.

## 2. Elegir a quién se entrega

| Consumidor | Cuándo | Qué hace el playbook |
|---|---|---|
| `longhorn` | Volúmenes de Kubernetes con réplicas entre nodos | Monta el disco y anota el nodo para que Longhorn lo use |
| `incus` | Más espacio para contenedores y VMs (máquinas virtuales) de Incus | Monta el disco y crea un storage pool nuevo, aparte del pool `local` |
| `local` | Repartir el disco entre varios usos | Solo lo monta. Con `longhorn_disk_path`, una carpeta va a Longhorn; otras se usan para [mover datos](#mover-datos-a-otro-disco) |

## 3. Declararlo en `host_vars`

En `host_vars/deborah.yml`:

```yaml
storage_provision_disks:
  - device: /dev/nvme0n1
    consumer: longhorn            # o incus
    mount_path: /var/lib/longhorn-nvme0n1
    filesystem: ext4
    # wipe: true                  # si el disco trae particiones (p. ej. de Windows): las borra
    # solo si consumer: incus
    # incus_pool_name: nvme-pool
```

Si el disco trae particiones de otro sistema, agrega `wipe: true`: sin eso el playbook no lo formatea. `wipe` nunca
actúa sobre un disco montado.

`deborah` usa la variante `local`: un solo disco para Longhorn, K3s y Ollama (ver su `host_vars`):

```yaml
storage_provision_disks:
  - device: /dev/nvme0n1
    consumer: local
    wipe: true
    mount_path: /srv/nvme
    mount_opts: noatime
    filesystem: ext4
    longhorn_disk_path: /srv/nvme/longhorn   # esta carpeta va a Longhorn
    longhorn_disk_name: nvme
    longhorn_storage_reserved_gib: 80        # lo que queda para K3s y Ollama
```

Sin esta variable, el playbook no hace nada en ese nodo.

## 4. Aplicar

```bash
ansible-playbook -i inventory.ini playbook-storage-provision.yml --limit deborah
```

Confirma en la pausa de seguridad cuando el dispositivo mostrado sea el
correcto.

## Verificar

El `ssh` entra con el [acceso por SSO](acceso-ssh.md) (`opkssh login` antes):

```bash
# montado, con la entrada en /etc/fstab
ssh devops@deborah.homelab.local findmnt /var/lib/longhorn-nvme0n1
```

- **Longhorn:**

    === "🖱️ Desde la interfaz"

        En la UI (interfaz de usuario), *Node → deborah* muestra el disco nuevo con *Schedulable* activado.

    === "⌨️ Desde la consola"

        Los discos del nodo están en el recurso `nodes.longhorn.io`; el disco nuevo debe aparecer con la condición
        `Schedulable` en `True`:

        ```bash
        kubectl -n longhorn-system get nodes.longhorn.io deborah -o jsonpath='{.status.diskStatus}'
        ```

- **Incus:** `sudo incus storage list` muestra el pool nuevo.

## Si falla

| Síntoma | Revisar |
|---|---|
| El playbook no hace nada | Falta `storage_provision_disks` en `host_vars` del nodo, o `--limit` apunta a otro nodo |
| "Ya tiene filesystem" y no formatea | Es a propósito: el disco no está vacío. Revisa qué tiene; si se puede borrar, agrega `wipe: true` |
| Falla en "Obtener UUID del disco" | El disco tiene una tabla de particiones (por ejemplo, de Windows) y falta `wipe: true` |
| Longhorn no muestra el disco | Revisa `kubectl -n longhorn-system get nodes.longhorn.io deborah -o jsonpath='{.spec.disks}'`: el playbook lo agrega ahí |

## Retirar el disco viejo de Longhorn

Si el disco nuevo reemplaza a otro del mismo nodo (en `deborah`, el eMMC), Longhorn mueve las réplicas sin cortar
los volúmenes:

1. Comprueba que todos los volúmenes estén `healthy`:
   `kubectl -n longhorn-system get volumes.longhorn.io`.
2. Deja de programar en el disco viejo y pide desalojarlo (el nombre del disco sale de `.spec.disks`):

    ```bash
    kubectl -n longhorn-system patch nodes.longhorn.io deborah --type merge \
      -p '{"spec":{"disks":{"<disco-viejo>":{"allowScheduling":false,"evictionRequested":true}}}}'
    ```

3. Espera a que el disco viejo quede sin réplicas y los volúmenes vuelvan a `healthy`:
   `kubectl -n longhorn-system get replicas.longhorn.io -o wide`.
4. Quítalo del nodo (en la interfaz: *Node → deborah → Edit node and disks → Remove*). La carpeta del disco viejo
   (`/var/lib/longhorn/`) se borra a mano después.

## Mover datos a otro disco

Con el disco montado como `local`, [`playbook-data-relocation.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-data-relocation.yml)
mueve carpetas al disco nuevo **sin cambiar sus rutas**: copia la carpeta, renombra la original (para volver atrás)
y monta la copia encima con un bind mount en `/etc/fstab`. Hoy **ningún nodo lo usa**: ver el aviso de abajo.

!!! danger "Lo que pasó en `deborah` (8 nov 2026)"
    Copiando las imágenes de contenedores (`/var/lib/rancher/k3s/agent/containerd`, unos 43 GB) al NVMe, la escritura
    sostenida lo calentó hasta que dejó de responder y se cayó del bus PCIe (`controller is down`); volvió solo después
    de apagar y encender el nodo. El corte todavía no había empezado, así que K3s siguió funcionando. El NVMe (sin
    disipador) marca 71 °C en reposo y 80 °C en uno de sus sensores, con el crítico en 82 °C.

    Por eso en `deborah` solo va al NVMe lo que se puede perder sin consecuencias: **Longhorn** (cada volumen tiene
    otra réplica en otro nodo). La base de datos de K3s y las imágenes se quedan en el eMMC: con el seguro de abajo,
    un NVMe que no aparece dejaría a K3s sin arrancar, y `deborah` es el único control plane. Hasta ponerle un
    disipador, ni siquiera Longhorn: su disco `nvme` está con `allowScheduling: false`. Las alertas
    `NvmeTemperaturaAlta`, `NvmeTemperaturaCritica` y `DiscoDesaparecido` avisan si vuelve a pasar
    ([Monitoreo](monitoreo.md)).

!!! info "Antes de mover algo, mide"
    Un NVMe no siempre es más rápido que el disco que reemplaza. El de `deborah` (SK hynix BC501, sin caché propia)
    medido con `fio` contra su eMMC: el doble en escritura aleatoria de 4k (41 300 contra 20 600 IOPS), pero la mitad
    en escritura secuencial (125 contra 250 MB/s) y bastante peor en escrituras con `fsync` (775 contra 1329 IOPS).
    Y mira la temperatura con escritura sostenida (`ansible/scripts/temperaturas.sh`) antes de confiarle algo.

!!! warning "Corta servicios"
    Antes de cada corte hay una pausa. Si lo que se mueve va dentro de k3s (containerd), el playbook vacía el nodo
    (`drain`), detiene k3s y sus contenedores (`k3s-killall.sh`), hace la copia final y vuelve a arrancar. En un nodo
    con control plane, el API del clúster no responde mientras dura la copia final.

Los items se declaran en `data_relocation_items` del `host_vars` del nodo (ejemplos en el
[README del rol](https://github.com/maceosoft/homelab/blob/main/ansible/roles/data_relocation/README.md)):

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-data-relocation.yml --limit <nodo> --check
ansible-playbook -i inventory.ini playbook-data-relocation.yml --limit <nodo>
```

El seguro es el drop-in `RequiresMountsFor` que el playbook agrega a cada servicio: si el disco no monta, el servicio
**no arranca**, en vez de arrancar con la carpeta vacía. Si algún día se mueve la base de datos de K3s
(`/var/lib/rancher/k3s/server`), ese seguro es obligatorio: sin él, K3s crearía un clúster nuevo. Y es justo la
razón para no hacerlo sobre un disco que puede desaparecer.

Las carpetas originales quedan como `*.emmc-old` (o el sufijo configurado). Bórralas cuando todo lleve un par de días
estable. Detalle y rollback en el README del rol.

Más detalle del rol: [`storage_provision`](https://github.com/maceosoft/homelab/blob/main/ansible/roles/storage_provision/README.md).
