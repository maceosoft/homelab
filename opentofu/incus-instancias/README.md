# incus-instancias

Ejemplo de lo más común en Incus, en la red OVN `ovn-lan`:

| Recurso | Qué es | Dónde |
|---|---|---|
| `incus_instance.web` | Contenedor de aplicación con la imagen OCI `docker:nginx:1.29-alpine` | `invincible` |
| `incus_instance.vm` | Máquina virtual `images:debian/13`, 1 CPU y 1 GiB | `eve` |
| `incus_network_lb.web` | Balanceador de OVN: publica el puerto 80 del nginx en `192.168.23.226` | red `ovn-lan` |

`ovn-lan` está aislada a propósito (NAT, sin ruta desde la LAN): a las instancias se llega desde la LAN solo por el
balanceador. Las dos quedan registradas solas en el DNS (zona `ovn.homelab.local` que genera Incus, con sus IPs
internas): `tofu-demo-web.ovn.homelab.local` y `tofu-demo-vm.ovn.homelab.local`.

## Probar

```bash
cd opentofu/incus-instancias
tofu init
tofu apply -parallelism=1        # con SSO; unos 25 s con las imágenes ya bajadas
tofu output                      # url, IPs internas y nombres DNS
curl -sI http://192.168.23.226 | head -1       # HTTP/1.1 200 OK (nginx)
dig +short tofu-demo-web.ovn.homelab.local     # 192.168.19.x
tofu destroy -parallelism=1
```

Probado el 18 nov 2026: tres ciclos seguidos de `apply` y `destroy` con SSO y `-parallelism=1`, cada uno con el
balanceador respondiendo `HTTP 200`. Sin `-parallelism=1` falla (ver [../README.md](../README.md)).

## Variables

| Variable | Default | Uso |
|---|---|---|
| `prefix` | `tofu-demo` | Prefijo de los nombres de las instancias |
| `network` | `ovn-lan` | Red de las instancias |
| `web_target` / `vm_target` | `invincible` / `eve` | Miembro del clúster de cada una (la VM necesita un nodo x86) |
| `lb_address` | `192.168.23.226` | IP del balanceador: libre dentro de `192.168.23.224/28` (`192.168.23.225` ya la usa otro balanceador) |

Para dos copias a la vez, cambia `prefix` y `lb_address` (`-var prefix=otro -var lb_address=192.168.23.227`), cada
una en su propia carpeta o workspace (`tofu workspace new otro`). La primera vez Incus baja las imágenes (nginx y
Debian 13) y quedan en su caché.
