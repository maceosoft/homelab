# Parchear los nodos

Los parches de Debian **no se instalan solos**: el monitoreo solo avisa. Cada nodo publica cuántos parches tiene
pendientes (y cuántos son de seguridad) y si necesita reiniciar; cuando algo lleva demasiado tiempo sin atenderse, llega una
alerta a Discord (`ParchesDeSeguridadPendientes`, `ReinicioPendiente`; ver [Monitoreo y alertas](monitoreo.md#que-te-puede-llegar)).
Este procedimiento es lo que haces al recibirla.

## Una sola vez: activar el aviso

Aplica el rol que publica las métricas en los tres nodos
([`playbook-apt-metrics.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-apt-metrics.yml)) desde `ansible/`:

```bash
ansible-playbook playbook-apt-metrics.yml
```

Instala un temporizador que cada 6 horas actualiza las listas de apt y escribe el resultado donde lo lee `node-exporter`. No instala
ningún paquete. Con el monitoreo ya desplegado, `SinDatosDePaquetes` te recuerda los nodos donde falta.

## Ver qué hay pendiente

En Grafana, el panel *Node Exporter Full* no lo muestra; consulta en *Explore* `node_apt_upgrades_pending` (etiqueta `origin`:
`security` u `other`). O directamente en el nodo:

```bash
sudo apt-get update && apt list --upgradable
```

## Orden recomendado

Un nodo a la vez, y `deborah` **al final**: es el servidor DNS (BIND) de la LAN y, hasta la mudanza del control plane, también
el de K3s, así que reiniciarla corta el DNS y la API del clúster unos minutos.

1. `oliver`
2. `invincible`
3. `deborah`

## Con Ansible (recomendado)

[`playbook-parchear.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-parchear.yml) (rol
[`node_patch`](https://github.com/maceosoft/homelab/tree/main/ansible/roles/node_patch)) hace el procedimiento completo en
ese orden, un nodo por vez. Necesita `kubectl` en tu equipo con `KUBECONFIG` apuntando al clúster (por defecto
`~/.kube/homelab-k3s.yaml`) y un terminal donde responder las confirmaciones. Desde `ansible/`:

Primero, una simulación. No drena ni reinicia: muestra qué paquetes se actualizarían en cada nodo y si haría falta reiniciar.

```bash
ansible-playbook -i inventory.ini playbook-parchear.yml --check
```

Después, nodo a nodo, o todos seguidos:

```bash
ansible-playbook -i inventory.ini playbook-parchear.yml -l oliver
ansible-playbook -i inventory.ini playbook-parchear.yml -l invincible
ansible-playbook -i inventory.ini playbook-parchear.yml -l deborah
```

```bash
ansible-playbook -i inventory.ini playbook-parchear.yml
```

En cada nodo:

1. **Pre-chequeo** (tag `precheck`): todos los nodos `Ready` y ningún volumen de Longhorn `degraded` o `faulted`. Si no, se
   detiene sin tocar nada. Los volúmenes desconectados (`detached`) aparecen como `unknown` y no cuentan como fallo.
2. **Actualización** (tag `upgrade`): lista los paquetes pendientes y ejecuta `apt-get update` y `dist-upgrade`.
3. **Reinicio** (tag `reboot`), solo si existe `/var/run/reboot-required`: drena el nodo desde tu equipo, lo reinicia, espera a
   que vuelva `Ready` y hace `uncordon`. Si no hace falta reiniciar, no drena. Si algo falla con el nodo drenado, intenta el
   `uncordon` y se detiene con un mensaje.
4. **Post-chequeo** (tag `postcheck`): espera, hasta 15 minutos, a que el nodo esté `Ready` y Longhorn sin volúmenes
   degradados antes de pasar al siguiente.

El orden lo fija la variable `node_patch_order`, no el inventario. El control plane de K3s y `deborah` se mueven siempre al
final, aunque se escriban antes, y **piden confirmación dos veces**: antes de actualizar (si se actualiza `bind9`, `named` se
reinicia y el DNS se corta unos segundos) y antes de reiniciar. Ante cualquier fallo, no sigue con el nodo siguiente.

Solo una parte:

```bash
ansible-playbook -i inventory.ini playbook-parchear.yml --tags precheck
ansible-playbook -i inventory.ini playbook-parchear.yml -l oliver --tags upgrade,postcheck
```

Variables útiles (con `-e`): `node_patch_order`, `node_patch_autoremove` (borra dependencias sin uso; por defecto `false`),
`node_patch_drain_timeout`, `node_patch_reboot_timeout`, `node_patch_postcheck_minutes`.

## A mano

Si no puedes usar Ansible, por cada nodo:

1. Comprueba que el clúster está sano: `kubectl get nodes` (todos `Ready`) y que los volúmenes de Longhorn no están degradados
   (UI de Longhorn, ver [URLs y accesos](urls-y-accesos.md)). Si un volumen ya tiene una sola réplica, no reinicies un nodo que tenga la otra.
2. Entra por SSH ([acceso](acceso-ssh.md)) e instala: `sudo apt-get update && sudo apt-get dist-upgrade`.
3. Si hace falta reiniciar (existe `/var/run/reboot-required`, o la alerta `ReinicioPendiente`):
   `kubectl drain <nodo> --ignore-daemonsets --delete-emptydir-data`, luego `sudo reboot`.
4. Cuando vuelva, `kubectl uncordon <nodo>` y espera a que el nodo esté `Ready` y los volúmenes de Longhorn sanos
   antes de pasar al siguiente.

Pasado un rato (hasta 6 horas, o ejecuta `sudo systemctl start node-apt-metrics.service`), las alertas de ese nodo se resuelven solas.
