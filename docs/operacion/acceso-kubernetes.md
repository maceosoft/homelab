# Entrar a Kubernetes con GitHub

Cómo usar `kubectl` contra el clúster K3s con tu cuenta de GitHub, en vez del certificado de administrador. Sirve si
perteneces al team `devops` de la org `maceosoft`, que tiene acceso total (`cluster-admin`). El kubeconfig de
administrador, el que usan los playbooks, se obtiene en
[Fase 4 — 4.1 Acceso kubectl](../implementacion/fase-4-gitops.md#41-acceso-kubectl); el de esta página no lleva
ninguna llave: solo la dirección del API, su CA y el login con GitHub. Si eres quien **administra** el clúster y el API
todavía no acepta estos logins, ve a [Activar OIDC y el cifrado de Secrets en un server ya instalado](#activar-oidc-y-el-cifrado-de-secrets-en-un-server-ya-instalado).

!!! info "Cómo es por dentro, en una línea"
    `kubectl` llama al plugin kubelogin, que abre el navegador para hacer login con GitHub a través de Dex (OIDC,
    OpenID Connect) y le entrega al API de K3s un token firmado por Dex. El API te reconoce como `oidc:<tu email>`, en
    el grupo `oidc:maceosoft:devops`, y te da los permisos de ese grupo.

## Qué necesitas

- Ser miembro del team `devops` de la org `maceosoft` en GitHub.
- Una estación que resuelva `*.homelab.local` (DNS `192.168.20.5`; ver
  [Resolver los nombres del HomeLab desde tu equipo](../networking/index.md#resolver-los-nombres-del-homelab-desde-tu-equipo))
  y que confíe en la CA (autoridad certificadora) del HomeLab, igual que para
  [entrar por SSH](acceso-ssh.md#preparar-tu-estacion-una-vez).
- El plugin **kubelogin** de int128 (`kubectl oidc-login`).

## Preparar tu estación (una vez)

1. **Instalar kubelogin.** Con asdf:

    ```bash
    asdf plugin add kubectl-oidc_login
    asdf install kubectl-oidc_login latest
    asdf set -u kubectl-oidc_login latest   # en asdf < 0.16: asdf global kubectl-oidc_login latest
    kubectl oidc-login --version            # tiene que decir v1.x
    ```

    Sin asdf: `brew install kubelogin` o `kubectl krew install oidc-login`.

    !!! warning "Hay dos kubelogin distintos"
        El plugin `kubelogin` de asdf instala el kubelogin **de Azure** (versiones `0.x`), que solo sirve para AKS
        (Azure Kubernetes Service) y no trae `kubectl oidc-login`. Si `kubectl` responde
        `unknown command "oidc-login"`, es que tienes ese. El correcto es el de int128 (versiones `1.x`).

2. **Armar tu kubeconfig** en `~/.kube/homelab-github.yaml`. K3s entrega su CA sin login en `/cacerts`; el `-k` es
   solo para esa descarga, que todavía no tiene con qué validar:

    ```bash
    curl -sk https://k3s.homelab.local:6443/cacerts -o /tmp/k3s-ca.crt
    openssl x509 -in /tmp/k3s-ca.crt -noout -subject -fingerprint -sha256
    ```

    El sujeto tiene que ser `CN=k3s-server-ca@…`. Si quieres comprobar la huella, compárala con la del archivo del
    server: `ssh devops@deborah.homelab.local sudo openssl x509 -in /var/lib/rancher/k3s/server/tls/server-ca.crt -noout -fingerprint -sha256`
    (con [SSH por Dex](acceso-ssh.md)). Después:

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

    Si ya tienes el kubeconfig de administrador, también puedes agregarle solo el usuario (`set-credentials`) y
    usarlo con `kubectl --user github`.

    El cliente `kubernetes` de Dex es público (PKCE, sin secreto) y recibe la respuesta en `http://localhost:8000`
    (o, de respaldo, `18000`): esos puertos tienen que estar libres en tu equipo.

## Uso diario

```bash
export KUBECONFIG=~/.kube/homelab-github.yaml
kubectl auth whoami          # oidc:<tu email>; grupos oidc:maceosoft:<team> de GitHub
kubectl get nodes
```

La primera vez se abre el navegador para el login con GitHub; kubelogin guarda el token en `~/.kube/cache/oidc-login`
y lo renueva solo.

El grupo `oidc:maceosoft:devops` tiene el ClusterRole `cluster-admin` por el ClusterRoleBinding `oidc-devops-admin`
([`addons/security/rbac`](https://github.com/maceosoft/gitops/tree/main/addons/security/rbac) en gitops, con sus
riesgos). Los cambios permanentes siguen yendo por git (Argo CD); el certificado de administrador queda para
emergencias, si Dex o GitHub fallan. Los otros teams (por ejemplo `oidc:maceosoft:ia`) llegan en el token, pero no
tienen ningún binding.

## Si falla

| Síntoma | Causa |
|---|---|
| `unknown command "oidc-login" for "kubectl"` | Falta kubelogin o es el de Azure (ver arriba) |
| `x509: certificate signed by unknown authority` hacia `argocd.homelab.local` | Tu estación no confía en la CA del HomeLab |
| `Unauthorized` para todos | El API no tiene el login con Dex activo: ver la sección siguiente |
| `Unauthorized` con tu cuenta | No estás en el team `devops` (el API rechaza a los demás teams), o el token es anterior a tu ingreso: `kubectl oidc-login clean` y vuelve a entrar |

## Activar OIDC y el cifrado de Secrets en un server ya instalado

Las banderas del server están en
[`k3s_install.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/group_vars/incus_cluster/k3s_install.yml)
(bloque `security`): el login con Dex, `--secrets-encryption` (cifrado de los Secrets en reposo) y los SAN (nombres
alternativos del certificado) del API, entre ellos `k3s.homelab.local`. El rol `k3s_server` solo las pone al
**instalar**: un server instalado antes de que existieran no las tiene. Para comprobarlo:

```bash
ssh amaceo@192.168.20.5 'sudo grep -cE "authentication-config|secrets-encryption" /etc/systemd/system/k3s.service; sudo k3s secrets-encrypt status'
```

El login con Dex no va en banderas `--oidc-*` sino en `/etc/rancher/k3s/authentication-config.yaml`
(`AuthenticationConfiguration` de Kubernetes, que el rol escribe desde `security.oidc`): además del issuer, los claims y la
CA, tiene una regla que **solo acepta tokens de los teams de `required_groups`** (hoy `maceosoft:devops`). Dex también
deja entrar a otros teams, como `ia` para Open WebUI; sin la regla, sus tokens autenticarían y recibirían lo que
Kubernetes da a cualquier usuario autenticado (por ejemplo, Calico deja editar políticas de red). El API vuelve a leer
el archivo cuando cambia: cambiar la lista no requiere reiniciar K3s, basta con
`ansible-playbook -i inventory.ini playbook-k3s.yml -l deborah --tags server`.

Si cuenta `0` o dice `Disabled`, aplícalas así. El API se corta unos segundos; los pods siguen corriendo.

1. **Respaldo** del datastore (SQLite) y de las credenciales. `systemctl stop k3s` solo detiene el API, no los pods:

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

2. **Reinstalar el server** con las banderas del repo (misma versión; vuelve a escribir la unidad systemd y
   reinicia K3s):

    ```bash
    cd ansible
    ansible-playbook -i inventory.ini playbook-k3s.yml -l deborah --tags server \
      -e k3s_server_reconfigure=true
    ```

3. **Cifrar los Secrets que ya existían.** Los nuevos se guardan cifrados desde el reinicio; los anteriores siguen
   en claro hasta rotar la llave. `rotate-keys` rota y vuelve a cifrar todo de una vez:

    ```bash
    ssh amaceo@192.168.20.5 'sudo k3s secrets-encrypt rotate-keys; sleep 20; sudo k3s secrets-encrypt status'
    ```

    Tiene que terminar en `Current Rotation Stage: reencrypt_finished`. No uses `reencrypt` suelto: solo vale en
    medio del flujo manual `prepare` → `rotate` → `reencrypt` y, en la etapa `start`, falla con
    `incorrect stage: start found on node deborah` (en el log del server).

4. **Comprobar.** El certificado del API con el nombre estable, y los Secrets cifrados en disco (lee la base en modo
   solo lectura y no muestra ningún valor):

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

    Debe decir `0 en claro`.

5. **Kubeconfig de administrador por nombre** (ya no por IP) y prueba de login con la sección [Uso diario](#uso-diario):

    ```bash
    ansible-playbook -i inventory.ini playbook-k3s.yml -l deborah --tags kubeconfig
    ```

**Volver atrás** (si el API no arranca): restaurar el respaldo, que trae la unidad systemd anterior.

```bash
ssh amaceo@192.168.20.5
sudo systemctl stop k3s
sudo tar xzf /root/k3s-respaldo-<fecha>.tgz -C /
sudo systemctl daemon-reload && sudo systemctl start k3s
```

Ver también [Mover el control plane](mover-control-plane.md), que aplica estas mismas banderas al server nuevo, y
[Actualizar K3s](actualizar-k3s.md).
