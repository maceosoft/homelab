#!/usr/bin/env bash
# Instalador del nodo Ollama para macOS. Sin sudo. Deja los LaunchAgents SIN cargar (estado OFF).
#   ./install.sh --registry-url https://ollama.homelab.local --ca-file ./homelab-ca.crt
# La CA del HomeLab se exporta desde cert-manager (en un equipo con kubectl y el kubeconfig del clúster):
#   kubectl -n cert-manager get secret homelab-ca -o jsonpath='{.data.ca\.crt}' | base64 -d > homelab-ca.crt
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SRC_DIR")"

APP_DIR="${OLLAMA_NODE_HOME:-$HOME/Library/Application Support/ollama-node}"
AGENTS_DIR="${OLLAMA_NODE_AGENTS_DIR:-$HOME/Library/LaunchAgents}"
LOG_DIR="${OLLAMA_NODE_LOG_DIR:-$HOME/Library/Logs/ollama-node}"
BIN_DIR="${OLLAMA_NODE_BIN_DIR:-$HOME/.local/bin}"

NAME="" URL="" REGISTRY_URL="" PRIORITY="" TAGS="" CIDRS="" TOKEN_FILE="" CA_FILE="" MODELS_DIR=""
PYTHON_BIN="" OLLAMA_BIN="" LISTEN_PORT="11434" INTERNAL_PORT="11435" IDLE_TIMEOUT="300"
KEYCHAIN=0 ASSUME_YES=0 UNINSTALL=0

usage() {
  cat <<USAGE
uso: install.sh [opciones]
  --name NOMBRE            nombre del nodo en el registro (por defecto: hostname corto)
  --url URL                URL por la que el router alcanza este Mac (ej. http://192.168.20.50:11434)
  --registry-url URL       URL base del registro (ej. https://ollama.homelab.local)
  --ca-file RUTA           CA del HomeLab en PEM (se copia al directorio del agente)
  --token-file RUTA        archivo con el token del registro (si falta, se pide sin eco)
  --keychain               guarda el token en el Keychain (lo escribes tú en el prompt de 'security')
  --priority N             prioridad (por defecto 10: los nodos siempre encendidos pasan primero)
  --tags a,b               etiquetas (por defecto: mac,gpu,large)
  --allowed-cidrs a,b      redes que pueden hablar con el proxy (ej. 192.168.20.0/24,192.168.23.0/24)
  --models-dir RUTA        OLLAMA_MODELS (por defecto ~/.ollama/models)
  --ollama-bin RUTA        binario ollama (se detecta si no se indica)
  --python RUTA            intérprete para los agentes (por defecto el python3 del PATH)
  --listen-port N          puerto de entrada (11434)    --internal-port N   puerto interno de Ollama (11435)
  --idle-timeout S         segundos sin conexiones antes de apagar Ollama (300)
  --yes                    no preguntar (falla si falta un dato obligatorio)
  --uninstall              descarga los agentes y borra plists, CLI y ollama_node.py; CONSERVA config.json,
                           token, CA y logs (bórralos a mano si quieres)
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --name) NAME="$2"; shift 2 ;;
    --url) URL="$2"; shift 2 ;;
    --registry-url) REGISTRY_URL="$2"; shift 2 ;;
    --ca-file) CA_FILE="$2"; shift 2 ;;
    --token-file) TOKEN_FILE="$2"; shift 2 ;;
    --keychain) KEYCHAIN=1; shift ;;
    --priority) PRIORITY="$2"; shift 2 ;;
    --tags) TAGS="$2"; shift 2 ;;
    --allowed-cidrs) CIDRS="$2"; shift 2 ;;
    --models-dir) MODELS_DIR="$2"; shift 2 ;;
    --ollama-bin) OLLAMA_BIN="$2"; shift 2 ;;
    --python) PYTHON_BIN="$2"; shift 2 ;;
    --listen-port) LISTEN_PORT="$2"; shift 2 ;;
    --internal-port) INTERNAL_PORT="$2"; shift 2 ;;
    --idle-timeout) IDLE_TIMEOUT="$2"; shift 2 ;;
    --yes) ASSUME_YES=1; shift ;;
    --uninstall) UNINSTALL=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "opción desconocida: $1" >&2; usage >&2; exit 2 ;;
  esac
done

LABELS=(local.homelab.ollama-node.socket local.homelab.ollama-node.register)
LAUNCHCTL="${OLLAMA_NODE_LAUNCHCTL:-launchctl}"

if [ "$UNINSTALL" = 1 ]; then
  for l in "${LABELS[@]}"; do
    "$LAUNCHCTL" bootout "gui/$(id -u)/$l" 2>/dev/null || true
    rm -f "$AGENTS_DIR/$l.plist"
  done
  rm -f "$BIN_DIR/ollama-node" "$APP_DIR/ollama_node.py"
  echo "Agentes descargados y plists/CLI eliminados."
  echo "Se conservan config.json, token y CA en $APP_DIR y los logs en $LOG_DIR; bórralos a mano si quieres."
  exit 0
fi

ask() { # ask VARNAME "pregunta" "por defecto"
  local var="$1" prompt="$2" def="${3:-}" cur ans
  cur="${!var}"
  [ -n "$cur" ] && return 0
  if [ "$ASSUME_YES" = 1 ] || [ ! -t 0 ]; then
    [ -n "$def" ] || { echo "falta un dato obligatorio: $prompt (usa las opciones o ejecuta en una terminal)" >&2; exit 1; }
    printf -v "$var" '%s' "$def"; return 0
  fi
  read -r -p "$prompt${def:+ [$def]}: " ans
  printf -v "$var" '%s' "${ans:-$def}"
  [ -n "${!var}" ] || { echo "dato obligatorio" >&2; exit 1; }
}

[ "$(uname -s)" = "Darwin" ] || { echo "este instalador es solo para macOS" >&2; exit 1; }

[ -n "$PYTHON_BIN" ] || PYTHON_BIN="$(command -v python3 || true)"
[ -x "$PYTHON_BIN" ] || { echo "no se encontró python3 (instala las Command Line Tools: xcode-select --install)" >&2; exit 1; }
"$PYTHON_BIN" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' || { echo "se requiere Python >= 3.9" >&2; exit 1; }

if [ -z "$OLLAMA_BIN" ]; then
  OLLAMA_BIN="$(command -v ollama || true)"
  [ -n "$OLLAMA_BIN" ] || for c in /opt/homebrew/bin/ollama /usr/local/bin/ollama; do [ -x "$c" ] && OLLAMA_BIN="$c" && break; done
fi
[ -x "$OLLAMA_BIN" ] || { echo "no se encontró ollama (brew install ollama)" >&2; exit 1; }

DEF_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
ask NAME "Nombre del nodo" "$(hostname -s | tr '[:upper:]' '[:lower:]')"
ask URL "URL con la que el router alcanza este Mac" "${DEF_IP:+http://$DEF_IP:$LISTEN_PORT}"
ask REGISTRY_URL "URL base del registro" "https://ollama.homelab.local"
ask PRIORITY "Prioridad (mayor = se prefiere antes)" "10"
ask TAGS "Etiquetas separadas por coma" "mac,gpu,large"
ask CIDRS "Redes permitidas (CIDR, separadas por coma)" ""
case "$REGISTRY_URL" in https://*) ;; http://localhost*|http://127.0.0.1*) ;; *) echo "aviso: el registro no usa https; el token viajaría en claro" >&2 ;; esac
if [ -n "$CA_FILE" ] && [ ! -f "$CA_FILE" ]; then echo "no existe --ca-file: $CA_FILE" >&2; exit 1; fi
if [ -n "$TOKEN_FILE" ] && [ ! -f "$TOKEN_FILE" ]; then echo "no existe --token-file: $TOKEN_FILE" >&2; exit 1; fi

umask 077
mkdir -p "$APP_DIR" "$AGENTS_DIR" "$BIN_DIR" "$LOG_DIR"
chmod 700 "$APP_DIR"

install -m 755 "$ROOT_DIR/ollama_node.py" "$APP_DIR/ollama_node.py"
install -m 755 "$SRC_DIR/ollama-node" "$BIN_DIR/ollama-node"

CFG_CA=""
if [ -n "$CA_FILE" ]; then
  install -m 644 "$CA_FILE" "$APP_DIR/homelab-ca.crt"
  CFG_CA="$APP_DIR/homelab-ca.crt"
fi

# Token: Keychain o archivo con permisos 600. Nunca va dentro del config ni se imprime.
CFG_TOKEN_FILE="" CFG_KEYCHAIN=""
if [ "$KEYCHAIN" = 1 ]; then
  [ -t 0 ] || { echo "--keychain necesita una terminal (escribirás el token en el prompt de 'security')" >&2; exit 1; }
  echo "Se guardará el token en el Keychain (servicio ollama-node, cuenta $NAME). 'security' te lo pedirá."
  security add-generic-password -U -s ollama-node -a "$NAME" -w
  CFG_KEYCHAIN="ollama-node"
else
  if [ -n "$TOKEN_FILE" ]; then
    install -m 600 "$TOKEN_FILE" "$APP_DIR/token"
  elif [ -t 0 ] && [ "$ASSUME_YES" = 0 ]; then
    read -r -s -p "Token del registro (no se muestra): " TOKEN_IN; echo
    [ -n "$TOKEN_IN" ] || { echo "token vacío" >&2; exit 1; }
    printf '%s\n' "$TOKEN_IN" > "$APP_DIR/token"; unset TOKEN_IN
  elif [ ! -f "$APP_DIR/token" ]; then
    echo "falta el token: usa --token-file, --keychain o una terminal" >&2; exit 1
  fi
  chmod 600 "$APP_DIR/token"
  CFG_TOKEN_FILE="$APP_DIR/token"
fi

# Config JSON (se genera con python para escapar bien los valores).
CFG="$APP_DIR/config.json"
N_NAME="$NAME" N_URL="$URL" N_REG="$REGISTRY_URL" N_TOKF="$CFG_TOKEN_FILE" N_KC="$CFG_KEYCHAIN" N_CA="$CFG_CA" \
N_PRIO="$PRIORITY" N_TAGS="$TAGS" N_CIDRS="$CIDRS" N_MODELS="$MODELS_DIR" N_BIN="$OLLAMA_BIN" \
N_INT="$INTERNAL_PORT" N_LIS="$LISTEN_PORT" N_IDLE="$IDLE_TIMEOUT" N_OUT="$CFG" "$PYTHON_BIN" - <<'PY'
import json, os
e = os.environ
csv = lambda s: [x.strip() for x in s.split(",") if x.strip()]
cfg = {
    "name": e["N_NAME"], "url": e["N_URL"], "registry_url": e["N_REG"],
    "token_file": e["N_TOKF"], "token_keychain": e["N_KC"], "ca_file": e["N_CA"],
    "priority": int(e["N_PRIO"]), "tags": csv(e["N_TAGS"]), "models_dir": e["N_MODELS"],
    "interval": 60, "allowed_cidrs": csv(e["N_CIDRS"]), "idle_timeout": int(e["N_IDLE"]),
    "ollama_bin": e["N_BIN"], "internal_port": int(e["N_INT"]), "listen_port": int(e["N_LIS"]),
    "keep_alive": "5m", "max_loaded_models": 1,
}
with open(e["N_OUT"], "w") as fh:
    json.dump(cfg, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
PY
chmod 600 "$CFG"

# Plists: se instalan sin cargar.
AGENT_PATH="$(dirname "$OLLAMA_BIN"):$(dirname "$PYTHON_BIN"):/usr/bin:/bin:/usr/sbin:/sbin"
for l in "${LABELS[@]}"; do
  tpl="$SRC_DIR/$l.plist.in"
  P_TPL="$tpl" P_OUT="$AGENTS_DIR/$l.plist" P_PY="$PYTHON_BIN" P_SCRIPT="$APP_DIR/ollama_node.py" P_CFG="$CFG" \
  P_PORT="$LISTEN_PORT" P_PATH="$AGENT_PATH" P_LOG="$LOG_DIR" "$PYTHON_BIN" - <<'PY'
import os
from xml.sax.saxutils import escape
e = os.environ
text = open(e["P_TPL"], encoding="utf-8").read()
for key, val in (("@PYTHON@", e["P_PY"]), ("@SCRIPT@", e["P_SCRIPT"]), ("@CONFIG@", e["P_CFG"]),
                 ("@LISTEN_PORT@", e["P_PORT"]), ("@PATH@", e["P_PATH"]), ("@LOG_DIR@", e["P_LOG"])):
    text = text.replace(key, escape(val))
open(e["P_OUT"], "w", encoding="utf-8").write(text)
PY
  chmod 644 "$AGENTS_DIR/$l.plist"
  plutil -lint "$AGENTS_DIR/$l.plist" >/dev/null
done

cat <<DONE

Instalado. Estado: OFF (ningún agente cargado; el Mac no escucha ni se registra).
  config:   $CFG
  agentes:  $AGENTS_DIR/${LABELS[0]}.plist
            $AGENTS_DIR/${LABELS[1]}.plist
  CLI:      $BIN_DIR/ollama-node   (añade $BIN_DIR al PATH si no está)

Siguiente:  ollama-node on      # encender
            ollama-node status
            ollama-node off     # apagar y salir del registro
DONE
case ":$PATH:" in *":$BIN_DIR:"*) ;; *) echo "Aviso: $BIN_DIR no está en tu PATH." ;; esac
