# k3s_cni

Instala el **CNI externo** tras el server K3s cuando `k3s_install.core.cni` no es
`flannel`. Requiere server con `--flannel-backend=none` y `--disable-network-policy`.

## Playbook

[`playbook-k3s.yml`](../../playbook-k3s.yml) — después del server, antes de agents. Tag `cni`.

## Hosts

`k3s_server` (control-plane).

## Variables

| Variable | Default | Descripción |
|---|---|---|
| `k3s_install.core.cni` | `flannel` | `flannel`, `canal`, `calico`, `cilium` |
| `k3s_install.core.cluster_cidr` | `10.42.0.0/16` | Pool Calico en template |
| `k3s_cni_calico_version` | `v3.33.0` | Manifests Calico/Canal |
| `k3s_cni_cilium_version` | `v1.20.2` | Versión del chart de Cilium |

## Qué hace

1. Salta si `cni == flannel` (Flannel embebido en K3s).
2. **Canal**: manifest oficial Calico/Canal.
3. **Calico**: CRDs + Tigera operator + `custom-resources` con pod CIDR (omitido si ArgoCD ya lo administra).
4. **Cilium**: `HelmChart` del helm-controller de K3s (chart oficial `cilium` de `helm.cilium.io`; el `quick-install.yaml` ya no se publica).
5. Espera pods Ready en `kube-system`.

**Calico**: este rol solo hace el bootstrap (ArgoCD necesita red de pods para arrancar). Una vez
que ArgoCD sigue el `Installation` (Applications `calico-operator` y `calico-config`), el rol
lo detecta y **omite** Calico. Alternativas GitOps: `canal`, `cilium`
(sync manual) en [`gitops`](https://github.com/maceosoft/gitops/tree/main/argocd/apps).

## Verificar

```bash
k3s kubectl get pods -n calico-system -l k8s-app=calico-node   # calico (Tigera operator)
k3s kubectl get pods -n kube-system -l k8s-app=canal           # canal
k3s kubectl get pods -n kube-system -l k8s-app=cilium          # cilium
k3s kubectl get tigerastatus                                    # solo calico
```

## Documentación

- [Fase 3 — K3s](../../../docs/implementacion/fase-3-k3s.md)
- [playbook-options — CNI](../../../docs/k3s/playbook-options.md#cni)
- [K3s networking](https://docs.k3s.io/networking/basic-network-options)
