# incus_ui

Instala la **UI nativa de Incus** (`incus-ui-canonical`) y configura
`core.https_address` en el nodo leader. No es un contenedor — la sirve el daemon
de Incus; no aplica GitOps.

## Playbook

[`playbook-incus-cluster.yml`](../../playbook-incus-cluster.yml) — play 3 (post), tag `ui`.

## Hosts

`invincible` (leader).

## Variables

| Variable | Default | Descripción |
|---|---|---|
| `incus_ui_https_address` | `:8443` | Valor de `core.https_address` |

Definida en [`group_vars/incus_cluster.yml`](../../group_vars/incus_cluster.yml).

## Qué hace

1. Instala `incus-ui-canonical` o lo actualiza a la última versión del repositorio (`state: latest`): son archivos estáticos que sirve el daemon, actualizarlos no reinicia Incus
2. `incus config set core.https_address :8443` (idempotente)

## Verificar

```bash
curl -kI https://incus.homelab.local:8443
# Tras /etc/hosts → ver Resumen del homelab
```

## Documentación

- [Fase 2 — Incus UI](../../../docs/implementacion/fase-2-incus.md)
- [Resumen del homelab](../../../docs/implementacion/resumen-homelab.md)
