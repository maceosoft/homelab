# OpenTofu para Incus

Ejemplos de infraestructura como código para el clúster de Incus del HomeLab, uno por carpeta. Cada carpeta es
independiente: su provider ([`lxc/incus`](https://search.opentofu.org/provider/lxc/incus/latest)), su
`.terraform.lock.hcl` y su README con qué crea y cómo probarlo.

| Carpeta | Qué crea |
|---|---|
| [`incus-cluster-groups/`](incus-cluster-groups/) | Los grupos del clúster `x86-nodes` y `arm64-nodes` (ya existen: se importan) |
| [`incus-instancias/`](incus-instancias/) | Una VM Debian 13 con cloud-init que instala nginx, un contenedor nginx que la publica en `/vm/` y un balanceador de OVN hacia el contenedor: se valida desde el navegador |

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

**En macOS exporta `GODEBUG=netdns=go`** antes de usar `incus` u OpenTofu contra el clúster:

```bash
export GODEBUG=netdns=go
```

Sin eso, `incus exec` (y el `exec` de los ejemplos) falla con
`Unable to connect to: incus.homelab.local:8443 (context cancelled)`. No es el SSO: es el DNS (Domain Name System)
de macOS con los nombres `.local`. El dominio `.local` está reservado para mDNS (multicast DNS, la resolución de
nombres en la red local sin servidor), y cuando varios programas o hilos preguntan a la vez por el mismo nombre
`.local`, macOS contesta al primero y hace esperar 5 s a los demás. `incus exec` abre 3 o 4 websockets a la vez
(control, stdin, stdout, stderr), cada uno resuelve el nombre por su cuenta y el cliente corta cada websocket a
los 5 s: el primero conecta y el resto vence. Con `GODEBUG=netdns=go` los programas en Go (el cliente `incus`,
`tofu` y el provider) usan su propio resolvedor, que pregunta directo al DNS del HomeLab (`192.168.20.5`) sin
esa espera. Los comandos REST normales (`incus list`, `incus file pull`) no fallan porque no tienen ese límite de
5 s, pero en paralelo también tardan 5 s de más cada uno.

Antes se usaba `-parallelism=1` para esquivarlo: baja las consultas simultáneas, pero no lo arregla (un
`incus exec` solo, sin OpenTofu, ya falla). Diagnóstico del 18 nov 2026 en
[Si falla](#si-falla).

### Certificado (pipelines)

Para algo que corre sin una persona (un pipeline): un certificado de cliente en el trust de Incus, como el de
CAPN ([CAPN — Credencial de Incus](https://homelab.maceo.cl/capn/#credencial-de-incus)). En la carpeta de
`incus_config_dir` van `client.crt`, `client.key` y `servercerts/homelab.crt`, y:

```bash
export TF_VAR_incus_authentication_type=tls
```

El problema del DNS de `.local` es igual con certificado: también necesita `GODEBUG=netdns=go` en macOS.

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
| `Unable to connect to: incus.homelab.local:8443 (context cancelled)` | Falta `export GODEBUG=netdns=go` (macOS, ver [SSO](#sso-personas)) |
| `Instance "…" already exists` | Un `apply` anterior falló a mitad y dejó la instancia fuera del state: bórrala (`incus delete -f homelab:<nombre>`) o impórtala (`tofu import`) |
| `not authorized` / `403` | Tu cuenta no está en el team `devops`, o el token venció: `incus remote remove homelab` y vuelve a agregarlo |
| `x509: certificate signed by unknown authority` hacia Incus | El remoto se agregó sin `--accept-certificate`: el certificado del servidor queda en `servercerts/homelab.crt` |

Cómo se comprobó la causa del `context cancelled` (18 nov 2026): `incus exec homelab:<instancia> -- true` fallaba
siempre a los ~5,3 s, también sin OpenTofu; con `--debug` se ve conectar un websocket y vencer los otros. Cinco
búsquedas simultáneas de `incus.homelab.local` desde Go (o desde Python con `AI_CANONNAME`) tardan 0,02 s la primera
y 5 s el resto; con `github.com` no pasa, y `dig` en paralelo contra `192.168.20.5` responde todo en ~10 ms (el DNS
del HomeLab está bien). Con `GODEBUG=netdns=go` el mismo `exec` tarda 0,5 s, y cuatro `incus query` en paralelo
bajan de 5–10 s a 0,2 s. La solución de fondo sería sacar el HomeLab de `.local` (por ejemplo a `home.arpa`, el
dominio reservado para redes de casa).

La CI (`docs-lint.yml`, job `opentofu`) corre `tofu fmt -check` y `tofu validate` en cada carpeta, sin conectarse a
Incus. Dependabot propone las versiones nuevas del provider en todas las carpetas.
