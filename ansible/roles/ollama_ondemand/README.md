# ollama_ondemand

Instala **Ollama** (solo CPU) en un nodo Linux (arm64 o amd64) y lo deja **apagado hasta que llega una petición real**.
Un socket de systemd escucha en la IP del nodo (`:11434`), despierta a Ollama, y tras `ollama_ondemand_idle_time` sin
tráfico todo se detiene y la RAM vuelve al sistema. Un **agente de registro** publica los modelos del nodo en el router
(`ollama-router`, ns `ai`) para que los clientes usen un único punto de entrada.

## Cómo funciona

```text
router -> ollama-proxy.socket (<ip>:11434) -> ollama-proxy.service (systemd-socket-proxyd) -> ollama.service (127.0.0.1:11435)

ollama-node-register.service -> PUT https://ollama.homelab.local/_registry/nodes/<nodo>  (cada 60 s)
```

- `ollama.service` está **deshabilitado y detenido**; no tiene `[Install]`. Su drop-in fija `OLLAMA_HOST=127.0.0.1:11435`,
  `OLLAMA_MODELS`, `OLLAMA_KEEP_ALIVE`, `OLLAMA_NUM_PARALLEL=1`, `OLLAMA_MAX_LOADED_MODELS=1`, `StopWhenUnneeded=yes` y,
  si se define, `MemoryMax`.
- `ollama-proxy.service` tiene `Requires=`/`After=ollama.service` y `--exit-idle-time`: al salir el proxy por inactividad,
  Ollama se detiene solo. El socket usa `FreeBind=yes` para poder enlazar la IP del nodo al arrancar.
- `ExecStartPost` espera a que `127.0.0.1:11435` responda, para que el proxy no falle en el arranque en frío.
- Los modelos se descargan **a través del socket** (`OLLAMA_HOST` = `ollama_ondemand_listen`): `StopWhenUnneeded=yes` haría que systemd detuviera a Ollama si se arrancara a mano. Al terminar se detienen el proxy y Ollama (tag `models`); lo ya presente no se vuelve a bajar.
- `ollama-node-register.service` (rol [`ollama_node`](../ollama_node/README.md); `Restart=always`, usuario `ollama_node_user`) ejecuta `ollama_node.py register --loop`.
  Lee los manifests de `ollama_ondemand_models_dir` sin despertar a Ollama.

## Playbook

[`playbook-ollama.yml`](../../playbook-ollama.yml) — `hosts: llm_nodes` (grupo del inventario).

```bash
ansible-playbook -i inventory.ini playbook-ollama.yml --check --diff
ansible-playbook -i inventory.ini playbook-ollama.yml
ansible-playbook -i inventory.ini playbook-ollama.yml -l oliver
ansible-playbook -i inventory.ini playbook-ollama.yml --tags models
```

Tags: `install` (binario), `units` (unidades systemd y socket), `models` (descarga), `register` (rol `ollama_node`: agente de registro).

## Agregar un nodo Linux

1. Línea del host en `[llm_nodes]` de `inventory.ini` (con `static_ip`).
2. `host_vars/<nodo>.yml` con `ollama_ondemand_models`, `ollama_ondemand_memory_max`, `ollama_node_priority` y `ollama_node_tags`.
3. `ansible-playbook -i inventory.ini playbook-ollama.yml -l <nodo>`.

El nodo aparece solo en el registro (`GET /_registry/nodes`).

## Variables

Ver `defaults/main.yml`.

| Variable | Para qué |
|---|---|
| `ollama_ondemand_version` | Versión única de Ollama |
| `ollama_ondemand_assets` | Por arquitectura (`linux-arm64`, `linux-amd64`): `name` y `checksum` (campo `digest` de GitHub) |
| `ollama_ondemand_listen` | Socket; por defecto `{{ static_ip }}:11434` (nunca `0.0.0.0`) |
| `ollama_ondemand_memory_max` | `MemoryMax` de `ollama.service` por host (vacío = sin tope) |
| `ollama_ondemand_models` | Modelos a descargar en el nodo |
| `ollama_ondemand_keep_alive`, `_idle_time` | Tiempo de modelo cargado y de inactividad del proxy |
| `ollama_node_priority`, `ollama_node_tags` | Preferencia del router y etiquetas del nodo |
| `ollama_node_registry_url` | Base del registro (`https://ollama.homelab.local`) |
| `ollama_node_token_item`, `_token_field` | Item y campo de 1Password (`ollama-router` / `registry_token`) |
| `ollama_node_enabled` | `false` omite el rol `ollama_node` (agente de registro) |

- **Release**: el rol usa los assets base `ollama-linux-<arch>.tar.zst` (se instala `zstd`). Al subir de versión, actualizar
  `ollama_ondemand_version` y los dos checksums con el `digest` que muestra la API de releases de GitHub para cada asset.
- **`systemd-socket-proxyd`**: se busca en `/usr/lib/systemd/` y `/lib/systemd/`; si no está, el rol falla con un mensaje claro.

## Token por nodo (opcional)

`ollama_node_token_field` indica el campo de 1Password del item `ollama-router` (por defecto `registry_token`, compartido). Para un
token propio de cada nodo, define en su `host_vars` `ollama_node_token_field: "registry_token_<nodo>"`: si ese campo no existe se usa
`ollama_node_token_fallback_field` (el compartido). El router debe aceptar ese token (lado gitops); el rol solo lo lee e instala.

## Disponibilidad

`qwen2.5:7b-instruct` está en invincible (prioridad 80, el preferido) y en deborah (prioridad 60, respaldo). Así el control-plane
y DNS no carga con cada respuesta del 7B, y si invincible está caído u ocupado el router usa deborah. Un 7B en Q4 pesa ~4,7 GB más
el contexto: en invincible cabe justo en `ollama_ondemand_memory_max: 5500M` y, con `MAX_LOADED_MODELS=1`, no convive con el de
código (Ollama descarga uno para cargar el otro). Subir el tope si el nodo (que aloja el monitoreo) lo permite.

## Mac u otros equipos

Un equipo fuera de este rol (p. ej. el Mac) debe añadirse a mano a dos listas: su IP/CIDR a `host_firewall_ollama_extra_cidrs`
(rol `host_firewall`, solo si hay que abrirle puertos) y a `ALLOWED_NODE_CIDRS` del router.

## Requisitos en la estación del operador

- App de 1Password desbloqueada y `pip install onepassword-sdk`: [`scripts/read_ollama_registry_token.py`](../../scripts/read_ollama_registry_token.py)
  lee el token y Ansible lo instala en el nodo (`/etc/ollama-node/registry-token`, 0600) sin mostrarlo (`no_log`).
- `KUBECONFIG` exportado: la CA del HomeLab se lee de `cert-manager/homelab-ca` (misma fuente que el rol `opkssh`) y se
  instala en `/etc/ollama-node/homelab-ca.crt` para validar `https://ollama.homelab.local`.
- `ollama-node/ollama_node.py` del repo (se copia a `/usr/local/lib/ollama-node/`).

## Seguridad

- `ollama.service` corre con `NoNewPrivileges`, `ProtectSystem=strict` (solo escribe en `ollama_ondemand_home`), `ProtectHome`,
  `PrivateTmp`, `CapabilityBoundingSet=` vacío, `RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX`, `LockPersonality` y `ProtectKernel*`/`ProtectControlGroups`.
  No se cierra `PrivateDevices` (Ollama lee `/sys/devices` para detectar la CPU) ni se filtran llamadas al sistema.
- `ollama-proxy.service` usa `DynamicUser=yes` y el mismo sandbox. No se restringe a 127.0.0.1 con `IPAddressDeny` porque ese filtro
  también cortaría las conexiones entrantes del router por el socket heredado.
- El agente de registro corre con otro usuario (`ollama-node`) que solo lee los modelos por pertenecer al grupo `ollama`;
  `/var/lib/ollama/.ollama/models` queda `0750` (dueño `ollama`). Los archivos que crea Ollama dentro deben ser legibles por el grupo
  (verificar en el nodo con `sudo -u ollama-node ls <models_dir>/manifests`).

El socket escucha solo en la IP del nodo y **sin autenticación**: el firewall del nodo debe admitir únicamente a los nodos K3s
(el router es el único cliente). El agente corre sin privilegios con `ProtectSystem=strict` y el token en un archivo 0600.

## Verificar en el nodo

```bash
systemctl is-active ollama                     # inactive en reposo
curl -s http://<ip-del-nodo>:11434/api/version # despierta a Ollama
systemctl is-active ollama                     # active; vuelve a inactive tras ~5 min sin tráfico
systemctl status ollama-node-register          # active (running)
```
