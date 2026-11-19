# incus_ovn

OVN para Incus (opcional, apagado por defecto): base de datos de OVN en alta disponibilidad en los tres nodos, red
*uplink* sobre `br0` y una red OVN. Con OVN, Incus puede crear balanceadores de red (`incus network load-balancer`).

## Playbook

Va dentro de [`playbook-incus-cluster.yml`](../../playbook-incus-cluster.yml) (tag `ovn`). Con `incus_ovn_enabled: false`
(el valor por defecto, en `group_vars/incus_cluster/ovn.yml`) ese playbook no lo toca.

```bash
cd ansible
# Preflight (solo lectura): nada se instala
ansible-playbook -i inventory.ini playbook-incus-cluster.yml --tags ovn --skip-tags always -e incus_ovn_enabled=true
# Instalar y crear las redes
ansible-playbook -i inventory.ini playbook-incus-cluster.yml --tags ovn --skip-tags always -e incus_ovn_enabled=true -e incus_ovn_confirm=true
```

`--skip-tags always` evita volver a pasar por los tramos de bootstrap y join del clúster.

## Fases (`incus_ovn_phase`)

| Fase | Hosts | Qué hace |
|---|---|---|
| `preflight` | todos los nodos | Versión de Incus, paquetes, memoria libre, bridge y que las IP reservadas no respondan |
| `install` | todos, `serial: 1` (el líder primero) | `ovn-central`, `ovn-host`, `openvswitch-switch`; la base de datos en clúster y `ovn-controller` |
| `networks` | `invincible` | Conexión de Incus a OVN, uplink sobre `br0` y red `ovn-lan` |
| `profile` | `invincible` | Perfil `ovn-lan` para sus instancias: NIC en la red y MTU del DHCP (1442) con cloud-init. Solo él: `--tags ovn-profile` |

## Variables

En `group_vars/incus_cluster/ovn.yml` (las que se editan) y `defaults/main.yml` (el resto).

| Variable | Valor | Qué es |
|---|---|---|
| `incus_ovn_enabled` | `false` | Activa el rol |
| `incus_ovn_confirm` | `false` | `true` instala; `false` solo preflight |
| `incus_ovn_lb_routes` | `192.168.23.224/28` | Segmento LB: `ipv4.routes` de la uplink |
| `incus_ovn_external_ranges` | `192.168.23.240-192.168.23.249` | Segmento OVN externo: `ipv4.ovn.ranges` |
| `incus_ovn_internal_cidr` | `192.168.19.1/24` | Segmento OVN interno: `ipv4.address` (con NAT) |
| `incus_ovn_profile_name` | `ovn-lan` | Perfil para las instancias de la red OVN (`-p default -p ovn-lan`) |

Los dos primeros son de la LAN: deben quedar fuera del DHCP (`192.168.20.31-192.168.23.191`) y del pool de MetalLB
(`192.168.23.200-192.168.23.220`); el preflight falla si solapan.
La base de datos de OVN va por `tcp` sin cifrar (como en la guía de Incus).

## Perfil `ovn-lan` (MTU)

`ovn-lan` tiene MTU 1442 (Geneve usa 58 bytes de los 1500 de `br0`). Las VMs no aplican el MTU del DHCP y quedan en
1500: las descargas grandes de algunos servidores se cuelgan. El perfil lo corrige con cloud-init; el porqué completo
está en [Instancias en `ovn-lan`](https://homelab.maceo.cl/incus/cluster-setup/#instancias-en-ovn-lan-el-perfil-y-el-mtu).

```bash
ansible-playbook -i inventory.ini playbook-incus-cluster.yml --tags ovn-profile --skip-tags always -e incus_ovn_enabled=true -e incus_ovn_confirm=true
incus launch images:debian/13/cloud vm1 --vm -p default -p ovn-lan
```
