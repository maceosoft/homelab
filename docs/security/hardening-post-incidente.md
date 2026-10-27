# Hardening post-incidente

!!! danger "Qué pasó (2026-09)"
    `deborah` (Orange Pi 5 Plus, control plane K3s) quedó expuesta
    directamente a internet — DMZ (zona desmilitarizada)/port-forward en el router hacia su IP —
    todavía con la contraseña por defecto de la imagen del fabricante. Fue
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
2. **Contraseña por defecto sin cambiar.** Las imágenes de SBC —Single Board Computer— (Orange Pi,
   Raspberry Pi, etc.) traen usuario/password documentados públicamente
   en el repo del fabricante — es lo primero que prueba un escáner
   automatizado.

La combinación es letal: no hace falta ni una vulnerabilidad de día cero,
alcanza con un escáner barriendo IPs de internet en busca de SSH (Secure Shell) con
credenciales default.

## El principio que reemplaza la DMZ: acceso remoto solo por la VPN del router

El servidor WireGuard es el router. Este repo no guarda ninguna
configuración ni clave de WireGuard.

- **Nunca** reenvíes en el router un puerto de administración (SSH, UI de
  Incus, API de K3s) directo a un host de la LAN.
- El **único** tráfico que debería llegar de internet a tu red es el de la
  VPN (red privada virtual) del router. Todo lo demás (SSH, Incus, K3s, BIND) se administra
  *a través* del túnel o desde la LAN — nunca directo desde internet.
- Si en algún momento necesitas publicar algo de verdad a internet (un
  servicio web, no de administración), la práctica estándar es un reverse
  proxy en una DMZ real y aislada — no el host que corre el servicio, y
  nunca el mismo host que administra el clúster.

La exposición se limita en el router **y en cada nodo** (ver la siguiente
sección). `roles/host_hardening` no configura el firewall de host: ufw entra
en conflicto con las reglas de iptables de kube-proxy y no es compatible con
K8s (Kubernetes); de eso se ocupa el rol `host_firewall`, que usa `nftables`.

## Firewall de host, servicios expuestos y autenticación

Una auditoría del repo y del clúster vivo encontró que, además de la DMZ del
incidente, los nodos tenían la cadena `INPUT` en `ACCEPT` y varios servicios
accesibles desde toda la LAN y el WiFi sin autenticación. El
resultado, y lo que se hizo con cada hallazgo, está resumido aquí; la regla
general y la lista de excepciones viven en
[Modelo de autenticación](modelo-de-autenticacion.md). La columna "Arreglo" describe el diseño; lo que se despliega por
etapas (NetworkPolicy `default-deny`, etiquetas PSA —Pod Security Admission—, `oauth2-proxy`) se indica como "por activar".

| Hallazgo | Arreglo |
|---|---|
| No había firewall de host gestionado: la LAN y el WiFi alcanzaban `22`, `6443`, `8443`, `10250`, `9100`, `11434`... | Rol `host_firewall` con `nftables`: tabla propia, evaluada antes de kube-proxy y sin tocar las cadenas de Calico |
| Ollama sin autenticación, con `/api/pull`, `/api/create` y `/api/delete` | Socket solo en la IP del nodo, `nftables` con el puerto `11434` solo desde los nodos de K3s y los pods, Kong solo por HTTPS y autenticación Bearer en el router, que además bloquea los verbos de gestión. El Ollama del nodo sigue sin autenticar: la protección real es el token del router más las NetworkPolicy |
| Kong Manager (puertos `8002` y `8445`, NodePort) y Admin API sin autenticación | Kong Manager desactivado; Admin API solo interna (su NetworkPolicy está por activar) |
| Argo CD con el usuario `admin` local y su secreto inicial | `admin.enabled: "false"` y borrar el secreto inicial; el pipeline usa un token `ci` con caducidad |
| Sin NetworkPolicy en `kong`, `monitoring`, `ai`, `longhorn-system`, `gateway` y `arc-*` | Manifiestos de `default-deny` y permisos explícitos por namespace, **por activar** una a una (las de logs, `ai/tools`, `alert-triage` y Open Terminal ya viajan con su aplicación) |
| Open WebUI con registro abierto y sin Dex | Dex con el team `devops`, registro cerrado |
| Incus (`8443`) abierto a la LAN | Limitado por `nftables`; grupo OIDC específico |
| `adbd` (Android Debug Bridge, sin credenciales) escuchando en `deborah:5555`, lanzado por `usbdevice.service` | Deshabilitar y enmascarar esa unidad y verificar que el puerto cierra |
| node-exporter y métricas de MetalLB y FRR abiertos a la LAN | Escuchar solo en la IP del nodo y `nftables` hacia el recolector |
| `alert-triage` y `mcpo` sin token | Token Bearer o clave de API, NetworkPolicy |
| BIND sin transferencias de zona y con la versión visible | `allow-transfer { none; }` y versión oculta. El DNS sirve a toda la red (otras subredes del router, VPN): no se limita por origen ni se activa el límite de tasa (opt-in con `bind_dns_restrict_clients` y `bind_dns_rate_limit_enabled`) |
| K3s sin Dex ni cifrado de Secrets | Banderas `oidc-*` hacia Dex, `--secrets-encryption` e instalador con suma de verificación, configurados en `k3s_install` (`group_vars/incus_cluster/k3s_install.yml`); el server los toma al reinstalarse o al [mover el control plane](../operacion/mover-control-plane.md) |
| `rpcbind`, `dnsmasq`, SSH con `AllowUsers` sin definir, `auditd` mínimo | Deshabilitar lo que no se usa, `AllowUsers devops amaceo` y reglas de `auditd` enviadas a [VictoriaLogs](../operacion/logs.md) |

!!! danger "El firewall se aplica con auto-reversión"
    Un error de `nftables` puede dejarte sin SSH. El rol aplica las reglas con una **auto-reversión a los 300
    segundos (5 minutos)**: se prueban conexiones nuevas (SSH, API de K3s) y hay que confirmar a mano; si no, un
    temporizador de systemd retira las reglas. Se aplica nodo a nodo (`playbook-firewall.yml`): primero
    `--check` en `oliver`, luego `invincible` y por último `deborah`. Para quitarlo de emergencia en el nodo:
    `sudo systemctl disable --now homelab-firewall`. El detalle del rol está en su
    [README](https://github.com/maceosoft/homelab/blob/main/ansible/roles/host_firewall/README.md).

El acceso por SSH con la identidad de Dex (opkssh) solo funciona si la política
desplegada en cada nodo coincide con la organización actual del equipo
(`maceosoft:devops`); si cambia la organización hay que volver a aplicar
`playbook-opkssh.yml`.

La cuenta compartida `devops` (con `sudo` sin contraseña) se mantiene como cuenta
de SSO (inicio de sesión único) por decisión explícita; el control es `AllowUsers` y el rastro de `auditd`.

## Qué hace el hardening (resumen)

Detalle completo en el [README del rol](https://github.com/maceosoft/homelab/blob/main/ansible/roles/host_hardening/README.md).
En corto: SSH sin password (solo key), eliminación de las cuentas por
defecto conocidas (`orangepi`, `pi`, `ubuntu`, `debian`) con su home,
sysctl de red básico, y auditd para tener rastro si algo vuelve a pasar. En
`deborah` además se **regeneran las claves de host de SSH** — las imágenes de
fábrica de SBC a veces repiten tanto la contraseña como las claves de host en
todas las unidades del mismo modelo.

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-hardening.yml --check --diff
ansible-playbook -i inventory.ini playbook-hardening.yml --limit deborah
```

## Orden de reconstrucción de `deborah`

`deborah` es el control plane K3s (`k3s_api_ip` en
`group_vars/all.yml`) — hay que rearmarla en orden antes
de que vuelva a ser útil. El orden completo, paso a paso con los comandos
exactos, vive en un solo lugar para no duplicarlo (y que no se desactualice
en dos partes distintas):

**→ [`ansible/bootstrap/README.md`](https://github.com/maceosoft/homelab/blob/main/ansible/bootstrap/README.md)**

Usa `--limit deborah` en cada paso. La IP fija (`playbook-set-static-ip.yml`) va
**antes** que el hardening.

Notas puntuales:

- **Manual, antes de cualquier paso de Ansible:** al flashear la imagen,
  cambiar la contraseña por defecto y cargar tu clave SSH *antes* de conectar el
  equipo a cualquier red que tenga salida a internet. `playbook-hardening.yml`
  asume que ya existe una clave en `authorized_keys` (aborta si no la
  encuentra) — no reemplaza este paso manual.
- **El hardening va antes de reincorporar `deborah` al clúster** (después
  de la IP fija): no tiene sentido volver a exponer un host sin blindar
  mientras se reconstruye.
- **La CA (autoridad certificadora) y los certificados de K3s (distribución ligera de Kubernetes) se regeneran solos** al hacer `k3s server` limpio en
  la `deborah` reinstalada (no hay backup/snapshot de etcd que restaurar) —
  es, en los hechos, una rotación completa de la raíz de confianza del
  cluster. Si en algún momento tienes un snapshot de etcd de antes del
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
  (ver [Siguiente nivel de endurecimiento](#siguiente-nivel-de-endurecimiento)) en vez de una LAN plana única.

Estos cambios se hacen **solo desde la interfaz web del router**; los menús dependen del modelo.

## Siguiente nivel de endurecimiento

- **Segmentación con VLANs** — separar la VLAN (red local virtual) del clúster HomeLab de
  cualquier otra cosa en la LAN (IoT, invitados, etc.), en vez de confiar
  en una LAN plana única. Requiere hardware/config de red que hoy no está
  declarado en este repo.
- **CIS (Center for Internet Security) Benchmark de Kubernetes / `kube-bench`** sobre K3s — K3s ya pasa
  varios controles CIS por defecto; para los que no, hay que optar
  explícitamente (`protect-kernel-defaults`, `secrets-encryption`,
  `NetworkPolicy`, Pod Security Admission). Ver
  [guía oficial de K3s](https://docs.k3s.io/security/hardening-guide) y
  [`kube-bench`](https://github.com/aquasecurity/kube-bench).
- **Cifrado de secrets en reposo** en K3s (`--secrets-encryption`): ya está en `k3s_install`; el server lo toma al
  reinstalarse (o al [mover el control plane](../operacion/mover-control-plane.md), si algún día se hace).
- **NetworkPolicies** `default-deny` entre namespaces (`ai`, `monitoring`, `longhorn-system`,
  `kong`, `gateway`, `arc-*`): los manifiestos están listos pero se activan por etapas,
  namespace por namespace. Ver [Qué está activo](modelo-de-autenticacion.md#que-esta-activo-y-que-esta-por-activar).
- **Pod Security Admission** (PSA) en modo `warn` y `audit` con el nivel `restricted`
  antes de hacerlo obligatorio (etiquetas listas, por activar).

## Fuentes consultadas

- [Linux Server Hardening Checklist for 2026 — SysWard](https://sysward.com/blog/2026-05-06-linux-server-hardening-checklist/)
- [SSH Hardening Checklist for 2026 (Ubuntu/Debian) — Let's Secure Me](https://letsecure.me/ssh-hardening-checklist-2026-ubuntu-debian/)
- [CIS Hardening Guide — K3s docs](https://docs.k3s.io/security/hardening-guide)
- [CIS Self Assessment Guide — K3s docs](https://docs.k3s.io/security/self-assessment)
- [Kubernetes hardening with kube-bench — CNCF blog](https://www.cncf.io/blog/2025/04/08/kubernetes-hardening-made-easy-running-cis-benchmarks-with-kube-bench/)
- [How to Secure Remote Access to a Homelab — HomelabAddiction](https://homelabaddiction.com/homelab-security/)
