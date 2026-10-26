#!/usr/bin/env bash
# audit_exposure.sh -- auditoría de exposición del HomeLab, SOLO LECTURA.
#
# Lista: Services NodePort/LoadBalancer, HTTPRoutes (y si su backend es un proxy de
# autenticación o una app con OIDC), NetworkPolicies por namespace y, opcionalmente,
# los puertos en escucha por nodo. Lo compara con files/exposure-allowlist.yml y sale
# con código 1 si encuentra algo fuera de la lista (2 si falta una herramienta).
#
# Uso:
#   export KUBECONFIG=~/.kube/homelab-k3s.yaml
#   ansible/scripts/audit_exposure.sh
#
# Variables:
#   AUDIT_ALLOWLIST   ruta de la lista de excepciones (por defecto ../files/exposure-allowlist.yml)
#   AUDIT_NODES       "deborah invincible oliver" -> además revisa puertos en escucha por SSH
#                     (el SSH del operador, solo `ss -H -ltnu`; vacío = omitido)
#   AUDIT_SSH_USER    usuario SSH para AUDIT_NODES (por defecto el usuario actual)
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALLOWLIST="${AUDIT_ALLOWLIST:-${SCRIPT_DIR}/../files/exposure-allowlist.yml}"
NODES="${AUDIT_NODES:-}"
SSH_USER="${AUDIT_SSH_USER:-}"
FINDINGS=0

for tool in kubectl jq; do
  command -v "$tool" >/dev/null 2>&1 || { echo "Falta '$tool' en el PATH." >&2; exit 2; }
done
[ -r "$ALLOWLIST" ] || { echo "No se puede leer la lista de excepciones: $ALLOWLIST" >&2; exit 2; }

# YAML -> JSON con yq o, si no, PyYAML.
yaml_to_json() {
  if command -v yq >/dev/null 2>&1 && yq --version 2>&1 | grep -qi mikefarah; then
    yq -o=json '.' "$1"
  elif PY="$(command -v python3)" && "$PY" -c 'import yaml' >/dev/null 2>&1; then
    "$PY" -c 'import sys, json, yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1]))))' "$1"
  else
    echo "Se necesita yq (mikefarah) o python3 con PyYAML para leer $1." >&2
    return 1
  fi
}
ALLOW="$(yaml_to_json "$ALLOWLIST")" || exit 2

finding() { FINDINGS=$((FINDINGS + 1)); printf '  FALLA  %s\n' "$*"; }
ok()      { printf '  ok     %s\n' "$*"; }
info()    { printf '  info   %s\n' "$*"; }

kjson() { kubectl get "$@" -o json; }

echo "== Services NodePort / LoadBalancer =="
SVC_JSON="$(kjson svc -A)" || { echo "kubectl no pudo leer los Services." >&2; exit 2; }
while IFS=$'\t' read -r ns name type ports lb; do
  [ -z "$ns" ] && continue
  if jq -e --arg ns "$ns" --arg n "$name" --arg t "$type" \
       '.services // [] | any(.namespace == $ns and .name == $n and .type == $t)' <<<"$ALLOW" >/dev/null; then
    ok "$ns/$name ($type $ports ${lb:+IP $lb}) en la lista"
  else
    finding "$ns/$name es $type ($ports ${lb:+IP $lb}) y NO está en la lista de excepciones"
  fi
done < <(jq -r '.items[] | select(.spec.type == "NodePort" or .spec.type == "LoadBalancer")
  | [.metadata.namespace, .metadata.name, .spec.type,
     ([.spec.ports[] | "\(.port)/\(.nodePort // "-")"] | join(",")),
     (.status.loadBalancer.ingress[0].ip // "")] | @tsv' <<<"$SVC_JSON")
EXT="$(jq -r '.items[] | select((.spec.externalIPs // []) | length > 0) | "\(.metadata.namespace)/\(.metadata.name)"' <<<"$SVC_JSON")"
for s in $EXT; do finding "$s usa externalIPs"; done

echo
echo "== HTTPRoutes y autenticación del backend =="
RT_JSON="$(kjson httproute -A 2>/dev/null || echo '{"items":[]}')"
while IFS=$'\t' read -r ns name hosts backends; do
  [ -z "$ns" ] && continue
  auth=""
  # 1) oauth2-proxy autodetectado por el nombre del backend
  if grep -qi 'oauth2-proxy' <<<"$backends"; then auth="oauth2-proxy (autodetectado)"; fi
  # 2) entrada explícita en la lista, con su motivo
  if [ -z "$auth" ]; then
    entry="$(jq -r --arg ns "$ns" --arg n "$name" \
      '.httproutes // [] | map(select(.namespace == $ns and .name == $n)) | first // empty
       | "\(.auth) -- \(.reason)"' <<<"$ALLOW")"
    [ -n "$entry" ] && auth="lista: $entry"
  fi
  if [ -n "$auth" ]; then
    ok "$ns/$name [$hosts] backend: ${backends:-sin backend} -> $auth"
  else
    finding "$ns/$name [$hosts] backend: ${backends:-sin backend} sin proxy de autenticación ni entrada en la lista"
  fi
done < <(jq -r '.items[] | [.metadata.namespace, .metadata.name, (.spec.hostnames // [] | join(",")),
  ([.spec.rules[]?.backendRefs[]? | "\(.name):\(.port // "")"] | unique | join(","))] | @tsv' <<<"$RT_JSON")
ING="$(kubectl get ingress -A --no-headers 2>/dev/null | awk '{print $1"/"$2}')"
for i in $ING; do finding "Ingress $i (el modelo usa Gateway API; revisar su autenticación)"; done

echo
echo "== NetworkPolicies por namespace =="
NP_JSON="$(kjson netpol -A)" || { echo "kubectl no pudo leer las NetworkPolicies." >&2; exit 2; }
for ns in $(kubectl get ns -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}'); do
  total="$(jq --arg ns "$ns" '[.items[] | select(.metadata.namespace == $ns)] | length' <<<"$NP_JSON")"
  deny="$(jq --arg ns "$ns" '[.items[] | select(.metadata.namespace == $ns)
      | select((.spec.podSelector // {}) == {} and ((.spec.policyTypes // []) | index("Ingress"))
               and ((.spec.ingress // []) | length) == 0)] | length' <<<"$NP_JSON")"
  if [ "$total" -eq 0 ]; then
    if jq -e --arg ns "$ns" '.namespaces_without_networkpolicy // [] | any(.name == $ns)' <<<"$ALLOW" >/dev/null; then
      ok "$ns: sin NetworkPolicy (aceptado en la lista)"
    else
      finding "$ns: sin NetworkPolicy y no está en la lista"
    fi
  elif [ "$deny" -eq 0 ]; then
    info "$ns: $total política(s), sin default-deny de ingreso (revisar cobertura)"
  else
    ok "$ns: $total política(s), con default-deny de ingreso"
  fi
done

echo
echo "== Pods con hostNetwork o hostPort (informativo) =="
kjson pods -A | jq -r '.items[] | select(.spec.hostNetwork == true or
  ([.spec.containers[].ports[]? | select(.hostPort)] | length > 0)) | .metadata.namespace' \
  | sort | uniq -c | while read -r n ns; do info "$ns: $n pod(s); sus puertos se limitan con el firewall del nodo"; done

if [ -n "$NODES" ]; then
  echo
  echo "== Puertos en escucha por nodo (SSH, solo lectura) =="
  for node in $NODES; do
    target="${SSH_USER:+$SSH_USER@}$node"
    out="$(ssh -o BatchMode=yes -o ConnectTimeout=8 "$target" 'ss -H -ltnu' 2>/dev/null)" || {
      finding "$node: no se pudo ejecutar 'ss' por SSH"; continue; }
    while read -r proto _ _ _ local _; do
      port="${local##*:}"; addr="${local%:*}"
      case "$addr" in 127.*|"[::1]"|::1) continue ;; esac
      if jq -e --argjson port "$port" --arg p "$proto" \
           '.node_ports // [] | any(.port == $port and .proto == $p)' <<<"$ALLOW" >/dev/null; then
        ok "$node $proto/$port ($addr)"
      else
        finding "$node escucha $proto/$port en $addr y NO está en la lista"
      fi
    done < <(sort -u <<<"$out")
  done
else
  echo
  info "Puertos por nodo omitidos (defina AUDIT_NODES=\"deborah invincible oliver\" para revisarlos)"
fi

echo
if [ "$FINDINGS" -gt 0 ]; then
  echo "RESULTADO: $FINDINGS hallazgo(s) fuera de la lista de excepciones."
  exit 1
fi
echo "RESULTADO: sin hallazgos fuera de la lista de excepciones."
