# Clúster Incus

!!! info "Parte de la guía de implementación"
    Sigue **[Fase 2 — Incus](../implementacion/fase-2-incus.md)** para el orden
    completo. **Ansible** ejecuta bootstrap, join, cluster groups, scheduler y UI (interfaz de usuario)
    vía [`playbook-incus-cluster.yml`](https://github.com/symintel/homelab/blob/main/ansible/playbook-incus-cluster.yml).
    Los bloques manuales siguientes son referencia.

## Automatización (Ansible)

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-bootstrap.yml
ansible-playbook -i inventory.ini playbook-incus-cluster.yml
```

Roles: [`incus_cluster`](https://github.com/symintel/homelab/blob/main/ansible/roles/incus_cluster/README.md),
[`incus_ui`](https://github.com/symintel/homelab/blob/main/ansible/roles/incus_ui/README.md).

## Almacenamiento

Default HomeLab: driver **`dir`**, pool **`local`**, ruta
`/var/lib/incus/storage-pools/local`. Ansible valida ≥ **20 GB** libres antes del
init (`incus_storage_min_free_gb` en
[`group_vars/incus_cluster/vars.yml`](https://github.com/symintel/homelab/blob/main/ansible/group_vars/incus_cluster/vars.yml)).

| Aspecto | Default |
|---|---|
| Driver | `dir` |
| Pool | `local` (uno por miembro) |
| Ruta | `/var/lib/incus/storage-pools/local` |
| Perfil `default` | root en `local`, NIC bridged a `br0` |

### Por nodo

| Nodo | Nota |
|---|---|
| invincible | 224 GB SSD; leader + UI |
| oliver | 120 GB SSD; pool local obligatorio; scheduler manual |
| deborah | eMMC boot; override opcional a NVMe: `incus_storage_path: /srv/incus/storage-pools/local` |

### Limitaciones de `dir`

- Sin CoW a nivel de pool; snapshots de instancia y export tarball sí.
- VMs (máquinas virtuales) más lentas que con `zfs`/`btrfs`.
- Cada miembro tiene pool local; no hay Ceph por defecto.

### Alternativas

| Driver | Cuándo | Variable |
|---|---|---|
| `dir` | **Default** HomeLab | `incus_storage_driver: dir` |
| `btrfs` | Snapshots eficientes | `incus_storage_driver: btrfs` + disco/subvolumen |
| `zfs` | VMs + snapshots avanzados | `incus_storage_driver: zfs` |
| `lvm` | Thin LVM para VMs | `incus_storage_driver: lvm` |

<div class="card">
  <div class="card-kicker">Análisis de trade-offs</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">Ansible (<code>playbook-incus-cluster.yml</code>)</div>
      <div class="text-muted">Bootstrap/join/UI idempotente</div>
      <div class="text-muted">Requiere playbook previo (<code>incus_install</code>)</div>
    </div>
    <div class="card-col">
      <div class="card-title">Manual</div>
      <div class="text-muted">Depuración nodo a nodo</div>
      <div class="text-muted">Tokens de un solo uso</div>
    </div>
    <div class="card-col">
      <div class="card-title"><code>dir</code></div>
      <div class="text-muted">Sin disco dedicado</div>
      <div class="text-muted">VMs lentas; sin CoW de pool</div>
    </div>
    <div class="card-col">
      <div class="card-title"><code>btrfs</code> / <code>zfs</code></div>
      <div class="text-muted">Snapshots eficientes</div>
      <div class="text-muted">Disco/loop; migración si ya clusterizado</div>
    </div>
    <div class="card-col">
      <div class="card-title">UI vía Ansible</div>
      <div class="text-muted">Mismo playbook que el clúster</div>
      <div class="text-muted">Solo en invincible (daemon nativo)</div>
    </div>
  </div>
</div>

!!! warning "Clúster ya inicializado"
    Cambiar driver requiere migración manual; elige antes del primer playbook.

Docs: [Storage pools](https://linuxcontainers.org/incus/docs/main/explanation/storage/)

## Bootstrap (invincible) — manual

```bash
curl https://pkgs.zabbly.com/get/incus-stable | sudo bash -x
sudo incus admin init
# clustering=yes, no te unes (bootstrap), storage backend dir
```

## Join (oliver y deborah) — manual

```bash
incus cluster add oliver           # ejecutar en invincible; genera token de un solo uso
incus cluster add deborah   # otro token distinto
```
En cada nodo: instalar Incus y `incus admin init`, respondiendo que sí te unes, con el token correspondiente.

## Cluster groups (arquitectura)

```bash
incus cluster group create x86-nodes
incus cluster group create arm64-nodes

incus cluster group assign invincible x86-nodes,default
incus cluster group assign oliver x86-nodes,default
incus cluster group assign deborah arm64-nodes,default
```

## Proteger la RAM de oliver (scheduler manual)

oliver tiene 7.7 GB medidos, así que se mantiene como nodo ligero para quorum
Incus sin instancias automáticas:

```bash
incus cluster set oliver scheduler.instance manual
```
Excluye a `oliver` del scheduling automático; solo recibe instancias si se apunta
explícitamente con `--target=oliver`. Sigue contando como voto de quorum.

## Máquinas virtuales (VM)

### Qué nodos pueden correr VMs

Una VM necesita KVM (Kernel-based Virtual Machine, virtualización por hardware del kernel), el módulo de kernel `vhost_vsock` y el driver `qemu` de
Incus. Cómo está cada nodo:

| Nodo | Arquitectura | ¿Corre VMs? | Motivo |
|---|---|---|---|
| invincible | x86_64 | Sí | Driver `lxc` + `qemu`, `vhost_vsock` disponible |
| oliver | x86_64 | Sí | Igual que invincible |
| deborah | ARM64 | **No** | Su kernel del fabricante (5.10, Rockchip) se compiló sin `vhost_vsock`, y su driver de Incus es solo `lxc` |

Si una VM se crea con el destino en `Auto` y el planificador elige a deborah, falla con
`Instance type "virtual-machine" is not supported on this server: vhost_vsock kernel module not loaded`.
Indica siempre el nodo:

```bash
incus launch images:debian/12 mi-vm --vm --target invincible
```

En la UI, en el formulario de creación, elige la imagen primero (hasta entonces **Instance type**, **Target** y
**Profiles** salen deshabilitados), después **Virtual machine** y en **Target** un nodo x86 (invincible u oliver).

### Imágenes `cloud` y el disco del agente

Las VMs de Incus se controlan desde fuera mediante `incus-agent`, un programa que corre dentro de la VM y permite
`incus exec`, la consola, copiar archivos, ver la IP y apagar la VM limpiamente. Incus se lo entrega a la VM como un
disco virtual de solo lectura llamado `agent:config`, que lleva el binario, sus certificados y el servicio que lo arranca.

Con una imagen normal (p. ej. `almalinux/8`) Incus lo añade solo. Las variantes `cloud` (p. ej. `almalinux/8/cloud`,
pensadas para cloud-init, que configura usuario, claves SSH y red al arrancar) exigen añadirlo a mano. Si falta, la VM
no arranca:

```text
Error: This virtual machine image requires an agent:config disk be added
```

El perfil `default` no lo incluye (tampoco debe: lo comparten los contenedores y `agent:config` solo vale en VMs).
Añádelo a la VM:

```bash
incus config device add mi-vm agent disk source=agent:config
incus start mi-vm
```

O, si usas imágenes `cloud` a menudo, crea un perfil aparte y aplícalo al lanzar:

```bash
incus profile create vm-agent
incus profile device add vm-agent agent disk source=agent:config
incus launch images:almalinux/8/cloud mi-vm --vm -p default -p vm-agent --target invincible
```

Desde la UI: **Instances → (la VM) → Configuration → YAML configuration**, y dentro de `devices:` agrega

```yaml
devices:
  agent:
    type: disk
    source: agent:config
```

Guarda con **Save changes** y pulsa **Start**.

## UI de administración

Incus expone una **interfaz web nativa** (`incus-ui-canonical`) para gestionar
instancias, perfiles, redes y el clúster. No usa kubeconfig; la autenticación
inicial es por **certificado de cliente** y, tras Fase 4, por **OIDC (OpenID Connect)** (Dex → GitHub).

### Instalación (Ansible o manual)

Ansible instala la UI en **invincible** (`incus_ui`, tag `ui`). La UI **no** es
un contenedor: la sirve el daemon de Incus en `core.https_address`.

=== "Ansible (recomendado)"

    Incluido en `playbook-incus-cluster.yml` (tag `ui`).

=== "Manual"

    En **invincible**:

    ```bash
    sudo apt install incus-ui-canonical
    sudo incus config set core.https_address=:8443
    ```

`/etc/hosts` en tu estación — bloque completo en
[Resumen del HomeLab](../implementacion/resumen-homelab.md#dns-en-tu-estacion-de-trabajo):

Acceso inicial: [`https://incus.homelab.local:8443`](https://incus.homelab.local:8443) → certificado de cliente.

<div class="card">
  <div class="card-kicker">UI</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">Ansible (tag <code>ui</code>)</div>
      <div class="text-muted">Incluido en <code>playbook-incus-cluster.yml</code></div>
      <div class="text-muted">Solo en invincible</div>
    </div>
    <div class="card-col">
      <div class="card-title">Manual (<code>apt</code> + <code>config set</code>)</div>
      <div class="text-muted">Sin Ansible</div>
      <div class="text-muted">Fácil desalinear con el resto del clúster</div>
    </div>
  </div>
</div>

### OIDC vía Dex (Fase 4)

Con OIDC configurado, la pantalla de acceso de la UI ofrece **Login with SSO** (GitHub a través de Dex) y **Login with TLS** (certificado de cliente):

??? note "Ver captura: acceso a Incus UI"
    ![Pantalla de acceso de Incus UI con las opciones «Login with SSO» y «Login with TLS»](../assets/screenshots/incus-ui-login.jpg){ loading=lazy }

Tras [Fase 4 — Incus UI OIDC](../implementacion/fase-4-gitops.md#incus-ui-oidc), con la CA del
HomeLab ya instalada en el nodo (ver el aviso de abajo):

```bash
incus config set oidc.issuer=https://argocd.homelab.local/api/dex
incus config set oidc.client.id=incus-ui
```

Incus (7.x) solo conoce cinco claves OIDC: `oidc.issuer`, `oidc.client.id`, `oidc.audience`,
`oidc.claim` y `oidc.scopes`. No existen `oidc.client.secret` ni `oidc.groups.claim`: Incus no envía
secreto, así que en Dex el cliente `incus-ui` es **público** (PKCE, `public: true`).

!!! warning "Incus tiene que confiar en la CA del HomeLab"
    El certificado de Dex lo firma la CA propia del HomeLab (cert-manager). Si el nodo
    no la conoce, Incus no puede validar al proveedor de identidad y el login falla. El
    playbook (`--tags incus`, o solo `--tags incus_ca`) la instala en `invincible` y
    reinicia `incus`. A mano, en el nodo:

    ```bash
    kubectl -n cert-manager get secret homelab-ca -o jsonpath='{.data.ca\.crt}' | base64 -d \
      | sudo tee /usr/local/share/ca-certificates/homelab-ca.crt > /dev/null
    sudo update-ca-certificates
    sudo systemctl restart incus
    ```

    Comprueba con `curl -s -o /dev/null -w "%{http_code} ssl_verify=%{ssl_verify_result}\n" https://argocd.homelab.local/api/dex/.well-known/openid-configuration`
    (debe dar `200 ssl_verify=0`). Detalle en la
    [Fase 4](../implementacion/fase-4-gitops.md#incus-ui-oidc).

### Permisos de los usuarios OIDC

Incus 7.x **no** trae `incus auth` (grupos y `identity-provider-group` son de LXD). Con OIDC:

| Escenario | Resultado |
|---|---|
| Miembro del team `devops` de la org `symintel` | Dex lo deja pasar y, con la configuración por defecto de Incus, tiene **acceso completo** |
| Cuenta que no está en ese team | Dex rechaza el login: nunca llega a Incus |

El control de acceso es, entonces, la pertenencia al team `devops` (filtro `orgs`/`teams` del
conector GitHub en `dex.config`). Para permisos granulares (por proyecto, solo lectura) Incus
usa [OpenFGA](https://linuxcontainers.org/incus/docs/main/authentication/), que no está
configurado en el HomeLab.

Referencias:

- [Incus OIDC](https://linuxcontainers.org/incus/docs/main/authentication/#openid-connect-oidc-authentication)

## Balanceo de carga y OVN

Incus tiene balanceadores de red (`incus network load-balancer`) y reenvíos de puertos (`incus network forward`), pero
**los balanceadores de red solo existen en redes OVN** (Open Virtual Network, red virtual definida por software). En el
HomeLab se despliega **OVN** (ver [Desplegar OVN y los segmentos](#desplegar-ovn-y-los-segmentos)):
`br0` sigue siendo un bridge sin administrar para las instancias existentes, y se crean la red uplink `UPLINK` y la red OVN `ovn-lan`,
con lo que los balanceadores de red están disponibles.

!!! note "`lb01` no es el balanceador de Incus"
    La instancia `lb01` que aparece en `incus list` es un contenedor OCI de `nginx` (de prueba). El balanceo real del
    HomeLab está en otras capas:

| Qué se balancea | Quién lo hace | Dónde |
|---|---|---|
| Aplicaciones de Kubernetes (Services `LoadBalancer`) | **MetalLB**, con las IP `192.168.23.200–.220` (el Gateway de Kong usa `.200`) | [Catálogo GitOps](../gitops/index.md) |
| Control plane de los clústeres de Cluster API | **CAPN**, con su propio balanceador (`LOAD_BALANCER='lxc: {}'`, un contenedor dentro de Incus) | [Fase 6 — CAPN](../implementacion/fase-6-capn.md) |
| API de K3s | La IP del control plane (`kube-vip` es opcional y está desactivado) | [Fase 3 — K3s](../implementacion/fase-3-k3s.md) |

### ¿Conviene habilitar OVN?

Qué exige OVN y qué implica para el HomeLab. Los segmentos y el despliegue están en [Desplegar OVN y los segmentos](#desplegar-ovn-y-los-segmentos).

| Requisito de OVN | Estado en el HomeLab |
|---|---|
| Paquetes `ovn-central` (3 nodos, base de datos en alta disponibilidad), `ovn-host` y `openvswitch-switch` | Están en Debian en los tres nodos, **con las mismas versiones** (OVN 25.03 y Open vSwitch 3.5) mientras los tres nodos estén en Debian 13 |
| Red de capa 2 compartida entre los nodos | Sí: los tres están en la misma LAN por `br0` |
| Uplink: un bridge sin administrar o una NIC sin usar | `br0` sirve; no haría falta rehacerlo |
| Rango de IP reservado fuera del DHCP para el router de OVN y las IP virtuales | Definido: `192.168.23.224/28` (LB) y `192.168.23.240–.249` (OVN externo), fuera del DHCP y de MetalLB. Ver [Desplegar OVN y los segmentos](#desplegar-ovn-y-los-segmentos) |
| Instancias dentro de una red OVN | Las instancias que cuelgan de `br0` (como `lb01`, `test` y `vm01`) tienen IP de la LAN: para usar OVN hay que conectarlas a `ovn-lan` |
| Memoria por nodo (OVS, `ovn-controller` y la base de datos central) | `oliver` tiene 7.7 GB: conviene medir allí el consumo de OVN |

| A favor | En contra |
|---|---|
| Balanceadores y reenvíos nativos en Incus | Tres componentes nuevos por nodo y una base de datos distribuida que operar |
| Redes virtuales aisladas por proyecto o clúster, con ACL | Hay que reservar un rango de IP nuevo y mover las instancias que quieran usarlas |
| `LOAD_BALANCER: ovn` en CAPN para los clústeres de la Fase 6 | Solo beneficia a instancias que se muevan a una red OVN; K3s corre en los hosts y no se beneficia |

### Desplegar OVN y los segmentos

El rol [`incus_ovn`](https://github.com/symintel/homelab/blob/main/ansible/roles/incus_ovn/README.md), dentro de
[`playbook-incus-cluster.yml`](https://github.com/symintel/homelab/blob/main/ansible/playbook-incus-cluster.yml), instala OVN en los tres
nodos (la base de datos en alta disponibilidad, con `invincible` creándola y los otros uniéndose), configura Incus y crea la red
*uplink* sobre `br0` y una red OVN. Es **seguro por defecto**: sin `-e incus_ovn_confirm=true` solo hace el preflight (versión de Incus,
paquetes, memoria libre, que `br0` exista y que las IP reservadas no respondan) y no instala nada. Con
`incus_ovn_enabled: false` (el valor por defecto) el playbook del clúster ni siquiera lo toca.

| Segmento | Valor | Dónde se configura | Variable |
|---|---|---|---|
| **LB** (IP de los balanceadores y reenvíos) | `192.168.23.224/28` | `ipv4.routes` de la uplink | `incus_ovn_lb_routes` |
| **OVN externo** (una IP por router virtual) | `192.168.23.240–192.168.23.249` | `ipv4.ovn.ranges` de la uplink | `incus_ovn_external_ranges` |
| **OVN interno** (subred privada, con NAT) | `192.168.19.1/24` | `ipv4.address` de la red `ovn-lan` | `incus_ovn_internal_cidr` |

Los dos primeros son de la LAN (`192.168.20.0/22`) y deben quedar **fuera del DHCP del router** (`192.168.20.31–192.168.23.191`) y del
pool de MetalLB (`192.168.23.200–.220`). El reparto de la zona libre alta de la LAN:

| Rango | Uso |
|---|---|
| `192.168.23.192–.199` | Libre |
| `192.168.23.200–.220` | **MetalLB** (21 IP; el Gateway de Kong usa `.200`) |
| `192.168.23.221–.223` | Libre |
| `192.168.23.224/28` (`.224–.239`) | **LB de Incus** (16 IP) |
| `192.168.23.240–.249` | **OVN externo** (10 IP, un router virtual por red OVN) |
| `192.168.23.250–.255` | Libre (`.255` es el broadcast de la `/22`, no se usa) |

El preflight **falla si los segmentos solapan** con el DHCP, con MetalLB, entre sí o con el broadcast. El interno es privado y no toca la
LAN: tampoco solapa con los rangos de K3s (`10.42.0.0/16` y `10.43.0.0/16`). Las instancias actuales (`lb01`, `test`, `vm01`) siguen en
`br0`: solo las que conectes a `ovn-lan` usan OVN.

```bash
cd ansible && source ../.venv/bin/activate
ansible-playbook -i inventory.ini playbook-incus-cluster.yml --tags ovn --skip-tags always -e incus_ovn_enabled=true                         # preflight
ansible-playbook -i inventory.ini playbook-incus-cluster.yml --tags ovn --skip-tags always -e incus_ovn_enabled=true -e incus_ovn_confirm=true  # instala
```

Después, un balanceador de red se crea con `incus network load-balancer create ovn-lan 192.168.23.225` y su configuración.
La dirección de escucha debe estar en el `ipv4.routes` de la uplink y no solapar con otra red en uso.

**Comprobar el despliegue:** `ovn-central`, `ovn-controller` y Open vSwitch activos en los tres nodos; la base de datos Northbound en clúster
con líder (`ovn-appctl -t /var/run/ovn/ovnnb_db.ctl cluster/status OVN_Northbound`); un *chassis* Geneve por nodo (`ovn-sbctl show`); y
`UPLINK` y `ovn-lan` en estado `Created` (`incus network list`).

!!! warning "La base de datos de OVN no va cifrada"
    Siguiendo la guía de Incus, el playbook publica las bases de datos de OVN por `tcp` sin SSL en la LAN de los nodos.
    Es aceptable en un laboratorio; para producción habría que activar SSL en OVN.

**Alternativas sin OVN:** MetalLB para aplicaciones, el balanceador de CAPN para los clústeres nuevos, y un contenedor con
HAProxy o nginx más `keepalived` si se necesita una IP virtual para instancias.

## Actualizar o desinstalar Incus

Ambos playbooks son **seguros por defecto**: sin la variable de confirmación solo muestran qué harían.

| Qué | Playbook | Confirmación | Efecto |
|---|---|---|---|
| Actualizar Incus a la última versión del repositorio | [`playbook-upgrade-incus.yml`](https://github.com/symintel/homelab/blob/main/ansible/playbook-upgrade-incus.yml) | `-e incus_upgrade_confirm=true` | Actualiza los paquetes `incus*` nodo por nodo y espera a que los tres miembros estén `ONLINE`. No borra instancias |
| Desinstalar el clúster (para rehacerlo) | [`playbook-uninstall-incus.yml`](https://github.com/symintel/homelab/blob/main/ansible/playbook-uninstall-incus.yml) | `-e incus_uninstall_confirm=true` | **Destructivo:** borra instancias, imágenes, redes gestionadas, el pool y los paquetes. No toca `br0`, K3s ni BIND |

El clúster exige **la misma versión de Incus en todos los miembros**: mientras difieren, el API queda bloqueado en los
ya actualizados hasta que los demás los alcanzan. Por eso el playbook de actualización recorre los tres nodos seguidos y
verifica al final. Para rehacer el clúster después de desinstalar: `playbook-bootstrap.yml` y `playbook-incus-cluster.yml`.

## Backup y snapshots (opcional)

No forman parte del bootstrap por defecto. Actívalos cuando quieras proteger
instancias o el estado del clúster.

| Método | Alcance | Cuándo usarlo |
|---|---|---|
| **Snapshots de instancia** | Una instancia, mismo storage pool | Rollback rápido; no sustituye backup offsite |
| **Export tarball** | Instancia o volumen portable | Copia restaurable en otro pool o servidor |
| **Volcado BD** | Metadatos Incus (redes, perfiles) | Complemento ligero en cron |
| **Tar de `/var/lib/incus`** | Servidor completo | DR del nodo bootstrap |

### Snapshots programados (por instancia)

```bash
# Diario a las 06:00; expira a los 7 días
incus config set <instancia> snapshots.schedule="0 6 * * *"
incus config set <instancia> snapshots.expiry=7d
incus config set <instancia> snapshots.pattern="{{ creation_date|date:'2006-01-02' }}"
```

Snapshot manual: `incus snapshot create <instancia> <nombre>`

### Export y volcado de metadatos

```bash
incus export <instancia> /backup/<instancia>.tar.gz
incus admin sql local .dump > /backup/incus-local.sql
incus admin sql global .dump > /backup/incus-global.sql
```

### Limitaciones

- Los snapshots viven en el **mismo storage pool** que la instancia; si pierdes
  el disco, pierdes snapshots y datos.
- En clúster, programa backups en el nodo que aloja la instancia o usa
  `incus copy --refresh` hacia otro servidor Incus para copias offsite.
- Para CAPN/workloads críticos, combina snapshots con export periódico o réplica.

Docs oficiales: [Backup instancias](https://linuxcontainers.org/incus/docs/main/howto/instances_backup/),
[Backup servidor](https://linuxcontainers.org/incus/docs/main/backup/).
