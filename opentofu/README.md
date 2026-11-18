# OpenTofu para Incus

Ejemplos de infraestructura como código para el clúster de Incus del HomeLab, uno por carpeta. Cada carpeta es
independiente: su provider ([`lxc/incus`](https://search.opentofu.org/provider/lxc/incus/latest)), su
`.terraform.lock.hcl` y su README con qué crea y cómo probarlo.

| Carpeta | Qué crea |
|---|---|
| [`incus-cluster-groups/`](incus-cluster-groups/) | Los grupos del clúster `x86-nodes` y `arm64-nodes` (ya existen: se importan) |
| [`incus-instancias/`](incus-instancias/) | Un contenedor (nginx, imagen OCI), una VM Debian 13 y un balanceador de OVN que publica el nginx en la LAN |

Para un recurso nuevo de Incus (instancia, balanceador, forward, perfil…), copia la carpeta más parecida y ajústala.

## Requisitos (una vez)

- OpenTofu: `asdf plugin add opentofu`, `asdf install opentofu latest`, `asdf set -u opentofu latest` (o
  `brew install opentofu`).
- El cliente `incus` con el remoto del clúster (`brew install incus`). OpenTofu usa su login.

## Entrar a Incus

Los ejemplos se conectan a `https://incus.homelab.local:8443` con el remoto `homelab` del cliente `incus` de tu
equipo. Hay dos formas:

### SSO (personas)

Tu cuenta de GitHub por Dex, la misma de la interfaz web de Incus (solo el team `devops`). Una vez:

```bash
incus remote add homelab https://incus.homelab.local:8443 --auth-type=oidc --accept-certificate
# Abre la URL que muestra, confirma el código y entra con GitHub
incus list homelab:
```

En macOS el cliente guarda la config en `~/Library/Application Support/incus` (en Linux, `~/.config/incus`):

```bash
export TF_VAR_incus_config_dir="$HOME/Library/Application Support/incus"
```

**Usa siempre `-parallelism=1`** en `plan`, `apply` y `destroy`. Dex renueva el token de un solo uso
(rotación de refresh tokens) y, con operaciones en paralelo, una invalida el token de las otras: falla con
`Unable to connect to: incus.homelab.local:8443 (context cancelled)` y deja instancias creadas fuera del state.
Para no olvidarlo:

```bash
export TF_CLI_ARGS_plan="-parallelism=1" TF_CLI_ARGS_apply="-parallelism=1" TF_CLI_ARGS_destroy="-parallelism=1"
```

### Certificado (pipelines)

Para algo que corre sin una persona (un pipeline): un certificado de cliente en el trust de Incus, como el de
CAPN ([CAPN — Credencial de Incus](https://homelab.maceo.cl/capn/#credencial-de-incus)). En la carpeta de
`incus_config_dir` van `client.crt`, `client.key` y `servercerts/homelab.crt`, y:

```bash
export TF_VAR_incus_authentication_type=tls
```

Con certificado no hace falta `-parallelism=1`.

## Uso

```bash
cd opentofu/<ejemplo>
tofu init
tofu plan
tofu apply
tofu destroy        # cuando sea una prueba
```

El state queda en la carpeta del ejemplo (`terraform.tfstate`, fuera de git por `.gitignore`). Si el equipo lo
pierde, OpenTofu deja de conocer lo que creó: se recupera con `tofu import`.

## Si falla

| Síntoma | Causa |
|---|---|
| `Unable to connect to: incus.homelab.local:8443 (context cancelled)` | SSO sin `-parallelism=1` |
| `Instance "…" already exists` | Un `apply` anterior falló a mitad y dejó la instancia fuera del state: bórrala (`incus delete -f homelab:<nombre>`) o impórtala (`tofu import`) |
| `not authorized` / `403` | Tu cuenta no está en el team `devops`, o el token venció: `incus remote remove homelab` y vuelve a agregarlo |
| `x509: certificate signed by unknown authority` hacia Incus | El remoto se agregó sin `--accept-certificate`: el certificado del servidor queda en `servercerts/homelab.crt` |

La CI (`docs-lint.yml`, job `opentofu`) corre `tofu fmt -check` y `tofu validate` en cada carpeta, sin conectarse a
Incus. Dependabot propone las versiones nuevas del provider en todas las carpetas.
