# Sacar o reemplazar un nodo

Retira un **worker** de K3s (distribución ligera de Kubernetes) y **miembro** de Incus: primero se vacía, después
se quita de cada clúster y por último del inventario. Para **reemplazar** un
equipo, saca el viejo con este procedimiento y agrega el nuevo con
[Agregar un nodo](agregar-nodo.md).

!!! danger "Nodos que no se sacan con este procedimiento"
    - **El nodo del control plane** de K3s (hoy `deborah`; `oliver` cuando se haga la
      [mudanza](mover-control-plane.md)): sacarlo apaga el clúster. Primero hay que
      [mover el control plane](mover-control-plane.md) a otro nodo o reconstruirlo (ver el
      [runbook de bootstrap](https://github.com/maceosoft/homelab/blob/main/ansible/bootstrap/README.md)).
    - **`deborah`** además es el DNS (BIND) de la LAN: antes de sacarla hay que mover el DNS.
    - **`invincible`** es el *leader* de Incus y aloja la UI (interfaz de usuario) de Incus:
      antes hay que mover esos roles a otro nodo.
    - **Quorum de Incus:** el clúster tiene 3 miembros. Con 2, sigue
      funcionando pero ya no tolera otra caída. Agrega el reemplazo pronto.

En los ejemplos, el nodo a sacar es **`nolan`**.

## 1. Vaciar el nodo en K3s

```bash
kubectl cordon nolan
kubectl drain nolan --ignore-daemonsets --delete-emptydir-data
```

Si el nodo aporta disco a Longhorn (`node.longhorn.io/create-default-disk: "true"`), en la UI de Longhorn: *Node → nolan → Edit* → desactiva
*Scheduling* y marca *Eviction Requested*. Espera a que sus réplicas se
muevan a otros nodos antes de seguir.

## 2. Vaciar el nodo en Incus

Desde cualquier nodo del clúster Incus:

```bash
# instancias en nolan
sudo incus list --all-projects --format csv --columns nL | grep nolan
# las mueve o detiene
sudo incus cluster evacuate nolan
```

## 3. Quitarlo de K3s

```bash
kubectl delete node nolan
cd ansible
ansible-playbook -i inventory.ini playbook-k3s-uninstall.yml --limit nolan
```

En un worker, el playbook solo quita el agent (nunca toca el control plane).

## 4. Quitarlo de Incus

Desde el leader (`invincible`). El `ssh` entra con el [acceso por SSO](acceso-ssh.md) (`opkssh login` antes):

```bash
ssh devops@invincible.homelab.local sudo incus cluster remove nolan
```

## 5. Inventario y DNS

1. Borra la línea del nodo en `inventory.ini` (grupo de arquitectura y
   `k3s_agent`) y su archivo `host_vars/nolan.yml`.
2. Si estaba en `reboot_schedule` (`group_vars/incus_cluster/k3s_install.yml`),
   quítalo de ahí.
3. Regenera el DNS para quitar `nolan.mco.local`:

```bash
ansible-playbook -i inventory.ini playbook-bind-dns.yml
```

## Verificar

```bash
# nolan ya no aparece
kubectl get nodes
# nolan ya no aparece
ssh devops@invincible.homelab.local sudo incus cluster list
# sin respuesta
dig +short nolan.mco.local @192.168.20.5
```

En Longhorn, los volúmenes tienen que quedar *Healthy* (sin réplicas en
`nolan`).

## Si falla

| Síntoma | Revisar |
|---|---|
| `drain` se queda esperando | Un pod con PodDisruptionBudget o sin controlador; revisa con `kubectl get pods -A -o wide \| grep nolan` |
| Volúmenes de Longhorn *Degraded* | No esperaste la evacuación de réplicas (paso 1); vuelve a agregar el disco o espera a que Longhorn reconstruya |
| `incus cluster remove` se niega | Quedan instancias en el nodo: repite `incus cluster evacuate nolan` |
| El nodo ya no enciende | Salta los pasos que requieren conectarse a él y usa `sudo incus cluster remove --force nolan` |
