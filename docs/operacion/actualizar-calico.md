# Calico (CNI) administrado por ArgoCD

Calico es el CNI (Container Network Interface, la red de los pods) del clúster. Se instala en
**dos etapas**:

1. **Bootstrap, con Ansible** (rol `k3s_cni`): al crear el clúster, ArgoCD todavía no existe y
   necesita red de pods para arrancar, así que Ansible instala Calico primero.
2. **Desde entonces, ArgoCD** lo administra y lo actualiza: dos Applications de
   [`maceosoft/gitops`](https://github.com/maceosoft/gitops).

| Application | Qué administra | Dónde |
|---|---|---|
| `calico-operator` | CRDs y el operador (`tigera-operator`) en la versión elegida | `cni/calico-operator/kustomization.yaml` |
| `calico-config` | `Installation` (pool de pods `10.42.0.0/16`, VXLAN cross-subnet) y `APIServer` | `cni/calico/custom-resources.yaml` |

!!! warning "Sync manual, sin prune"
    Las dos Applications **no** sincronizan solas. Un cambio de versión en git actualiza la red
    de los pods de los 3 nodos, así que se aplica a mano (UI de ArgoCD → **Sync**). Tampoco
    tienen `prune` ni finalizer: si se borra la Application, el CNI no se toca.

## Qué versión corre

```bash
kubectl get installation default -o jsonpath='{.status.calicoVersion}{"\n"}'
kubectl -n tigera-operator get deploy tigera-operator -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

## Adoptar y actualizar: 3.29.1 → 3.31.7 → 3.33.0 (en dos etapas)

Calico se instaló con **v3.29.1** (operador `v1.36.2`). La v3.33 solo soporta actualizar desde la **v3.31 o la v3.32**
(documentación de Calico), así que el salto directo desde la 3.29 **no está soportado**. Se hace en dos etapas, cada una
con su Sync y su verificación:

| Etapa | `cni/calico-operator/kustomization.yaml` | Operador | Qué hace |
|---|---|---|---|
| 1 | `v3.31.7` | `v1.40.15` | Adopta los recursos existentes y actualiza el CNI de 3.29.1 a 3.31.7 |
| 2 | `v3.33.0` | `v1.44.0` | Actualiza de 3.31.7 a 3.33.0 |

Desde la v3.31 los CRDs vienen en un archivo aparte (`operator-crds.yaml`), que ya incluye el kustomization.

Las dos Applications llevan `argocd.argoproj.io/compare-options: ServerSideDiff=true`: sin eso, Argo CD muestra `OutOfSync`
fantasma en los CRD de Calico y en los campos que el operador completa (como `assignmentMode` en el pool, nuevo en la v3.31),
aunque `kubectl diff --server-side` salga vacío.

!!! danger "Es la red de los pods de los tres nodos"
    Si una etapa falla, la red de pods queda comprometida y **no hay vuelta atrás sencilla**. Hazlo con ventana de
    mantenimiento y con acceso directo a los nodos. Es el mismo error que rompió Longhorn al saltar de la 1.6 a la 1.13:
    nunca saltes más versiones de las que soporta la documentación del proyecto.

**Antes:**

```bash
kubectl get tigerastatus                       # calico y apiserver: AVAILABLE=True
kubectl get nodes                              # los 3 Ready
kubectl get pods -A --no-headers | awk '$4!="Running" && $4!="Completed"'   # sin pods raros
```

**Vista previa de lo que cambiaría** (solo lectura, contra el servidor):

```bash
kustomize build gitops/cni/calico-operator | kubectl diff --server-side --force-conflicts -f - | grep -cE '^[+-] '
kubectl diff --server-side --force-conflicts -f gitops/cni/calico/custom-resources.yaml
```

La segunda debe salir **vacía**: el YAML de `calico-config` declara todos los campos que el
operador escribe, para que ArgoCD y el operador no se pisen.

**Sync, en orden:**

1. Activa las dos Applications: ya están en `bootstrap/root-appset.yaml`; aplica el ApplicationSet
   (`kubectl apply -f gitops/bootstrap/root-appset.yaml`).
2. En ArgoCD, **Sync** de `calico-operator` (con *Server-Side Apply*, ya activo). El operador se
   actualiza y reinicia los `calico-node` **de a un nodo** (`maxUnavailable: 1`).
3. Vigila: `kubectl -n calico-system get pods -w` y `kubectl get tigerastatus`.
4. Cuando todo esté `Available`, **Sync** de `calico-config`.
5. Verifica la etapa 1 (siguiente bloque) y **repite los pasos 2–4 para la etapa 2**, tras cambiar las URLs a `v3.33.0`
   y hacer push.

**Después:**

```bash
kubectl get installation default -o jsonpath='{.status.calicoVersion}{"\n"}'   # v3.31.7 tras la etapa 1; v3.33.0 tras la 2
kubectl get tigerastatus
kubectl -n argocd run curl-test --rm -i --restart=Never --image=curlimages/curl --quiet -- \
  curl -s -o /dev/null -w "%{http_code}\n" http://kong-gateway-proxy.kong.svc:80/
```

El último comprueba que un pod aún llega a un servicio de otro nodo.

## Cambios posteriores

- **Subir de versión:** cambia las dos URLs de `cni/calico-operator/kustomization.yaml`, haz push
  y **Sync** manual. Sube de a una o dos versiones menores y revisa las notas de cada versión.
- **No cambies** `cidr`, `encapsulation` ni `blockSize` del pool sin una ventana de
  mantenimiento: cambian la red de todos los pods.
- **No vuelvas a correr** `--tags cni` de Ansible sobre un clúster ya adoptado: el rol detecta
  que ArgoCD sigue el `Installation` y se salta Calico, para no pelear con él.

## Si falla

| Síntoma | Qué revisar |
|---|---|
| `calico-operator` queda `OutOfSync` tras el Sync | Es normal un momento por los campos que el operador agrega; si persiste, `kubectl diff --server-side` para ver qué difiere |
| `tigerastatus calico` en `Degraded` | `kubectl -n tigera-operator logs deploy/tigera-operator --tail=50` |
| Pods nuevos sin red | `kubectl -n calico-system get pods`; `calico-node` debe estar `Running` en los 3 nodos |
| ArgoCD no puede sincronizar (porque el CNI cayó) | Corrige el CNI con `kubectl` directo desde la estación, no a través de ArgoCD |
