# CAPN (Cluster API Provider Incus)

!!! info "Parte de la guía de implementación"
    **[Fase 6 — CAPN](../implementacion/fase-6-capn.md)** — recorrido ejecutable.

El K3s (distribución ligera de Kubernetes) existente actúa como *management cluster* de [Cluster API](https://cluster-api.sigs.k8s.io/).
Provider: [CAPN](https://capn.linuxcontainers.org/).

## Instalación

```bash
curl -L https://github.com/kubernetes-sigs/cluster-api/releases/download/v1.10.10/clusterctl-linux-amd64 -o clusterctl
chmod +x clusterctl && sudo mv clusterctl /usr/local/bin/

mkdir -p ~/.cluster-api
curl -o ~/.cluster-api/clusterctl.yaml https://capn.linuxcontainers.org/static/v0.1/clusterctl.yaml
clusterctl init -i incus
```

## Credenciales de Incus como Secret

Ver [`gitops/sealed-secrets/`](https://github.com/maceosoft/gitops/tree/main/sealed-secrets) — el secreto
`lxc-secret` se cifra con Sealed Secrets antes de commitear, nunca en texto plano.

## Generar un workload cluster

```bash
export LXC_SECRET_NAME=lxc-secret
export LOAD_BALANCER='lxc: {}'
export DEPLOY_KUBE_FLANNEL=true
export LXC_IMAGE_NAME=kubeadm/v1.36.1
export CONTROL_PLANE_MACHINE_TARGET="@x86-nodes"
export CONTROL_PLANE_MACHINE_TYPE=container
export WORKER_MACHINE_TARGET="@arm64-nodes"
# arm64: solo container, sin imágenes VM oficiales
export WORKER_MACHINE_TYPE=container

clusterctl generate cluster demo -i incus \
  --kubernetes-version v1.36.2 \
  --control-plane-machine-count 1 \
  --worker-machine-count 2 > gitops/capn/clusters/demo.yaml

kubectl apply -f gitops/capn/clusters/demo.yaml
```

> Nota: CAPN provisiona clusters **kubeadm** vainilla (no K3s anidado) — más
> pesado por nodo. Bien para clusters efímeros de dev/test, no para 24/7 en oliver.

El manifiesto generado se sincroniza vía ArgoCD con sync manual — ver
[`capn-demo.yaml`](https://github.com/maceosoft/gitops/blob/main/argocd/apps/capn-demo.yaml).
