# Change the Gateway Controller

The HomeLab publishes its services with [Gateway API](https://gateway-api.sigs.k8s.io/)
(`Gateway` and `HTTPRoute`), not with `Ingress`. There is a single `Gateway`, called
`homelab` (namespace `gateway`), with an HTTP listener (80) and one HTTPS (443)
for `*.homelab.local`. Each app hooks up with its own `HTTPRoute`
(`argocd/route`, `vcluster/route`).

Only **one controller at a time** handles that Gateway; the three share the
IP 80/443 from MetalLB and cannot coexist:

| Application | Controller | Notes |
|---|---|---|
| `kong` (**default**) | [Kong Ingress Controller](https://developer.konghq.com/kubernetes-ingress-controller/) (KIC) | Uses the Kong installed by the chart (unmanaged mode) |
| `traefik` | [Traefik](https://doc.traefik.io/traefik/routing/providers/kubernetes-gateway/) | Only Gateway API: no `Ingress` or `IngressRoute` |
| `nginx-gateway` | [NGINX Gateway Fabric](https://docs.nginx.com/nginx-gateway-fabric/) | Also needs `nginx-gateway-helm-repo` (OCI chart registry) |

The `Gateway` of each is in `gateway/<kong|traefik|nginx>/` of the repo
[`gitops`](https://github.com/maceosoft/gitops); `GatewayClass`, ports, and
annotations differ from one to another, the `HTTPRoute` do not.

## How TLS Works

- **cert-manager** (`cert-manager`) and a custom CA (certificate authority) (`cert-manager-config`,
  `ClusterIssuer homelab-ca`) issue the certificate. The `Gateway` has the
  annotation `cert-manager.io/cluster-issuer: homelab-ca` and cert-manager creates only
  the Secret `homelab-tls`.
- The Gateway **terminates TLS** (Transport Layer Security) and speaks HTTP with the services. That's why
  `argocd-server` runs with `server.insecure` (in `argocd/config`) and the
  `HTTPRoute` points to its port 80. The diff of the `gitops` pipeline uses
  `--plaintext` for the same reason.
- **Kong is the exception.** KIC (Kong Ingress Controller) 3.5 with Kong 3.9 rejects (`value must be null`) the
  certificate it builds for a Gateway API listener, and Kong never gets
  `Ready`. That's why Kong's Gateway does not use `certificateRefs`: cert-manager issues
  `kong-default-tls` (`gateway/kong/certificate.yaml`), the chart mounts it in the pod and
  Kong loads it as the default certificate with `KONG_SSL_CERT` and `KONG_SSL_CERT_KEY`.
  Kong reads it only on startup: **after each renewal (every ~60 days) restart the
  pod**: `kubectl -n kong rollout restart deploy/kong-gateway`. Traefik and NGINX Gateway
  Fabric use the certificate that cert-manager creates from the Gateway (`homelab-tls`)
  and update automatically.

- To make the browser trust the CA, import its root certificate:

    ```bash
    kubectl -n cert-manager get secret homelab-ca -o jsonpath='{.data.ca\.crt}' | base64 -d > homelab-ca.crt
    ```

## Why the Service Uses `externalTrafficPolicy: Local`

With the default policy (`Cluster`), traffic arriving from the LAN to a node that
**does not** have the controller pod is forwarded to another node, and in this cluster
that connection does not respond: `curl` to `192.168.23.200` expired even though DNS resolved correctly.
It only happened with external traffic entering via `deborah` or `oliver`; pods, services, and connections
from the nodes themselves worked fine. With `Local`, MetalLB
advertises the IP from the node where the controller runs and the traffic goes directly to the pod
(and also preserves the client IP). The three controllers bring it in
`gitops/argocd/apps/`.

!!! note "Underlying issue unresolved"
    The reason why inter-node forwarding of external traffic fails (the Calico overlay between pods works) is not clear. It affects any other Service `LoadBalancer` or
    `NodePort` with policy `Cluster`. To investigate, packet captures are needed on
    the nodes (`tcpdump` is not installed).

## Change the Controller

1. In `bootstrap/root-appset.yaml` (repo `gitops`), **comment out** the current controller
   and **uncomment** the new one (and `nginx-gateway-helm-repo` if it's NGINX).
   Push the changes.
2. Reapply the ApplicationSet (Argo CD does not manage it):

    ```bash
    kubectl apply -f gitops/bootstrap/root-appset.yaml
    ```

3. The Applications of the controllers carry the Argo CD finalizer: when you
   comment out the app, `homelab-root` deletes the Application **and** its resources (the
   Gateway and the IP are freed for the new one). Wait for it to disappear:

    ```bash
    kubectl -n argocd get applications
    ```

4. Verify that the Gateway is scheduled and has an IP:

    ```bash
    kubectl get gateway homelab -n gateway
    kubectl get httproute -A
    ```

    It should show `PROGRAMMED=True`, an address between `192.168.23.200` and
    `.220`, and the `HTTPRoute` with `Accepted`.

## First Time (Coming from ingress-nginx)

`ingress-nginx` and the `Ingress` of Argo CD no longer exist in `gitops`. Their
Applications disappear when you reapply the ApplicationSet, but what
they created remains in the cluster:

```bash
kubectl -n argocd delete ingress argocd-server
kubectl delete namespace ingress-nginx
kubectl delete clusterrole,clusterrolebinding,ingressclass,validatingwebhookconfiguration \
  -l app.kubernetes.io/instance=ingress-nginx
```

Apply the change to `argocd` first (activate `server.insecure`): until the
Gateway is `Programmed`, access Argo CD with
`kubectl port-forward svc/argocd-server -n argocd 8080:80` ([`http://localhost:8080`](http://localhost:8080)).

## If it fails

| Symptom | Check |
|---|---|
| `Gateway` without address or `PROGRAMMED=False` | `kubectl describe gateway homelab -n gateway`: GatewayClass missing (controller not active) or Gateway API CRDs absent (`gateway-api` not synced) |
| `curl https://argocd.homelab.local` expires even though DNS resolves to `192.168.23.200` | Check that the controller Service has `externalTrafficPolicy: Local` (`kubectl -n kong get svc kong-gateway-proxy -o jsonpath='{.spec.externalTrafficPolicy}'`) and that the pod runs on a node MetalLB can announce |
| Two active controllers | Comment out one: they fight for MetalLB IPs |
| The Gateway has no certificate (`homelab-tls` does not exist) | `kubectl describe certificate -n gateway`; `cert-manager-config` must be `Healthy` |
| `HTTPRoute` without `Accepted` | `kubectl describe httproute -n argocd argocd-server`: `parentRefs` must point to `homelab` in `gateway` |
| With Kong, pods do not reach `Ready` and the controller log says `failed posting new config to /config` | See the Kong point in *How it works with TLS*; confirm that the Secret `kong-default-tls` (`kubectl -n kong get certificate,secret`) exists |
| With Kong, the listener remains unprogrammed | KIC links the Gateway to the Kong chart ports; check `kubectl describe gateway` and the Service ports `kong-gateway-proxy` |
| With Kong, `kubectl -n kong logs deploy/kong-controller` says `invalid config.location: missing host in url` | A `HTTPRoute` with filter `RequestRedirect` without `hostname`: Kong builds the plugin `redirect` with a full URL. Add `hostname` to the filter (already in `argocd/route` and `vcluster/route`) |
| Argo CD responds `307` to the same URL (loop) or `too many redirects` | `server.insecure` is read only on startup: restart the pod (`kubectl -n argocd rollout restart deploy/argocd-server`) and check the value (`kubectl -n argocd get cm argocd-cmd-params-cm -o yaml`) |
| With Kong, `http://…` responds `426 Upgrade Required` | The HTTPS-only route wins over the redirect route: the annotation `konghq.com/https-redirect-status-code: "301"` of `HTTPRoute` makes Kong redirect (already in `argocd/route` and `vcluster/route`) |
