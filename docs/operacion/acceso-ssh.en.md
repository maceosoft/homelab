# SSH into the servers

How to SSH (Secure Shell, an encrypted terminal connection) into `invincible`, `oliver` and `deborah`
with your GitHub account, without asking for or storing keys. This applies if you belong to the `devops` team in the
`maceosoft` org. If you are the one who **installs** or administers it, go to
[4.12 — SSH to the hosts with Dex](../implementacion/fase-4-gitops.md#412-ssh-to-hosts-with-dex-optional).

!!! info "How it works inside, in one line"
    You log in with GitHub through Dex (OIDC, OpenID Connect) and receive an SSH key that expires after
    24 hours. Each server checks that you are in the `devops` team and lets you in as the `devops` user.

## What you need

- Be a member of the `devops` team in the `maceosoft` org on GitHub.
- A workstation that resolves the `*.homelab.local` names (it uses the network's DNS, Domain Name System: `192.168.20.5`) and
  trusts the HomeLab CA (certificate authority).
- The `opkssh` client.

## Set up your workstation (once)

1. **DNS.** Your workstation must use `192.168.20.5` as its DNS. If you can't, the fallback is the `/etc/hosts`
   file (see the [HomeLab Overview](../implementacion/resumen-homelab.md)).

2. **Trust the HomeLab CA.** You need `kubectl` with access to the cluster
   (`export KUBECONFIG=~/.kube/homelab-k3s.yaml`). Export the root certificate:

    ```bash
    kubectl -n cert-manager get secret homelab-ca -o jsonpath='{.data.ca\.crt}' | base64 -d > homelab-ca.crt
    ```

    Install it as a trusted certificate:

    === "macOS"

        ```bash
        sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain homelab-ca.crt
        ```

    === "Linux (Debian/Ubuntu)"

        ```bash
        sudo cp homelab-ca.crt /usr/local/share/ca-certificates/homelab-ca.crt
        sudo update-ca-certificates
        ```

3. **Install the client.** On macOS, `brew install opkssh`. On other systems, use the
   [opkssh releases page](https://github.com/openpubkey/opkssh/releases).

4. **Define the provider** in `~/.opk/config.yml`:

    ```yaml
    ---
    default_provider: homelab

    providers:
      - alias: homelab
        issuer: https://argocd.homelab.local/api/dex
        client_id: opkssh
        scopes: openid email profile groups
        redirect_uris:
          - http://localhost:3000/login-callback
          - http://localhost:10001/login-callback
          - http://localhost:11110/login-callback
    ```

    The list goes under the `providers:` key. With `default_provider` set, `opkssh login` is enough.

5. **Verify** (in a new terminal):

    ```bash
    curl -s -o /dev/null -w "%{http_code} ssl_verify=%{ssl_verify_result}\n" https://argocd.homelab.local/api/dex/.well-known/openid-configuration
    ```

    It should return `200 ssl_verify=0`. With `ssl_verify=20`, Dex works but your workstation doesn't know the CA.

## Log in

The key lasts 24 hours. Every day:

```bash
opkssh login
ssh -o IdentitiesOnly=yes -i ~/.ssh/id_ecdsa devops@oliver.homelab.local
```

`opkssh login` opens the browser: you log in with GitHub and return to the terminal. `IdentitiesOnly=yes` makes
SSH offer only the opkssh key; without it, your client tries your other keys first and the server disconnects with
`Too many authentication failures`.

To avoid typing the flag every time, add this to `~/.ssh/config`:

```text
Host invincible oliver deborah
    HostName %h.homelab.local
    User devops
    IdentityFile ~/.ssh/id_ecdsa
    IdentitiesOnly yes
```

and log in with `ssh oliver`.

!!! warning "Shared account with `sudo`"
    Everyone logs in as `devops`, with passwordless `sudo`. Anyone in the team is an administrator of
    all the servers.

## If something fails

| Symptom | What it means | What to do |
|---|---|---|
| `opkssh login`: `cannot unmarshal !!seq into config.ClientConfig` | `~/.opk/config.yml` without the `providers:` key | Use the format from step 4 |
| `opkssh login`: `invalid provider config string` | You used `--provider=homelab`: that flag only accepts `<emisor>,<client_id>` | Use `opkssh login` or `opkssh login homelab` |
| `opkssh login` fails with invalid `redirect_uri` | One of the three callback addresses is missing | Check `redirect_uris` from step 4 |
| `x509: certificate signed by unknown authority`, or `ssl_verify=20` | Your workstation doesn't trust the CA | Step 2 |
| `Too many authentication failures` | SSH offers other keys first | Use `-o IdentitiesOnly=yes` |
| `Permission denied (publickey)` | The server doesn't recognize you | Check with `opkssh inspect ~/.ssh/id_ecdsa-cert.pub` that the token lists the `maceosoft:devops` group. If it does, tell your administrator: the problem is on the server ([4.12](../implementacion/fase-4-gitops.md#412-ssh-to-hosts-with-dex-optional)) |
| `oliver.homelab.local` doesn't resolve | Your workstation doesn't use the HomeLab DNS | Step 1 |

If Dex or the cluster is down, SSO doesn't work. The administrator has an emergency key on
each server.
