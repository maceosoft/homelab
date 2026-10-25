# Entrar por SSH a los servidores

Cómo entrar por SSH (Secure Shell, conexión cifrada por terminal) a `invincible`, `oliver` y `deborah`
con tu cuenta de GitHub, sin pedir ni guardar llaves. Sirve si perteneces al team `devops` de la org
`maceosoft`. Si eres quien lo **instala** o lo administra, ve a
[4.12 — SSH a los hosts con Dex](../implementacion/fase-4-gitops.md#412-ssh-a-los-hosts-con-dex-opcional).

!!! info "Cómo es por dentro, en una línea"
    Haces login con GitHub a través de Dex (OIDC, OpenID Connect) y recibes una llave SSH que caduca a las
    24 horas. Cada servidor comprueba que eres del team `devops` y te deja entrar como el usuario `devops`.

## Qué necesitas

- Ser miembro del team `devops` de la org `maceosoft` en GitHub.
- Una estación que resuelva los nombres `*.homelab.local` (usa el DNS, sistema de nombres de dominio, de la red: `192.168.20.5`) y
  que confíe en la CA (autoridad certificadora) del HomeLab.
- El cliente `opkssh`.

## Preparar tu estación (una vez)

1. **DNS.** Tu estación tiene que usar `192.168.20.5` como DNS. Si no puedes, el respaldo es el archivo
   `/etc/hosts` (ver el [Resumen del HomeLab](../implementacion/resumen-homelab.md)).

2. **Confiar en la CA del HomeLab.** Necesitas `kubectl` con acceso al clúster
   (`export KUBECONFIG=~/.kube/homelab-k3s.yaml`). Exporta el certificado raíz:

    ```bash
    kubectl -n cert-manager get secret homelab-ca -o jsonpath='{.data.ca\.crt}' | base64 -d > homelab-ca.crt
    ```

    Instálalo como certificado de confianza:

    === "macOS"

        ```bash
        sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain homelab-ca.crt
        ```

    === "Linux (Debian/Ubuntu)"

        ```bash
        sudo cp homelab-ca.crt /usr/local/share/ca-certificates/homelab-ca.crt
        sudo update-ca-certificates
        ```

3. **Instalar el cliente.** En macOS, `brew install opkssh`. En otros sistemas, la
   [página de releases de opkssh](https://github.com/openpubkey/opkssh/releases).

4. **Definir el proveedor** en `~/.opk/config.yml`:

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

    La lista va bajo la clave `providers:`. Con `default_provider` basta `opkssh login`.

5. **Comprobar** (en una terminal nueva):

    ```bash
    curl -s -o /dev/null -w "%{http_code} ssl_verify=%{ssl_verify_result}\n" https://argocd.homelab.local/api/dex/.well-known/openid-configuration
    ```

    Debe dar `200 ssl_verify=0`. Con `ssl_verify=20`, Dex funciona pero tu estación no conoce la CA.

## Entrar

La llave dura 24 horas. Cada día:

```bash
opkssh login
ssh -o IdentitiesOnly=yes -i ~/.ssh/id_ecdsa devops@oliver.homelab.local
```

`opkssh login` abre el navegador: entras con GitHub y vuelves a la terminal. `IdentitiesOnly=yes` hace que
SSH ofrezca solo la llave de opkssh; sin él, tu cliente prueba antes las demás llaves y el servidor corta con
`Too many authentication failures`.

Para no escribir el flag cada vez, añade a `~/.ssh/config`:

```text
Host invincible oliver deborah
    HostName %h.homelab.local
    User devops
    IdentityFile ~/.ssh/id_ecdsa
    IdentitiesOnly yes
```

y entra con `ssh oliver`.

!!! warning "Cuenta compartida con `sudo`"
    Todos entran como `devops`, con `sudo` sin contraseña. Quien está en el team es administrador de
    los tres servidores.

## Si algo falla

| Síntoma | Qué significa | Qué hacer |
|---|---|---|
| `opkssh login`: `cannot unmarshal !!seq into config.ClientConfig` | `~/.opk/config.yml` sin la clave `providers:` | Usa el formato del paso 4 |
| `opkssh login`: `invalid provider config string` | Usaste `--provider=homelab`: ese flag solo acepta `<emisor>,<client_id>` | Usa `opkssh login` o `opkssh login homelab` |
| `opkssh login` falla con `redirect_uri` no válido | Falta alguna de las tres direcciones de callback | Revisa `redirect_uris` del paso 4 |
| `x509: certificate signed by unknown authority`, o `ssl_verify=20` | Tu estación no confía en la CA | Paso 2 |
| `Too many authentication failures` | SSH ofrece otras llaves antes | Usa `-o IdentitiesOnly=yes` |
| `Permission denied (publickey)` | El servidor no te reconoce | Comprueba con `opkssh inspect ~/.ssh/id_ecdsa-cert.pub` que el token lista el grupo `maceosoft:devops`. Si es así, avisa a quien administra: el problema está en el servidor ([4.12](../implementacion/fase-4-gitops.md#412-ssh-a-los-hosts-con-dex-opcional)) |
| No resuelve `oliver.homelab.local` | Tu estación no usa el DNS del HomeLab | Paso 1 |

Si Dex o el clúster están caídos, el SSO no funciona. Quien administra tiene una llave de emergencia en
cada servidor.
