# incus_dns_zone

Zona DNS de Incus con las instancias de la red OVN (`dns_incus_zone`, hoy `ovn.homelab.local`, para la red
`dns_incus_zone_network`, `ovn-lan`). Incus la genera sola: cada instancia nueva en esa red queda como
`<instancia>.ovn.homelab.local`. BIND (rol [`bind_dns`](../bind_dns/)) la copia como secundario. Guía:
[DNS automático](https://homelab.maceo.cl/networking/dns-automatico/).

## Playbook

[`playbook-bind-dns.yml`](../../playbook-bind-dns.yml), primera play (en `invincible`, el líder del clúster).

## Qué hace

1. `core.dns_address` = `<static_ip>:<dns_incus_port>` en cada miembro del clúster (`--target`), para que BIND pueda
   pedir la zona a cualquiera.
2. Crea la zona si no existe y le fija `dns.nameservers` (sin NS, BIND rechaza la transferencia con
   `has no NS records`) y `peers.bind.address` = `dns_primary` (solo ese servidor puede transferirla, y a él le avisa
   los cambios con NOTIFY).
3. `dns.zone.forward` de la red OVN apuntando a la zona.

Todas las tareas comparan antes de cambiar: una segunda corrida no cambia nada.

## Variables

| Variable | Default | Uso |
|---|---|---|
| `incus_dns_zone_name` | `dns_incus_zone` (`ovn.homelab.local`) | Nombre de la zona |
| `incus_dns_zone_network` | `dns_incus_zone_network` (`ovn-lan`) | Red cuyas instancias se registran |
| `incus_dns_zone_port` | `dns_incus_port` (`8853`) | Puerto del DNS de Incus en cada miembro |
| `incus_dns_zone_peer` | `dns_primary` | Servidor que puede transferir la zona |
| `incus_dns_zone_nameserver` | `ns.homelab.local` | NS de la zona |

Las IPs de la zona son las internas de OVN: con `ovn-lan` aislada (NAT, sin ruta desde la LAN) se resuelven pero no
se alcanzan desde fuera.
