# SSH into the Servers

How to SSH (Secure Shell, encrypted terminal connection) into `invincible`, `oliver` and `deborah`
with your GitHub account, without requesting or saving keys. It works if you belong to the team `devops` of the org
`maceosoft`. If you are the one who **installs** or administers it, go to
[4.12 — SSH to the hosts with Dex](../implementacion/fase-4-gitops.md#412-ssh-to-hosts-with-dex-optional).

!!! info "How it works, in one line"
    You log in with GitHub through Dex (OIDC, OpenID Connect) and receive an SSH key that expires in
    24 hours. Each server checks that you are in the team `devops` and lets you in as the user `devops`.

## What you need

- Be a member of the team `devops` of the org `maceosoft` on GitHub.
- A station that resolves the names `*.homelab.local` (use the DNS, domain name system, of the network: `192.168.20.5`) and
  that trusts the HomeLab CA (certificate authority).
- The client `opkssh`.

## Prepare your station (once)

1. **DNS.** Your station needs to use `192.168.20.5` as DNS. If you can't, the backup is the file
   `/etc/hosts` (see the [HomeLab Summary](../implementacion/resumen-homelab.md)).

2. **Trust the HomeLab CA.** You need `kubectl` access to the cluster
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

3. **Install the client.** On macOS, `brew install opkssh`. On other systems, the
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

    The list goes under the key `providers:`. With `default_provider` is enough `opkssh login`.

5. **Check** (in a new terminal):

    ```bash
    curl -s -o /dev/null -w "%{http_code} ssl_verify=%{ssl_verify_result}\n" https://argocd.homelab.local/api/dex/.well-known/openid-configuration
    ```

    It should give `200 ssl_verify=0`. With `ssl_verify=20`, Dex works but your station doesn't know the CA.

## Enter

The key lasts 24 hours. Every day:

```bash
opkssh login
ssh -o IdentitiesOnly=yes -i ~/.ssh/id_ecdsa devops@oliver.homelab.local
```

`opkssh login` opens the browser: you log in with GitHub and return to the terminal. `IdentitiesOnly=yes` makes SSH offer only the opkssh key; without it, your client tries other keys first and the server cuts with
`Too many authentication failures`.

To avoid typing the flag every time, add to `~/.ssh/config`:

```text
Host invincible oliver deborah
    HostName %h.homelab.local
    User devops
    IdentityFile ~/.ssh/id_ecdsa
    IdentitiesOnly yes
```

and enter with `ssh oliver`.

!!! warning "Shared account with `sudo`"
    Everyone logs in as `devops`, with `sudo` without a password. Whoever is in the team is an administrator
    of the three servers.

## If something fails

| Symptom | What it means | What to do |
|---|---|---|
| `opkssh login`: `cannot unmarshal !!seq into config.ClientConfig` | `~/.opk/config.yml` without the key `providers:` | Use the format from step 4 |
| `opkssh login`: `invalid provider config string` | You used `--provider=homelab`: that flag only accepts `<emisor>,<client_id>` | Use `opkssh login` or `opkssh login homelab` |
| `opkssh login` fails with `redirect_uri` not valid | Missing one of the three callback addresses | Check `redirect_uris` from step 4 |
| `x509: certificate signed by unknown authority`, or `ssl_verify=20` | Your station doesn't trust the CA | Step 2 |
| `Too many authentication failures` | SSH offers other keys first | Use `-o IdentitiesOnly=yes` |
| `Permission denied (publickey)` | The server doesn't recognize you | Check with `opkssh inspect ~/.ssh/id_ecdsa-cert.pub` that the token lists the group `maceosoft:devops`. If it does, alert the administrator: the problem is on the server ([4.12](../implementacion/fase-4-gitops.md#412-ssh-to-hosts-with-dex-optional)) |
| Doesn't resolve `oliver.homelab.local` | Your station doesn't use the HomeLab DNS | Step 1 |

If Dex or the cluster are down, SSO doesn't work. The administrator has an emergency key on each server.
