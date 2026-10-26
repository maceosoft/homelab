# Bootstrap de un nodo — orden de pasos

Runbook de referencia: **el orden correcto** para llevar un nodo (o los 3)
de bare-metal a completamente operativo. No es un playbook nuevo —
consolida en un solo lugar una secuencia que hoy está repartida en 9+
playbooks sueltos, cada uno documentado por separado. Pensado sobre todo
para el caso real de este repo ahora mismo: reconstruir `deborah` desde
cero tras el incidente de seguridad (ver
[Hardening post-incidente](../../docs/security/hardening-post-incidente.md)).

Incluye `setup_sudo.yml` de este mismo directorio (`bootstrap/`),
que resuelve el problema de "día 0": un nodo recién instalado no tiene
python3 ni sudo listos para que el resto de `ansible/` funcione — ver
Paso -1 abajo.

No automatiza la cadena completa a propósito — cada paso es un comando
separado para poder revisar el resultado (y frenar) antes de seguir al
siguiente, según el mismo criterio de seguridad que ya usa este repo (ver
`playbook-set-static-ip.yml`, que tiene su propia pausa de seguridad).

## Dos escenarios

- **Fleet nueva (los 3 nodos, primera vez):** corré cada paso sin `--limit`
  (aplica a `incus_cluster` = los 3).
- **Reconstruir un nodo puntual** (ej. `deborah` post-incidente): agregá
  `--limit deborah` a cada comando. Los demás nodos no hace falta
  re-tocarlos, solo que su estado en `inventory.ini` / `host_vars/` sea el
  actual.

Todos los comandos se corren desde `ansible/`:

```bash
cd ansible
```

## Qué usuario recibe `sudo`

`setup_sudo.yml` da `sudo` sin contraseña al **usuario administrador que creaste al instalar Debian**. No hay un
nombre fijo en el repo:

- Por defecto es el **nombre de tu usuario en la estación** desde la que corres Ansible (variable `USER`). Es el
  mismo con el que Ansible se conecta después, porque `ansible.cfg` no fija `remote_user`.
- Si en el nodo se llama distinto, indícalo y dile a Ansible cómo conectarse:

  ```bash
  ansible-playbook -i bootstrap/inventory.ini bootstrap/setup_sudo.yml --ask-pass -e bootstrap_admin_user=<usuario>
  ```

  y agrega `ansible_user=<usuario>` a las variables de los nodos en `inventory.ini` (o `remote_user = <usuario>` en
  `ansible.cfg`).
- El usuario **debe existir ya** en el nodo: el playbook se detiene si no. Solo admite minúsculas, dígitos, `_` y `-`
  (un punto haría que `sudo` ignore el archivo de `/etc/sudoers.d/`).

## Orden

| # | Paso | Comando | Depende de |
|---|---|---|---|
| — | **Manual, antes de conectar a ninguna red con salida a internet:** flashear el OS. Debian netinst ya te hace crear un usuario normal (tu usuario administrador) durante la instalación — no hace falta más todavía; la SSH key y el hardening real de cuentas vienen después. | — | — |
| -1 | **Día 0:** instalar python3+sudo y sumar tu usuario administrador al grupo sudo (conectando como `root` con password — único acceso posible en un nodo recién instalado) | `ansible-playbook -i bootstrap/inventory.ini bootstrap/setup_sudo.yml --ask-pass` | Root SSH con password todavía habilitado (se cierra en el paso 4) |
| — | **Manual:** cargar tu SSH key en tu usuario administrador (`ssh-copy-id`, no hace falta un playbook para esto) | `ssh-copy-id <usuario-admin>@<ip-actual-del-nodo>` | Paso -1 (tu usuario ya existe y ya tiene shell propia) |
| 0 | Discovery (opcional, recomendado 1ª vez) | `ansible-playbook -i inventory.ini playbook-discovery.yml` | Paso -1 |
| 1 | IP fija en `br0` + gateway/DNS | `ansible-playbook -i inventory.ini playbook-set-static-ip.yml --check --diff` luego sin `--check` | SSH key cargada (paso anterior); Paso 0 opcional |
| 2 | **BIND** en deborah (instala y configura el DNS `192.168.20.5`, el primer DNS de los 3 nodos) | `ansible-playbook -i inventory.ini playbook-bind-dns.yml` | Paso 1 (deborah con IP fija y salida a internet) |
| 3 | Paquete Incus | `ansible-playbook -i inventory.ini playbook-bootstrap.yml` | Paso 1 |
| 4 | **Hardening** (SSH, cuentas default, sysctl, auditd) | `ansible-playbook -i inventory.ini playbook-hardening.yml --check --diff` luego sin `--check` | Paso 1 (IP ya fija) |
| 5 | Cluster Incus (join/groups/UI) | `ansible-playbook -i inventory.ini playbook-incus-cluster.yml` | Paso 3, 4 |
| 6 | K3s (control-plane/agent) | `ansible-playbook -i inventory.ini playbook-k3s.yml` | Paso 5 |
| 7 | WiFi de respaldo (nodos con `has_wifi: true`) | `ansible-playbook -i inventory.ini playbook-wifi-failover.yml` | Paso 1 |
| — | Rotar password de root (opcional, periódico) | `ansible-playbook -i inventory.ini playbook-rotate-root-passwords.yml` | Cualquier momento tras el paso 4 |
| — | Provisionar disco libre (opcional, destructivo) | `ansible-playbook -i inventory.ini playbook-storage-provision.yml --limit <host>` | `storage_provision_disks` definido en host_vars; ver paso 0 |

Todos con `--limit <host>` para un nodo puntual.

## Fuera de esta secuencia (no son "bootstrap de nodo")

- `playbook-dex-oauth-secrets.yml` — secretos OAuth a nivel de clúster
  (Argo CD/Incus/vCluster), se corre una vez que K3s+Argo CD ya están
  arriba, no por nodo. Ver [Gestión de secretos](../../docs/secrets/index.md).
- `playbook-k3s-uninstall.yml` — apéndice fuera del recorrido normal.

## Por qué no es un solo playbook encadenado

Cada paso puede cortar la conexión SSH activa (netplan, hardening) o dejar
un cluster a medio converger si algo falla a mitad de camino en un nodo
físico real — no es un entorno descartable. Encadenar los pasos con
`import_playbook` sin pausas intermedias sería más cómodo pero elimina la
oportunidad de revisar cada `--check --diff` antes de aplicar el
siguiente. Si en algún momento se automatiza esta cadena, que sea explícito
y opt-in, no el camino por defecto.

## Nota sobre `docs/implementacion/` (Fase 0–6)

La guía de implementación publicada (Fase 0 a 6) ya enlaza tres pasos de
este runbook: el paso -1 de día 0 (Fase 0), y BIND (paso 2) y el hardening
(paso 4) en Fase 1, justo después de la IP fija. El WiFi de respaldo todavía
no tiene un lugar formal en esa guía. Esta tabla sigue siendo la única
referencia con el orden completo de todos los pasos juntos.
