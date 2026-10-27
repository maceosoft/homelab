# incus_install

Instala el paquete **Incus** desde el repo [Zabbly stable](https://github.com/zabbly/incus)
en los nodos del clúster. No ejecuta bootstrap ni join — eso lo hace `incus_cluster`.

## Playbook

[`playbook-bootstrap.yml`](../../playbook-bootstrap.yml) — Fase 2 (primer paso).

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-bootstrap.yml
```

## Hosts

`incus_cluster` (los 3 nodos).

## Variables

Ninguna específica del rol.

## Qué hace

1. Descarga el script de instalación Zabbly a `/tmp/incus-install.sh`.
2. Ejecuta el instalador (idempotente: `creates: /usr/bin/incus`).
3. Muestra la arquitectura del nodo (`uname -m`).
4. Recuerda que `br0` se configura con el rol `netplan_bridge`.

## Verificar

```bash
incus version
which incus
```

## Siguiente paso

```bash
ansible-playbook -i inventory.ini playbook-incus-cluster.yml
```

Rol: [`incus_cluster`](../incus_cluster/README.md) ·
[`incus_ui`](../incus_ui/README.md)

## Documentación

- [Fase 2 — Incus](../../../docs/implementacion/fase-2-incus.md)
- [Clúster Incus](../../../docs/incus/cluster-setup.md)
