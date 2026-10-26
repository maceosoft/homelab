# Mover el control plane de K3s a otro nodo (deborah → oliver)

Procedimiento para pasar el **control plane** (el servidor de K3s que guarda el estado del clúster y atiende la
API) de `deborah` a `oliver`, y dejar a `deborah` como **worker**. Se hace en una **ventana de mantenimiento**,
con una persona al teclado: el playbook se detiene en varios **puntos de pausa** para que confirmes cada etapa.

## Por qué se mueve

`deborah` es el equipo con más memoria (31 GB), pero también ejecuta Ollama, es el DNS de la LAN (red local) y
tiene una eMMC (memoria flash soldada) lenta. Un modelo cargado compite con el control plane por memoria.
`oliver` es un nodo ligero (etiqueta `workload-tier=light`) con una carga estable, y `deborah` queda libre para
los modelos y las cargas pesadas.

!!! danger "El clúster no se reconstruye"
    Longhorn (el almacenamiento) guarda su metadata dentro del estado del clúster: si se pierde, los volúmenes
    quedan huérfanos. Por eso este procedimiento **traslada el estado existente**; no reinstala desde cero. Sin
    backup verificado no se empieza.

## Cómo se hace el traslado

Hoy K3s corre con un solo servidor y SQLite (un archivo). La documentación oficial de K3s no describe cómo llevar
ese archivo a otro nodo (y el token incluye el hash de la CA, la autoridad certificadora del clúster). Lo que sí está
documentado es convertir el almacén de datos a **etcd embebido** (la base de datos distribuida de Kubernetes, integrada en K3s), unir otro servidor con el mismo token y quedar con
un solo servidor. El playbook
[`playbook-k3s-move-controlplane.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-k3s-move-controlplane.yml)
hace exactamente eso, por etapas, cada una con su etiqueta (`tag`):

| Etapa | Etiqueta | Qué hace | API |
|---|---|---|---|
| 1 | `preflight` | Verificaciones: nodos `Ready`, Longhorn sin volúmenes degradados, ArgoCD sincronizado | arriba |
| 2 | `backup` | Backup **cifrado** del estado, guardado fuera del nodo (detiene K3s unos minutos en el origen) y generación de un *agent-token* distinto del token de servidor | cae un rato |
| 3 | `convert` | Convierte `deborah` a etcd (`--cluster-init`) con los flags de seguridad y repunta los agentes al nombre `k3s.homelab.local` | cae un rato |
| 4 | `join` | Drena `oliver`, quita su agent y lo une como segundo servidor | arriba |
| 5 | `dns` | `k3s.homelab.local` pasa a apuntar a `oliver` | arriba |
| 6 | `retire` | Deja a `oliver` como único miembro de etcd y a `deborah` como agent | cae un rato |
| 7 | `verify` | Verificación final, resumen de pasos manuales y borrado seguro (`shred`) del backup en claro y de `/root/k3s-move-*` en los nodos | arriba |

El rollback (`--tags rollback`) **nunca corre solo**.

!!! warning "Durante la ventana hay dos miembros de etcd"
    Entre las etapas 4 y 6 el clúster tiene dos miembros de etcd (`deborah` y `oliver`). Con dos miembros no hay
    tolerancia a fallos: si uno cae, el otro pierde el quórum y la API deja de responder. No toques los nodos por
    fuera del playbook durante ese intervalo.

## Prerrequisitos

- [ ] Una ventana en la que la API pueda quedar sin responder varios minutos en las etapas 2, 3 y 6: ArgoCD
      no sincroniza y `kubectl` no responde; las cargas ya en marcha siguen corriendo, salvo los pods de
      `deborah`, que se drenan en la etapa 6.
- [ ] Acceso por SSH a `deborah` y `oliver` ([Entrar por SSH](acceso-ssh.md)) y acceso físico a `deborah`.
- [ ] Longhorn sano y ArgoCD sincronizado (el `preflight` lo comprueba; se puede saltar lo de ArgoCD con
      `k3s_move_allow_unsynced`, pero no conviene).
- [ ] `playbook-bind-dns.yml` ya aplicado, con el registro `k3s` en la zona `homelab.local`: la variable
      `k3s_api_endpoint` (`k3s.homelab.local`) reemplaza a la IP fija del control plane en los agents, el
      kubeconfig y los SAN (nombres alternativos del certificado de la API).
- [ ] La CA del HomeLab en los nodos (rol `opkssh`), porque los servidores nuevos confían en Dex para el login de
      personas.
- [ ] Un método de cifrado para el backup (contiene el token y los certificados del clúster): una clave pública de
      `age` (`k3s_move_backup_age_recipient`) o una contraseña para `gpg` (`k3s_move_backup_passphrase`, mejor por
      variable de entorno). Sin ninguno de los dos el playbook aborta, salvo que lo fuerces con
      `-e k3s_move_backup_unencrypted=true` (no recomendado).
- [ ] `oliver` con unos 5 GB de memoria libre. Si tiene cargas pesadas, muévelas antes.

## Paso a paso

Desde `ansible/`:

1. **Ensayo, sin cambiar nada:**

    ```bash
    ansible-playbook -i inventory.ini playbook-k3s-move-controlplane.yml --check --diff
    ```

2. **Ejecución real.** Con las pausas activas (por defecto), el playbook te pide confirmar antes del backup, antes
   de convertir a etcd, antes de unir a `oliver`, antes de repuntar el DNS y antes de retirar el origen:

    ```bash
    ansible-playbook -i inventory.ini playbook-k3s-move-controlplane.yml
    ```

    Variables útiles: `k3s_move_target` (el destino, por defecto `oliver`), `k3s_move_backup_dir` (dónde se
    guarda el backup, por defecto `~/k3s-move-backups` en tu equipo), `k3s_move_backup_age_recipient` o
    `k3s_move_backup_passphrase` (cifrado), `k3s_move_agent_token` (si quieres fijar el *agent-token* en vez de
    generarlo), `k3s_move_drain_source`, `k3s_move_rotate_secrets`, `k3s_move_allow_unsynced` y
    `k3s_move_confirm=false` para no interactivo (no recomendado).

3. **Puntos de pausa.**
    - Tras el backup: abre el archivo y comprueba su suma antes de seguir.
    - Antes de convertir: es el paso que **no se deshace sin el rollback**.
    - Tras unir a `oliver`: `kubectl get nodes` debe mostrar dos servidores.
    - Tras repuntar el DNS: `dig +short k3s.homelab.local @192.168.20.5` debe devolver la IP de `oliver`.

!!! tip "Si algo no te convence, para"
    Cada pausa admite abortar con `Ctrl+C`. Si el playbook se interrumpe después de la etapa 3, no reanudes con
    `--tags` sueltos: las etapas 4 y 6 necesitan el token que se obtiene en la 3, dentro de la misma ejecución.

Al terminar, el playbook **no modifica el inventario**: lo haces tú, como se explica más abajo. Los agents dejan de usar
el token de servidor y pasan a un **agent-token** propio, que queda en `<k3s_move_backup_dir>/agent-token`.

Con la mudanza también quedan aplicados los endurecimientos del servidor nuevo: banderas `oidc-*` hacia Dex (login
de personas, con `--oidc-username-prefix=oidc:` y `--oidc-groups-prefix=oidc:`), `--secrets-encryption` (cifrado de Secrets en reposo) y el instalador de K3s verificado por suma de
control en vez de `curl | sh`. El certificado de administrador queda solo para emergencias. Ver
[Modelo de autenticación](../security/modelo-de-autenticacion.md).

## Verificación

| Qué | Cómo |
|---|---|
| Nodos | `kubectl get nodes -o wide`: `oliver` con rol `control-plane`, y los tres en `Ready` |
| ArgoCD | `kubectl -n argocd get applications`: todas `Synced` y `Healthy` |
| Longhorn | UI o `kubectl -n longhorn-system get volumes.longhorn.io`: sin volúmenes degradados |
| Kong | `curl -kI https://argocd.homelab.local` responde |
| DNS | `dig +short k3s.homelab.local @192.168.20.5` devuelve la IP de `oliver` |
| Pods | `kubectl get pods -A` sin pods atascados (`Pending`, `CrashLoopBackOff`); los que vivían en `deborah` se reprograman |

## Qué cambia en el inventario después

El playbook no toca estos archivos; edítalos a mano al terminar (y haz commit tú):

- [`inventory.ini`](https://github.com/maceosoft/homelab/blob/main/ansible/inventory.ini): `deborah` pasa de
  `[k3s_server]` a `[k3s_agent]` y `oliver` pasa de `[k3s_agent]` a `[k3s_server]` (y su `k3s_role`).
- `group_vars/all.yml`: `k3s_api_ip` pasa a `192.168.20.7` (la IP de `oliver`) y `k3s_move_done` a `true`.
- `host_vars/deborah.yml` y `host_vars/oliver.yml`: las etiquetas y las opciones de K3s siguen a `k3s_move_done`;
  `deborah` conserva `workload-tier=heavy` y `oliver` sigue siendo `light`.
- Vuelve a aplicar `playbook-bind-dns.yml` para que la zona quede alineada con `k3s_api_ip`.
- **Planes del SUC** (*System Upgrade Controller*, el actualizador automático de K3s; [`k3s-upgrade/`](https://github.com/maceosoft/gitops/tree/main/k3s-upgrade)): seleccionan
  el control plane por la etiqueta `node-role.kubernetes.io/control-plane`, así que no cambian y ahora actualizan primero a `oliver`.

Otras guías que hablan del control plane: [Sacar o reemplazar un nodo](sacar-nodo.md),
[Agregar un nodo](agregar-nodo.md), [Actualizar K3s](actualizar-k3s.md) y la
[Fase 3](../implementacion/fase-3-k3s.md).

## Rollback

Restaura el SQLite original en `deborah` desde el backup y devuelve a `oliver` a agent:

```bash
ansible-playbook -i inventory.ini playbook-k3s-move-controlplane.yml --tags rollback \
  -e k3s_move_backup_stamp=<AAAAMMDDTHHMMSS> \
  -e k3s_move_backup_age_identity=<archivo de identidad age>   # o -e k3s_move_backup_passphrase=...
```

La marca es la parte de fecha del nombre del archivo de backup en el directorio de backups. El rollback son cuatro
pasos, en este orden: **1)** el DNS vuelve a apuntar a `deborah` y se espera unos 300 segundos a que se propague (si
no, el agent reinstalado en `oliver` intentaría unirse a sí mismo por `k3s.homelab.local`); **2)** se restaura el
origen; **3)** `oliver` vuelve a agent; **4)** los demás agents recuperan el token original. **Se pierde todo cambio
del clúster posterior al backup**: decide con calma antes de revertir. Si ya habías editado el inventario, vuelve a
dejarlo como estaba.

## Pasos manuales al terminar

1. **Kubeconfig.** Regenera el de tu equipo, que apuntaba a la IP vieja:

    ```bash
    ansible-playbook -i inventory.ini playbook-k3s.yml --tags kubeconfig
    ```

2. **Guarda los secretos de la mudanza en 1Password.** El *agent-token* (`<k3s_move_backup_dir>/agent-token`) y la
   clave o contraseña con la que cifraste el backup. El backup en claro y los archivos `/root/k3s-move-*` de los nodos
   se borran solos al final (`shred`); lo único que queda es el backup cifrado en tu equipo, que es el que sirve para el
   rollback.
3. **Revisa ArgoCD, Longhorn y Kong** con la tabla de [Verificación](#verificacion).
4. **Permisos del login con Dex.** El repo `gitops` trae el ClusterRoleBinding
   [`oidc-devops-view`](https://github.com/maceosoft/gitops/blob/main/security/rbac/oidc-devops.yaml)
   (Application `security-rbac`, ya activa), que da el ClusterRole `view` (solo lectura) al grupo
   `oidc:maceosoft:devops`. Es inofensivo hasta que haya tokens OIDC.

    !!! info "Por qué solo lectura y no `cluster-admin`"
        Entrar con Dex no debe dar control total del clúster por defecto: el cambio de estado pasa por git y
        ArgoCD, y el certificado de administrador queda para emergencias. Si una persona necesita escribir en un
        namespace, amplía con un `RoleBinding` que enlace el ClusterRole `edit` al mismo grupo **solo en ese
        namespace**, en lugar de ampliar el ClusterRoleBinding.

5. **Opcional, riesgo de Calico.** Comprueba que una cuenta de servicio común no pueda crear políticas globales (ver
   [Comprobaciones opcionales](../security/modelo-de-autenticacion.md#comprobaciones-opcionales)).

### Login de personas con Dex (kubelogin)

Con las banderas `oidc-*` activas, puedes entrar a la API con tu cuenta de GitHub en lugar del certificado de
administrador. Instala el plugin `kubelogin` (`kubectl oidc-login`) y pide un token:

```bash
kubectl oidc-login get-token \
  --oidc-issuer-url=https://argocd.homelab.local/api/dex \
  --oidc-client-id=kubernetes \
  --oidc-extra-scope=email,groups
```

Se abre el navegador; el cliente de Dex `kubernetes` es público (PKCE) y recibe la respuesta en
`http://localhost:8000` (o, de respaldo, `18000`): esos puertos tienen que estar libres en tu equipo. Para usarlo
siempre, configura un usuario en tu kubeconfig con `exec` hacia ese comando.

## Riesgos

- Es un **único** control plane (sin HA, alta disponibilidad): si `oliver` cae, el clúster pierde su API hasta
  restaurar. Las cargas ya iniciadas siguen corriendo.
- Pasar de SQLite a etcd es un cambio de almacén de datos: por eso el backup y el rollback son parte del
  procedimiento, no un extra.

Ver también [Sacar o reemplazar un nodo](sacar-nodo.md), [Actualizar K3s](actualizar-k3s.md) y la
[Fase 3 — K3s](../implementacion/fase-3-k3s.md).
