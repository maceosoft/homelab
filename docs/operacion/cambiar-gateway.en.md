# Change the Gateway Controller

The HomeLab publishes its services with [Gateway API](https://gateway-api.sigs.k8s.io/)
(`Gateway` and `HTTPRoute`), not with `Ingress`. There is a single `Gateway`, called
`homelab` (namespace `gateway`), with an HTTP listener (80) and an HTTPS listener (443)
for `*.homelab.local`. Each app connects with its own `HTTPRoute`
(`addons/argocd/route`, `addons/cluster/vcluster/route`).

Only **one controller at a time** serves that Gateway; the three share the
MetalLB 80/443 IPs and cannot coexist:

| Application | Controller | Notes |
|---|---|---|
| `kong` (**default**) | [Kong Ingress Controller](https://developer.konghq.com/kubernetes-ingress-controller/) (KIC) | Uses the Kong installed by the chart (unmanaged mode) |
| `traefik` | [Traefik](https://doc.traefik.io/traefik/routing/providers/kubernetes-gateway/) | Gateway API only: no `Ingress` or `IngressRoute` |
| `nginx-gateway` | [NGINX Gateway Fabric](https://docs.nginx.com/nginx-gateway-fabric/) | Also needs `nginx-gateway-helm-repo` (chart OCI registry) |

Each `Gateway` is in `addons/network/gateway/<kong|traefik|nginx>/` of the repo
[`gitops`](https://github.com/maceosoft/gitops); `GatewayClass`, ports and
annotations differ between them, the `HTTPRoute` do not.

## How TLS Works

- **cert-manager** (`cert-manager`) and a custom CA (Certificate Authority) (`cert-manager-config`,
  `ClusterIssuer homelab-ca`) issue the certificate. The `Gateway` carries the
  annotation `cert-manager.io/cluster-issuer: homelab-ca` and cert-manager creates only
  the Secret `homelab-tls`.
- The Gateway **terminates TLS** (Transport Layer Security) and speaks HTTP to the services. That's why
  `argocd-server` runs with `server.insecure` (in `addons/argocd/config`) and the
  `HTTPRoute` points to its port 80. The `gitops` pipeline diff uses
  `--plaintext` for the same reason.
- **Kong is the exception.** KIC (Kong Ingress Controller) 3.5 with Kong 3.9 rejects (`value must be null`) the
  certificate it builds for a Gateway API listener, and Kong never becomes
  `Ready`. That's why the Kong Gateway doesn't use `certificateRefs`: cert-manager issues
  `kong-default-tls` (`addons/network/gateway/kong/certificate.yaml`), the chart mounts it in the pod and
  Kong loads it as the default certificate with `KONG_SSL_CERT` and `KONG_SSL_CERT_KEY`.
  Kong reads it only at startup: **after each renewal (every ~60 days) restart the
  pod**: `kubectl -n kong rollout restart deploy/kong-gateway`. Traefik and NGINX Gateway
  Fabric use the certificate cert-manager creates from the Gateway (`homelab-tls`)
  and update automatically.
- For the browser to trust the CA, import its root certificate:

    ```bash
    kubectl -n cert-manager get secret homelab-ca -o jsonpath='{.data.ca\.crt}' | base64 -d > homelab-ca.crt
    ```

    === "🖱️ From the UI"

        - **macOS:** open `homelab-ca.crt` by double-clicking (added to *Keychain Access*), open it in the list and under
          **Trust** choose *Always Trust*.
        - **Firefox** (has its own store; if it doesn't trust the system CA): *Settings → Privacy & Security → Certificates →
          View Certificates → Authorities → Import*, and mark it to trust for identifying websites.

    === "⌨️ From the console"

        ```bash
        # macOS (llavero del sistema)
        sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain homelab-ca.crt
        # Debian/Ubuntu
        sudo cp homelab-ca.crt /usr/local/share/ca-certificates/ && sudo update-ca-certificates
        ```

        If Firefox still doesn't trust it (on Linux it doesn't read the system store), import it from its interface.

## Why the Service Uses `externalTrafficPolicy: Local`

With the default policy (`Cluster`), traffic arriving from the LAN to a node that
**does not** have the controller pod gets forwarded to another node, and in this cluster that
connection doesn't respond: `curl` to `192.168.23.200` timed out even though DNS resolved correctly.
It only happened with external traffic entering via `deborah` or `oliver`; pods,
services, and connections from the nodes themselves worked. With `Local`, MetalLB
announces the IP from the node where the controller runs and traffic goes straight to the pod
(and the client IP is preserved too). All three controllers include it in
their `gitops/bootstrap/components/` Application (Kong) or `bootstrap/components/apagadas/` (Traefik and NGINX).

!!! note "Underlying cause not resolved"
    It wasn't clarified why inter-node forwarding of external traffic fails (the Calico
    overlay between pods works fine). It affects any other `LoadBalancer` or
    `NodePort` Service with `Cluster` policy. To investigate, packet captures on
    the nodes are needed (`tcpdump` is not installed).

## Switch Controllers

1. In the `gitops` repo, move the current controller's file to `bootstrap/components/apagadas/` and the new one's from
   `apagadas/` to `bootstrap/components/` (if NGINX, also uncomment
   `repositories/nginx-gateway-helm-repo.yaml` in `bootstrap/kustomization.yaml`). Merge into `main`: nothing needs
   to be applied, `homelab-bootstrap` and the ApplicationSet `homelab` read git.
2. With `applicationsSync: create-update` (current mode) the ApplicationSet **does not** delete the old controller's
   Application: delete it manually. The controller Applications carry the Argo CD finalizer, so they delete the
   Application **and** its resources (the Gateway and IPs are freed for the new one):

    ```bash
    kubectl -n argocd delete application kong   # el controlador que sale
    ```

3. Wait for it to disappear and for the new one to become `Healthy` (runs in wave 3):

    ```bash
    kubectl -n argocd get applications -L homelab.maceo.cl/rollout-wave
    ```

4. Verify the Gateway is programmed and has an IP:

    ```bash
    kubectl get gateway homelab -n gateway
    kubectl get httproute -A
    ```

    It must show `PROGRAMMED=True`, an address between `192.168.23.200` and
    `.220`, and the `HTTPRoute` with `Accepted`.

## First Time (Coming from ingress-nginx)

`ingress-nginx` and the `Ingress` of Argo CD no longer exist in `gitops`. If their
Application still remains in the cluster, delete it manually (the ApplicationSet `homelab`
doesn't delete Applications in its current mode); what they created stays in the cluster:

```bash
kubectl -n argocd delete ingress argocd-server
kubectl delete namespace ingress-nginx
kubectl delete clusterrole,clusterrolebinding,ingressclass,validatingwebhookconfiguration \
  -l app.kubernetes.io/instance=ingress-nginx
```

Apply the `argocd` change first (enables `server.insecure`): until the
Gateway is `Programmed`, access Argo CD with
`kubectl port-forward svc/argocd-server -n argocd 8080:80` ([`http://localhost:8080`](http://localhost:8080)).

## If it fails

| Symptom | Check |
|---|---|
| `Gateway` without address or `PROGRAMMED=False` | `kubectl describe gateway homelab -n gateway`: nonexistent GatewayClass (controller not active) or missing Gateway API CRDs (`gateway-api` not synced) |
| `curl https://argocd.homelab.local` times out even though DNS resolves to `192.168.23.200` | Verify that the controller Service has `externalTrafficPolicy: Local` (`kubectl -n kong get svc kong-gateway-proxy -o jsonpath='{.spec.externalTrafficPolicy}'`) and that the pod runs on a node MetalLB can announce |
| Two active controllers | Comment out one: they fight over MetalLB IPs |
| Gateway has no certificate (`homelab-tls` does not exist) | `kubectl describe certificate -n gateway`; `cert-manager-config` must be `Healthy` |
| `HTTPRoute` without `Accepted` | `kubectl describe httproute -n argocd argocd-server`: `parentRefs` must point to `homelab` in `gateway` |
| With Kong, pods don't reach `Ready` and controller log says `failed posting new config to /config` | See Kong point in *How TLS works*; confirm Secret `kong-default-tls` exists (`kubectl -n kong get certificate,secret`) |
| With Kong, listener remains unscheduled | KIC binds Gateway to chart Kong ports; check `kubectl describe gateway` and Service ports `kong-gateway-proxy` |
| With Kong, `kubectl -n kong logs deploy/kong-controller` says `invalid config.location: missing host in url` | A `HTTPRoute` with filter `RequestRedirect` without `hostname`: Kong builds plugin `redirect` with a full URL. Add `hostname` to filter (already in `addons/argocd/route` and `addons/cluster/vcluster/route`) |
| Argo CD responds `307` to same URL (loop) or `too many redirects` | `server.insecure` is read only at startup: restart pod (`kubectl -n argocd rollout restart deploy/argocd-server`) and verify value (`kubectl -n argocd get cm argocd-cmd-params-cm -o yaml`) |
| With Kong, `http://…` responds `426 Upgrade Required` | HTTPS-only route beats redirect route: the `konghq.com/https-redirect-status-code: "301"` annotation on the `HTTPRoute` makes Kong redirect (already in `addons/argocd/route` and `addons/cluster/vcluster/route`) |
