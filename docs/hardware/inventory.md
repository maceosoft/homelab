# Inventario de Hardware

> Los hostnames siguen la serie *Invincible* — ver
> [categoría de personajes](https://invincible.fandom.com/es/wiki/Categor%C3%ADa:Personajes).
> `deborah` fue antes `orangepi5plus`.

Datos **medidos** con [`playbook-discovery.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-discovery.yml).
Donde el valor nominal difiere del medido, la columna *Medido*
es la fuente de verdad para planificación.

<div class="option-grid">
  <div class="card">
    <div class="card-title"><code>invincible</code> <span class="tag tag-neutral">x86_64</span></div>
    <div class="text-muted">Lenovo M920q · i7-8700T 6c/12t</div>
    <div class="hr"></div>
    <div class="card-body">RAM: <span class="card-highlight">15.5 GB</span></div>
    <div class="card-body">IP estática: <span class="card-highlight">192.168.20.6</span></div>
    <div class="card-meta">Incus: leader · K3s: Worker (agent)</div>
  </div>
  <div class="card">
    <div class="card-title"><code>oliver</code> <span class="tag tag-neutral">x86_64</span></div>
    <div class="text-muted">Lenovo M700 · i3-6100T 2c/4t</div>
    <div class="hr"></div>
    <div class="card-body">RAM: <span class="card-highlight">7.7 GB</span></div>
    <div class="card-body">IP estática: <span class="card-highlight">192.168.20.7</span></div>
    <div class="card-meta">Incus: Miembro (scheduler manual) · K3s: Worker (agent)</div>
  </div>
  <div class="card">
    <div class="card-title"><code>deborah</code> <span class="tag tag-accent">ARM64</span></div>
    <div class="text-muted">Orange Pi 5 Plus · RK3588 8c</div>
    <div class="hr"></div>
    <div class="card-body">RAM: <span class="card-highlight">31.0 GB</span></div>
    <div class="card-body">IP estática: <span class="card-highlight">192.168.20.5</span></div>
    <div class="card-meta">Incus: Miembro (grupo arm64) · K3s: Control-plane (server)</div>
  </div>
  <div class="card">
    <div class="card-title"><code>eve</code> <span class="tag tag-neutral">x86_64</span></div>
    <div class="text-muted">MacBook Pro 16" 2019 · i9-9980HK 8c/16t</div>
    <div class="hr"></div>
    <div class="card-body">RAM: <span class="card-highlight">31 GB</span></div>
    <div class="card-body">IP estática: <span class="card-highlight">192.168.20.8</span></div>
    <div class="card-meta">Incus: Miembro (grupo x86) · K3s: Worker (agent)</div>
  </div>
</div>

!!! note "Specs nominales vs medidas"
    Medido en los propios nodos con `playbook-discovery.yml` (y comprobado con `lscpu`, `free`, `dmidecode` y `lsblk`); la RAM se da en GiB, como la reporta el discovery:
    **invincible** es el M920q con i7-8700T y 15.5 GB, y **oliver** es el M700 con i3-6100T y 7.7 GB.

## Esquema de IPs

| Concepto | invincible | oliver | deborah | eve |
|---|---|---|---|---|
| IP SSH hoy (`ansible_host`) | `192.168.20.6` | `192.168.20.7` | `192.168.20.5` | `192.168.20.8` |
| IP estática en `br0` | `192.168.20.6` | `192.168.20.7` | `192.168.20.5` | `192.168.20.8` |
| Interfaz física → bridge | `eno2` | `eno1` | `enP4p65s0` | `enx9c69d3a4be6a` (adaptador USB TP-Link) |
| WiFi de respaldo (`wifi_ip`) | `192.168.20.10` | — | `192.168.20.9` | `192.168.20.11` |

Tras `playbook-set-static-ip.yml`, actualizar `ansible_host` en
[`inventory.ini`](https://github.com/maceosoft/homelab/blob/main/ansible/inventory.ini)
si la IP de conexión cambió.

## Almacenamiento e I/O

| Nodo | Disco principal | Escritura 4k (dd/fio) |
|---|---|---|
| invincible | Kingston SA400 224GB | **78.4 MB/s** |
| oliver | TECLAST 120GB SSD | 73.9 MB/s |
| deborah | eMMC `mmcblk1` 233GB (raíz) | 59.5 MB/s |

Prueba: `dd` de 40 MB en bloques de 4k con escritura directa (`oflag=direct`). La medición de `deborah` de esta
tabla es del eMMC.

`deborah` tiene además un NVMe SK hynix BC501 de 256 GB (`nvme0n1`), que reemplazó al WDC de 250 GB cuyo enlace
PCIe no levantaba (`rk-pcie … PCIe Link Fail`). Está formateado y montado en `/srv/nvme` (con `nofail`) como disco
de Longhorn, pero **sin uso hasta ponerle disipador**: sin carga marca 71 °C (79 °C en su segundo sensor) y su
temperatura crítica es 82 °C. Copiando 40 GB seguidos dejó de responder y se cayó del bus PCIe
(`controller is down`, `D3cold`), y volvió solo después de cortarle la corriente. Por eso en él va solo lo que
aguanta perder el disco: la base de datos de K3s y las imágenes de containerd siguen en el eMMC (ver
[Agregar un disco a un nodo](../operacion/agregar-disco.md)).

### Temperaturas

[`ansible/scripts/temperaturas.sh`](https://github.com/maceosoft/homelab/blob/main/ansible/scripts/temperaturas.sh)
muestra, por nodo, cada sensor de temperatura con su nombre (CPU y núcleos, placa, GPU, NVMe, batería y, en `eve`,
los sensores del SMC de la Mac) y marca con `!` los que pasan de 75 °C (`AVISO_C`). El NVMe de `deborah` no aparece
en `hwmon` (por eso tampoco llega a las métricas): el script lo lee con `smartctl`.

```bash
ansible/scripts/temperaturas.sh            # todos los nodos
ansible/scripts/temperaturas.sh deborah    # uno solo
```

La RK3588 de `deborah` empieza a bajar la frecuencia sobre 85 °C. Por temperatura, `deborah` ya no corre Ollama:
es el control plane y el DNS.

## eve: MacBook Pro con chip T2

`eve` es una MacBook Pro 16" 2019 (`MacBookPro16,1`) con Debian 13. Tiene el chip T2 (coprocesador de seguridad de
Apple): el teclado, el trackpad, la Touch Bar y el audio internos pasan por él, y el kernel de Debian no los ve.
[`playbook-t2-mac.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-t2-mac.yml) instala el
kernel `linux-t2` de [t2linux](https://wiki.t2linux.org/), el control de ventiladores (`t2fanrd`) y la deja lista
para correr como servidor (tapa cerrada, sin suspensión, GPU Intel como principal, pantalla que se apaga al cerrar la tapa y
sola a los 5 minutos, arranque sin modo gráfico, GPU AMD apagada, trackpad en la consola (`gpm`), `thermald` y batería limitada al 80 % de carga porque vive enchufada). Detalle en el
[README del rol](https://github.com/maceosoft/homelab/blob/main/ansible/roles/t2_mac/README.md).

- **WiFi (BCM4364):** el firmware solo viene con macOS. Como macOS se borró, se baja una vez a mano con
  `sudo get-apple-firmware` desde una imagen de recuperación de Apple de **Sonoma** (el script recomienda
  Monterey, Ventura o Sonoma; Tahoe puede dejar archivos incompletos). Si la descarga se traba, sirve el
  firmware de otra Mac con macOS: así se hizo con `eve`. Pasos en el
  [README del rol](https://github.com/maceosoft/homelab/blob/main/ansible/roles/t2_mac/README.md#firmware-wifi-paso-manual).
- **Touch ID:** no funciona. Linux solo usa huellas registradas desde macOS.
- **Red:** no tiene puerto Ethernet. El `br0` va sobre un adaptador USB (`bridge_iface` en `inventory.ini`); al
  cambiar de adaptador cambia el nombre de la interfaz, se actualiza `bridge_iface` y se vuelve a correr
  `playbook-set-static-ip.yml`. La IP fija (`192.168.20.8`) no cambia, así que Incus y K3s no se enteran. El WiFi
  queda de respaldo (`playbook-wifi-failover.yml`): si se corta el cable, `br0` se baja y se entra por SSH a
  `eve-wifi` (`192.168.20.11`).
- **Adaptador actual:** TP-Link con chip ASIX AX88179B (`enx9c69d3a4be6a`), conectado directo a un puerto
  Thunderbolt para que vaya por USB 3. Linux lo maneja con el driver genérico `cdc_ncm` y rinde ~940 Mb/s en
  `iperf3` contra `oliver`, sin errores. Conectado en caliente, eve no lo detectó: apareció recién al reiniciar.
  Un hub USB 2.0 limita cualquier adaptador a ~300 Mb/s aunque el enlace diga 1000 Mb/s.
- **Batería:** el prompt de bash empieza con `[AC 80%]` (verde) si está con cargador o `[BAT 74%]` (amarillo, rojo
  bajo el 20 %) si está a batería. Si dice `BAT` sin que la hayas desenchufado a propósito, enchúfala: a batería el
  nodo se apaga cuando se agota.
- **Pantalla:** se apaga al cerrar la tapa y sola a los 5 minutos sin teclado (`consoleblank=300`); nunca suspende.
  Con la tapa abierta, una tecla la enciende. Si queda negra y una tecla no la despierta:

    1. Despertarla desde otra máquina (pasa si se apagó a mano con `setterm --blank force`):

        ```bash
        ssh 192.168.20.8 'sudo sh -c "TERM=linux setterm --blank poke </dev/tty1 >/dev/tty1"'
        ```

    2. Si sigue negra, la consola quedó en el dispositivo vacío (`dummy`). Se ve con
       `cat /sys/class/vtconsole/vtcon*/name`: la que está en uso lleva `(S)` y tiene que ser `frame buffer device`.
       Pasa si la GPU AMD (`amdgpu`) carga después de la Intel (`i915`) y le quita la consola; el rol lo evita con
       `softdep i915 pre: amdgpu` en `/etc/modprobe.d/t2-mac-gpu-order.conf`. Para recuperarla sin reiniciar:

        ```bash
        ssh 192.168.20.8 'echo 1 | sudo tee /sys/class/vtconsole/vtcon1/bind'
        ```

## Presupuesto de RAM (recalculado)

- **invincible (15.5 GB)**: K3s (distribución ligera de Kubernetes) agent + Argo CD controller + Incus leader. Es el nodo x86 con más margen y el disco más rápido: admite CAPN (Cluster API Provider for Incus) management y Longhorn a la vez.
- **oliver (7.7 GB)**: K3s agent (CoreDNS, metrics-server) + Incus en `scheduler.instance manual`. RAM ajustada: por eso queda como nodo ligero y, en el diseño, fuera de Longhorn (ver [Longhorn v1](../storage/index.md#longhorn-v1-ha-selectiva-cross-arch)).
- **eve (31 GB)**: K3s agent + Incus miembro + Ollama bajo demanda (el nodo preferido para los modelos de 7B: es el x86 más rápido). Aporta disco a Longhorn como los demás, porque `createDefaultDiskLabeledNodes` está en `false` (ver [Longhorn](../storage/index.md)).
- **deborah (31 GB)**: control plane K3s + BIND (rol `bind_dns`) + Ollama bajo demanda (rol `ollama_ondemand`, grupo `llm_nodes`, junto a `invincible`, `oliver` y `eve`): solo usa RAM mientras responde y la libera unos 5 minutos después (ver [Asistente de IA local](../operacion/ia-ollama.md)). Raíz en eMMC; tiene un NVMe (disco SSD por PCIe) de 256 GB que todavía no se usa (ver [Almacenamiento e I/O](#almacenamiento-e-io)).

## Decisión: control plane en deborah

!!! info "Mover el control plane es solo una opción"
    El control plane se queda en `deborah`. Si algún día conviene pasarlo a otro nodo (por ejemplo, a `oliver`), el
    procedimiento está en [Mover el control plane](../operacion/mover-control-plane.md); hoy no está planificado.

**Estado:** el API (Application Programming Interface) server responde en `192.168.20.5:6443` (deborah).
Workers en invincible (`192.168.20.6`), oliver (`192.168.20.7`) y eve (`192.168.20.8`). Se instala con
**K3s v1.37.2+k3s1** (`k3s_install.core.version`); después el SUC (System Upgrade Controller) lo actualiza solo
([Actualizar K3s](../operacion/actualizar-k3s.md)). Versión real: `kubectl get nodes`.

<div class="card">
  <div class="card-kicker">Análisis de trade-offs</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">A: deborah <span class="tag tag-accent">elegida</span></div>
      <div class="text-muted">31 GB RAM, ARM64 (raíz en eMMC; NVMe de 256 GB sin usar todavía)</div>
      <div class="text-muted">SBC; throttling térmico; servicios extra en el mismo nodo</div>
    </div>
    <div class="card-col">
      <div class="card-title">B: invincible</div>
      <div class="text-muted">I/O 78.4 MB/s (el mejor medido); 15.5 GB RAM; i7-8700T</div>
      <div class="text-muted">Es el leader de Incus; migración CP costosa</div>
    </div>
    <div class="card-col">
      <div class="card-title">C: oliver</div>
      <div class="text-muted">Nodo ligero ya reservado para quórum</div>
      <div class="text-muted">Solo 7.7 GB RAM; I/O 73.9 MB/s</div>
    </div>
  </div>
</div>

**Nota del discovery:** medido antes de tener NVMe, `deborah` mide el I/O más bajo de los tres (59.5 MB/s en eMMC) e `invincible` el más alto (78.4 MB/s); el propio informe sugiere considerar a `invincible` como control plane. La decisión de `deborah` se mantiene hasta medir la latencia de fsync (`fio`), que es lo que importa para etcd.

!!! warning "deborah tras reboot"
    Si después de un reinicio `deborah` tiene el binario `k3s` pero no el servicio activo ni el puerto `:6443`, revisa
    `sudo systemctl enable --now k3s` y los logs (`sudo journalctl -u k3s -n 50`).

## Ver también

- [Discovery de hardware (Ansible)](discovery.md)
- [K3s — instalación y despliegue](../k3s/index.md)
