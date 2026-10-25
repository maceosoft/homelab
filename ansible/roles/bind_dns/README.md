# bind_dns

Instala BIND en `deborah`, ejecutándolo en un chroot (`/var/lib/named`),, lo configura como DNS de la LAN y
sirve tres zonas generadas desde el inventario y las variables de Ansible:
`mco.local` (nombres de los hosts), `20.168.192.in-addr.arpa` (reversa) y
`homelab.local` (servidores y servicios publicados, cada uno con su registro
explícito; no hay comodín).

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
4. `/etc/bind/named.conf.local`: declara las zonas `mco.local`,
   `20.168.192.in-addr.arpa` y `homelab.local`.
5. Genera `/var/lib/bind/db.mco.local` (un `A` por host de `incus_cluster`, con su
   `static_ip`; `ns` es `dns_primary` y `k3s` es `k3s_control_plane_host`),
   `/var/lib/bind/db.mco.local.inv` (los `PTR`) y `/var/lib/bind/db.homelab.local`
   (dominio de servicios publicados: un registro por cada servidor de `incus_cluster` con su `static_ip`; `incus` → `incus_cluster_leader`; `argocd`, `vcluster`, `api` y `grafana` → `gateway_ip`, la IP fija del Gateway en MetalLB, definida en `group_vars/all.yml`).
   El serial es la fecha (`YYYYMMDD01`).
6. Habilita `named`; recarga las zonas (`rndc reload`) si cambian los archivos
   y reinicia `named` si cambia la configuración.

## Verificar

```bash
ansible deborah -m command -a "dig @192.168.20.5 oliver.mco.local +short"
ansible deborah -m command -a "dig @192.168.20.5 deb.debian.org +short"
ansible deborah -m command -a "ps -o pid,args -C named"   # named -u bind -t /var/lib/named
```
