# Red

!!! info "Parte de la guía de implementación"
    Ejecuta esta fase con **[Fase 1 — Red](../implementacion/fase-1-red.md)** y
    `playbook-set-static-ip.yml`.

## Bridge L2 hacia la LAN física

Los **3 nodos** usan un bridge Linux (`br0`) sobre la interfaz física,
para que las instancias Incus reciban IP directa de la LAN (red local) y sean
alcanzables entre hosts sin necesitar OVN (Open Virtual Network).

| Nodo | Interfaz física | IP en br0 (estática) |
|---|---|---|
| invincible | `eno2` | 192.168.20.6 |
| oliver | `eno1` | 192.168.20.7 |
| deborah | `enP4p65s0` | 192.168.20.5 |

> Confirmá con `ip -br link` en el nodo antes de aplicar — el nombre de la
> interfaz física puede diferir de esta tabla tras una actualización de OS.

Ejemplo netplan — invincible:

```yaml
# /etc/netplan/br0.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eno2:
      dhcp4: no
  bridges:
    br0:
      interfaces: [eno2]
      addresses: [192.168.20.6/22]
      routes:
        - to: default
          via: 192.168.20.1
      nameservers:
        addresses: [192.168.20.5, 192.168.20.1]
```

Ejemplo netplan — deborah (misma subred, distinta interfaz y último octeto):

```yaml
# /etc/netplan/br0.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enP4p65s0:
      dhcp4: no
  bridges:
    br0:
      interfaces: [enP4p65s0]
      addresses: [192.168.20.5/22]
      routes:
        - to: default
          via: 192.168.20.1
      nameservers:
        addresses: [192.168.20.5, 192.168.20.1]
```

```bash
ip -br link
sudo apt install -y netplan.io   # Debian no lo trae instalado por defecto
sudo netplan apply              # corta SSH si cambias de IP
```

El playbook Ansible instala `netplan.io`, habilita `systemd-networkd` y migra
la NIC (tarjeta de red) fuera de ifupdown antes de escribir `/etc/netplan/br0.yaml`.

```bash
ansible-playbook -i inventory.ini playbook-set-static-ip.yml --limit deborah
```

Perfil de Incus para usar el bridge en las instancias:

```bash
incus profile device add default eth0 nic nictype=bridged parent=br0
```

## IP fija — por qué es obligatoria aquí

1. **Incus cluster**: `cluster.https_address` queda grabada por IP al hacer join.
2. **K3s (distribución ligera de Kubernetes)**: kubelet usa la IP del nodo como identidad.
3. **CAPN (Cluster API Provider for Incus)**: el `Secret` `lxc-secret` apunta a `https://<IP>:8443` como string fijo.

## Esquema de IPs

| Nodo | IP actual (DHCP/pre-bridge) | IP en br0 |
|---|---|---|
| invincible | 192.168.23.162 | 192.168.20.6 |
| oliver | 192.168.20.87 | 192.168.20.7 |
| deborah | 192.168.21.211 | 192.168.20.5 |

> La LAN es un `/22` (`192.168.20.0`–`192.168.23.255`), no un `/24` — las
> IPs "actuales" de esta tabla son leases DHCP dentro de ese mismo rango
> (no subredes distintas). La fuente de verdad en todo momento es
> `ansible_host` en `inventory.ini`.

### Direccionamiento de la LAN (`192.168.20.0/22`, gateway `192.168.20.1`)

El DHCP del router reparte **`192.168.20.31` a `192.168.23.191`**. Todo lo fijo vive **fuera** de ese rango:

| Rango | Uso | Dónde se configura |
|---|---|---|
| `192.168.20.1` | Gateway (router) | Router |
| `192.168.20.4` | VIP del API de K3s (kube-vip, opcional) | `kube_vip.address` en `k3s_install.yml` |
| `192.168.20.5`, `.6`, `.7` | deborah, invincible, oliver | `static_ip` en `inventory.ini` |
| `192.168.20.31 – 192.168.23.191` | **DHCP del router** | Router |
| `192.168.23.192 – .199` | Libre | — |
| `192.168.23.200 – .220` | **MetalLB** (`LoadBalancer`, Gateway; el Gateway de Kong usa `.200`) | [`gitops/metallb/ipaddresspool.yaml`](https://github.com/maceosoft/gitops/blob/main/metallb/ipaddresspool.yaml) |
| `192.168.23.221 – .223` | Libre | — |
| `192.168.23.224/28` (`.224–.239`) | **LB de Incus** (OVN), `ipv4.routes` de la uplink | `incus_ovn_lb_routes` en `group_vars/incus_cluster/ovn.yml` |
| `192.168.23.240 – .249` | **OVN externo**, `ipv4.ovn.ranges` (un router virtual por red OVN) | `incus_ovn_external_ranges` en el mismo archivo |
| `192.168.23.250 – .255` | Libre (`.255` es el broadcast de la `/22`) | — |

Fuera de la LAN, redes privadas que no se pueden solapar con ella ni entre sí:

| Red | Uso |
|---|---|
| `10.42.0.0/16` y `10.43.0.0/16` | Pods y Services de K3s |
| `192.168.19.0/24` | Red interna de OVN (`ovn-lan`, con NAT) |

!!! warning "Fuera del DHCP"
    Las IPs fijas, el pool de MetalLB y los segmentos de OVN tienen que quedar **fuera del rango del DHCP**
    (`192.168.20.31–192.168.23.191`). Si no, el router puede dárselas a otro equipo y chocar. El preflight del rol
    `incus_ovn` falla si sus segmentos solapan con el DHCP o con MetalLB.

Tras `playbook-set-static-ip.yml`, actualizar `ansible_host` en
[`inventory.ini`](https://github.com/maceosoft/homelab/blob/main/ansible/inventory.ini)
al valor de `static_ip` si la IP de conexión cambió.

### Ollama: router y nodos

El asistente de IA tiene **una sola entrada**: el router `ollama-router` (namespace `ai`). Los clientes dentro del
clúster usan el Service `http://ollama-router.ai.svc`; los de fuera, `https://ollama.homelab.local` (Kong, solo
HTTPS; el nombre está en la zona `homelab.local` de BIND). El router exige un token Bearer.

Cada nodo de Ollama (`deborah` `192.168.20.5`, `invincible` `192.168.20.6`, `oliver` `192.168.20.7` y, cuando está
encendido, el Mac) tiene un **socket en el puerto `11434`** que despierta a Ollama; internamente Ollama escucha solo
en `127.0.0.1:11435`. El socket escucha **únicamente en la IP del nodo** (variable `ollama_ondemand_listen`) y el
firewall del nodo admite el puerto desde los nodos de K3s y desde los pods (el router puede estar en el mismo nodo). El Ollama del nodo no autentica: la protección de la inferencia es el token del router más las NetworkPolicy del namespace `ai` (que se activan por etapas). Detalle en
[Asistente de IA local](../operacion/ia-ollama.md) y [Agregar un nodo al clúster de Ollama](../operacion/agregar-nodo-ollama.md).

### Nombres de la API de K3s

Los agentes, el kubeconfig y los certificados usan el nombre `k3s.homelab.local` para la API (puerto `6443`) en
lugar de la IP de un nodo concreto. Así el control plane se puede mover sin tocar a los clientes
([procedimiento](../operacion/mover-control-plane.md)).

## Puertos expuestos y firewall de host

Cada nodo tiene un firewall de host con `nftables` (rol `host_firewall`): una tabla propia, evaluada antes de
kube-proxy y sin modificar las cadenas de Calico. La política es `accept` con denegaciones explícitas (para no cortar a K3s, Calico, Longhorn ni MetalLB si cambian sus puertos), y el tráfico entre nodos es de confianza. Se restringe lo siguiente:

- SSH (`22`) desde la LAN (red local), con autenticación por Dex.
- El API de K3s (`6443`), el kubelet (`10250`), el tráfico de BGP (`179`), de FRR (`2623`) y de MetalLB (`7946`), y Typha
  (`5473`): solo entre los nodos y el rango de pods.
- Las métricas (`9100`, `9120`, `9140`, `9141`): solo hacia el recolector y los nodos.
- Incus (`8443`): nodos, pods y operador. Ollama (`11434`): nodos de K3s, pods y los equipos que se agreguen a `host_firewall_ollama_extra_cidrs` (el Mac).
- DNS (`53`) desde la LAN.

La lista de lo que queda sin autenticación propia, con el motivo y el control de red que la sustituye, está en
[Modelo de autenticación](../security/modelo-de-autenticacion.md#excepciones-controladas-por-red). Las reglas se
aplican con una auto-reversión por seguridad (ver [Hardening post-incidente](../security/hardening-post-incidente.md)).
