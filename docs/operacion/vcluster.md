# Operaciones frecuentes de vCluster

Comandos del día a día con [vCluster](../vcluster/index.md) open source. Todos usan tu kubeconfig de GitHub
([Entrar a Kubernetes con GitHub](acceso-kubernetes.md)) y el CLI `vcluster` 0.38.0 (instalación en la
[Fase 5](../implementacion/fase-5-vcluster.md#antes-de-empezar)). En los ejemplos el vCluster se llama `prueba` y vive en
el namespace `vcluster-prueba`.

```bash
export KUBECONFIG=~/.kube/homelab-github.yaml
```

## Crear

```bash
curl -fsSLo /tmp/vcluster-values.yaml \
  https://raw.githubusercontent.com/maceosoft/gitops/main/addons/cluster/vcluster/values/demo.yaml
vcluster create prueba -n vcluster-prueba -f /tmp/vcluster-values.yaml --chart-version 0.38.0 --connect=false
kubectl -n vcluster-prueba rollout status statefulset/prueba --timeout=300s
```

Tarda alrededor de un minuto. Sin los values (o sin `storageClass`), el volumen queda `Pending`: el clúster no tiene
StorageClass por defecto. Para uno gestionado por Argo CD, ver la [Fase 5](../implementacion/fase-5-vcluster.md#ejecutar).

## Activar el vCluster de GitOps (`vcluster-demo`)

Para uno que quede declarado en git y lo mantenga Argo CD. La Application de ejemplo está apagada en `gitops`.

1. **Activarla en git** (en tu copia de `gitops`, en una rama nueva):

    ```bash
    cd ~/src/maceosoft/gitops
    git checkout main && git pull
    git checkout -b vcluster/activar-demo
    git mv bootstrap/components/apagadas/vcluster-demo.yaml bootstrap/components/vcluster-demo.yaml
    git commit -m "vCluster: activar vcluster-demo"
    ```

    Quita también su línea de la regla "Applications opcionales que NO están activas" en `renovate.json5`, para que
    Renovate avise de versiones nuevas del chart. Sube la rama, abre el PR y mergéalo.

2. **Esperar a que aparezca la Application.** El ApplicationSet `homelab` la crea en uno o dos minutos con la ola
   `manual`: queda `OutOfSync` y `Missing`, sin desplegar nada, porque no tiene sync automático.

    ```bash
    KUBECONFIG=~/.kube/homelab-k3s.yaml kubectl -n argocd get application vcluster-demo
    ```

3. **Sincronizarla a mano.**

    === "🖱️ Desde la interfaz"

        Abre [`https://argocd.homelab.local`](https://argocd.homelab.local), entra con GitHub, busca la Application
        `vcluster-demo` y pulsa **Sync** → **Synchronize**.

    === "⌨️ Desde la consola"

        Con la CLI de Argo CD (`brew install argocd`). El usuario `admin` está desactivado: se entra con GitHub
        (`--sso` abre el navegador).

        ```bash
        argocd login argocd.homelab.local --sso --grpc-web
        argocd app sync vcluster-demo
        argocd app wait vcluster-demo --health --timeout 300
        ```

4. **Comprobar y entrar.** Tarda alrededor de un minuto en quedar `Synced` y `Healthy`:

    ```bash
    export KUBECONFIG=~/.kube/homelab-github.yaml
    kubectl -n argocd get application vcluster-demo     # Synced / Healthy
    vcluster list                                       # demo   vcluster-demo   Running
    vcluster connect demo -n vcluster-demo -- kubectl get ns
    ```

Cada cambio posterior (otra versión del chart, otros values) se hace en git y se vuelve a sincronizar a mano. Para
apagarlo, ver [Borrar](#borrar).

## Ver los que hay

```bash
vcluster list
```

Muestra nombre, namespace, estado (`Running`, `Paused`), versión y antigüedad.

## Entrar

**Un comando suelto** (abre el túnel, corre el comando y lo cierra):

```bash
vcluster connect prueba -n vcluster-prueba -- kubectl get ns
```

**Una sesión de trabajo:** en una terminal deja abierto un túnel al Service del vCluster en un puerto fijo; en otra,
genera su kubeconfig apuntando a ese puerto y úsalo. Así no se toca tu kubeconfig de GitHub:

```bash
# Terminal 1 (queda abierta mientras trabajas)
kubectl -n vcluster-prueba port-forward svc/prueba 11443:443

# Terminal 2
vcluster connect prueba -n vcluster-prueba --local-port 11443 --print --silent > ~/.kube/vcluster-prueba.yaml
chmod 600 ~/.kube/vcluster-prueba.yaml
export KUBECONFIG=~/.kube/vcluster-prueba.yaml
kubectl get ns
```

Para salir, `Ctrl+C` en la terminal 1. El archivo `~/.kube/vcluster-prueba.yaml` lleva una llave de administrador del
vCluster: no lo compartas y bórralo cuando termines (`rm ~/.kube/vcluster-prueba.yaml`).

`vcluster connect prueba -n vcluster-prueba` sin más argumentos también abre el túnel, pero agrega el contexto del
vCluster al kubeconfig que estés usando y lo deja como actual; para volver, `vcluster disconnect`.

## Probar que funciona

Dentro del vCluster:

```bash
vcluster connect prueba -n vcluster-prueba -- sh -c '
  kubectl create deployment web --image=nginx:1.29-alpine &&
  kubectl expose deployment web --port 80 &&
  kubectl rollout status deploy/web --timeout=120s &&
  kubectl run curl --image=curlimages/curl:8.17.0 --rm -i --restart=Never -- \
    curl -s -o /dev/null -w "HTTP %{http_code}\n" http://web.default.svc'
```

Tiene que responder `HTTP 200`. En el anfitrión verás los pods con el nombre traducido:

```bash
kubectl -n vcluster-prueba get pods
# web-7fbc579fd4-9l5hg-x-default-x-prueba   1/1   Running
```

## Pausar y reanudar

Pausar baja a cero el control plane y las cargas del vCluster (libera CPU y RAM) y conserva los datos en su volumen:

```bash
vcluster pause prueba -n vcluster-prueba
kubectl -n vcluster-prueba get pods      # No resources found
vcluster resume prueba -n vcluster-prueba
kubectl -n vcluster-prueba rollout status statefulset/prueba --timeout=300s
```

Al reanudar, lo que habías creado adentro sigue ahí.

## Ver logs y estado

```bash
kubectl -n vcluster-prueba logs statefulset/prueba -c syncer --tail=50     # API y syncer del vCluster
kubectl -n vcluster-prueba get pods,pvc
vcluster connect prueba -n vcluster-prueba -- kubectl get events -A --sort-by=.lastTimestamp
```

## Actualizar

Usa la misma versión en el CLI y en el chart. Para un vCluster creado con el CLI:

```bash
vcluster create prueba -n vcluster-prueba -f /tmp/vcluster-values.yaml --chart-version <nueva> --upgrade
```

Para uno gestionado por Argo CD, cambia `targetRevision` en su Application de `gitops` (Renovate avisa de versiones
nuevas cuando la app está activa). Antes de subir de versión mayor, lee las
[notas de la versión](https://github.com/loft-sh/vcluster/releases).

## Borrar

```bash
vcluster delete prueba -n vcluster-prueba --delete-namespace
vcluster list
```

Borra el control plane, las cargas sincronizadas, el volumen de Longhorn y el namespace. Para uno gestionado por Argo
CD, quita su archivo de `bootstrap/components/` (o muévelo a `apagadas/`), borra la Application y después el namespace,
que Argo CD no elimina:

```bash
kubectl -n argocd delete application vcluster-demo
kubectl delete ns vcluster-demo
```

## Si falla

| Síntoma | Causa |
|---|---|
| `Forbidden` al crear | No usas el kubeconfig de GitHub o no eres del team `devops` (`kubectl auth whoami`) |
| `prueba-0` en `Pending` | Sin `storageClass` en los values |
| `vcluster connect` se queda esperando | El vCluster está `Paused` o su pod no está listo (`vcluster list`) |
| `address already in use` | El puerto de `--local-port` está ocupado: usa otro |
| El pod de una app no arranca adentro | Míralo en el anfitrión: `kubectl -n vcluster-prueba describe pod <nombre>-x-<ns>-x-prueba` |
