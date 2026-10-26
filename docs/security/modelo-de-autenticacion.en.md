# Authentication model

General HomeLab rule: **nothing is exposed without authentication, or without an explicit and documented network restriction when authentication is not possible.**

- **People → Dex.** Anyone opening something in the browser or via SSH (*Secure Shell*, the remote terminal connection) logs in with their GitHub account through Dex
  (the HomeLab identity provider, using the `devops` team from the `maceosoft` organization). If the service
  speaks OIDC (OpenID Connect, the login protocol over OAuth 2.0 —Open Authorization—) natively, it connects
  directly; if not, `oauth2-proxy` is placed in front.
- **Machines → own token or key + network restriction.** A program calling another uses a token
  (a random secret, one per client) and, additionally, can only reach it from where it belongs.
- **What cannot authenticate** (inter-node protocols, exporters) is limited by network and listed as
  [exception](#network-controlled-exceptions).

## Who authenticates whom

| Service | Used by | How it authenticates |
|---|---|---|
| Argo CD, Grafana | People | Dex (GitHub, team `devops`). A local emergency access remains (`admin` of Grafana); the local `admin` of Argo CD is disabled (`admin.enabled: "false"`) and the pipeline uses its own token (`ci`) with expiration |
| Open WebUI | People | Dex (SSO, *Single Sign-On*: single sign-on, with GitHub): public client with PKCE (*Proof Key for Code Exchange*, a protection for clients without a secret), no shared secret. SSO only: no local form or password registration, not even for the first administrator; only the `devops` team enters |
| vCluster, Incus | People | Dex (OIDC). Incus also limits port `8443` by firewall |
| SSH to nodes | People | opkssh with Dex identity (group `maceosoft:devops`); no password or root |
| K3s API (`6443`) | People and machines | K3s certificates for machines; Dex (flags `oidc-*`) for people |
| Ollama Router (`/api/*`, `/v1/*`) | Machines: Open WebUI, K8sGPT, translation, reports, alert-triage | Token `Authorization: Bearer`, **one per client** (item `ollama-router`) + ingress NetworkPolicy (when active; see [What is active](#what-is-active-and-what-is-pending-activation)); the router blocks model management verbs (`pull`, `create`, `delete`, `copy`, `push`) and `blobs` |
| Ollama Router (`/_registry`) | Machines: each Ollama node | Bearer token different from the clients' (field `registry_token` of item `ollama-router`) |
| Ollama Nodes (`11434`) | Only the router | **Ollama does not authenticate.** Listens on the node IP and the firewall allows port `11434` from K3s nodes **and from pods** (because the router may be on the same node). The real protection is the router token plus the NetworkPolicy of the `ai` namespace. See [exceptions](#network-controlled-exceptions) |
| `alert-triage` | Alertmanager | Bearer token in header (`http_config.authorization`) + NetworkPolicy |
| Open Terminal (`ai-sandbox`) | Machine: Open WebUI | Bearer API key mounted as file (item `open-terminal`, field `api_key`) + NetworkPolicy that only admits Open WebUI; use restricted to administrators and the `maceosoft:devops` group |
| `mcpo` and MCP tools | Open WebUI | API key (`--api-key`, item `mcp-api-key`) + NetworkPolicy; tools only for administrators |
| Kong (gateway) | Everyone entering via `*.homelab.local` | Terminates TLS. **Kong Manager** disabled and **Admin API** internal only (ClusterIP; its NetworkPolicy is pending activation) |
| Alertmanager, vmui/vmalert, Longhorn UI, VictoriaLogs | People, if needed | No own login: they are internal (ClusterIP, no route). To view them in the browser, `oauth2-proxy` + Dex (optional, pending activation) |
| DNS (BIND) | Entire network (LAN, other subnets, VPN) | Does not authenticate or limit by origin; no zone transfers, hidden version and the port is not forwarded to the internet |

## What is active and what is pending activation

Some controls are deployed in stages, to avoid breaking the cluster all at once. In the repo
[`gitops`](https://github.com/maceosoft/gitops/blob/main/bootstrap/root-appset.yaml) they are **commented out** in
`root-appset.yaml` until they are activated one by one, after reading their README:

| Control | Status |
|---|---|
| NetworkPolicy `default-deny` per namespace (`ai`, `monitoring`, `longhorn-system`, `kong`, `gateway`, `arc-runners`) | **Pending activation**, one by one and in this order: `netpol-ai`, `netpol-monitoring`, `netpol-longhorn-system`, `netpol-kong` and `netpol-gateway`, `netpol-arc-runners` (read the README of [`security/networkpolicies/`](https://github.com/maceosoft/gitops/tree/main/security/networkpolicies) first) |
| Pod Security Admission labels (`warn`/`audit` with `restricted`) | **Pending activation** (application `namespace-labels`) |
| `oauth2-proxy` in front of internal interfaces (e.g. Alertmanager) | **Pending activation** and optional |
| NetworkPolicies that travel with their own application: logs (VictoriaLogs and Vector), `ai/tools`, `alert-triage` and Open Terminal (the one from `ai-sandbox` goes with the pod) | **Active** when deploying that application |
| People login to K3s API: ClusterRoleBinding `oidc-devops-view` (Application `security-rbac`) | **Active**, read-only (`view`); harmless until OIDC exists |
| K8sGPT | **Staged**: the decision is up to the user (see below) |
| Router Bearer tokens, Open Terminal key, Dex in Open WebUI, Kong Manager disabled, `admin` of Argo CD disabled | **Active** on deploy |

While a NetworkPolicy is not active, the network control for that service is only the node firewall and
the service's own token or key. The tables below describe the complete design; the "Control" column of the
exceptions applies when the corresponding control is active.

## Rules for a new service

Before publishing anything, answer these questions. If any lacks an answer, it does not get published.

1. **Who uses it, a person or a machine?**
    - Person: does it speak OIDC? Then a Dex client (public with PKCE —Proof Key for Code Exchange— if possible, confidential with secret if not). Does it not speak OIDC? `oauth2-proxy` in front, with `--allowed-group=maceosoft:devops`.
    - Machine: its own random token (`openssl rand -hex 32`), stored in 1Password and applied with `playbook-platform-secrets.yml`. **One token per client**, so you can revoke one without touching the rest.
2. **Where is it reached from?** Internal services: ClusterIP and NetworkPolicy; no Kong route unless needed. Services on a node: listen only on the required IP and the node firewall (`nftables`) allows only who corresponds.
3. **No NodePort, LoadBalancer, or `hostPort`** unless essential and on the exception list below.
4. **Its NetworkPolicy** in the namespace: `default-deny` and explicit ingress and egress permissions.
5. **Secrets never go to Git** (`homelab` is a public repo and `gitops`, though private, doesn't store secrets either): 1Password and cluster Secrets.
6. **If it cannot carry authentication**, add it to the exception table, with the reason and the control that replaces it.

!!! info "Why `oauth2-proxy` and not a Kong plugin"
    The Kong OIDC plugin is Enterprise edition, and Gateway API external authentication is not available in the KIC (Kong Ingress Controller) version used. `oauth2-proxy` is deployed as the **HTTPRoute backend** for each service, with a confidential Dex client per service and PKCE (`S256`).

## Network-controlled exceptions

What **cannot or must not** carry its own authentication stays only with an explicit network restriction:

| Service | Why no login | Replacing control |
|---|---|---|
| BGP `179` (Calico/bird), FRR `2623`, `7946` (MetalLB memberlist), `5473` (Typha) | Node-to-node protocols, no user authentication (BGP without MD5) | `nftables`: only node IPs and pod range; `rpcbind` (`111`) is disabled |
| `9100` (node-exporter), `9120`, `9140` and `9141` (MetalLB and FRR metrics) | Exporters without authentication in this deployment | `nftables` only to the metrics collector and nodes; node-exporter with TLS and basic auth if the chart allows |
| `30980` (`healthCheckNodePort` of `kong-gateway-proxy`) | Standard Kubernetes mechanism with `externalTrafficPolicy: Local`: only tells how many local endpoints exist | `nftables` only from nodes |
| `19443` (MetalLB webhook, `statuscleaner`) | Admission webhook: called by the API server | `nftables` only from nodes and the API server |
| DNS `53` (BIND) | DNS does not authenticate clients and serves the whole network (LAN, other subnets, VPN) | No zone transfers and hidden version; the port is filtered by the router (not forwarded to internet) |
| Ollama `11434` on each node (and on the Mac) | Ollama API has no authentication | Node firewall: `11434` from K3s nodes and from pods (`host_firewall_ollama_allow_pods`), and from machines added to `host_firewall_ollama_extra_cidrs` (the Mac); on the Mac, `allowed_cidrs` of the proxy. **The node does not authenticate**: what protects inference is the router's Bearer token and the `ai` namespace NetworkPolicies. Clients don't talk to a node, only to the router |
| Internal services without login (Alertmanager, vmsingle/vmui, vmalert, Longhorn UI, VictoriaLogs, Kong Admin API, `/metrics` of the router, kubelet `10250`) | Internal ClusterIPs without native authentication (kubelet does authenticate) | NetworkPolicy `default-deny` with explicit permissions; for the browser, `oauth2-proxy` + Dex |
| Open Terminal egress (`ai-sandbox`) | Runs arbitrary code and needs to download packages | Egress NetworkPolicy only to internet on 80/443, no access to cluster or internal network; no `docker.sock` |
| Calico VXLAN (UDP `4789`), OVN Geneve (UDP `6081`), etcd (`2379`, `2380`), calico-node metrics (`9091`), kube-proxy healthz (`10256`) | Internal cluster traffic, no user authentication | `nftables`: only nodes (and pods where needed); Geneve only between nodes |
| SSH `22`, K3s API `6443`, kubelet `10250`, Incus `8443` | Have their own authentication (keys and Dex, certificates, kubelet authn/authz, OIDC), but listen on the network | `nftables`: LAN and operator workstation (SSH), nodes, pods and operator (the rest) |
| `kong-gateway-proxy` service (LoadBalancer `192.168.23.200`) | It is the HomeLab entry point; each route carries its own authentication | HTTP listeners only redirect to HTTPS |
| Dex (`/api/dex`) and Kong HTTP listeners | Dex is the login mechanism itself; HTTP only redirects to HTTPS | By design |

The source of truth for this list is
[`ansible/files/exposure-allowlist.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/files/exposure-allowlist.yml),
which the audit script reads; if this table and the file differ, the file wins.

!!! info "Audit scope"
    The audit covers Kubernetes services, Gateway routes, and node ports. It does not cover the router's WireGuard, services inside Incus instances (`lb01`, `vm01`, `test`), or the `deborah` Docker socket (it is a Unix socket, not a network socket).

## Re-run the audit

[`ansible/scripts/audit_exposure.sh`](https://github.com/maceosoft/homelab/blob/main/ansible/scripts/audit_exposure.sh)
is a **read-only** script: it lists NodePort and LoadBalancer Services, HTTPRoutes (and whether their backend is an auth proxy or an app with OIDC), and the NetworkPolicies of each namespace, and compares them against the
[exception list](https://github.com/maceosoft/homelab/blob/main/ansible/files/exposure-allowlist.yml).
It exits with code `1` if it finds anything **outside that list** (and `2` if a tool is missing; for example, if the system Python lacks PyYAML, use one that has it). The list includes temporary entries, with a review date, for namespaces that still lack a NetworkPolicy, so it serves to detect regressions:

```bash
export KUBECONFIG=~/.kube/homelab-k3s.yaml
ansible/scripts/audit_exposure.sh
# 0 = sin sorpresas
echo $?

# Además, los puertos que escucha cada nodo (por SSH, solo lectura):
AUDIT_NODES="deborah invincible oliver" ansible/scripts/audit_exposure.sh
```

When you add a legitimate exception, update this table **and** the script's list in the same change.
The firewall that closes the node ports is described in
[Post-incident hardening](hardening-post-incidente.md).

## Optional checks

- **Calico and global policies.** By default, a service account without permissions should not be able to create a
  `GlobalNetworkPolicy`. This is verified with:

    ```bash
    kubectl --as=system:serviceaccount:default:default create --dry-run=server -f globalnetworkpolicy.yaml
    ```

    (with any test `GlobalNetworkPolicy`). If it responds `created`, that account can change the pods' firewall: remove the `calico-tiered-policy-passthrough` binding that allows it.
    Mitigation steps are in [`security/calico-policy-edit/`](https://github.com/maceosoft/gitops/tree/main/security/calico-policy-edit).
- **K8sGPT.** Its chart ships a ClusterRole `*/*/*` (effectively, cluster admin) and its dynamic RBAC reads Secrets across the entire cluster. That is why it is **staged** (commented out in `root-appset.yaml`). To enable it there are three paths, in [`security/k8sgpt-rbac/`](https://github.com/maceosoft/gitops/tree/main/security/k8sgpt-rbac): accept the risk and uncomment the line; use the proposed scoped role (untested); or also enable the namespace's NetworkPolicy.

## Pending decisions

The following does not activate on its own: each item is decided and executed by a person.

1. **Enable the default-deny NetworkPolicy `default-deny`** in the order indicated above, verifying each namespace before the next. `netpol-longhorn-system` affects the `arc-cache` volume of the runners (NFS): test with a CI workflow.
2. **K8sGPT**: accept the risk, scope its role, or leave it disabled.
3. **Calico mitigation**: verify with `--dry-run=server` and, if it responds `created`, remove the binding.
4. **Expose internal interfaces with `oauth2-proxy`** (Alertmanager, vmui, Longhorn, VictoriaLogs): requires a confidential Dex client, its Secrets, and a DNS name.
5. **Protect the `main` branch** of the `gitops` repo (required review).
6. **K8sGPT in the `-skip` of the reusable workflow `core-pipelines`** (private repo, manual change) while it remains staged.

See also [Local AI Assistant](../operacion/ia-ollama.md), [Secrets Management](../secrets/index.md) and
[Rotate Credentials](../operacion/rotar-credenciales.md).
