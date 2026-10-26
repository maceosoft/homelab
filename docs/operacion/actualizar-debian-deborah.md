# Actualizar Debian en deborah (12 → 13)

`deborah` (Orange Pi 5 Plus, ARM64) corre **Debian 12 (bookworm)**; los otros dos nodos ya están en **Debian 13
(trixie)**. El playbook
[`playbook-upgrade-debian13.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-upgrade-debian13.yml)
la actualiza con respaldo, una simulación previa y una **compuerta de arranque** que se valida antes de reiniciar.

!!! danger "Es la operación más delicada del HomeLab"
    `deborah` es el **control plane de K3s**, el **DNS de la LAN** (BIND) y miembro de **Incus**. Mientras dura, el
    API de Kubernetes y el DNS no responden (los pods de los otros nodos siguen corriendo). Y si el equipo no arranca
    tras el reinicio, hace falta **acceso físico** (HDMI o consola serie). Haz esto con ventana de mantenimiento.

!!! tip "Más sencillo si el control plane ya se mudó"
    Una vez que el control plane esté en `oliver` ([Mover el control plane](mover-control-plane.md)), `deborah` es
    solo un worker: el API de Kubernetes sigue respondiendo durante la actualización y solo cae su parte de
    carga (el DNS de la LAN, Ollama y los pods que viven en ella). Conviene hacer la mudanza **antes** de esta
    actualización.

## Qué cambia y qué no

| Cambia | No cambia |
|---|---|
| Los paquetes de Debian pasan a trixie (~611 se actualizan; ~42 librerías viejas se eliminan) | **El kernel del fabricante** (`5.10.160-rockchip-rk3588`) y el arranque con u-boot: no vienen de Debian y apt no los toca |
| `systemd`, `glibc`, `openssh`, `bind9`… a las versiones de trixie | K3s (su binario es independiente), Incus (se conserva la versión) y los pods |
| `/tmp` pasa a ser memoria (`tmpfs`) tras el reinicio | `docker-ce` y `containerd.io` (no son de Debian; quedan como están) |

El kernel 5.10 cumple el mínimo recomendado por `systemd` 257 (5.4), pero es un caso fuera de lo habitual: Debian
documenta la actualización para sistemas «puros», no para imágenes de fabricante. Por eso existe la compuerta.

## Antes de empezar

- [ ] **Incus alineado en los tres nodos.** El clúster exige la misma versión en todos los miembros. Hoy `deborah`
  tenía Incus 7.4 y el repositorio ofrecía 7.5.1: actualiza primero Incus en los tres nodos con
  [`playbook-upgrade-incus.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-upgrade-incus.yml)
  (`-e incus_upgrade_confirm=true`; ver [Actualizar o desinstalar Incus](../incus/cluster-setup.md#actualizar-o-desinstalar-incus)).
  El playbook se detiene si no coincide (`upgrade_skip_incus_check=true` lo salta, solo para ensayar).
- [ ] **Acceso físico** a `deborah` (HDMI o consola serie) y, si puedes, una **imagen de la eMMC** (`dd` desde otro
  equipo). Es la única vuelta atrás completa.
- [ ] K3s sano: `kubectl get nodes` con los tres `Ready`, e `incus cluster list` con los tres `ONLINE`.
- [ ] Nadie va a necesitar el DNS ni el API de Kubernetes durante ~30–60 minutos.

## Paso 1 — Preflight y simulación (no cambia nada)

```bash
cd ansible
export KUBECONFIG=~/.kube/homelab-k3s.yaml
ansible-playbook -i inventory.ini playbook-upgrade-debian13.yml
```

Sin `-e upgrade_confirm=true` solo corre `preflight`: comprueba que es Debian 12 en ARM64, espacio libre
(6 GB en `/`, 300 MB en `/boot`), que `dpkg` no tenga problemas, **el arranque** (u-boot, `uInitrd` en gzip, UUID de la
raíz) y la versión de Incus. Después baja los índices de trixie a un directorio aparte (`/var/tmp`), **simula** la
actualización y **falla si eliminaría el kernel, el arranque o un servicio del HomeLab** (`linux-image`, `orangepi`,
`k3s`, `incus`, `bind9`, `openssh-server`, `netplan`…). Luego borra ese directorio.

## Paso 2 — Actualizar

```bash
ansible-playbook -i inventory.ini playbook-upgrade-debian13.yml -e upgrade_confirm=true
```

| Fase (tag) | Qué hace |
|---|---|
| `backup` | Respalda `/etc`, `/boot`, el estado de `dpkg`/`apt`, BIND y K3s (SQLite, certificados y token; **detiene K3s** antes). Trae los archivos a `ansible/backups/` (ignorada por git) |
| `upgrade` | Pausa las actualizaciones automáticas, deja Debian 12 al día, cambia los repositorios a trixie (Debian y Zabbly) y hace `upgrade` y `full-upgrade` conservando tus archivos de configuración (`--force-confold`) |
| `gate` | **Antes de reiniciar:** regenera y valida el `initrd`, comprueba `uInitrd`, `boot.scr`, el DTB, los módulos del kernel, el UUID de la raíz, `sshd -t`, `netplan generate` y la IP de `br0` |
| `reboot` | Reinicia y espera hasta 20 minutos |
| `verify` | Confirma Debian 13 con el mismo kernel, K3s `Ready`, servicios, DNS e Incus |
| `cleanup` | Reactiva los temporizadores de apt y **lista** los paquetes obsoletos (no los borra) |

Si algo falla **antes** del reinicio, el playbook vuelve a arrancar K3s, deja el equipo encendido y te dice dónde
están los logs (`/var/log/pre-trixie-upgrade-*.log`) y el respaldo. Para ensayar sin reiniciar:
`-e upgrade_reboot=false`; el reinicio y la verificación los haces tú (`--tags reboot,verify`).

### Por qué existe la compuerta de arranque

El arranque de la placa depende de un script de u-boot (`boot.scr`) y de un `uInitrd` que el hook
`/etc/initramfs/post-update.d/99-uboot` crea declarándolo **gzip**. Si la actualización dejara el `initrd`
comprimido de otra forma, u-boot no podría descomprimirlo y el equipo **no arrancaría**. El playbook exige
`COMPRESS=gzip` en `initramfs.conf` (se conserva con `--force-confold`) y valida el resultado con `gzip -t` y
`mkimage -l` antes de reiniciar.

## Si el equipo no vuelve

1. Conecta una pantalla o la consola serie y mira dónde se detiene (u-boot, kernel o `systemd`).
2. Si es el arranque: restaura la imagen de la eMMC que hiciste antes. Con la imagen, `deborah` vuelve a Debian 12.
3. Sin imagen: reinstala el sistema de la placa y restaura el respaldo de `ansible/backups/deborah-<fecha>/`:
   `etc.tgz`, `boot.tgz`, `k3s.tgz` (certificados, token y base de datos del control plane, mientras `deborah` lo sea) y `bind.tgz`.
   Sin el token y los certificados de K3s habría que reinstalar el clúster.
4. Los otros dos nodos siguen funcionando mientras tanto, pero sin control plane no hay cambios ni sincronización.

## Después

- `ansible-playbook -i inventory.ini playbook-upgrade-debian13.yml --tags verify` repite la verificación cuando quieras.
- **No purgues a ciegas** la lista de paquetes obsoletos: incluye `linux-image-legacy-rockchip-rk3588`,
  `orangepi-*` y `linux-u-boot-*`, que son los que hacen arrancar la placa.
- Con `deborah` en Debian 13, las versiones de OVN y Open vSwitch ya coinciden con las de los otros nodos (condición
  previa para considerar OVN: ver [Balanceo de carga y OVN](../incus/cluster-setup.md#balanceo-de-carga-y-ovn)).
- **Dos unidades pueden quedar en `failed` tras el reinicio** (`systemctl --failed`), sin afectar al clúster:
  `smartmontools` (la eMMC no tiene SMART y en Debian 13 el servicio viene habilitado) y `dnsmasq` (el puerto 53 ya lo
  ocupa BIND, que es el DNS de la LAN). Si no usas esas unidades, deshabilítalas con `systemctl disable --now dnsmasq
  smartmontools`.
- El paquete `wiringpi` está retenido (`apt-mark hold`) y los `docker-ce` / `containerd.io` no son de Debian: siguen
  como estaban; revísalos si dan problemas.

## Variables

Se pasan con `-e nombre=valor` (nunca con puntos).

| Variable | Por defecto | Para qué |
|---|---|---|
| `upgrade_confirm` | `false` | `true` ejecuta de verdad; `false` solo preflight |
| `upgrade_reboot` | `true` | `false` se detiene antes del reinicio |
| `upgrade_autoremove` | `false` | `true` ejecuta `apt autoremove` al final |
| `upgrade_skip_incus_check` | `false` | `true` salta la comprobación de versión de Incus (solo para ensayar) |
| `upgrade_debian_mirror` | `http://ftp.cl.debian.org/debian` | Espejo de Debian |
| `upgrade_security_mirror` | `http://security.debian.org/debian-security` | Repositorio de seguridad |
