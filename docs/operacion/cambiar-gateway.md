# Cambiar el controlador de Gateway

El HomeLab publica sus servicios con [Gateway API](https://gateway-api.sigs.k8s.io/)
(`Gateway` y `HTTPRoute`), no con `Ingress`. Hay un solo `Gateway`, llamado
`homelab` (namespace `gateway`), con un listener HTTP (80) y uno HTTPS (443)
para `*.homelab.local`. Cada app se engancha con su propio `HTTPRoute`
(`argocd/route`, `vcluster/route`).

Quien atiende ese Gateway es **un controlador a la vez**; los tres comparten las
IP 80/443 de MetalLB y no pueden convivir:

| Application | Controlador | Notas |
|---|---|---|
| `kong` (**predeterminado**) | [Kong Ingress Controller](https://developer.konghq.com/kubernetes-ingress-controller/) (KIC) | Usa el Kong que instala el chart (modo *unmanaged*) |
| `traefik` | [Traefik](https://doc.traefik.io/traefik/routing/providers/kubernetes-gateway/) | Solo Gateway API: sin `Ingress` ni `IngressRoute` |
| `nginx-gateway` | [NGINX Gateway Fabric](https://docs.nginx.com/nginx-gateway-fabric/) | Necesita también `nginx-gateway-helm-repo` (registro OCI del chart) |

El `Gateway` de cada uno está en `gateway/<kong|traefik|nginx>/` del repo
[`gitops`](https://github.com/maceosoft/gitops); `GatewayClass`, puertos y
anotaciones cambian de uno a otro, los `HTTPRoute` no.

## Cómo funciona el TLS

- **cert-manager** (`cert-manager`) y una CA propia (`cert-manager-config`,
  `ClusterIssuer homelab-ca`) emiten el certificado. El `Gateway` lleva la
  anotación `cert-manager.io/cluster-issuer: homelab-ca` y cert-manager crea solo
  el Secret `homelab-tls`.
- El Gateway **termina el TLS** y habla HTTP con los servicios. Por eso
  `argocd-server` corre con `server.insecure` (en `argocd/config`) y el
  `HTTPRoute` apunta a su puerto 80. El diff del pipeline de `gitops` usa
  `--plaintext` por el mismo motivo.
- **Kong es la excepción.** KIC 3.5 con Kong 3.9 rechaza (`value must be null`) el
  certificado que arma para un listener de Gateway API, y Kong no llega a estar
  `Ready`. Por eso el Gateway de Kong no usa `certificateRefs`: cert-manager emite
  `kong-default-tls` (`gateway/kong/certificate.yaml`), el chart lo monta en el pod y
  Kong lo carga como certificado por defecto con `KONG_SSL_CERT` y `KONG_SSL_CERT_KEY`.
  Kong lo lee solo al arrancar: **tras cada renovación (cada ~60 días) reinicia el
  pod**: `kubectl -n kong rollout restart deploy/kong-gateway`. Traefik y NGINX Gateway
  Fabric usan el certificado que cert-manager crea a partir del Gateway (`homelab-tls`)
  y se actualizan solos.
- Para que el navegador confíe en la CA, importa su certificado raíz:

    ```bash
    kubectl -n cert-manager get secret homelab-ca -o jsonpath='{.data.ca\.crt}' | base64 -d > homelab-ca.crt
    ```

## Por qué el Service usa `externalTrafficPolicy: Local`

Con la política por defecto (`Cluster`), el tráfico que llega desde la LAN a un nodo que
**no** tiene el pod del controlador se reenvía a otro nodo, y en este clúster esa
conexión no responde: `curl` a `192.168.23.200` expiraba aunque el DNS resolvía bien.
Pasaba solo con tráfico externo que entraba por `deborah` u `oliver`; los pods, los
servicios y las conexiones desde los propios nodos funcionaban. Con `Local`, MetalLB
anuncia la IP desde el nodo donde corre el controlador y el tráfico va directo al pod
(y además se conserva la IP del cliente). Los tres controladores lo traen en
`gitops/argocd/apps/`.

!!! note "Causa de fondo sin resolver"
    No se aclaró por qué falla el reenvío entre nodos del tráfico externo (el overlay de
    Calico entre pods sí funciona). Afecta a cualquier otro Service `LoadBalancer` o
    `NodePort` con política `Cluster`. Para investigarlo hace falta capturar paquetes en
    los nodos (`tcpdump` no está instalado).

## Cambiar de controlador

1. En `bootstrap/root-appset.yaml` (repo `gitops`), **comenta** el controlador
   actual y **descomenta** el nuevo (y `nginx-gateway-helm-repo` si es NGINX).
   Haz push.
2. Vuelve a aplicar el ApplicationSet (ArgoCD no lo gestiona):

    ```bash
    kubectl apply -f gitops/bootstrap/root-appset.yaml
    ```

3. Las Applications de los controladores llevan el finalizer de ArgoCD: al
   comentar la app, `homelab-root` borra la Application **y** sus recursos (el
   Gateway y las IP quedan libres para el nuevo). Espera a que desaparezca:

    ```bash
    kubectl -n argocd get applications
    ```

4. Verifica que el Gateway quede programado y con IP:

    ```bash
    kubectl get gateway homelab -n gateway
    kubectl get httproute -A
    ```

    Tiene que mostrar `PROGRAMMED=True`, una dirección entre `192.168.23.200` y
    `.220`, y los `HTTPRoute` con `Accepted`.

## Primera vez (viniendo de ingress-nginx)

`ingress-nginx` y el `Ingress` de ArgoCD ya no existen en `gitops`. Sus
Applications desaparecen al volver a aplicar el ApplicationSet, pero lo que
crearon queda en el clúster:

```bash
kubectl -n argocd delete ingress argocd-server
kubectl delete namespace ingress-nginx
kubectl delete clusterrole,clusterrolebinding,ingressclass,validatingwebhookconfiguration \
  -l app.kubernetes.io/instance=ingress-nginx
```

Aplica primero el cambio de `argocd` (activa `server.insecure`): hasta que el
Gateway esté `Programmed`, entra a ArgoCD con
`kubectl port-forward svc/argocd-server -n argocd 8080:80` ([`http://localhost:8080`](http://localhost:8080)).

## Si falla

| Síntoma | Revisar |
|---|---|
| `Gateway` sin dirección o `PROGRAMMED=False` | `kubectl describe gateway homelab -n gateway`: GatewayClass inexistente (controlador no activo) o CRDs de Gateway API ausentes (`gateway-api` sin sincronizar) |
| `curl https://argocd.homelab.local` expira aunque el DNS resuelve a `192.168.23.200` | Revisa que el Service del controlador tenga `externalTrafficPolicy: Local` (`kubectl -n kong get svc kong-gateway-proxy -o jsonpath='{.spec.externalTrafficPolicy}'`) y que el pod corra en un nodo que MetalLB pueda anunciar |
| Dos controladores activos | Comenta uno: se pelean por las IP de MetalLB |
| El Gateway no tiene certificado (`homelab-tls` no existe) | `kubectl describe certificate -n gateway`; `cert-manager-config` debe estar `Healthy` |
| `HTTPRoute` sin `Accepted` | `kubectl describe httproute -n argocd argocd-server`: `parentRefs` debe apuntar a `homelab` en `gateway` |
| Con Kong, los pods no llegan a `Ready` y el log del controlador dice `failed posting new config to /config` | Ver el punto de Kong en *Cómo funciona el TLS*; confirma que existe el Secret `kong-default-tls` (`kubectl -n kong get certificate,secret`) |
| Con Kong, el listener queda sin programar | KIC enlaza el Gateway con los puertos del Kong del chart; revisa `kubectl describe gateway` y los puertos del Service `kong-gateway-proxy` |
| Con Kong, `kubectl -n kong logs deploy/kong-controller` dice `invalid config.location: missing host in url` | Un `HTTPRoute` con filtro `RequestRedirect` sin `hostname`: Kong arma el plugin `redirect` con una URL completa. Agrega `hostname` al filtro (ya está en `argocd/route` y `vcluster/route`) |
| ArgoCD responde `307` hacia la misma URL (bucle) o `too many redirects` | `server.insecure` se lee solo al arrancar: reinicia el pod (`kubectl -n argocd rollout restart deploy/argocd-server`) y comprueba el valor (`kubectl -n argocd get cm argocd-cmd-params-cm -o yaml`) |
| Con Kong, `http://…` responde `426 Upgrade Required` | La ruta solo-HTTPS gana a la de redirección: la anotación `konghq.com/https-redirect-status-code: "301"` del `HTTPRoute` hace que Kong redirija (ya está en `argocd/route` y `vcluster/route`) |
