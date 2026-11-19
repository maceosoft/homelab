# CAPN (Cluster API Provider Incus)

!!! info "Parte de la guía de implementación"
    **[Fase 6 — CAPN](../implementacion/fase-6-capn.md)** — recorrido, estado en el HomeLab y problemas conocidos.

El K3s (distribución ligera de Kubernetes) del HomeLab actúa como *management cluster* de
[Cluster API](https://cluster-api.sigs.k8s.io/), y [CAPN](https://capn.linuxcontainers.org/) crea los nodos de cada
clúster nuevo como instancias de Incus. Versiones probadas el 18 nov 2026: `clusterctl` 1.13.8, CAPI 1.14.4, CAPN
0.9.1 y Kubernetes v1.37.0 en los clústeres creados.

!!! info "Probado de punta a punta el 18 nov 2026"
    Con los comandos de esta página (y `kube-vip` en la IPv4 reservada `192.168.20.12`), el clúster quedó listo en
    2 min 15 s. `LOAD_BALANCER='lxc: {}'` no sirve en `br0`: el endpoint queda en IPv6 y el K3s no llega a él. Detalle en
    [Estado en el HomeLab](../implementacion/fase-6-capn.md#estado-en-el-homelab).

## Instalación

```bash
brew install clusterctl                     # ≥ 1.13; el 1.10 de guías viejas no admite K8s 1.37
mkdir -p ~/.cluster-api
curl -fsSLo ~/.cluster-api/clusterctl.yaml https://capn.linuxcontainers.org/static/v0.1/clusterctl.yaml
export KUBECONFIG=~/.kube/homelab-github.yaml
export CLUSTER_TOPOLOGY=true
clusterctl init -i incus:v0.9.1
```

## Credencial de Incus

CAPN habla con la API de Incus (`https://192.168.20.6:8443`) con un certificado de cliente propio, que se agrega al
trust de Incus solo para él. El certificado, su llave y el certificado del servidor de Incus se guardan en 1Password
(item `capn-incus`, bóveda `HomeLab`); de ahí sale el Secret de cada clúster.

Una vez, desde tu Mac, en una carpeta temporal:

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

El Secret de cada clúster se arma desde ese item con `op read` (las claves `server`, `server-crt`, `client-crt`,
`client-key` y `project` son las que espera CAPN; con `endpoints.yaml`/`client.crt` responde
`server "" is not unix:// or https://`): ver
[Operaciones frecuentes — Crear un clúster](../operacion/capn.md#crear-un-cluster).

Para revocarla: `ssh amaceo@192.168.20.6 'sudo incus config trust list'` y
`sudo incus config trust remove <huella>`; después borra el item de 1Password.

## Generar un clúster

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

Los destinos no incluyen `deborah` (su kernel no tiene `netlink_diag`, que el perfil kubeadm exige) ni `oliver` (poca
RAM y un SSD con sectores reasignados). Un clúster mínimo (control plane y un worker; `kube-vip` corre dentro del
control plane) usa unos 1 GB de RAM y baja una imagen kubeadm de ~600 MB a Incus.

Para gestionarlo con Argo CD en vez de `kubectl apply`, el manifiesto generado va a
`gitops/addons/cluster/capn/clusters/` y se activa [`capn-demo.yaml`](https://github.com/maceosoft/gitops/blob/main/bootstrap/components/apagadas/capn-demo.yaml)
(hoy es solo un marcador). Una cosa u otra, no las dos sobre el mismo archivo.

## Borrar

```bash
kubectl delete clusters.cluster.x-k8s.io demo -n capn-demo
kubectl delete namespace capn-demo
ssh amaceo@192.168.20.6 'sudo incus config trust list -f csv'      # columnas: nombre, tipo, descripción, huella, vence
ssh amaceo@192.168.20.6 'sudo incus config trust remove <huella-de-capn>'
```

Desinstalar CAPI/CAPN y los restos que puede dejar `clusterctl delete`: ver
[Fase 6 — Desinstalar](../implementacion/fase-6-capn.md#desinstalar).
