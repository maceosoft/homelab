# Access Kubernetes with GitHub

How to use `kubectl` against the K3s cluster with your GitHub account, instead of the admin certificate. Works if
you belong to the `devops` team of the `maceosoft` org, which has full access (`cluster-admin`). The admin kubeconfig,
the one used by the playbooks, is obtained in
[Phase 4 — 4.1 kubectl Access](../implementacion/fase-4-gitops.md#41-kubectl-access); the one on this page carries
no key: only the API address, its CA, and the GitHub login. If you are the one who **administers** the cluster and the API
does not yet accept these logins, go to [Enable OIDC and Secrets Encryption on an Already Installed Server](#enable-oidc-and-secrets-encryption-on-an-already-installed-server).

!!! info "How it works inside, in one line"
    `kubectl` calls the kubelogin plugin, which opens the browser to log in with GitHub via Dex (OIDC,
    OpenID Connect) and hands the K3s API a token signed by Dex. The API recognizes you as `oidc:<tu email>`, in
    the group `oidc:maceosoft:devops`, and grants you that group's permissions.

## What you need

- Be a member of the `devops` team of the `maceosoft` org on GitHub.
- A workstation that resolves `*.homelab.local` (DNS `192.168.20.5`; see
  [Resolve HomeLab Names from Your Machine](../networking/index.md#resolve-homelab-names-from-your-machine))
  and that trusts the HomeLab CA (certificate authority), just like for
  [SSH access](acceso-ssh.md#preparar-tu-estacion-una-vez).
- The **kubelogin** plugin by int128 (`kubectl oidc-login`).

## Prepare your workstation (once)

1. **Install kubelogin.** With asdf:

    ```bash
    asdf plugin add kubectl-oidc_login
    asdf install kubectl-oidc_login latest
    asdf set -u kubectl-oidc_login latest   # en asdf < 0.16: asdf global kubectl-oidc_login latest
    kubectl oidc-login --version            # tiene que decir v1.x
    ```

    Without asdf: `brew install kubelogin` or `kubectl krew install oidc-login`.

    !!! warning "There are two different kubelogin tools"
        The `kubelogin` plugin of asdf installs the **Azure** kubelogin (versions `0.x`), which only works for AKS
        (Azure Kubernetes Service) and does not include `kubectl oidc-login`. If `kubectl` responds
        `unknown command "oidc-login"`, that's the one you have. The correct one is int128's (versions `1.x`).

2. **Build your kubeconfig** at `~/.kube/homelab-github.yaml`. K3s serves its CA without login at `/cacerts`; the `-k`
   is only for that download, which still has nothing to validate with:

    ```bash
    curl -sk https://k3s.homelab.local:6443/cacerts -o /tmp/k3s-ca.crt
    openssl x509 -in /tmp/k3s-ca.crt -noout -subject -fingerprint -sha256
    ```

    The subject must be `CN=k3s-server-ca@…`. If you want to verify the fingerprint, compare it with the server's file: `ssh devops@deborah.homelab.local sudo openssl x509 -in /var/lib/rancher/k3s/server/tls/server-ca.crt -noout -fingerprint -sha256`
    (via [SSH through Dex](acceso-ssh.md)). Then:

    ```bash
    export KUBECONFIG=~/.kube/homelab-github.yaml
    kubectl config set-cluster homelab --server=https://k3s.homelab.local:6443 \
      --certificate-authority=/tmp/k3s-ca.crt --embed-certs=true
    kubectl config set-credentials github \
      --exec-api-version=client.authentication.k8s.io/v1 --exec-command=kubectl \
      --exec-arg=oidc-login --exec-arg=get-token \
      --exec-arg=--oidc-issuer-url=https://argocd.homelab.local/api/dex \
      --exec-arg=--oidc-client-id=kubernetes \
      --exec-arg=--oidc-extra-scope=email --exec-arg=--oidc-extra-scope=groups \
      --exec-interactive-mode=IfAvailable
    kubectl config set-context homelab --cluster=homelab --user=github
    kubectl config use-context homelab
    chmod 600 ~/.kube/homelab-github.yaml
    ```

    If you already have the admin kubeconfig, you can also just add the user (`set-credentials`) to it and
    use it with `kubectl --user github`.

    The Dex `kubernetes` client is public (PKCE, no secret) and receives the response at `http://localhost:8000`
    (or, as a fallback, `18000`): those ports must be free on your machine.

## Daily use

```bash
export KUBECONFIG=~/.kube/homelab-github.yaml
kubectl auth whoami          # oidc:<tu email>; grupos oidc:maceosoft:<team> de GitHub
kubectl get nodes
```

The first time, the browser opens for the GitHub login; kubelogin stores the token in `~/.kube/cache/oidc-login`
and renews it automatically.

The `oidc:maceosoft:devops` group has the ClusterRole `cluster-admin` via the ClusterRoleBinding `oidc-devops-admin`
([`addons/security/rbac`](https://github.com/maceosoft/gitops/tree/main/addons/security/rbac) in gitops, with its
risks). Permanent changes still go through git (Argo CD); the admin certificate remains for
emergencies, if Dex or GitHub fail. Other teams (for example `oidc:maceosoft:ia`) arrive in the token, but
have no binding.

## If it fails

| Symptom | Cause |
|---|---|
| `unknown command "oidc-login" for "kubectl"` | Missing kubelogin or it's the Azure one (see above) |
| `x509: certificate signed by unknown authority` to `argocd.homelab.local` | Your workstation doesn't trust the HomeLab CA |
| `Unauthorized` for everyone | The API doesn't have Dex login enabled: see the next section |
| `Unauthorized` with your account | You are not in the `devops` team (the API rejects other teams), or the token is from before you joined: `kubectl oidc-login clean` and log in again |

## Enable OIDC and Secrets encryption on an already installed server

The server flags are in
[`k3s_install.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/group_vars/incus_cluster/k3s_install.yml)
(block `security`): Dex login, `--secrets-encryption` (encryption of Secrets at rest), and the API certificate SANs (Subject Alternative Names), including `k3s.homelab.local`. The `k3s_server` role only sets them at **install time**: a server installed before they existed doesn't have them. To verify:

```bash
ssh amaceo@192.168.20.5 'sudo grep -cE "authentication-config|secrets-encryption" /etc/systemd/system/k3s.service; sudo k3s secrets-encrypt status'
```

Dex login isn't in `--oidc-*` flags but in `/etc/rancher/k3s/authentication-config.yaml`
(`AuthenticationConfiguration` of Kubernetes, which the role writes from `security.oidc`): besides the issuer, claims, and CA, it has a rule that **only accepts tokens from the `required_groups` teams** (currently `maceosoft:devops`). Dex also lets other teams in, such as `ia` for Open WebUI; without the rule, their tokens would authenticate and receive what Kubernetes gives any authenticated user (for example, Calico allows editing network policies). The API re-reads the file when it changes: changing the list doesn't require restarting K3s, just
`ansible-playbook -i inventory.ini playbook-k3s.yml -l deborah --tags server`.

If it shows `0` or says `Disabled`, apply them like this. The API goes down for a few seconds; pods keep running.

1. **Back up** the datastore (SQLite) and credentials. `systemctl stop k3s` only stops the API, not the pods:

    ```bash
    ssh amaceo@192.168.20.5
    sudo systemctl stop k3s
    sudo tar czf /root/k3s-respaldo-$(date +%F).tgz \
      /var/lib/rancher/k3s/server/db /var/lib/rancher/k3s/server/cred \
      /var/lib/rancher/k3s/server/tls /var/lib/rancher/k3s/server/token \
      /etc/systemd/system/k3s.service /etc/systemd/system/k3s.service.env
    sudo systemctl start k3s
    exit
    ```

2. **Reinstall the server** with the repo flags (same version; rewrites the systemd unit and restarts K3s):

    ```bash
    cd ansible
    ansible-playbook -i inventory.ini playbook-k3s.yml -l deborah --tags server \
      -e k3s_server_reconfigure=true
    ```

3. **Encrypt existing Secrets.** New ones are stored encrypted from the restart; previous ones remain in cleartext until the key is rotated. `rotate-keys` rotates and re-encrypts everything at once:

    ```bash
    ssh amaceo@192.168.20.5 'sudo k3s secrets-encrypt rotate-keys; sleep 20; sudo k3s secrets-encrypt status'
    ```

    It must end with `Current Rotation Stage: reencrypt_finished`. Don't use `reencrypt` alone: it's only valid in the middle of the manual flow `prepare` → `rotate` → `reencrypt` and, at the `start` stage, fails with
    `incorrect stage: start found on node deborah` (in the server log).

4. **Verify.** The API certificate with the stable name, and Secrets encrypted on disk (reads the DB in read-only mode and shows no values):

    ```bash
    openssl s_client -connect k3s.homelab.local:6443 -servername k3s.homelab.local </dev/null 2>/dev/null \
      | openssl x509 -noout -ext subjectAltName
    ssh amaceo@192.168.20.5 'sudo python3 -c "
    import sqlite3
    c = sqlite3.connect(\"file:/var/lib/rancher/k3s/server/db/state.db?mode=ro\", uri=True)
    q = \"SELECT k.value FROM kine k JOIN (SELECT name, MAX(id) id FROM kine WHERE name LIKE \x27/registry/secrets/%\x27 GROUP BY name) u ON k.id = u.id WHERE k.deleted = 0\"
    v = [r[0] or b\"\" for r in c.execute(q)]
    print(len(v), \"Secrets,\", sum(not x.startswith(b\"k8s:enc:\") for x in v), \"en claro\")"'
    ```

    It must say `0 en claro`.

5. **Admin kubeconfig by name** (no longer by IP) and login test with the [Daily use](#daily-use) section:

    ```bash
    ansible-playbook -i inventory.ini playbook-k3s.yml -l deborah --tags kubeconfig
    ```

**Roll back** (if the API won't start): restore the backup, which brings back the previous systemd unit.

```bash
ssh amaceo@192.168.20.5
sudo systemctl stop k3s
sudo tar xzf /root/k3s-respaldo-<fecha>.tgz -C /
sudo systemctl daemon-reload && sudo systemctl start k3s
```

See also [Move the control plane](mover-control-plane.md), which applies these same flags to the new server, and
[Upgrade K3s](actualizar-k3s.md).
