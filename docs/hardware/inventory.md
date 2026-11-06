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
    <div class="card-body">IP: <span class="card-highlight">DHCP (pendiente)</span></div>
    <div class="card-meta">Solo drivers T2 · sin Incus ni K3s por ahora</div>
  </div>
</div>

!!! note "Specs nominales vs medidas"
    Medido en los propios nodos con `playbook-discovery.yml` (y comprobado con `lscpu`, `free`, `dmidecode` y `lsblk`); la RAM se da en GiB, como la reporta el discovery:
    **invincible** es el M920q con i7-8700T y 15.5 GB, y **oliver** es el M700 con i3-6100T y 7.7 GB.

## Esquema de IPs

| Concepto | invincible | oliver | deborah |
|---|---|---|---|
| IP SSH hoy (`ansible_host`) | `192.168.20.6` | `192.168.20.7` | `192.168.20.5` |
| IP estática en `br0` | `192.168.20.6` | `192.168.20.7` | `192.168.20.5` |
| Interfaz física → bridge | `eno2` | `eno1` | `enP4p65s0` |

Tras `playbook-set-static-ip.yml`, actualizar `ansible_host` en
[`inventory.ini`](https://github.com/maceosoft/homelab/blob/main/ansible/inventory.ini)
si la IP de conexión cambió.

## Almacenamiento e I/O

| Nodo | Disco principal | Escritura 4k (dd/fio) |
|---|---|---|
| invincible | Kingston SA400 224GB | **78.4 MB/s** |
| oliver | TECLAST 120GB SSD | 73.9 MB/s |
| deborah | eMMC `mmcblk1` 233GB (raíz) | 59.5 MB/s |

Prueba: `dd` de 40 MB en bloques de 4k con escritura directa (`oflag=direct`). El NVMe WDC 250GB (`nvme0n1`) de `deborah` **no se detecta**: `lsblk` y `lspci` no lo ven y `dmesg` dice `rk-pcie … PCIe Link Fail` (el enlace de la ranura no levanta).

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
- **Red:** por ahora, DHCP con un adaptador USB. La IP fija, Incus y K3s quedan para después.

## Presupuesto de RAM (recalculado)

- **invincible (15.5 GB)**: K3s (distribución ligera de Kubernetes) agent + Argo CD controller + Incus leader. Es el nodo x86 con más margen y el disco más rápido: admite CAPN (Cluster API Provider for Incus) management y Longhorn a la vez.
- **oliver (7.7 GB)**: K3s agent (CoreDNS, metrics-server) + Incus en `scheduler.instance manual`. RAM ajustada: por eso queda como nodo ligero y, en el diseño, fuera de Longhorn (ver [Longhorn v1](../storage/index.md#longhorn-v1-ha-selectiva-cross-arch)).
- **deborah (31 GB)**: control plane K3s + BIND (rol `bind_dns`) + Ollama bajo demanda (rol `ollama_ondemand`, grupo `llm_nodes`, junto a `invincible` y `oliver`): solo usa RAM mientras responde y la libera unos 5 minutos después (ver [Asistente de IA local](../operacion/ia-ollama.md)). Raíz en eMMC; el NVMe (disco SSD por PCIe) no se detecta (ver [Almacenamiento e I/O](#almacenamiento-e-io)).

## Decisión: control plane en deborah

!!! info "Mover el control plane es solo una opción"
    El control plane se queda en `deborah`. Si algún día conviene pasarlo a otro nodo (por ejemplo, a `oliver`), el
    procedimiento está en [Mover el control plane](../operacion/mover-control-plane.md); hoy no está planificado.

**Estado:** el API (Application Programming Interface) server responde en `192.168.20.5:6443` (deborah).
Workers en invincible (`192.168.20.6`) y oliver (`192.168.20.7`). Se instala con
**K3s v1.36.5+k3s1** (`k3s_install.core.version`); después el SUC (System Upgrade Controller) lo actualiza solo
([Actualizar K3s](../operacion/actualizar-k3s.md)). Versión real: `kubectl get nodes`.

<div class="card">
  <div class="card-kicker">Análisis de trade-offs</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">A: deborah <span class="tag tag-accent">elegida</span></div>
      <div class="text-muted">31 GB RAM, ARM64 (raíz en eMMC; el NVMe no se detecta)</div>
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

**Nota del discovery:** sin NVMe, `deborah` mide el I/O más bajo de los tres (59.5 MB/s en eMMC) e `invincible` el más alto (78.4 MB/s); el propio informe sugiere considerar a `invincible` como control plane. La decisión de `deborah` se mantiene hasta medir la latencia de fsync (`fio`), que es lo que importa para etcd.

!!! warning "deborah tras reboot"
    Si después de un reinicio `deborah` tiene el binario `k3s` pero no el servicio activo ni el puerto `:6443`, revisa
    `sudo systemctl enable --now k3s` y los logs (`sudo journalctl -u k3s -n 50`).

## Ver también

- [Discovery de hardware (Ansible)](discovery.md)
- [K3s — instalación y despliegue](../k3s/index.md)
