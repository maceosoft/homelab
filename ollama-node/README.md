# ollama-node

Agente de nodo para el Ollama dinámico del HomeLab. Un solo archivo, `ollama_node.py`
(biblioteca estándar, Python >= 3.9), que sirve igual en los nodos Linux y en el Mac.

- **Registro**: manda al router (`PUT /_registry/nodes/<name>`) el nombre, la URL, el hardware
  y los modelos instalados, cada 60 s. El registro caduca a los 180 s sin latido.
- **Modelos sin despertar a Ollama**: lee `OLLAMA_MODELS/manifests` y `manifests-v2`
  (v2 gana si hay repetidos) y los blobs de configuración.
- **Proxy bajo demanda (solo macOS)**: launchd escucha en `:11434`; al llegar una petición
  arranca `ollama serve` en `127.0.0.1:11435`, reenvía y, tras 5 min sin conexiones,
  lo apaga y sale. Mientras hay conexiones mantiene `caffeinate -i`.

## Uso

```text
ollama_node.py [--config RUTA] register [--loop | --once]   # latido / un registro
ollama_node.py deregister                                   # DELETE: sale del registro
ollama_node.py list-models [--models-dir RUTA]              # JSON de modelos
ollama_node.py payload                                      # cuerpo que se enviaría
ollama_node.py status                                       # ¿figura este nodo?
ollama_node.py proxy [--listen HOST:PUERTO]                 # macOS (launchd) o pruebas
```

Config por defecto: `/etc/ollama-node/config.json` (Linux) o
`~/Library/Application Support/ollama-node/config.json` (macOS); también `OLLAMA_NODE_CONFIG`.

| Clave | Significado |
|---|---|
| `name`, `url` | nombre en el registro y URL por la que el router alcanza este nodo |
| `registry_url` | base del registro (`https://ollama.homelab.local`); el agente añade `/_registry/nodes/<name>` |
| `token_file` / `token_keychain` | token del registro (archivo con permisos 600 o Keychain); también `OLLAMA_NODE_TOKEN` |
| `ca_file` | CA del HomeLab para validar TLS (opcional) |
| `priority`, `tags` | prioridad de enrutado y etiquetas |
| `models_dir` | `OLLAMA_MODELS` (si se omite: `~/.ollama/models` en macOS; en Linux `/usr/share/ollama/.ollama/models` o `/var/lib/ollama/.ollama/models`) |
| `interval` | segundos entre latidos (60) |
| `allowed_cidrs` | redes que pueden usar el proxy; lista vacía = nadie |
| `idle_timeout`, `ollama_bin`, `internal_port`, `listen_port` | proxy: inactividad (300 s), binario, puerto interno (11435) y de entrada (11434) |
| `keep_alive`, `max_loaded_models` | `OLLAMA_KEEP_ALIVE` (5m) y `OLLAMA_MAX_LOADED_MODELS` (1) del Ollama que lanza el proxy |

## Mac

```bash
brew install ollama                       # la fórmula, no la app de escritorio
kubectl -n cert-manager get secret homelab-ca -o jsonpath='{.data.ca\.crt}' | base64 -d > homelab-ca.crt
./macos/install.sh --registry-url https://ollama.homelab.local --ca-file ./homelab-ca.crt \
  --url http://192.168.20.X:11434 --allowed-cidrs 192.168.20.0/24
ollama-node on        # carga los dos LaunchAgents
ollama-node status
ollama-node off       # los retira y da de baja el nodo
```

`install.sh` no usa sudo y deja los agentes **sin cargar** (estado OFF). `--keychain`
guarda el token en el Keychain en lugar de un archivo. `--uninstall` deshace la instalación.

## Seguridad

- El token es **solo del registro**; nunca se imprime ni se guarda dentro del config.
- El agente se niega a mandar el token por `http` fuera de loopback.
- La inferencia no lleva token en el nodo: la protegen el router (Bearer) y el firewall;
  en el Mac, además, `allowed_cidrs` descarta antes de arrancar Ollama cualquier origen no permitido.
  Usa solo las IP de los nodos K3s.

## Pruebas

```bash
python3 -m unittest discover -s tests
```

`tests/manual_launchd_socket.py` ejercita `launch_activate_socket` con `launchctl` real y
requiere `OLLAMA_NODE_MANUAL=1` y permiso del usuario.
