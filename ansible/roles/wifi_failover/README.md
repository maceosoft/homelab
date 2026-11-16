# wifi_failover

WiFi como respaldo del cable, solo en nodos con hardware WiFi
(`has_wifi: true` y `wifi_iface` en `host_vars`).

## Playbook

[`playbook-wifi-failover.yml`](../../playbook-wifi-failover.yml).

## Variables

| Variable | Dónde | Descripción |
|---|---|---|
| `has_wifi` | `host_vars` | Gate del role |
| `wifi_iface` | `host_vars` | Interfaz WiFi física (`ip -br link`) |
| `wifi_ip` | `inventory.ini` | IP fija del WiFi, fuera del DHCP del router (`.9` deborah, `.10` invincible, `.11` eve). Sin ella, DHCP. El rol `bind_dns` la publica como `<nodo>-wifi` |
| `wifi_failover_op_item` | `defaults` | Item de 1Password con el SSID y la clave (`wifi-homelab`, bóveda `HomeLab`) |
| `wifi_failover_op_ssid_field` / `wifi_failover_op_psk_field` | `defaults` | Campos del item (`ssid`, `psk`) |
| `wifi_failover_connection` | `defaults` | Perfil de NetworkManager (`homelab-backup`) |
| `wifi_failover_route_metric` | `defaults` | Métrica del WiFi (`700`, mayor que la del cable) |

El SSID y la clave nunca van al repo: se leen de 1Password en la estación del operador
(`scripts/read_onepassword_field.py`), con la app desbloqueada y `ONEPASSWORD_ACCOUNT_NAME` exportado.

## Qué hace

1. Instala `network-manager`.
2. NetworkManager gestiona **solo** la interfaz WiFi (`unmanaged-devices=*,except:interface-name:<wifi_iface>`).
   Todo lo demás es de netplan (`br0`, la NIC cableada), Calico (`cali*`, `vxlan.calico`), OVN/Open vSwitch o
   Incus: si NetworkManager las toma, les pide IP por DHCP y las deja caídas (pasó en `eve`: sin red en los pods y
   sin salida en la red OVN).
3. `dns=none`: NetworkManager no toca `/etc/resolv.conf` (lo gestiona el rol `netplan_bridge`).
4. Crea el perfil `homelab-backup` con `route-metric 700`: el cable manda mientras esté, el WiFi solo lleva tráfico
   si se cae. Con `wifi_ip`, el perfil usa esa IP fija (también corrige los perfiles que ya existían con DHCP).
5. `arp_ignore=1` y `arp_announce=2` en el WiFi y en `br0`: las dos interfaces están en la misma LAN y, sin esto,
   cada una responde el ARP de la IP de la otra (otros equipos podrían mandar el tráfico del cable por el WiFi).

6. `BindCarrier=<bridge_iface>` para `br0` (drop-in en `/etc/systemd/network/10-netplan-br0.network.d/`):
   `br0` tiene puertos que nunca pierden el enlace (`incusovn1a` de OVN, `tap*` de Incus), así que sin el cable
   seguía "UP" y sus rutas le ganaban al WiFi, que quedaba inalcanzable (pasó en `eve`). Con esto `br0` se baja
   cuando la NIC física pierde el enlace y vuelve a subir cuando vuelve.

Si se corta el cable, la IP fija del nodo (la de `br0`) se cae con él: para el clúster el nodo queda caído igual.
El WiFi da salida a Internet y acceso de emergencia por SSH (`ssh <usuario>@<nodo>-wifi.mco.local`).

Si cambia la clave del WiFi: actualízala en 1Password, borra el perfil en el nodo
(`sudo nmcli connection delete homelab-backup`) y vuelve a correr el playbook.

## Verificar

```bash
ansible <nodo> -i inventory.ini -b -m command -a "nmcli -t -f DEVICE,STATE device"
ansible <nodo> -i inventory.ini -b -m command -a "nmcli -t -f NAME,DEVICE connection show --active"
```
