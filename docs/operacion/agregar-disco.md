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

## 3. Declararlo en `host_vars`

En `host_vars/deborah.yml`:

```yaml
storage_provision_disks:
  - device: /dev/nvme0n1
    consumer: longhorn            # o incus
    mount_path: /var/lib/longhorn-nvme0n1
    filesystem: ext4
    # solo si consumer: incus
    # incus_pool_name: nvme-pool
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
| "Ya tiene filesystem" y no formatea | Es a propósito: el disco no está vacío. Revisa qué tiene antes de borrarlo a mano |
| Longhorn no muestra el disco | Espera un minuto y revisa la anotación del nodo: `kubectl get node deborah -o yaml \| grep longhorn` |

Más detalle del rol: [`storage_provision`](https://github.com/maceosoft/homelab/blob/main/ansible/roles/storage_provision/README.md).
