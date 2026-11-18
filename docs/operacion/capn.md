# Operaciones frecuentes de CAPN

Comandos del día a día con [CAPN](../capn/index.md): clústeres de Kubernetes (kubeadm) creados a mano con
`clusterctl` y `kubectl`, cuyos nodos son contenedores de Incus. El porqué, el estado y los problemas conocidos están
en la [Fase 6](../implementacion/fase-6-capn.md).

En los ejemplos el clúster se llama `demo` y vive en el namespace `capn-demo`. Todos los comandos usan el kubeconfig
de administrador del K3s (o el de GitHub del team `devops`, que también es `cluster-admin`):

```bash
export KUBECONFIG=~/.kube/homelab-k3s.yaml
```

## Una vez: instalar CAPI y CAPN en el K3s

```bash
brew install clusterctl                      # ≥ 1.13
mkdir -p ~/.cluster-api
curl -fsSLo ~/.cluster-api/clusterctl.yaml https://capn.linuxcontainers.org/static/v0.1/clusterctl.yaml
export CLUSTER_TOPOLOGY=true                 # la plantilla de CAPN usa ClusterClass
clusterctl init -i incus:v0.9.1
kubectl get pods -A | grep -E 'capi|capn'                 # 4 controladores Running
```

Y la credencial de Incus en 1Password (item `capn-incus`): pasos en
[CAPN — Credencial de Incus](../capn/index.md#credencial-de-incus).

## Crear un clúster

1. **Namespace y credencial** (el Secret sale de 1Password; no queda ningún archivo con la llave):

    ```bash
    kubectl create namespace capn-demo
    kubectl -n capn-demo create secret generic lxc-secret \
      --from-literal=server=https://192.168.20.6:8443 \
      --from-literal=project=default \
      --from-file=server-crt=<(op read "op://HomeLab/capn-incus/server-crt") \
      --from-file=client-crt=<(op read "op://HomeLab/capn-incus/client-crt") \
      --from-file=client-key=<(op read "op://HomeLab/capn-incus/client-key")
    kubectl -n capn-demo label secret lxc-secret clusterctl.cluster.x-k8s.io/move=true
    ```

2. **Generar y aplicar** (control plane en `eve`, workers en `invincible`, API en la IPv4 reservada):

    ```bash
    export LXC_SECRET_NAME=lxc-secret
    export LOAD_BALANCER='kube-vip: {host: 192.168.20.12}'
    export DEPLOY_KUBE_FLANNEL=true
    export CONTROL_PLANE_MACHINE_TARGET='"eve"'
    export CONTROL_PLANE_MACHINE_TYPE=container
    export WORKER_MACHINE_TARGET='"invincible"'
    export WORKER_MACHINE_TYPE=container
    clusterctl generate cluster demo --target-namespace capn-demo -i incus:v0.9.1 \
      --kubernetes-version v1.37.0 \
      --control-plane-machine-count 1 \
      --worker-machine-count 1 > /tmp/capn-demo.yaml
    kubectl apply -f /tmp/capn-demo.yaml
    ```

3. **Esperar** (unos 2 minutos):

    ```bash
    kubectl -n capn-demo wait clusters.cluster.x-k8s.io/demo --for=condition=Available --timeout=600s
    clusterctl describe cluster demo -n capn-demo
    ```

`192.168.20.12` es una sola IP: un segundo clúster al mismo tiempo necesita otra IPv4 libre fuera del DHCP y de
MetalLB (reservarla en la tabla de [Red](../networking/index.md)).

## Ver los clústeres

```bash
kubectl get clusters.cluster.x-k8s.io,machines.cluster.x-k8s.io -A
clusterctl describe cluster demo -n capn-demo
```

Los nombres cortos `clusters` y `machines` no sirven aquí: `clusters` es el de PostgreSQL (CloudNativePG).

## Entrar al clúster (kubeconfig)

```bash
clusterctl get kubeconfig demo -n capn-demo > ~/.kube/capn-demo.yaml
chmod 600 ~/.kube/capn-demo.yaml
kubectl --kubeconfig ~/.kube/capn-demo.yaml get nodes -o wide
```

Es un kubeconfig de administrador **de ese clúster** (con su llave): no lo compartas y bórralo cuando ya no exista el
clúster.

## Probar que funciona

```bash
export KC=~/.kube/capn-demo.yaml
kubectl --kubeconfig $KC create deployment web --image=nginx:1.29-alpine --replicas=2
kubectl --kubeconfig $KC expose deployment web --port 80
kubectl --kubeconfig $KC rollout status deploy/web --timeout=180s
kubectl --kubeconfig $KC run curl --image=curlimages/curl:8.17.0 --rm -i --restart=Never -- \
  curl -s -o /dev/null -w "HTTP %{http_code}\n" http://web.default.svc
```

## Escalar los workers

El clúster se describe con `spec.topology` (ClusterClass): se cambia el número de réplicas y CAPN crea o borra
contenedores en Incus.

```bash
kubectl -n capn-demo patch clusters.cluster.x-k8s.io demo --type=json \
  -p '[{"op":"replace","path":"/spec/topology/workers/machineDeployments/0/replicas","value":2}]'
kubectl get machines.cluster.x-k8s.io -n capn-demo -w      # Ctrl+C cuando las nuevas estén Running
```

## Actualizar la versión de Kubernetes

Cambia la versión en `spec.topology.version`: CAPI reemplaza los nodos de a uno (primero el control plane, después
los workers) por contenedores nuevos con la imagen de esa versión. Tiene que existir la imagen `kubeadm/<versión>` de
CAPN (por ejemplo `v1.36.4` → `v1.37.0`).

```bash
kubectl -n capn-demo patch clusters.cluster.x-k8s.io demo --type=json \
  -p '[{"op":"replace","path":"/spec/topology/version","value":"v1.37.0"}]'
kubectl get machines.cluster.x-k8s.io -n capn-demo -o wide -w
```

## Entrar a un nodo

Los nodos son contenedores de Incus con el nombre de la `Machine`:

```bash
kubectl get machines.cluster.x-k8s.io -n capn-demo -o custom-columns=MAQUINA:.metadata.name,NODO:.status.nodeRef.name
ssh amaceo@192.168.20.6 'sudo incus list | grep demo'
ssh -t amaceo@192.168.20.6 'sudo incus exec <maquina> -- bash'
```

## Ver logs

```bash
kubectl -n capn-system logs deploy/capn-controller-manager --tail=50                       # CAPN (instancias de Incus)
kubectl -n capi-system logs deploy/capi-controller-manager --tail=50                       # CAPI (clústeres y máquinas)
kubectl -n capi-kubeadm-control-plane-system logs deploy/capi-kubeadm-control-plane-controller-manager --tail=50
kubectl get events -n capn-demo --sort-by=.lastTimestamp
```

## Borrar un clúster

```bash
kubectl delete clusters.cluster.x-k8s.io demo -n capn-demo     # borra los contenedores de Incus (~20 s)
kubectl delete namespace capn-demo
rm -f ~/.kube/capn-demo.yaml /tmp/capn-demo.yaml
```

Quedan en Incus la imagen kubeadm (~600 MB) y, en los nodos que tuvieron máquinas, los módulos del kernel del perfil
de CAPN: para quitarlos y para desinstalar CAPI/CAPN, ver [Fase 6 — Desinstalar](../implementacion/fase-6-capn.md#desinstalar).

## Si falla

| Síntoma | Causa |
|---|---|
| La `Machine` se queda en `Provisioning` | Log de CAPN: credencial de Incus (Secret), destino inexistente o imagen que no existe para esa versión |
| `server "" is not unix:// or https://` | El Secret no tiene las claves `server`, `server-crt`, `client-crt`, `client-key`, `project` |
| `connect: network is unreachable` hacia `[fd23:…]` | Se usó `LOAD_BALANCER='lxc: {}'`: en `br0` queda en IPv6. Usa `kube-vip` |
| `kubectl wait` no termina y la API de `192.168.20.12` no responde | Otra cosa ya usa esa IP, o `kube-vip` no arrancó: `incus exec` al control plane y `crictl ps` |
| `modprobe: FATAL: Module netlink_diag not found` | Una máquina cayó en `deborah`: cambia el destino |
