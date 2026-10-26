# Actualizar Argo CD

Argo CD se actualiza **solo**, siempre a la última versión estable. La
Application `argocd` de [`maceosoft/gitops`](https://github.com/maceosoft/gitops)
instala el manifiesto oficial de la rama `stable` del repo de Argo CD y le suma
la configuración propia (Dex, RBAC —control de acceso por roles—, health check, cuenta `ci`): cuando sale una
versión nueva, Argo CD se aplica a sí mismo.

| Pieza | Qué hace |
|---|---|
| `argocd/apps/argocd.yaml` | La Application: sigue `argocd/config` con sincronización automática y `ServerSideApply` |
| `argocd/config/kustomization.yaml` | Base: [`https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml`](https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml). Encima, `configMapGenerator` con `behavior: merge` para `argocd-cm`, `argocd-rbac-cm` y `argocd-cmd-params-cm` |
| Rol Ansible `k3s_argocd` | Primera instalación y saltos de versión mayor (`version: latest` en `k3s_install.yml`) |

!!! warning "Es una actualización sin supervisión"
    Una versión nueva se aplica sin preguntarte, y Argo CD es lo que despliega
    todo lo demás. Ya pasa por el pipeline de `gitops` (los manifiestos de la
    versión nueva se validan al cambiar tu repo), pero **no** cuando cambia
    el repo de Argo CD. Si una versión nueva da problemas, ver
    [Si una versión nueva falla](#si-una-version-nueva-falla).

## Cuánto tarda en enterarse

El repo-server guarda los manifiestos generados una hora
(`reposerver.default.cache.expiration: 1h` en `argocd-cmd-params-cm`), así que
una versión nueva se detecta como máximo **una hora después** de publicada.
Para adelantarlo:

```bash
kubectl -n argocd annotate application argocd argocd.argoproj.io/refresh=hard --overwrite
```

## La primera vez: actualizar a mano, y después activar la app

!!! danger "El orden importa"
    Una Argo CD vieja (2.x) **no puede compararse a sí misma** en un clúster
    con Kubernetes 1.36 (`.status.terminatingReplicas: field not declared in schema`), así que no puede ser ella quien se actualice. La primera
    actualización la hace el rol de Ansible. **No hagas `git push` del cambio
    de `gitops` antes** (reemplaza `argocd-config` por `argocd` en el
    ApplicationSet).

1. **Comprueba la versión actual y la que va a instalar:**

    ```bash
    export KUBECONFIG=~/.kube/homelab-k3s.yaml
    kubectl -n argocd get deploy argocd-server -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
    curl -s https://raw.githubusercontent.com/argoproj/argo-cd/stable/VERSION
    ```

2. **Simulación en el servidor, sin cambiar nada** (tiene que terminar sin
   errores; los avisos *failed to migrate last-applied-configuration* son
   normales):

    ```bash
    curl -sL https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml \
      | kubectl apply -n argocd --server-side --force-conflicts --dry-run=server -f -
    ```

3. **Actualiza con Ansible** (desde `ansible/` en `homelab`):

    ```bash
    ansible-playbook -i inventory.ini playbook-k3s.yml --tags argocd
    ```

    El rol resuelve `version: latest` (la última estable) y aplica el manifiesto
    oficial con `--server-side --force-conflicts` (obligatorio desde Argo CD 3.3,
    cuyo CRD de `ApplicationSet` supera el límite del apply normal).

4. **Verifica** que todo vuelve a sano. Con la versión nueva desaparece el error
   de comparación de las apps:

    ```bash
    kubectl -n argocd get pods
    kubectl -n argocd get deploy argocd-server -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
    kubectl -n argocd get applications
    ```

5. **Ahora sí, `git push`** de `gitops`. El ApplicationSet cambia `argocd-config`
   por `argocd`: la Application vieja se borra **sin** borrar sus recursos
   (los ConfigMaps de Dex y RBAC quedan), y la nueva los adopta. Vuelve a
   comprobar con `kubectl -n argocd get applications`.

## Mantenerse en una versión (pausar las actualizaciones)

Para fijar una versión, cambia la base de `argocd/config/kustomization.yaml`,
en `gitops`, de `stable` a un tag:

```yaml
resources:
  - https://raw.githubusercontent.com/argoproj/argo-cd/v3.5.3/manifests/install.yaml
```

Para volver a las actualizaciones automáticas, vuelve a poner `stable`. En el
rol de Ansible, el equivalente es `k3s_install.gitops_argocd.version: v3.5.3`.

## Si una versión nueva falla

1. **Fija la versión anterior** en `gitops` (sección anterior) y espera a que se
   aplique.
2. Si Argo CD no arranca y no puede aplicar nada, vuelve a instalar la versión que
   funcionaba directo con `kubectl` (no depende de Argo CD):

    ```bash
    kubectl apply -n argocd --server-side --force-conflicts \
      -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.5.3/manifests/install.yaml
    ```

3. Las [notas de actualización](https://argo-cd.readthedocs.io/en/stable/operator-manual/upgrading/overview/)
   de Argo CD dicen qué cambia en cada versión menor.

## Si falla

| Síntoma | Revisar |
|---|---|
| `ComparisonError … terminatingReplicas: field not declared in schema` | Argo CD es anterior a la 3.5: hay que hacer la primera actualización con Ansible (arriba) |
| `argocd` queda `OutOfSync` tras activarla | Es normal unos minutos: Argo CD le agrega a cada recurso su anotación de seguimiento |
| `The CustomResourceDefinition "applicationsets.argoproj.io" is invalid: metadata.annotations: Too long` | Se aplicó sin `--server-side`; usa los comandos de esta página |
| Se pierde el login con GitHub tras actualizar | `argocd-cm` debe tener la clave `dex.config` (`kubectl -n argocd get cm argocd-cm -o jsonpath='{.data.dex\.config}'`) y el Secret `argocd-secret` sus claves `dex.*` ([Dex](../implementacion/fase-4-gitops.md)) |
| Una versión nueva no se detecta | Espera una hora, o fuerza: `kubectl -n argocd annotate application argocd argocd.argoproj.io/refresh=hard --overwrite` |
