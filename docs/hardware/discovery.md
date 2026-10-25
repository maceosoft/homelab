# Discovery de hardware (Ansible)

Playbook que escanea los 3 nodos y genera una ficha Markdown por nodo, para
confirmar (o contradecir) con datos medidos los roles asignados en el
[Inventario de hardware](inventory.md) — en particular, si `deborah`
sigue siendo el mejor candidato a control-plane K3s (distribución ligera de Kubernetes).

Código: [`ansible/playbook-discovery.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-discovery.yml)
(dos plays en un mismo archivo: escaneo por nodo + consolidado).

## Uso

```bash
cd ansible/
ansible-playbook -i inventory.ini playbook-discovery.yml
```

El segundo play (consolidado) lee los facts recolectados por el primero
desde `hostvars`, que solo están disponibles en memoria durante la misma
invocación de `ansible-playbook` -- por eso viven en el mismo archivo en
vez de en un playbook aparte que habría que recordar pasar junto al otro.

## Qué recolecta por nodo

- **CPU** — arquitectura, modelo, núcleos físicos/lógicos.
- **Memoria** — RAM total y swap.
- **Almacenamiento** — cada disco (rotacional o no, tamaño, modelo) +
  benchmark de escritura 4k (`fio`, o `dd` como fallback) para estimar
  aptitud para etcd.
- **Red** — interfaces con su velocidad negociada.
- **Sistema operativo** — distro, kernel, uptime, temperatura (sensor
  `vcgencmd` en SBC o `thermal_zone0` genérico).
- **Stack instalado** — si `/dev/kvm` está disponible, versión de Incus y
  de K3s.
- **Paquetes clave** — versión (o "no instalado") de docker, containerd,
  python3, git, qemu-img, virsh.
- **Instancias Incus** — nombre/tipo/estado de cada container o VM (máquina virtual).
- **K3s** — `kubectl get nodes` y `get pods -A` (si el nodo tiene acceso al
  API server).
- **Contenedores sueltos** — `crictl ps -a` / `docker ps -a`, para detectar
  drift fuera de K3s/Incus.
- **Servicios systemd** — estado active/enabled de k3s, k3s-agent, incus,
  docker, containerd.
- **Puertos en escucha** (`ss -tlnp`), **uso de disco por filesystem**
  (`df -h`), **módulos de kernel** (overlay/br_netfilter/veth) y **estado
  de firewall** (ufw o nftables, el que exista).

## Salida

```
ansible/reports/            (gitignored -- datos de un escaneo en vivo)
├── invincible.md
├── oliver.md
├── deborah.md
└── summary.md
```

`summary.md` pone los 3 nodos lado a lado y lista los 4 criterios usados
para decidir el rol de control-plane:

1. Menor latencia de escritura (fsync) — el factor decisivo para etcd.
2. Fuente de alimentación estable (NVMe + alimentación dedicada, no USB).
3. Margen de RAM por encima del uso normal del clúster (no es el factor
   decisivo por sí solo).
4. Temperatura bajo carga sostenida — throttling térmico en una SBC (Single Board Computer).

## Cómo leer una ficha

Esto es un extracto **real** de la ficha de `invincible`, recortado a lo que es solo
hardware. La ficha completa también lista puertos, servicios y contenedores, y por eso no se publica.

```text
## CPU
Arquitectura     x86_64
Modelo           Intel(R) Core(TM) i7-8700T CPU @ 2.40GHz
Núcleos físicos  6          Núcleos lógicos  12

## Memoria
RAM total        15.5 GB (15834 MB)          Swap total  0 MB

## Almacenamiento
sda   SSD   223.6GB   KINGSTON SA400S3   En uso
Benchmark I/O (escritura 4k): 40960000 bytes (41 MB) copied, 0.52 s, 78.4 MB/s
```

| Campo | Qué significa y para qué sirve |
|---|---|
| **Núcleos físicos y lógicos** | Los lógicos cuentan los hilos (hyper-threading): 6 físicos dan 12 lógicos. Kubernetes y Incus planifican por lógicos. |
| **RAM total** | Se da en GB que son GiB (15834 MB ÷ 1024 = 15.5). Con 0 MB de swap, si se acaba la RAM el kernel mata procesos. |
| **Tipo** | `HDD (rotacional)` es un disco mecánico: mucho más lento y no sirve para etcd. También distingue `SSD`, `NVMe`, `eMMC/SD` (la memoria de las placas ARM), `flash SPI` y `zram` (RAM comprimida, que no es un disco). Aquí no hay discos mecánicos. |
| **Benchmark de escritura 4k** | Escribe 40 MB en bloques de 4 KB **directo al disco**. Sirve para comparar nodos entre sí, no como cifra absoluta. |

!!! warning "El benchmark no es la latencia de fsync"
    Para etcd lo que importa es la **latencia de fsync** (cuánto tarda en confirmarse cada escritura), que se mide con
    `fio --fsync=1`. El `dd` de 4k da una idea del orden de magnitud: 59.5 MB/s en la eMMC de `deborah` frente a 78.4 MB/s
    en el SSD de `invincible`. Una cifra muy distinta de otra corrida casi siempre es una prueba mal hecha (caché de
    por medio), no un disco más rápido.

Si algún resultado contradice el rol asignado en
[Inventario de hardware](inventory.md), ese documento es el que se
actualiza — los reportes de `ansible/reports/` no se versionan.
