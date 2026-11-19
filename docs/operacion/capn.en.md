# Frequent CAPN operations

Daily commands with [CAPN](../capn/index.md): Kubernetes (kubeadm) clusters created manually with
`clusterctl` and `kubectl`, whose nodes are Incus containers. The why, status, and known issues are
in [Phase 6](../implementacion/fase-6-capn.md).

In the examples the cluster is called `demo` and lives in the namespace `capn-demo`. All commands use the K3s
admin kubeconfig (or the GitHub one for team `devops`, which is also `cluster-admin`):

```bash
export KUBECONFIG=~/.kube/homelab-k3s.yaml
```

## One time: install CAPI and CAPN on K3s

```bash
brew install clusterctl                      # ≥ 1.13
mkdir -p ~/.cluster-api
curl -fsSLo ~/.cluster-api/clusterctl.yaml https://capn.linuxcontainers.org/static/v0.1/clusterctl.yaml
export CLUSTER_TOPOLOGY=true                 # la plantilla de CAPN usa ClusterClass
clusterctl init -i incus:v0.9.1
kubectl get pods -A | grep -E 'capi|capn'                 # 4 controladores Running
```

And the Incus credential in 1Password (item `capn-incus`): steps in
[CAPN — Incus Credential](../capn/index.md#incus-credential).

## Create a cluster

1. **Namespace and credential** (the Secret comes from 1Password; no file with the key remains):

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

2. **Generate and apply** (control plane on `eve`, workers on `invincible`, API on the reserved IPv4):

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

3. **Wait** (about 2 minutes):

    ```bash
    kubectl -n capn-demo wait clusters.cluster.x-k8s.io/demo --for=condition=Available --timeout=600s
    clusterctl describe cluster demo -n capn-demo
    ```

`192.168.20.12` is a single IP: a second cluster at the same time needs another free IPv4 outside DHCP and
MetalLB (reserve it in the [Network](../networking/index.md) table).

## View clusters

```bash
kubectl get clusters.cluster.x-k8s.io,machines.cluster.x-k8s.io -A
clusterctl describe cluster demo -n capn-demo
```

The short names `clusters` and `machines` don't work here: `clusters` is the PostgreSQL one (CloudNativePG).

## Access the cluster (kubeconfig)

```bash
clusterctl get kubeconfig demo -n capn-demo > ~/.kube/capn-demo.yaml
chmod 600 ~/.kube/capn-demo.yaml
kubectl --kubeconfig ~/.kube/capn-demo.yaml get nodes -o wide
```

It's an admin kubeconfig **for that cluster** (with its key): don't share it and delete it when the cluster
no longer exists.

## Test that it works

```bash
export KC=~/.kube/capn-demo.yaml
kubectl --kubeconfig $KC create deployment web --image=nginx:1.29-alpine --replicas=2
kubectl --kubeconfig $KC expose deployment web --port 80
kubectl --kubeconfig $KC rollout status deploy/web --timeout=180s
kubectl --kubeconfig $KC run curl --image=curlimages/curl:8.17.0 --rm -i --restart=Never -- \
  curl -s -o /dev/null -w "HTTP %{http_code}\n" http://web.default.svc
```

## Scale workers

The cluster is described with `spec.topology` (ClusterClass): change the replica count and CAPN creates or deletes
containers in Incus.

```bash
kubectl -n capn-demo patch clusters.cluster.x-k8s.io demo --type=json \
  -p '[{"op":"replace","path":"/spec/topology/workers/machineDeployments/0/replicas","value":2}]'
kubectl get machines.cluster.x-k8s.io -n capn-demo -w      # Ctrl+C cuando las nuevas estén Running
```

## Update Kubernetes version

Change the version in `spec.topology.version`: CAPI replaces nodes one by one (first the control plane, then
the workers) with new containers with the image for that version. The CAPN `kubeadm/<versión>` image must exist
(for example `v1.36.4` → `v1.37.0`).

```bash
kubectl -n capn-demo patch clusters.cluster.x-k8s.io demo --type=json \
  -p '[{"op":"replace","path":"/spec/topology/version","value":"v1.37.0"}]'
kubectl get machines.cluster.x-k8s.io -n capn-demo -o wide -w
```

## Access a node

Nodes are Incus containers named after the `Machine`:

```bash
kubectl get machines.cluster.x-k8s.io -n capn-demo -o custom-columns=MAQUINA:.metadata.name,NODO:.status.nodeRef.name
ssh amaceo@192.168.20.6 'sudo incus list | grep demo'
ssh -t amaceo@192.168.20.6 'sudo incus exec <maquina> -- bash'
```

## View logs

```bash
kubectl -n capn-system logs deploy/capn-controller-manager --tail=50                       # CAPN (instancias de Incus)
kubectl -n capi-system logs deploy/capi-controller-manager --tail=50                       # CAPI (clústeres y máquinas)
kubectl -n capi-kubeadm-control-plane-system logs deploy/capi-kubeadm-control-plane-controller-manager --tail=50
kubectl get events -n capn-demo --sort-by=.lastTimestamp
```

## Delete a cluster

```bash
kubectl delete clusters.cluster.x-k8s.io demo -n capn-demo     # borra los contenedores de Incus (~20 s)
kubectl delete namespace capn-demo
rm -f ~/.kube/capn-demo.yaml /tmp/capn-demo.yaml
```

The kubeadm image (~600 MB) remains in Incus, and on nodes that had machines, the CAPN profile's kernel modules
remain: to remove them and to uninstall CAPI/CAPN, see [Phase 6 — Uninstall](../implementacion/fase-6-capn.md#uninstall).

## If it fails

| Symptom | Cause |
|---|---|
| The `Machine` stays in `Provisioning` | CAPN log: Incus credential (Secret), nonexistent destination, or image that doesn't exist for that version |
| `server "" is not unix:// or https://` | The Secret is missing keys `server`, `server-crt`, `client-crt`, `client-key`, `project` |
| `connect: network is unreachable` to `[fd23:…]` | `LOAD_BALANCER='lxc: {}'` was used: in `br0` it stays on IPv6. Use `kube-vip` |
| `kubectl wait` doesn't finish and the `192.168.20.12` API doesn't respond | Something else is already using that IP, or `kube-vip` didn't start: `incus exec` the control plane and `crictl ps` |
| `modprobe: FATAL: Module netlink_diag not found` | A machine landed in `deborah`: change the destination |
