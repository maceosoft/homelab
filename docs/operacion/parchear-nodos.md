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

Un nodo a la vez, y `deborah` **al final**: es el control plane de K3s y el servidor DNS (BIND) de la LAN, así que reiniciarla
corta el DNS y el clúster entero unos minutos.

1. `oliver`
2. `invincible`
3. `deborah`

Para cada nodo:

1. Comprueba que el clúster está sano: `kubectl get nodes` (todos `Ready`) y que los volúmenes de Longhorn no están degradados
   (UI de Longhorn, ver [URLs y accesos](urls-y-accesos.md)). Si un volumen ya tiene una sola réplica, no reinicies un nodo que tenga la otra.
2. Entra por SSH ([acceso](acceso-ssh.md)) e instala: `sudo apt-get update && sudo apt-get dist-upgrade`.
3. Si hace falta reiniciar (existe `/var/run/reboot-required`, o la alerta `ReinicioPendiente`):
   `kubectl drain <nodo> --ignore-daemonsets --delete-emptydir-data`, luego `sudo reboot`.
4. Cuando vuelva, `kubectl uncordon <nodo>` y espera a que el nodo esté `Ready` y los volúmenes de Longhorn sanos
   antes de pasar al siguiente.

Pasado un rato (hasta 6 horas, o ejecuta `sudo systemctl start node-apt-metrics.service`), las alertas de ese nodo se resuelven solas.
