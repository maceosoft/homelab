# Backups y snapshots de Incus

Cómo respaldar instancias de Incus (contenedores y VMs) y cómo recuperarlas.
Hay tres niveles, de más rápido a más seguro:

| Nivel | Qué protege | Dónde queda | Sirve si se pierde el disco |
|---|---|---|---|
| **Snapshot** | Una instancia, para volver atrás | En el mismo storage pool | No |
| **Export** | Una instancia completa, restaurable en otro nodo | Un archivo `.tar.gz` | Sí, si lo guardas fuera del nodo |
| **Volcado de la base de datos** | Configuración del clúster Incus (redes, perfiles) | Archivos `.sql` | Sí, si lo guardas fuera del nodo |

Los comandos van en el nodo que aloja la instancia, con `sudo`.

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
