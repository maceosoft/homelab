# k3s_argocd

Instala el **controller Argo CD** en el clúster K3s (bootstrap GitOps).
Solo el controller — las Applications viven en [`gitops`](https://github.com/maceosoft/gitops).

## Playbook

[`playbook-k3s.yml`](../../playbook-k3s.yml) — Fase 3.

Con `k3s_install.gitops_argocd.enabled: true` en
[`group_vars/incus_cluster/k3s_install.yml`](../../group_vars/incus_cluster/k3s_install.yml)
(no con `-e`: Ansible no fusiona claves con puntos en un diccionario):

```bash
ansible-playbook -i inventory.ini playbook-k3s.yml --tags argocd
```

## Hosts

`k3s_server` (deborah).

## Tags

`argocd`, `gitops`.

## Variables

| Variable | Default | Descripción |
|---|---|---|
| `k3s_install.gitops_argocd.enabled` | `false` | Activa el rol |
| `k3s_install.gitops_argocd.version` | `latest` | `latest` = última versión estable (rama `stable` del repo oficial); o un tag fijo, p. ej. `v3.5.3` |
| `k3s_install.gitops_argocd.gitops_repo_url` | gitops | URL informativa en mensaje final |

## Qué hace

1. Crea namespace `argocd`.
2. Aplica manifest oficial `argoproj/argo-cd` (versión fijada).
3. Espera `argocd-server` Available.
4. Recuerda aplicar `gitops/bootstrap/root-appset.yaml` (Fase 4).

## Verificar

```bash
sudo k3s kubectl get pods -n argocd
sudo k3s kubectl get secret argocd-initial-admin-secret -n argocd \
  -o jsonpath='{.data.password}' | base64 -d; echo
```

## Siguiente paso

[Fase 4 — GitOps](../../../docs/implementacion/fase-4-gitops.md): `kubectl apply -f gitops/bootstrap/root-appset.yaml`

## Documentación

- [Fase 3 — K3s](../../../docs/implementacion/fase-3-k3s.md)
- [Catálogo GitOps](../../../docs/gitops/index.md)
