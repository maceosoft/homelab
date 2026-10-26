# Agregar un nodo

Suma un equipo nuevo al HomeLab como miembro del clúster Incus y como
**worker (agent) de K3s (distribución ligera de Kubernetes)**. Es la misma secuencia que la construcción inicial
([Fases 0 a 3](../implementacion/index.md)), pero limitada a un nodo con
`--limit`, para no tocar los que ya funcionan.

!!! info "Antes de empezar"
    - Debian instalado en el equipo nuevo, con tu usuario administrador creado
      durante la instalación (ver [qué usuario recibe `sudo`](../implementacion/fase-0-preparacion.md#dia-0-nodos-recien-instalados-solo-la-primera-vez-por-nodo)),
      y conectado a la LAN (red local).
    - Una IP fija libre en `192.168.20.0/22` para el nodo.
    - El clúster actual funcionando: Incus y K3s con los 3 nodos sanos.
    - Un nombre para el nodo (los actuales siguen la serie *Invincible*:
      `invincible`, `oliver`, `deborah`). En los ejemplos: **`nolan`**.

Todos los comandos se corren desde `ansible/`.

## 1. Día 0: python3, sudo y tu llave SSH

Un Debian recién instalado no tiene lo que Ansible necesita. Agrega la IP
actual del nodo (la que le dio el DHCP) a `bootstrap/inventory.ini`, en el
grupo `servidores_debian`, y corre:

```bash
ansible-playbook -i bootstrap/inventory.ini bootstrap/setup_sudo.yml --ask-pass --limit <ip-actual>
ssh-copy-id <usuario-admin>@<ip-actual>
```

Detalle: [Fase 0 — Día 0](../implementacion/fase-0-preparacion.md#dia-0-nodos-recien-instalados-solo-la-primera-vez-por-nodo).

## 2. Inventario y variables del nodo

En `inventory.ini`, agrega el nodo a su grupo de arquitectura
(`x86_nodes` o `arm64_nodes`) y al grupo `k3s_agent`:

```ini
[x86_nodes]
# ... nodos existentes ...
nolan ansible_host=<ip-actual> static_ip=192.168.20.8 ip_static=false bridge_iface=eno1 ram_gb=16 cpu_model="..." k3s_role=agent

[k3s_agent]
invincible
oliver
nolan
```

`bridge_iface` es la interfaz de red física: confírmala en el nodo con
`ip -br link`. Los grupos `incus_cluster` y los de K3s están separados a
propósito: un nodo nuevo es **agent**, nunca control plane, salvo que lo
agregues a `k3s_server` a propósito.

Crea `host_vars/nolan.yml` (copia uno existente como base):

```yaml
---
incus_role: "Miembro"
incus_cluster_role: member
incus_cluster_groups: [x86-nodes, default]   # arm64-nodes si es ARM64
k3s_role: agent
ip_static: true
k3s_node_labels:
  node.longhorn.io/create-default-disk: "false"   # "true" si aporta disco a Longhorn
ansible_python_interpreter: /usr/bin/python3
```

!!! tip "Sin tocar playbooks"
    El *join* a Incus, los cluster groups, el scheduler manual, las etiquetas
    de K3s y el DNS se calculan desde `inventory.ini` y `host_vars/`. No hay
    que editar ningún playbook para un nodo nuevo.

Si usas actualizaciones automáticas del SO (`k3s_install.os_hardening`), agrega
también su horario de reinicio en `group_vars/incus_cluster/k3s_install.yml`
(`reboot_schedule`), distinto del de los demás nodos.

## 3. Discovery (opcional, recomendado)

Mide el hardware real del nodo (RAM, discos, red, temperatura) antes de
decidir su rol:

```bash
ansible-playbook -i inventory.ini playbook-discovery.yml --limit nolan
```

El informe queda en `reports/nolan.md`.

## 4. IP fija

Primero revisa qué va a cambiar y después aplica. El playbook tiene una pausa
de seguridad, porque puede cortar la conexión SSH (Secure Shell):

```bash
ansible-playbook -i inventory.ini playbook-set-static-ip.yml --limit nolan --check --diff
ansible-playbook -i inventory.ini playbook-set-static-ip.yml --limit nolan
```

Después, en `inventory.ini`, cambia `ansible_host` a la IP fija y
`ip_static=true`.

## 5. Paquete Incus y hardening

```bash
ansible-playbook -i inventory.ini playbook-bootstrap.yml --limit nolan
ansible-playbook -i inventory.ini playbook-hardening.yml --limit nolan --check --diff
ansible-playbook -i inventory.ini playbook-hardening.yml --limit nolan
```

El hardening desactiva el login con contraseña por SSH: si el paso 1 no
cargó tu llave, el rol se detiene solo antes de dejarte afuera.

## 6. Unir el nodo al clúster Incus

Incluye `invincible` en el `--limit`: es el *leader* que genera el token de
unión y el que asigna los cluster groups.

```bash
ansible-playbook -i inventory.ini playbook-incus-cluster.yml --limit invincible,nolan
```

## 7. Unir el nodo a K3s

Incluye el nodo del control plane (hoy `deborah`; `oliver` tras la [mudanza](mover-control-plane.md)) en el `--limit`: de ahí sale el token
con el que el agent se une. Con solo `--limit nolan` falla con *Falta
k3s_token*.

!!! warning "Versión de K3s"
    El [SUC (System Upgrade Controller)](actualizar-k3s.md) actualiza el
    clúster solo, pero Ansible instala la versión fija de
    `k3s_install.core.version` (`group_vars/incus_cluster/k3s_install.yml`).
    Antes de este paso, pon ahí la versión que tienen hoy los nodos
    (`kubectl get nodes` → columna `VERSION`); si no, el nodo nuevo entra
    con una versión más vieja.

```bash
# el primero es el control plane
ansible-playbook -i inventory.ini playbook-k3s.yml --limit deborah,nolan
```

El mismo playbook aplica las etiquetas de `k3s_node_labels`.

## 8. DNS y extras

Agrega el registro `nolan.mco.local` al DNS (las zonas se generan desde el
inventario):

```bash
ansible-playbook -i inventory.ini playbook-bind-dns.yml
```

Si el nodo tiene WiFi (`has_wifi: true` y `wifi_iface` en su `host_vars`),
configura el WiFi de respaldo:

```bash
ansible-playbook -i inventory.ini playbook-wifi-failover.yml --limit nolan
```

## Verificar

Los `ssh` entran con el [acceso por SSO](acceso-ssh.md): corre `opkssh login` antes (requiere el paso
[4.12](../implementacion/fase-4-gitops.md#412-ssh-a-los-hosts-con-dex-opcional)).

```bash
# nolan en Ready, misma VERSION que el resto
kubectl get nodes -o wide
# etiquetas de k3s_node_labels
kubectl get node nolan --show-labels
# nolan ONLINE
ssh devops@deborah.homelab.local sudo incus cluster list
ssh devops@deborah.homelab.local sudo incus cluster group show x86-nodes
# 192.168.20.8
dig +short nolan.mco.local @192.168.20.5
```

## Si falla

| Síntoma | Revisar |
|---|---|
| `setup_sudo.yml` no conecta | IP actual en `bootstrap/inventory.ini`; que Debian permita todavía root por SSH con contraseña |
| Pierdes SSH tras la IP fija | Conéctate por la IP nueva; revisa `bridge_iface` con `ip -br link` en la consola del equipo |
| El *join* a Incus falla | `--limit` sin `invincible`; espacio libre (≥ 20 GB) en el nodo |
| K3s: *Falta k3s_token* | `--limit` sin el nodo del control plane (`deborah` hoy, `oliver` tras la mudanza) |
| El nodo entra con otra versión de K3s | `k3s_install.core.version` desactualizada (ver el aviso del paso 7) |
