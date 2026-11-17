# k3s_argocd

Instala el **controller Argo CD** en el clúster K3s y, la primera vez y solo si se pide, aplica el bootstrap de
[`gitops`](https://github.com/maceosoft/gitops) (`bootstrap/`: Application `homelab-bootstrap`, ApplicationSet
`homelab` y repos Helm). Las Applications viven en `gitops/bootstrap/components/`.

## Playbook

[`playbook-k3s.yml`](../../playbook-k3s.yml) — Fase 3.

Con `k3s_install.gitops_argocd.enabled: true` en
[`group_vars/incus_cluster/k3s_install.yml`](../../group_vars/incus_cluster/k3s_install.yml)
(no con `-e`: Ansible no fusiona claves con puntos en un diccionario):

```bash
ansible-playbook -i inventory.ini playbook-k3s.yml --tags argocd
# Primera instalación, después de playbook-platform-secrets.yml: además aplica gitops/bootstrap/
ansible-playbook -i inventory.ini playbook-k3s.yml --tags argocd -e k3s_argocd_bootstrap_confirm=true
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
| `k3s_install.gitops_argocd.gitops_local_path` | `{{ playbook_dir }}/../../gitops` | Copia local de gitops (en `main`) desde la que se renderiza `bootstrap/` |
| `k3s_argocd_bootstrap_confirm` | `false` | `true` (con `-e`) aplica `gitops/bootstrap/` si el ApplicationSet `homelab` todavía no existe |

## Qué hace

1. Crea namespace `argocd`.
2. Aplica manifest oficial `argoproj/argo-cd` (versión fijada).
3. Espera `argocd-server` Available.
4. Asegura en `argocd-cmd-params-cm` las claves que necesita el ApplicationSet `homelab`
   (`applicationsetcontroller.enable.progressive.syncs=true` para RollingSync y
   `applicationsetcontroller.enable.new.git.file.globbing=true` para que `components/*.yaml` no entre en
   `apagadas/`). El controller las lee solo al arrancar: si el rol tuvo que agregarlas, reinicia
   `argocd-applicationset-controller` una vez. Si ya están, no toca nada. Después las mantiene gitops
   (`addons/argocd/config/kustomization.yaml`, mismos valores).
5. Bootstrap de gitops, **solo con `k3s_argocd_bootstrap_confirm=true` y solo si el ApplicationSet `homelab` no
   existe**: exige la copia local de gitops en `main` y el Secret `argocd/repo-gitops` (de
   `playbook-platform-secrets.yml`), renderiza `bootstrap/` en la estación del operador (`kubectl kustomize`;
   gitops es privado y el server no tiene credenciales de GitHub), lo prueba con `--dry-run=server` y lo aplica.
   Si el ApplicationSet ya existe no lo vuelve a aplicar: lo administra ArgoCD (`homelab-bootstrap`) y aplicarlo a
   mano repondría `values.pausadas` y despausaría todas las apps. El rol nunca borra Applications ni
   ApplicationSets.

Con `--check` solo lee y prueba (`--dry-run=server`); no parchea, no reinicia ni aplica.

## Verificar

```bash
sudo k3s kubectl get pods -n argocd
sudo k3s kubectl get secret argocd-initial-admin-secret -n argocd \
  -o jsonpath='{.data.password}' | base64 -d; echo
```

## Siguiente paso

[Fase 4 — GitOps](../../../docs/implementacion/fase-4-gitops.md): `playbook-platform-secrets.yml` y después el
bootstrap (`-e k3s_argocd_bootstrap_confirm=true`, o a mano desde gitops: `kubectl apply -k bootstrap/`).

## Documentación

- [Fase 3 — K3s](../../../docs/implementacion/fase-3-k3s.md)
- [Catálogo GitOps](../../../docs/gitops/index.md)
