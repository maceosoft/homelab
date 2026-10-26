# k3s_fetch_kubeconfig

Copia el **kubeconfig del server** al operador y reescribe la URL del API
con `k3s_api_url` (nombre estable `k3s_api_endpoint` o VIP kube-vip). El certificado del API incluye ese nombre solo si el server se instaló o reconfiguró con él como SAN (la mudanza lo hace en deborah).

## Playbook

[`playbook-k3s.yml`](../../playbook-k3s.yml) — Fase 3.

Con `k3s_install.fetch_kubeconfig.enabled: true` en
[`group_vars/incus_cluster/k3s_install.yml`](../../group_vars/incus_cluster/k3s_install.yml)
(no con `-e`: Ansible no fusiona claves con puntos en un diccionario):

```bash
ansible-playbook -i inventory.ini playbook-k3s.yml --tags kubeconfig
```

## Hosts

`k3s_server` (lee `/etc/rancher/k3s/k3s.yaml`, escribe en la estación operador).

## Tags

`kubeconfig`.

## Variables

| Variable | Default | Descripción |
|---|---|---|
| `k3s_install.fetch_kubeconfig.enabled` | `false` | Activa el rol |
| `k3s_install.fetch_kubeconfig.dest` | `~/.kube/homelab-k3s.yaml` | Ruta local destino |
| `k3s_api_url` | derivada | URL del API en el kubeconfig |

## Qué hace

1. Lee `k3s.yaml` del server.
2. Sustituye `server: https://...:6443` por `k3s_api_url`.
3. Escribe el archivo en la estación Ansible (`delegate_to: localhost`).

## Verificar

```bash
export KUBECONFIG=~/.kube/homelab-k3s.yaml
kubectl get nodes
```

Alternativa web tras Fase 5: kubeconfig desde [vCluster Platform](../../../docs/implementacion/fase-5-vcluster.md).

## Documentación

- [Fase 3 — K3s](../../../docs/implementacion/fase-3-k3s.md)
- [Fase 4 — Acceso kubectl](../../../docs/implementacion/fase-4-gitops.md#41--acceso-kubectl)
