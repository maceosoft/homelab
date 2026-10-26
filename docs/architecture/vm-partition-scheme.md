# Esquema de particiones de las VMs de workload (CAPN)

Convención para las VM (máquinas virtuales) que CAPN (Cluster API Provider for Incus) provisione como clústeres de
workload (por ejemplo `demo`, ver [Workload Clusters](nivel-3-componentes.md#33-workload-clusters)). Es una
plantilla para la imagen base de esas VM, no un estado medido.

Sale de la revisión de particiones de los 3 nodos bare-metal (el informe de
[`playbook-discovery.yml`](../hardware/discovery.md), sección "Recomendaciones — esquema de partición del SO"):
ningún nodo tiene `/var` separado de `/`, y el swap de cada uno se dimensionó con un criterio distinto (entre 13 % y
94 % de diferencia contra `min(RAM/2, 8GB)`). En un nodo ya instalado eso no se puede corregir sin reparticionar
la raíz montada; en una VM nueva se define desde el primer arranque.

## Esquema

| Partición | Tamaño | Filesystem | Notas |
|---|---|---|---|
| `/boot` (o `/boot/efi` si UEFI) | 1 GB | vfat/ext4 | Igual que los 3 nodos bare-metal |
| swap | `min(RAM/2, 8GB)` | swap | Fórmula fija, la misma en todas las VM |
| `/var` | ≥20 % del disco, o 20 GB mínimo | ext4 | Separado de `/`: un crecimiento descontrolado de logs, imágenes de containerd o volúmenes locales no llena la raíz |
| `/` | Resto del disco | ext4 | Sistema base |

## Por qué separar `/var`

Los workloads de K3s (containerd, logs, caché de imágenes, `local-path-provisioner`/OpenEBS si aplica dentro de la
VM) escriben todos bajo `/var`. Sin partición separada, si eso crece sin control puede llenar `/` y tumbar el nodo
entero, no solo el workload. En bare-metal ya instalado, separar `/var` obliga a reinstalar; en una VM nueva de
CAPN no cuesta nada definirlo en la plantilla desde el primer día.

## Aplicación

El esquema va en la imagen o plantilla base que CAPN use para provisionar las VM, no en Ansible después de
instalar. Este repo todavía no tiene esa plantilla.
