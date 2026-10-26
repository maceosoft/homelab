# k3s_agent

Une **workers K3s** (agents) al control-plane usando el token del server.

En el homelab: **invincible** y **oliver** (`k3s_role: agent`).

## Playbook

[`playbook-k3s.yml`](../../playbook-k3s.yml) — Fase 3.

```bash
ansible-playbook -i inventory.ini playbook-k3s.yml --tags agent
```

Requiere que el play `k3s_server` haya corrido antes (publica `k3s_token`).

## Hosts

`k3s_agent` (lista explícita en `inventory.ini`: invincible, oliver).

## Tags

`agent`, `core`.

## Variables

| Variable | Origen | Descripción |
|---|---|---|
| `k3s_api_url` | `group_vars/incus_cluster/k3s_install.yml` | URL del API (`https://k3s.homelab.local:6443`, o la VIP con kube-vip); el DNS debe resolver el nombre antes de instalar |
| `k3s_token` | Fact del server | Token de unión (automático) |
| `k3s_agent_token` | opcional | Si está definido, se usa en lugar de `k3s_token` (agent-token distinto del de server; lo pasa la mudanza) |
| `k3s_agent_kubelet_args` | `host_vars/` | Args extra del kubelet (opcional) |
| `k3s_node_labels` | `host_vars/` | Etiquetas si `node_labels.at_join: true` |

Ejemplo en [`host_vars/oliver.yml`](../../host_vars/oliver.yml):

```yaml
k3s_agent_kubelet_args:
  - max-pods=110
k3s_node_labels:
  workload-tier: light
  node.longhorn.io/create-default-disk: "false"
```

## Qué hace

1. Obtiene `k3s_token` del primer host en `k3s_server`.
2. Instala K3s agent con `K3S_URL` + `K3S_TOKEN` si no está activo.
3. Opcionalmente aplica `--node-label` en el join (`at_join: true`).

## Verificar

```bash
sudo systemctl status k3s-agent
# En el server:
sudo k3s kubectl get nodes
```

## Documentación

- [Fase 3 — K3s](../../../docs/implementacion/fase-3-k3s.md)
- [Opciones del playbook](../../../docs/k3s/playbook-options.md)
