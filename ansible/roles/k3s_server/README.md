# k3s_server

Instala el **K3s control-plane** (server) en el nodo designado como `k3s_server`.

En el homelab: **deborah** (`k3s_role: server`); pasa a **oliver** con [`playbook-k3s-move-controlplane.yml`](../../playbook-k3s-move-controlplane.yml).

## Playbook

[`playbook-k3s.yml`](../../playbook-k3s.yml) — Fase 3.

```bash
ansible-playbook -i inventory.ini playbook-k3s.yml --tags server
```

## Hosts

`k3s_server` (lista explícita en `inventory.ini`: deborah). `serial: 1`.

## Tags

`server`, `core`.

## Variables

Desde [`group_vars/incus_cluster/k3s_install.yml`](../../group_vars/incus_cluster/k3s_install.yml):

| Variable | Default | Descripción |
|---|---|---|
| `k3s_install.core.version` | `v1.36.5+k3s1` | Versión K3s (canal stable) |
| `k3s_install.core.disable_components` | traefik, servicelb | `--disable` en install |
| `k3s_install.core.cluster_cidr` | `10.42.0.0/16` | Pod CIDR |
| `k3s_install.core.service_cidr` | `10.43.0.0/16` | Service CIDR |
| `k3s_install.core.cni` | `flannel` | `flannel`, `canal`, `calico`, `cilium` |
| `k3s_install.core.flannel_backend` | `vxlan` | Solo si `cni: flannel` |
| `k3s_install.core.tls_sans_extra` | `[]` | SANs extra en cert API |
| `k3s_install.core.embedded_registry` | `false` | `--embedded-registry` |
| `k3s_install.kube_vip.enabled` | `false` | Si true, añade VIP a TLS SANs |
| `k3s_server_tls_sans` | endpoint, IP del API, deborah | SANs adicionales (`group_vars/all.yml`); el rol agrega además IP y nombre del nodo |
| `k3s_install.security.secrets_encryption` | `true` | `--secrets-encryption` (igual en todos los servers) |
| `k3s_install.security.oidc.*` | Dex, cliente `kubernetes` | `--kube-apiserver-arg=oidc-*` (issuer, client-id, username-claim `email`, groups-claim `groups`, CA) |
| `k3s_server_cluster_init` / `k3s_server_join_url` / `k3s_server_token` | `false` / vacío / vacío | Usados por la mudanza: `--cluster-init`, `--server`, token compartido |
| `k3s_server_reconfigure` | `false` | Re-ejecuta el instalador aunque K3s esté activo (la mudanza) |
| `k3s_agent_kubelet_args` | `host_vars` | También se pasan como `--kubelet-arg` al server |

## Qué hace

1. Calcula TLS SANs (IP, hostname, kube-vip opcional).
2. Instala K3s server con el instalador verificado por checksum ([`k3s_installer`](../k3s_installer/README.md)) si no está activo; los flags de seguridad solo aplican al instalar o reconfigurar, un server activo no se reinicia solo (`--flannel-backend=none` si `cni` ≠ flannel).
3. Espera API en `:6443`.
4. Publica `k3s_token` en facts para el play de agents (siguiente).

Siguiente play opcional: rol [`k3s_cni`](../k3s_cni/README.md) si `cni` es canal/calico/cilium.

## Verificar

```bash
sudo systemctl status k3s
sudo k3s kubectl get nodes
```

## Documentación

- [Fase 3 — K3s](../../../docs/implementacion/fase-3-k3s.md)
- [K3s manual (legacy)](../../../docs/k3s/index.md)

## Tokens

- `K3S_TOKEN` (server) une servers y también sirve a agents; `K3S_AGENT_TOKEN` (`k3s_server_agent_token`) es el que deben
  usar los agents. La mudanza los deja DISTINTOS. Ambos se pasan por entorno (`environment:`), no por argumentos, y el
  instalador los guarda en `/etc/systemd/system/k3s.service.env` (0600).
- Rotación: `k3s token rotate --token <actual> --new-token <nuevo>`; después hay que reiniciar todos los servers y los
  agents que entraron con el token viejo. Los snapshots anteriores a la rotación piden el token viejo al restaurar.

## Advertencia: dos miembros de etcd

Durante la mudanza el clúster tiene dos servers etcd. Con dos miembros el quórum es 2: **no hay tolerancia a fallos**,
si uno cae el API cae. Es una ventana corta y prevista; la mudanza termina con `--cluster-reset` y un solo miembro (oliver).
