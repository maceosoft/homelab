# Actualizar K3s

K3s (distribución ligera de Kubernetes) se actualiza **solo**: el SUC (System Upgrade Controller) revisa el canal
`stable` de K3s y, cuando sale una versión nueva, actualiza un nodo a la vez
(primero el control plane, el nodo con la etiqueta `node-role.kubernetes.io/control-plane`: `deborah`; después los workers), vaciándolo antes
(*cordon* y *drain*). Este procedimiento es para revisar que eso funciona,
fijar una versión cuando haga falta y mantener alineado Ansible.

Los planes están en [`maceosoft/gitops` → `k3s-upgrade/`](https://github.com/maceosoft/gitops/tree/main/k3s-upgrade)
y los aplica la Application `k3s-upgrade` de Argo CD.

## 1. Comprobar que el SUC está instalado

La Application `k3s-upgrade` solo aplica los *planes*. El controlador que
los ejecuta se instala a mano una vez
([K3s — Instalación manual, 6.1](../k3s/index.md)):

```bash
kubectl -n system-upgrade get deploy system-upgrade-controller
kubectl -n system-upgrade get plans
```

Tienen que aparecer el controlador y los planes `k3s-server` y `k3s-agent`.

## 2. Ver el estado de las actualizaciones

```bash
# columna VERSION de cada nodo
kubectl get nodes -o wide
# versión objetivo (LATESTVERSION)
kubectl -n system-upgrade get plans -o wide
# un job por nodo actualizado
kubectl -n system-upgrade get jobs
```

Todos los nodos deberían terminar con la misma `VERSION`.

## 3. Fijar una versión (opcional)

Para no seguir `stable` (por ejemplo, para esperar antes de subir de versión
menor), cambia `channel` por `version` en los **dos** planes de
`k3s-upgrade/k3s-plans.yaml`, en el repo `gitops`:

```yaml
spec:
  # channel: https://update.k3s.io/v1-release/channels/stable
  version: v1.36.5+k3s1
```

Mergea el cambio: Argo CD lo aplica y el SUC deja los nodos en esa versión.

## 4. Alinear Ansible con la versión real

Ansible instala los nodos **nuevos** con `k3s_install.core.version`
(`group_vars/incus_cluster/k3s_install.yml` en `homelab`). El SUC no toca ese
archivo, así que después de cada actualización queda desfasado. Actualízalo a
la versión que muestra `kubectl get nodes`:

```yaml
k3s_install:
  core:
    version: "v1.37.0+k3s1"   # la VERSION actual de los nodos
```

Es indispensable antes de [agregar un nodo](agregar-nodo.md): si no, el nodo
nuevo entra con una versión más vieja.

## Si falla

| Síntoma | Revisar |
|---|---|
| `get plans` no muestra nada | La Application `k3s-upgrade` no sincroniza: falta el controlador o sus CRDs (paso 1) |
| Un nodo queda `SchedulingDisabled` | La actualización se cortó a mitad: revisa el job con `kubectl -n system-upgrade logs job/<job>` y, cuando esté resuelto, `kubectl uncordon <nodo>` |
| Nodos con versiones distintas por mucho tiempo | El `drain` no termina (PodDisruptionBudget o pods sin controlador); revisa los jobs del paso 2 |
