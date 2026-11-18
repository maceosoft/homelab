# incus-cluster-groups

Los grupos del clúster de Incus que se usan como destino de instancias (`--target @x86-nodes`) y en CAPN:

| Grupo | Miembros (los asigna Ansible, rol `incus_cluster`) |
|---|---|
| `x86-nodes` | `invincible`, `oliver`, `eve` |
| `arm64-nodes` | `deborah` |

OpenTofu maneja el grupo (nombre y descripción), no sus miembros: la asignación la hace Ansible
(`incus_cluster_group_assignments`).

## Primera vez: importar

Los grupos ya existen (los creó Ansible), así que primero se importan al state. El import solo escribe el state
local; no cambia nada en Incus:

```bash
cd opentofu/incus-cluster-groups
tofu init
tofu import incus_cluster_group.x86_nodes x86-nodes
tofu import incus_cluster_group.arm64_nodes arm64-nodes
tofu plan
```

El `plan` propone **agregar las descripciones** (Ansible los creó sin descripción): `0 to add, 2 to change`. Con
`tofu apply` quedan puestas. Probado el 18 nov 2026 (import y plan).

Con SSO: `-parallelism=1` en cada comando (ver [../README.md](../README.md)).
