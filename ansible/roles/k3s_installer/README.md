# k3s_installer

Descarga el instalador `install.sh` de K3s del **tag de la versión fijada** y verifica su
SHA-256 antes de ejecutarlo. Reemplaza `curl -sfL https://get.k3s.io | sh -`, que ejecutaba
lo que devolviera el servidor sin verificar nada.

Lo usan los roles [`k3s_server`](../k3s_server/README.md) y [`k3s_agent`](../k3s_agent/README.md)
(`include_role`); no tiene play propio.

## Variables

| Variable | Origen | Descripción |
|---|---|---|
| `k3s_install.core.version` | `group_vars/incus_cluster/k3s_install.yml` | Versión (tag) de K3s |
| `k3s_install.core.installer_sha256` | idem | SHA-256 de `install.sh` en ese tag |

Al cambiar la versión hay que recalcular el checksum (el comando está en el comentario de
`k3s_install.yml`); si no coincide, la descarga falla y no se instala nada.

## Qué hace

1. Exige que exista el checksum.
2. Descarga a `/usr/local/lib/k3s-install/install-<versión>.sh` (modo 0700) con `get_url` + `checksum`.
3. Publica `k3s_installer_path`.

El script a su vez verifica el hash del binario contra `sha256sum-<arch>.txt` de la release.
