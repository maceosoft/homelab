# opkssh

Acceso SSH a los hosts (`invincible`, `oliver`, `deborah`) con la identidad de
Dex: el usuario hace login con GitHub y entra si es del team `devops` de la org
`maceosoft`. Instalación y administración: [4.12 — SSH a los hosts con Dex](https://homelab.maceo.cl/implementacion/fase-4-gitops/#412-ssh-a-los-hosts-con-dex-opcional).
Uso (quien solo quiere entrar): [Entrar por SSH a los servidores](https://homelab.maceo.cl/operacion/acceso-ssh/).

Es **aditivo**: no toca `authorized_keys` ni `99-hardening.conf` de
[`host_hardening`](../host_hardening/README.md), así que la llave de emergencia
sigue funcionando.

## Qué hace

1. Crea el usuario de sistema `opksshuser` (ejecuta el `AuthorizedKeysCommand`).
2. Descarga `opkssh` **con versión fijada** y verifica el checksum contra
   `checksums.txt` de la release.
3. `/etc/opk/providers`: solo Dex (no hereda Google, Microsoft, etc.).
4. Policy plugin (`/etc/opk/policy.d/devops-team.yml` + `/etc/opk/devops-team.sh`):
   entra a la cuenta Linux `devops` quien traiga en el token el grupo
   `maceosoft:devops` (el team de GitHub, vía Dex). `/etc/opk/auth_id` queda sin
   reglas. opkssh no puede comparar en `auth_id` grupos que contienen `:`.
5. Crea la cuenta compartida `devops` (grupo `sudo`, sin contraseña, `sudo` sin
   clave porque no tiene contraseña).
6. Instala la CA del HomeLab (la lee de cert-manager con `kubectl`) para que el
   host valide el certificado de Dex.
7. Drop-in `/etc/ssh/sshd_config.d/50-opkssh.conf` con el `AuthorizedKeysCommand`.

## Playbook

[`playbook-opkssh.yml`](../../playbook-opkssh.yml) — `hosts: incus_cluster`.

```bash
export KUBECONFIG=~/.kube/homelab-k3s.yaml
ansible-playbook -i inventory.ini playbook-opkssh.yml --limit oliver --check --diff
ansible-playbook -i inventory.ini playbook-opkssh.yml --limit oliver
```

## Variables

Ver `defaults/main.yml`. Las relevantes: `opkssh_version`, `opkssh_issuer`,
`opkssh_client_id`, `opkssh_key_expiration`, `opkssh_login_user`,
`opkssh_allowed_group`, `opkssh_login_user_sudo_nopasswd`,
`opkssh_install_homelab_ca`.

## Rollback y desinstalación

Para quitar todo lo que instala este rol (sshd, binario, `/etc/opk`, cuenta `devops`):
[`playbook-uninstall-opkssh.yml`](../../playbook-uninstall-opkssh.yml). Es seguro por
defecto: sin `-e opkssh_uninstall_confirm=true` solo muestra qué haría.

## Si el login SSO es rechazado (`Permission denied (publickey)`)

Causa conocida: la política **desplegada** en los nodos quedó con la organización
anterior (`/etc/opk/policy.d/devops-team.yml` y `/etc/opk/devops-team.sh` comparan
contra `symintel:devops`), mientras que el token de Dex trae `maceosoft:devops`. El
repo ya está bien (`opkssh_allowed_group: "maceosoft:devops"`); falta re-aplicar el rol.
En el log de sshd aparece `AuthorizedKeysCommand opkssh verify ... failed, status 1`.

Re-aplicar (el rol es idempotente; solo cambian la política y su script):

```bash
export KUBECONFIG=~/.kube/homelab-k3s.yaml
ansible-playbook -i inventory.ini playbook-opkssh.yml --check --diff   # revisar primero
ansible-playbook -i inventory.ini playbook-opkssh.yml --limit oliver   # piloto
sudo journalctl -u ssh -n 30 --no-pager                                # en el nodo, tras un intento
```

Ansible entra con el usuario local (`amaceo`) y la llave del agente SSH; no depende
del login SSO que se está reparando.
