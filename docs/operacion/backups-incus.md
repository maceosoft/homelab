# Backups y snapshots de Incus

Cómo respaldar instancias de Incus (contenedores y VMs) y cómo recuperarlas.
Hay tres niveles, de más rápido a más seguro:

| Nivel | Qué protege | Dónde queda | Sirve si se pierde el disco |
|---|---|---|---|
| **Snapshot** | Una instancia, para volver atrás | En el mismo storage pool | No |
| **Export** | Una instancia completa, restaurable en otro nodo | Un archivo `.tar.gz` | Sí, si lo guardas fuera del nodo |
| **Volcado de la base de datos** | Configuración del clúster Incus (redes, perfiles) | Archivos `.sql` | Sí, si lo guardas fuera del nodo |

Los comandos van en el nodo que aloja la instancia, con `sudo`.

**Esta decisión en otros entornos**

=== "🏠 En casa"

    Snapshots programados de Incus para volver atrás rápido, y `incus export` a un archivo que copias fuera del nodo.
    Sin licencias ni servidor de backup: alcanza para unas pocas instancias, siempre que pruebes restaurar.

=== "🏢 En la empresa"

    - **Beneficios:** un sistema de backup centralizado programa, cifra y verifica las copias de todas las máquinas,
      avisa si una falla y permite restaurar una VM o un archivo suelto sin depender de quien la creó.
    - **Regla 3-2-1:** tres copias de los datos, en dos medios distintos y una fuera del sitio; muchas empresas suman
      una copia inmutable o desconectada contra ransomware.
    - **RPO y RTO definidos:** cuántos datos se pueden perder (RPO) y en cuánto tiempo hay que volver (RTO) por cada
      sistema; de ahí sale cada cuánto se respalda y se prueba la restauración, con evidencia para auditoría.
    - **Productos con soporte:** [Veeam Backup & Replication](https://www.veeam.com/products/veeam-data-platform/backup-recovery.html)
      para VMs en hipervisores soportados, y para Kubernetes
      [Veeam Kasten](https://www.veeam.com/products/cloud/kubernetes-data-protection.html) o
      [Velero](https://velero.io/) (código abierto). Incus no tiene integración con estos productos, así que se
      respalda con sus propios comandos o por archivos.
    - **Cuándo sí conviene lo mismo:** en sitios pequeños o desconectados, con pocas instancias, donde un script con
      snapshots y exports hacia otro disco cubre el RPO pedido.

=== "☁️ En la nube"

    | Nube | Servicio equivalente |
    |---|---|
    | GCP | [Backup and DR Service](https://cloud.google.com/backup-disaster-recovery) (VMs) y [Backup for GKE](https://docs.cloud.google.com/kubernetes-engine/docs/add-on/backup-for-gke/concepts/backup-for-gke) |
    | AWS | [AWS Backup](https://aws.amazon.com/backup/) (EC2, EBS, EKS y más) |
    | Azure | [Azure Backup](https://learn.microsoft.com/en-us/azure/backup/backup-overview) (VMs, discos y AKS) |
    | Oracle Cloud (OCI) | [Block Volume Backups](https://docs.oracle.com/en-us/iaas/Content/Block/Concepts/blockvolumebackups.htm), con [políticas programadas](https://docs.oracle.com/en-us/iaas/Content/Block/Tasks/schedulingvolumebackups.htm) |

    Ganas políticas de backup administradas, copias en otra región y retención o inmutabilidad configurables sin
    cuidar un servidor de backup. Pierdes portabilidad (cada nube restaura solo en la suya) y pagas por cada GB
    guardado y por las restauraciones entre regiones.

## Snapshot manual (antes de un cambio riesgoso)

```bash
sudo incus snapshot create <instancia> antes-de-cambio
# ... haces el cambio ...
# si salió mal
sudo incus snapshot restore <instancia> antes-de-cambio
```

## Snapshots programados

Un snapshot diario a las 06:00, que se borra solo a los 7 días:

```bash
sudo incus config set <instancia> snapshots.schedule="0 6 * * *"
sudo incus config set <instancia> snapshots.expiry=7d
sudo incus config set <instancia> snapshots.pattern="{{ creation_date|date:'2006-01-02' }}"
```

Revisa los que existen con `sudo incus snapshot list <instancia>`.

## Export (respaldo fuera del nodo)

```bash
sudo incus export <instancia> /backup/<instancia>.tar.gz
```

Copia el archivo a otro equipo o disco: un export que queda en el mismo
nodo no sirve si el nodo se pierde. Para restaurar, en cualquier nodo del
clúster:

```bash
sudo incus import /backup/<instancia>.tar.gz
```

## Configuración del clúster

```bash
sudo incus admin sql local .dump > /backup/incus-local.sql
sudo incus admin sql global .dump > /backup/incus-global.sql
```

## Verificar

- `sudo incus snapshot list <instancia>` muestra los snapshots programados
  con fecha reciente.
- Prueba de vez en cuando un `incus import` de un export en otro nodo: un
  backup que nunca se restauró no está probado.

Más detalle y links oficiales:
[Incus — Backup y snapshots](../incus/cluster-setup.md#backup-y-snapshots-opcional).
