# CAPN (Cluster API Provider Incus)

!!! info "Part of the implementation guide"
    **[Phase 6 — CAPN](../implementacion/fase-6-capn.md)** — walkthrough, status in the homelab, and known issues.

The K3s (lightweight Kubernetes distribution) in the homelab acts as the *management cluster* for
[Cluster API](https://cluster-api.sigs.k8s.io/), and [CAPN](https://capn.linuxcontainers.org/) creates the nodes of each new
cluster as Incus instances. Versions tested on Nov 18, 2026: `clusterctl` 1.13.8, CAPI 1.14.4, CAPN
0.9.1, and Kubernetes v1.37.0 in the created clusters.

!!! info "End-to-end tested on Nov 18, 2026"
    With the commands on this page (and `kube-vip` on the reserved IPv4 `192.168.20.12`), the cluster was ready in
    2 min 15 s. `LOAD_BALANCER='lxc: {}'` does not work on `br0`: the endpoint is in IPv6 and K3s cannot reach it. Details in
    [Status in the Homelab](../implementacion/fase-6-capn.md#status-in-the-homelab).

## Installation

```bash
brew install clusterctl                     # ≥ 1.13; el 1.10 de guías viejas no admite K8s 1.37
mkdir -p ~/.cluster-api
curl -fsSLo ~/.cluster-api/clusterctl.yaml https://capn.linuxcontainers.org/static/v0.1/clusterctl.yaml
export KUBECONFIG=~/.kube/homelab-github.yaml
export CLUSTER_TOPOLOGY=true
clusterctl init -i incus:v0.9.1
```

## Incus Credential

CAPN communicates with the Incus API (`https://192.168.20.6:8443`) using its own client certificate, which is added to the
Incus trust store only for it. The certificate, its key, and the Incus server certificate are stored in 1Password
(item `capn-incus`, vault `HomeLab`); from there, the Secret of each cluster is retrieved.

Once, from your Mac, in a temporary folder:

```bash
mkdir -p /tmp/capn && cd /tmp/capn
# 1. Llave y certificado de cliente (10 años)
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:secp384r1 -nodes -days 3650 \
  -subj "/CN=capn" -keyout capn.key -out capn.crt
# 2. Darle acceso en Incus
scp capn.crt amaceo@192.168.20.6:/tmp/capn.crt
ssh amaceo@192.168.20.6 'sudo incus config trust add-certificate /tmp/capn.crt --name capn && rm /tmp/capn.crt'
ssh amaceo@192.168.20.6 'sudo incus config trust list' | grep capn
# 3. Certificado del servidor de Incus (sed: deja solo el PEM, sin el aviso de bienvenida del SSH)
ssh amaceo@192.168.20.6 'sudo cat /var/lib/incus/cluster.crt' | sed -n '/BEGIN CERTIFICATE/,/END CERTIFICATE/p' > incus-cluster.crt
openssl x509 -in incus-cluster.crt -noout -subject      # O=Linux Containers, CN=root@invincible
# 4. Guardar los tres en 1Password y borrar los archivos
op item create --vault HomeLab --category "Secure Note" --title capn-incus \
  "client-crt[text]=$(cat capn.crt)" \
  "client-key[concealed]=$(cat capn.key)" \
  "server-crt[text]=$(cat incus-cluster.crt)"
op read "op://HomeLab/capn-incus/client-key" | openssl pkey -noout && echo "llave OK"
cd / && rm -rf /tmp/capn
```

The Secret of each cluster is constructed from that item with `op read` (the keys `server`, `server-crt`, `client-crt`,
`client-key`, and `project` are what CAPN expects; with `endpoints.yaml`/`client.crt` it responds
`server "" is not unix:// or https://`): see
[Frequent Operations — Create a cluster](../operacion/capn.md#crear-un-cluster).

To revoke it: `ssh amaceo@192.168.20.6 'sudo incus config trust list'` and
`sudo incus config trust remove <huella>`; then delete the 1Password item.

## Generate a cluster

```bash
export LXC_SECRET_NAME=lxc-secret
export LOAD_BALANCER='kube-vip: {host: 192.168.20.12}'
export DEPLOY_KUBE_FLANNEL=true
export CONTROL_PLANE_MACHINE_TARGET='"eve"'      # con comillas dentro: "@x86-nodes" sin ellas rompe el YAML
export CONTROL_PLANE_MACHINE_TYPE=container
export WORKER_MACHINE_TARGET='"invincible"'
export WORKER_MACHINE_TYPE=container
# Sin LXC_IMAGE_NAME: CAPN usa capi:kubeadm/<versión>, que existe para v1.37.0 y v1.36.4

clusterctl generate cluster demo --target-namespace capn-demo -i incus:v0.9.1 \
  --kubernetes-version v1.37.0 \
  --control-plane-machine-count 1 \
  --worker-machine-count 1 > /tmp/capn-demo.yaml
kubectl apply -f /tmp/capn-demo.yaml
```

The targets do not include `deborah` (its kernel does not have `netlink_diag`, which the kubeadm profile requires) or `oliver` (low
RAM and an SSD with reallocated sectors). A minimal cluster (control plane and one worker; `kube-vip` runs inside the
control plane) uses about 1 GB of RAM and downloads a ~600 MB kubeadm image to Incus.

To manage it with Argo CD instead of `kubectl apply`, the generated manifest goes to
`gitops/addons/cluster/capn/clusters/` and is activated [`capn-demo.yaml`](https://github.com/maceosoft/gitops/blob/main/bootstrap/components/apagadas/capn-demo.yaml)
(it is just a placeholder today). One or the other, not both on the same file.

## Delete

```bash
kubectl delete clusters.cluster.x-k8s.io demo -n capn-demo
kubectl delete namespace capn-demo
ssh amaceo@192.168.20.6 'sudo incus config trust list -f csv'      # columnas: nombre, tipo, descripción, huella, vence
ssh amaceo@192.168.20.6 'sudo incus config trust remove <huella-de-capn>'
```

Uninstall CAPI/CAPN and the leftovers that `clusterctl delete` may leave: see
[Phase 6 — Uninstall](../implementacion/fase-6-capn.md#uninstall).
