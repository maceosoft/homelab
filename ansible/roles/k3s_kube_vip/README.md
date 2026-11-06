# k3s_kube_vip

Despliega **[kube-vip](https://kube-vip.io/)** como DaemonSet en el control-plane
para una **VIP estable del API server** (`:6443`).

Solo VIP del control-plane — **no** gestiona Services `LoadBalancer` (`svc_enable=false`).

## Playbook

[`playbook-k3s.yml`](../../playbook-k3s.yml) — Fase 3 (fork opcional).

Con `k3s_install.kube_vip.enabled: true` en
[`group_vars/incus_cluster/k3s_install.yml`](../../group_vars/incus_cluster/k3s_install.yml)
(no con `-e`: Ansible no fusiona claves con puntos en un diccionario):

```bash
ansible-playbook -i inventory.ini playbook-k3s.yml --tags kube_vip
```

## Hosts

`k3s_server` (deborah).

## Tags

`kube_vip`.

## Variables

| Variable | Default | Descripción |
|---|---|---|
| `k3s_install.kube_vip.enabled` | `false` | Activa el rol |
| `k3s_install.kube_vip.address` | `192.168.20.4` | VIP en LAN |
| `k3s_install.kube_vip.interface` | `br0` | Interfaz L2 |
| `k3s_install.kube_vip.mode` | `arp` | Modo ARP o BGP |
| `k3s_install.kube_vip.image_version` | `v1.3.1` | Imagen kube-vip |

Con VIP habilitada, `k3s_api_url` apunta a la VIP y los agents se unen por ella.

## Qué hace

1. Aplica RBAC kube-vip desde [`templates/kube-vip-rbac.yaml.j2`](templates/kube-vip-rbac.yaml.j2).
2. Renderiza y aplica DaemonSet desde [`templates/kube-vip-daemonset.yaml.j2`](templates/kube-vip-daemonset.yaml.j2).
3. Assert: `svc_enable=false` (no compite con MetalLB).
4. Espera API accesible en la VIP.

## Verificar

```bash
curl -k https://192.168.20.4:6443/version
sudo k3s kubectl get pods -n kube-system -l app.kubernetes.io/name=kube-vip
```

## Documentación

- [Opciones del playbook](../../../docs/k3s/playbook-options.md)
- [Fase 4 — kube-vip vs MetalLB](../../../docs/implementacion/fase-4-gitops.md#46--kube-vip-vs-metallb)
