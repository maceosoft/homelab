# host_firewall

Firewall de host con nftables para los 3 nodos, en una tabla **propia**
(`inet homelab_filter`): nunca hace `flush ruleset` ni toca las tablas de kube-proxy,
Calico o Incus. Se carga con **auto-reversión**: si el operador no confirma, las reglas
vuelven solas al estado anterior.

## Diseño

- Cadena `input`, hook con prioridad -10 y **política accept**. Un `accept` aquí no salta
  las cadenas de kube-proxy ni de Calico (siguen después, en prioridad 0). Se eligió
  accept con drops explícitos porque una política drop que olvide un puerto de K3s,
  Calico, Longhorn, MetalLB o Incus corta el clúster.
- Orden: conexiones establecidas, loopback, ICMP/ICMPv6, DHCP cliente; puertos
  bloqueados para todos (5555 adbd, 111 rpcbind); **todo el tráfico entre nodos**; y por
  servicio, los orígenes permitidos más un drop del resto.
- Persistencia: unidad propia `homelab-firewall.service` que carga
  `/etc/homelab-firewall/homelab_filter.nft`. No usa `nftables.service`, cuyo
  `/etc/nftables.conf` trae `flush ruleset` y borraría las otras tablas.

## Variables (defaults/main.yml)

| Variable | Para qué |
|---|---|
| `host_firewall_operator_cidrs` | Estaciones del operador (sin valor por defecto). |
| `host_firewall_keep_ssh_client` | Añade sola la IP del cliente SSH actual. |
| `host_firewall_extra_node_ips` | IP de nodos adicionales (p. ej. WiFi de respaldo). |
| `host_firewall_ollama_extra_cidrs` | El Mac u otros clientes directos de Ollama (11434). |
| `host_firewall_ollama_allow_pods` | Admite pods en 11434 (el router puede estar en el mismo nodo). |
| `host_firewall_bgp_peer_cidrs` | Pares BGP externos (p. ej. el router). |
| `host_firewall_trusted_ifaces` | Interfaces cuyo tráfico hacia el host no se filtra. |
| `host_firewall_services`, `host_firewall_blocked_ports` | Puertos con sus orígenes y puertos bloqueados. |
| `host_firewall_strict` | Descarta además todo lo de la LAN no permitido. |
| `host_firewall_revert_seconds` | Plazo de la auto-reversión (300). |
| `host_firewall_verify_kubectl`, `host_firewall_kubeconfig` | Comprobaciones con kubectl. |

Las IP de los nodos salen del inventario; los CIDR de pods y servicios, de `k3s_install`.

## Flujo de aplicación segura

1. Valida la sintaxis con `nft -c` en el nodo y escribe un archivo candidato.
2. Arma un temporizador systemd transitorio (`homelab-firewall-revert`).
3. Carga el candidato de forma atómica y espera unos segundos.
4. Prueba conexiones **nuevas** desde la estación: SSH, 6443 en el server y, con kubectl
   (solo lectura), nodos Ready, calico-node y nodos de Longhorn.
5. Pide escribir `SI`. La confirmación y la reversión compiten por un bloqueo atómico
   (`/run/homelab-firewall.lock`): si la reversión ganó, el playbook falla y las reglas no
   quedan activas.
6. Cancela el temporizador, promueve el candidato y habilita el servicio.

Cualquier fallo, Ctrl+C o sesión rota revierte sola. Emergencia en el nodo:
`sudo systemctl disable --now homelab-firewall` o `sudo /usr/local/sbin/homelab-firewall-revert --force`.

## Orden de aplicación

Siempre con `-l <host>`, de a un nodo y esperando a que quede sano: primero `--check
--diff`, después oliver, invincible y por último deborah (BIND y, antes de la mudanza,
la API de K3s). El orden lo fija el `-l` que escribas, no el del inventario. Ver
`playbook-firewall.yml`.

## Operador y estaciones

La sesión SSH de Ansible siempre queda permitida, pero **kubectl (6443) e Incus (8443)
desde otras estaciones** requieren definirlas en `host_firewall_operator_cidrs`
(group_vars o `-e`). Sin eso, esas estaciones quedan cortadas al aplicar.

## Limitaciones y dependencias

- **IPv6**: los conjuntos son IPv4. Por IPv6 solo pasan ICMPv6 y lo establecido: SSH y DNS
  por IPv6 quedan cortados. El inventario usa IPv4.
- **Incus**: si hay puentes gestionados por Incus y las instancias usan el DHCP/DNS del
  host, añada la interfaz a `host_firewall_trusted_ifaces` (revise `incus network list` y
  `ip -br link`) antes de aplicar o activar el modo estricto.
- Los NodePort pasan por FORWARD, no por INPUT: este firewall no los filtra.
- Los puertos de la tabla (VXLAN 4789, Geneve 6081, etcd 2379/2380, 9091, 10256…) se
  limitan a nodos y pods; ajuste `host_firewall_services` si cambia el CNI.
