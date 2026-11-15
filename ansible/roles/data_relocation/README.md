# data_relocation

Mueve carpetas de un nodo a otro disco ya montado (con `storage_provision`) **sin cambiar las rutas** que usan los
servicios: copia la carpeta, renombra la original y monta la copia encima con un bind mount en `/etc/fstab`. K3s,
Ollama o lo que sea siguen leyendo la misma ruta.

**Corta servicios.** Cada carpeta tiene una pausa antes del corte. Con `drain: true` (K3s) el nodo se vacía y su
API no responde mientras dura la copia final.

## Playbook

[`playbook-data-relocation.yml`](../../playbook-data-relocation.yml).

## Variables (host_vars)

Ejemplo con los dos casos que contempla el rol (`deborah` hoy mueve solo `containerd`, ver su `host_vars`):

```yaml
data_relocation_old_suffix: .emmc-old     # sufijo de la carpeta original (rollback); default .pre-relocation
data_relocation_items:
  - name: ollama
    src: /var/lib/ollama/.ollama/models   # ruta original: queda como punto de montaje
    dest: /srv/nvme/ollama-models         # en el disco nuevo
    stop: [ollama-proxy.socket, ollama-proxy.service, ollama.service, ollama-node-register.service]
    start: [ollama-proxy.socket, ollama-node-register.service]
    guard: [ollama.service, ollama-node-register.service]   # no arrancan sin el montaje
  - name: k3s
    src: /var/lib/rancher/k3s
    dest: /srv/nvme/k3s
    drain: true      # cordon + drain antes, uncordon al final
    killall: true    # k3s-killall.sh: para k3s y sus contenedores
    start: [k3s.service]
    guard: [k3s.service]
```

Sin `data_relocation_items` el playbook no hace nada en ese nodo. Con
`-e '{"data_relocation_only": ["ollama"]}'` mueve solo esos items.

## Qué hace, por cada carpeta

1. Si `src` ya es un punto de montaje, solo se asegura de los drop-ins (idempotente).
2. Comprueba que `dest` esté en otro disco montado (no en `/`): si el disco no montó, se detiene antes de copiar.
3. Copia previa en caliente (`rsync -aHAX --numeric-ids`) con el mismo dueño y permisos.
4. Pausa; `drain`, para los servicios (`stop`) y, con `killall`, corre `k3s-killall.sh`.
5. Copia final con `--delete`, renombra `src` a `src<sufijo>` y crea el punto de montaje vacío.
6. Bind mount en fstab (`bind,x-systemd.requires-mounts-for=<dest>`), sin `nofail`.
7. Drop-in `RequiresMountsFor=<src>` en cada servicio de `guard`. Es el seguro importante: sin el disco, K3s
   arrancaría con un datastore vacío y crearía **otro clúster**; con el drop-in, no arranca.
8. Arranca `start`, espera el nodo `Ready` y hace `uncordon` (si `drain`).

`k3s-killall.sh` no desmonta `/var/lib/rancher/k3s` (solo `/run/k3s`, los volúmenes de kubelet y la red), así que
el bind mount sobrevive a un `killall`.

## Rollback

Con el servicio parado: quitar la línea del bind en `/etc/fstab`, `umount <src>`, `rmdir <src>`,
`mv <src><sufijo> <src>`, borrar el drop-in `10-data-relocation.conf`, `systemctl daemon-reload` y arrancar.

## Verificar

```bash
ansible deborah -i inventory.ini -m command -a "findmnt /var/lib/rancher/k3s/agent/containerd"
ansible deborah -i inventory.ini -b -m command -a "systemctl cat k3s.service"   # muestra RequiresMountsFor
```
