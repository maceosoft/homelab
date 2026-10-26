# CAPN (Cluster API Provider Incus)

!!! info "Part of the implementation guide"
    **[Phase 6 — CAPN](../implementacion/fase-6-capn.md)** — runnable walkthrough.

The existing K3s (lightweight Kubernetes distribution) acts as the *management cluster* for [Cluster API](https://cluster-api.sigs.k8s.io/).
Provider: [CAPN](https://capn.linuxcontainers.org/).

## Installation

```bash
curl -L https://github.com/kubernetes-sigs/cluster-api/releases/download/v1.10.10/clusterctl-linux-amd64 -o clusterctl
chmod +x clusterctl && sudo mv clusterctl /usr/local/bin/

mkdir -p ~/.cluster-api
curl -o ~/.cluster-api/clusterctl.yaml https://capn.linuxcontainers.org/static/v0.1/clusterctl.yaml
clusterctl init -i incus
```

## Incus credentials as a Secret

See [`gitops/sealed-secrets/`](https://github.com/maceosoft/gitops/tree/main/sealed-secrets) — the
`lxc-secret` secret is encrypted with Sealed Secrets before committing, never in plain text.

## Generate a workload cluster

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

> Note: CAPN provisions vanilla **kubeadm** clusters (not nested K3s) — heavier
> per node. Good for ephemeral dev/test clusters, not for 24/7 on oliver.

The generated manifest is synced by Argo CD with manual sync — see
[`capn-demo.yaml`](https://github.com/maceosoft/gitops/blob/main/argocd/apps/capn-demo.yaml).
