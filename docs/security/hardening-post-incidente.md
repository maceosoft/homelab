# Hardening post-incidente

!!! danger "Qué pasó (2026-09)"
    `deborah` (Orange Pi 5 Plus, control-plane K3s) quedó expuesta
    directamente a internet — DMZ/port-forward en el router hacia su IP —
    todavía con la password default de la imagen del fabricante. Fue
    comprometida y hubo que reinstalarla desde cero.

Esta página es la guía para reconstruir `deborah` de forma segura y para
que este incidente no se repita en `invincible`/`oliver`. El playbook y el
rol que la acompañan están en
[`ansible/roles/host_hardening/`](https://github.com/maceosoft/homelab/blob/main/ansible/roles/host_hardening/README.md).

## Causa raíz (y por qué importa el orden)

Dos fallas independientes, cualquiera de las dos sola ya era suficiente:

1. **Exposición directa a internet.** Un port-forward/DMZ en el router
   manda tráfico de internet directo a un host de la LAN (red local), sin ningún
   control intermedio. Cualquier servicio con una vulnerabilidad, o
   cualquier puerto de administración (SSH incluido), queda alcanzable
   por cualquiera en internet.
2. **Password default sin cambiar.** Las imágenes de SBC (Orange Pi,
   Raspberry Pi, etc.) traen usuario/password documentados públicamente
   en el repo del fabricante — es lo primero que prueba un scanner
   automatizado.

La combinación es letal: no hace falta ni una vulnerabilidad de día cero,
alcanza con un scanner barriendo IPs de internet en busca de SSH (Secure Shell) con
credenciales default.

## El principio que reemplaza la DMZ: acceso remoto solo por la VPN del router

El servidor WireGuard es el router. Este repo no guarda ninguna
configuración ni clave de WireGuard.

- **Nunca** forwardees en el router un puerto de administración (SSH, UI de
  Incus, API de K3s) directo a un host de la LAN.
- El **único** tráfico que debería llegar de internet a tu red es el de la
  VPN (red privada virtual) del router. Todo lo demás (SSH, Incus, K3s, BIND) se administra
  *a través* del túnel o desde la LAN — nunca directo desde internet.
- Si en algún momento necesitás publicar algo de verdad a internet (un
  servicio web, no de administración), la práctica estándar es un reverse
  proxy en una DMZ (zona desmilitarizada) real y aislada — no el host que corre el servicio, y
  nunca el mismo host que administra el cluster.

La exposición se limita en el router.
`roles/host_hardening` no configura firewall de host: ufw entra en
conflicto con las reglas de iptables de kube-proxy y no es compatible con
K8s.

## Qué hace el hardening (resumen)

Detalle completo en el [README del rol](https://github.com/maceosoft/homelab/blob/main/ansible/roles/host_hardening/README.md).
En corto: SSH sin password (solo key), eliminación de las cuentas por
defecto conocidas (`orangepi`, `pi`, `ubuntu`, `debian`) con su home,
sysctl de red básico, y auditd para tener rastro si algo vuelve a pasar. En
`deborah` además se **regeneran las host keys SSH** — las imágenes de
fábrica de SBC (Single Board Computer) a veces repiten tanto la password como las host keys en
todas las unidades del mismo modelo.

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-hardening.yml --check --diff
ansible-playbook -i inventory.ini playbook-hardening.yml --limit deborah
```

## Orden de reconstrucción de `deborah`

`deborah` es el control-plane K3s (`k3s_control_plane_host` en
`group_vars/all.yml`) — hay que rearmarla en orden antes
de que vuelva a ser útil. El orden completo, paso a paso con los comandos
exactos, vive en un solo lugar para no duplicarlo (y que no se desactualice
en dos partes distintas):

**→ [`ansible/bootstrap/README.md`](https://github.com/maceosoft/homelab/blob/main/ansible/bootstrap/README.md)**

Usá `--limit deborah` en cada paso. La IP fija (`playbook-set-static-ip.yml`) va
**antes** que el hardening.

Notas puntuales:

- **Manual, antes de cualquier paso de Ansible:** al flashear la imagen,
  cambiar la password default y cargar tu SSH key *antes* de conectar el
  equipo a cualquier red que tenga salida a internet. `playbook-hardening.yml`
  asume que ya existe una key en `authorized_keys` (aborta si no la
  encuentra) — no reemplaza este paso manual.
- **El hardening va antes de reincorporar `deborah` al cluster** (después
  de la IP fija): no tiene sentido volver a exponer un host sin blindar
  mientras se reconstruye.
- **El CA/certs de K3s (distribución ligera de Kubernetes) se regeneran solos** al hacer `k3s server` limpio en
  la `deborah` reinstalada (no hay backup/snapshot de etcd que restaurar) —
  es, en los hechos, una rotación completa de la raíz de confianza del
  cluster. Si en algún momento tenés un snapshot de etcd de antes del
  incidente, **no lo restaures** — traería de vuelta certificados
  potencialmente comprometidos.

## Rotar la password de root

Además del hardening de SSH, conviene rotar la password local de
`root` en los 3 nodos (defensa en profundidad para consola/`su -` — el
login de `root` por SSH ya está deshabilitado). Hay un playbook dedicado
que genera una password nueva por host y la guarda en 1Password (bóveda
`HomeLab`): ver [Gestión de secretos](../secrets/index.md#rotacion-de-password-de-root-1password-sdk-local).

```bash
ansible-playbook -i inventory.ini playbook-rotate-root-passwords.yml \
  --limit deborah
```

## En el router

- Borrar cualquier regla de DMZ/port-forward que apunte a `192.168.20.5`
  (o a cualquier otro nodo).
- Dejar expuesto **únicamente** el servidor WireGuard del router.
- Si el router lo soporta, este es también el momento de evaluar VLANs (redes locales virtuales)
  (ver roadmap abajo) en vez de una LAN plana única.

## Roadmap (no implementado todavía, siguiente nivel)

- **Segmentación con VLANs** — separar la VLAN (red local virtual) del cluster HomeLab de
  cualquier otra cosa en la LAN (IoT, invitados, etc.), en vez de confiar
  en una LAN plana única. Requiere hardware/config de red que hoy no está
  declarado en este repo.
- **CIS (Center for Internet Security) Benchmark de Kubernetes / `kube-bench`** sobre K3s — K3s ya pasa
  varios controles CIS por defecto; para los que no, hay que optar
  explícitamente (`protect-kernel-defaults`, `secrets-encryption`,
  `NetworkPolicy`, Pod Security Admission). Ver
  [guía oficial de K3s](https://docs.k3s.io/security/hardening-guide) y
  [`kube-bench`](https://github.com/aquasecurity/kube-bench).
- **Cifrado de secrets en reposo** en K3s (`--secrets-encryption`).
- **NetworkPolicies** entre namespaces del cluster (hoy no hay ninguna
  declarada en `gitops/`).

## Fuentes consultadas

- [Linux Server Hardening Checklist for 2026 — SysWard](https://sysward.com/blog/2026-05-06-linux-server-hardening-checklist/)
- [SSH Hardening Checklist for 2026 (Ubuntu/Debian) — Let's Secure Me](https://letsecure.me/ssh-hardening-checklist-2026-ubuntu-debian/)
- [CIS Hardening Guide — K3s docs](https://docs.k3s.io/security/hardening-guide)
- [CIS Self Assessment Guide — K3s docs](https://docs.k3s.io/security/self-assessment)
- [Kubernetes hardening with kube-bench — CNCF blog](https://www.cncf.io/blog/2025/04/08/kubernetes-hardening-made-easy-running-cis-benchmarks-with-kube-bench/)
- [How to Secure Remote Access to a Homelab — HomelabAddiction](https://homelabaddiction.com/homelab-security/)
