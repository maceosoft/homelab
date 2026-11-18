# bind_dns

Instala BIND en `deborah`, ejecutándolo en un chroot (`/var/lib/named`),, lo configura como DNS de la LAN y
sirve estas zonas:

- `mco.local` (nombres de los hosts) y `20.168.192.in-addr.arpa` (reversa): estáticas, generadas desde el
  inventario.
- `homelab.local`: **dinámica**. Ansible escribe los nombres fijos (nodos, `<nodo>-wifi`, `k3s`, `incus`, `ns`) con
  `nsupdate` y ExternalDNS (gitops) los de las apps de Kubernetes. Ver
  [DNS automático](https://homelab.maceo.cl/networking/dns-automatico/).
- `ovn.homelab.local`: secundaria, copiada de la zona que genera Incus con las instancias de `ovn-lan` (rol
  [`incus_dns_zone`](../incus_dns_zone/)).

## Playbook

[`playbook-bind-dns.yml`](../../playbook-bind-dns.yml) — corre después de
`playbook-set-static-ip.yml` (necesita la IP fija y salida a internet para
`apt`).

## Host

Solo `deborah`.

## Qué hace

1. Instala `bind9` y `bind9-dnsutils` (dig).
2. Chroot en `/var/lib/named`, siguiendo el procedimiento de la
   [wiki de Debian](https://wiki.debian.org/Bind9): crea los directorios,
   monta por bind mount (en `/etc/fstab`) `/dev/null`, `/dev/random`,
   `/usr/share/dns`, `/var/cache/bind`, `/var/lib/bind`, `/run/named` y
   `/run/systemd/notify`, mueve `/etc/bind` al chroot y lo deja como symlink,
   pone `OPTIONS="-u bind -t /var/lib/named"` en `/etc/default/named` y, si
   AppArmor está activo, agrega las rutas del chroot a
   `/etc/apparmor.d/local/usr.sbin.named`.
3. `/etc/bind/named.conf.options`: escucha en `127.0.0.1` y en la `static_ip`
   del host (`192.168.20.5`), responde queries y recursion desde cualquier
   origen (`allow-query`/`allow-recursion any`), y reenvía al `gateway`
   (`192.168.20.1`).
4. Genera `/var/lib/bind/db.mco.local` (un `A` por host de `incus_cluster`, con su `static_ip`; `ns` es
   `dns_primary` y `k3s` es `k3s_api_ip`) y `/var/lib/bind/db.mco.local.inv` (los `PTR`). El serial es la fecha
   (`YYYYMMDD01`).
5. Lee de 1Password (item `bind_dns_tsig_op_item`, `bind-tsig`) las llaves TSIG `homelab-ansible` y
   `homelab-externaldns` y las escribe en `/etc/bind/<llave>.key` (`root:bind 0640`). Para probar sin 1Password se
   pueden pasar con `-e '{"bind_dns_tsig_secrets": {"ansible": "…", "externaldns": "…"}}'`.
6. Crea `/var/lib/bind/db.homelab.local` **solo la primera vez** (SOA, NS y `ns`) y le pone dueño `bind`: desde ahí
   la mantiene BIND, con su diario `.jnl`. Volver a templarla borraría los registros de ExternalDNS.
7. `/etc/bind/named.conf.local`: las llaves, las zonas estáticas, `homelab.local` con su `update-policy` (la llave de
   Ansible escribe todo; la de ExternalDNS todo menos los nombres de `bind_dns_static_records` y el apex) y, con
   `bind_dns_incus_zone_enabled`, la secundaria `ovn.homelab.local` con todos los miembros de Incus como primarios
   (puerto `dns_incus_port`).
8. Reinicia `named` si cambió la configuración y después aplica con `nsupdate -k /etc/bind/homelab-ansible.key`:
   - `homelab-removals.nsupdate`, solo cuando cambia `bind_dns_removed_names` (nombres que antes escribía Ansible y
     ahora publica ExternalDNS, o que ya no existen);
   - `homelab-records.nsupdate`, cuando cambia la lista de fijos o con `-e bind_dns_force_records=true`.

## Verificar

```bash
ansible deborah -m command -a "dig @192.168.20.5 oliver.mco.local +short"
ansible deborah -m command -a "dig @192.168.20.5 deb.debian.org +short"
ansible deborah -m command -a "ps -o pid,args -C named"   # named -u bind -t /var/lib/named
```

## Quién puede consultar el DNS

Este DNS sirve a toda la red: la LAN, otras subredes del mismo router y las VPN. Por defecto
`allow-query` y `allow-recursion` son `any` y el límite de respuestas está apagado, porque
limitarlos dejó sin DNS a equipos de otra subred. Lo que sí se endurece sin bloquear a nadie es
`allow-transfer { none; }` y la versión oculta (`version "none"`). La excepción es `homelab.local`, que se puede
transferir solo con una de sus dos llaves TSIG (ExternalDNS la lee así para saber qué registros son suyos).

Para restringir por origen hay que activarlo de forma explícita: `bind_dns_restrict_clients: true`
(usa la lista `bind_dns_allowed_clients`) y, para limitar ráfagas, `bind_dns_rate_limit_enabled: true`.
Antes de hacerlo, revisa en `journalctl -u named` qué IP de cliente consultan realmente.
