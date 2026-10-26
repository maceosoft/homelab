# host_hardening

Baseline de endurecimiento de host para los 3 nodos (`invincible`, `oliver`,
`deborah`), compatible con K3s: no gestiona iptables/nftables, que manejan
kube-proxy y el CNI. La exposición a internet se limita en el router (solo
VPN del router reenviada).

## Que hace

1. **SSH** — drop-in en `/etc/ssh/sshd_config.d/99-hardening.conf`:
   `PasswordAuthentication no`, `PermitRootLogin no`, banner legal, timeouts
   de sesion, `MaxAuthTries` bajo. Antes de aplicarlo verifica que el usuario
   de conexion ya tenga una key en `authorized_keys` — si no la tiene, la
   play aborta con un mensaje claro en vez de dejarte afuera del host.
2. **Eliminación de cuentas por defecto** (`host_hardening_known_default_accounts`:
   `orangepi`, `pi`, `ubuntu`, `debian`, más `host_hardening_purge_default_accounts`
   por host) — si existen, se borran con su home (`state: absent, remove: true`).
   El rol se niega a eliminar la cuenta con la que Ansible está conectado, así
   que hace falta otra cuenta admin con key SSH.
   Las cuentas de `host_hardening_disable_password_accounts` solo se bloquean
   (`usermod -L`), sin borrarlas.
3. **Regeneración de host keys SSH** (`host_hardening_regenerate_ssh_host_keys`,
   opt-in por host — hoy `true` en `deborah`) — borra `/etc/ssh/ssh_host_*` y
   corre `ssh-keygen -A`. Idempotente vía un archivo marca.
4. **sysctl** — `/etc/sysctl.d/90-host-hardening.conf`, separado de
   `/etc/sysctl.d/k3s.conf` (rol `k3s_prereqs`): no toca `ip_forward` ni
   `bridge-nf-call-iptables`, los necesitan Incus/K3s.
5. **auditd** — reglas mínimas (`/etc/passwd`, `/etc/shadow`, `sudoers`,
   `sshd_config`).
6. **Sincronización horaria** — instala y habilita `systemd-timesyncd`. Sin
   esto, un nodo puede quedar con el reloj sin corregir (visto en
   `invincible`/`oliver`: sin NTP instalado), lo que rompe la validación de
   certificados TLS del cluster de Incus (`the provided certificate isn't
   valid yet`).

7. **journald** — drop-in `50-homelab.conf`. En hosts con `/var/log` en disco queda
   persistente (tope 200M). En **deborah**, `/var/log` es un tmpfs de 200 MB
   (orangepi-ramlog, con copia periódica en `/var/log.hdd`): un journal persistente ahí
   viviría en RAM, así que se deja **volátil** con tope de 64M (`RuntimeMaxUse`) y los
   logs duraderos van a VictoriaLogs. Interruptor:
   `host_hardening_journald_persist_on_ramlog: true` (persistente bajo `/var/log`, tope
   `host_hardening_journald_ramlog_max_use`).

## Playbook

[`playbook-hardening.yml`](../../playbook-hardening.yml) — `hosts: incus_cluster`
(los 3 nodos), `become: true`.

```bash
# Dry-run primero:
ansible-playbook -i inventory.ini playbook-hardening.yml --check --diff

# Un host por vez la primera vez:
ansible-playbook -i inventory.ini playbook-hardening.yml --limit deborah
```

## Variables

Ver `defaults/main.yml`. Las más relevantes por host van en
`host_vars/<host>.yml`:

- `host_hardening_purge_default_accounts` — cuentas adicionales a eliminar
  en ese host.
- `host_hardening_disable_password_accounts` — cuentas a bloquear sin borrar.
- `host_hardening_regenerate_ssh_host_keys` — regenerar host keys (punto 3).

## Rollback rápido

- SSH: borrar `/etc/ssh/sshd_config.d/99-hardening.conf` y `systemctl reload ssh`
  (requiere acceso por consola/LAN si ya perdiste SSH).
