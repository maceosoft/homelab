# Modelo de autenticación

Regla general del HomeLab: **nada queda expuesto sin autenticación, o sin una restricción de red explícita
y documentada cuando la autenticación no es posible.**

- **Personas → Dex.** Quien abre algo en el navegador o por SSH (*Secure Shell*, la conexión remota por terminal) entra con su cuenta de GitHub a través de Dex
  (el proveedor de identidad del HomeLab, con el team `devops` de la organización `maceosoft`). Si el servicio
  habla OIDC (OpenID Connect, el protocolo de inicio de sesión sobre OAuth 2.0) de forma nativa, se conecta
  directo; si no, se pone `oauth2-proxy` delante.
- **Máquinas → token o clave propia + restricción de red.** Un programa que llama a otro usa un token
  (un secreto aleatorio, uno por cliente) y, además, solo puede alcanzarlo desde donde corresponde.
- **Lo que no puede autenticar** (protocolos entre nodos, exporters) se limita por red y se lista como
  [excepción](#excepciones-controladas-por-red).

## Quién autentica a quién

| Servicio | Quién lo usa | Cómo se autentica |
|---|---|---|
| ArgoCD, Grafana | Personas | Dex (GitHub, team `devops`). Queda un acceso local de emergencia (`admin` de Grafana); el `admin` local de ArgoCD se desactiva (`admin.enabled: "false"`) y el pipeline usa un token propio (`ci`) con caducidad |
| Open WebUI | Personas | Dex (SSO, *Single Sign-On*: inicio de sesión único, con GitHub): cliente público con PKCE (*Proof Key for Code Exchange*, una protección para clientes sin secreto), sin secreto compartido. Solo SSO: sin formulario local ni registro con contraseña, ni siquiera para el primer administrador; solo entra el team `devops` |
| vCluster, Incus | Personas | Dex (OIDC). Incus además limita el puerto `8443` por firewall |
| SSH a los nodos | Personas | opkssh con la identidad de Dex (grupo `maceosoft:devops`); sin contraseña ni root |
| API de K3s (`6443`) | Personas y máquinas | Certificados de K3s para las máquinas; Dex (banderas `oidc-*`) para personas |
| Router de Ollama (`/api/*`, `/v1/*`) | Máquinas: Open WebUI, K8sGPT, traducción, reportes, alert-triage | Token `Authorization: Bearer`, **uno por cliente** (item `ollama-router`) + NetworkPolicy de ingreso (cuando está activa; ver [Qué está activo](#que-esta-activo-y-que-esta-por-activar)); el router bloquea los verbos de gestión de modelos (`pull`, `create`, `delete`, `copy`, `push`) y `blobs` |
| Router de Ollama (`/_registry`) | Máquinas: cada nodo Ollama | Token Bearer distinto del de los clientes (campo `registry_token` del item `ollama-router`) |
| Nodos Ollama (`11434`) | Solo el router | **Ollama no autentica.** Escucha en la IP del nodo y el firewall admite el puerto `11434` desde los nodos de K3s **y desde los pods** (porque el router puede estar en el mismo nodo). La protección real es el token del router más las NetworkPolicy del namespace `ai`. Ver [excepciones](#excepciones-controladas-por-red) |
| `alert-triage` | Alertmanager | Token Bearer en la cabecera (`http_config.authorization`) + NetworkPolicy |
| Open Terminal (`ai-sandbox`) | Máquina: Open WebUI | Clave de API Bearer montada como archivo (item `open-terminal`, campo `api_key`) + NetworkPolicy que solo admite a Open WebUI; uso restringido a administradores y al grupo `maceosoft:devops` |
| `mcpo` y herramientas MCP | Open WebUI | Clave de API (`--api-key`, item `mcp-api-key`) + NetworkPolicy; herramientas solo para administradores |
| Kong (gateway) | Todos los que entran por `*.homelab.local` | Termina TLS. **Kong Manager** desactivado y **Admin API** solo interna (ClusterIP; su NetworkPolicy está por activar) |
| Alertmanager, vmui/vmalert, Longhorn UI, VictoriaLogs | Personas, si hace falta | Sin login propio: son internos (ClusterIP, sin ruta). Para verlos en el navegador, `oauth2-proxy` + Dex (opcional, por activar) |
| DNS (BIND) | Toda la LAN | No autentica: ACL a la red local, sin recursión abierta |

## Qué está activo y qué está por activar

Algunos controles se despliegan por etapas, para no cortar el clúster de golpe. En el repo
[`gitops`](https://github.com/maceosoft/gitops/blob/main/bootstrap/root-appset.yaml) están **comentados** en
`root-appset.yaml` hasta que se activen uno a uno, tras leer su README:

| Control | Estado |
|---|---|
| NetworkPolicy `default-deny` por namespace (`ai`, `monitoring`, `longhorn-system`, `kong`, `gateway`, `arc-runners`) | **Por activar**, de a una y en este orden: `netpol-ai`, `netpol-monitoring`, `netpol-longhorn-system`, `netpol-kong` y `netpol-gateway`, `netpol-arc-runners` (leer antes el README de [`security/networkpolicies/`](https://github.com/maceosoft/gitops/tree/main/security/networkpolicies)) |
| Etiquetas de Pod Security Admission (`warn`/`audit` con `restricted`) | **Por activar** (aplicación `namespace-labels`) |
| `oauth2-proxy` delante de interfaces internas (p. ej. Alertmanager) | **Por activar** y opcional |
| NetworkPolicy que viajan con su propia aplicación: logs (VictoriaLogs y Vector), `ai/tools`, `alert-triage` y Open Terminal (la de `ai-sandbox` va junto al pod) | **Activas** al desplegar esa aplicación |
| Login de personas a la API de K3s: ClusterRoleBinding `oidc-devops-view` (Application `security-rbac`) | **Activo**, solo lectura (`view`); inofensivo hasta que haya OIDC |
| K8sGPT | **Etapado**: la decisión es del usuario (ver más abajo) |
| Tokens Bearer del router, clave de Open Terminal, Dex en Open WebUI, Kong Manager desactivado, `admin` de ArgoCD desactivado | **Activos** al desplegar |

Mientras una NetworkPolicy no esté activa, el control de red de ese servicio es solo el firewall de los nodos y el
token o la clave del propio servicio. Las tablas de abajo describen el diseño completo; la columna "Control" de las
excepciones vale cuando el control correspondiente está activo.

## Reglas para un servicio nuevo

Antes de publicar algo, responde estas preguntas. Si alguna no tiene respuesta, no se publica.

1. **¿Quién lo usa, una persona o una máquina?**
    - Persona: ¿habla OIDC? Entonces cliente de Dex (público con PKCE si se puede, confidencial con secreto si
      no). ¿No habla OIDC? `oauth2-proxy` delante, con `--allowed-group=maceosoft:devops`.
    - Máquina: un token propio, aleatorio (`openssl rand -hex 32`), guardado en 1Password y aplicado con
      `playbook-platform-secrets.yml`. **Un token por cliente**, para poder revocar uno sin tocar el resto.
2. **¿Desde dónde se llega?** Servicios internos: ClusterIP y NetworkPolicy; ninguna ruta de Kong si no hace falta.
   Servicios en un nodo: que escuchen solo en la IP necesaria y que el firewall del nodo (`nftables`) admita solo a quien
   corresponde.
3. **Nada de NodePort, LoadBalancer ni `hostPort`** salvo que sea imprescindible y esté en la lista de
   excepciones de abajo.
4. **Su NetworkPolicy** del namespace: `default-deny` y permisos explícitos de ingreso y egreso.
5. **Los secretos nunca van a git** (`homelab` es un repo público y `gitops`, aunque es privado, tampoco guarda secretos): 1Password y Secrets del clúster.
6. **Si no puede llevar autenticación**, se agrega a la tabla de excepciones, con el motivo y el control que la sustituye.

!!! info "Por qué `oauth2-proxy` y no un plugin de Kong"
    El plugin de OIDC de Kong es de la edición Enterprise, y la autenticación externa de Gateway API no está
    disponible en la versión de KIC (Kong Ingress Controller) que se usa. `oauth2-proxy` se despliega como
    **backend de la HTTPRoute** de cada servicio, con un cliente de Dex confidencial por servicio y PKCE
    (`S256`).

## Excepciones controladas por red

Lo que **no puede o no debe** llevar autenticación propia queda solo con una restricción de red explícita:

| Servicio | Por qué no lleva login | Control que lo sustituye |
|---|---|---|
| BGP `179` (Calico/bird), FRR `2623`, `7946` (memberlist de MetalLB), `5473` (Typha) | Protocolos entre nodos, sin autenticación de usuario (BGP sin MD5) | `nftables`: solo IP de los nodos y rango de pods; `rpcbind` (`111`) se deshabilita |
| `9100` (node-exporter), `9120`, `9140` y `9141` (métricas de MetalLB y FRR) | Exporters sin autenticación en este despliegue | `nftables` solo hacia el recolector de métricas y los nodos; node-exporter con TLS y basic auth si el chart lo permite |
| `30980` (`healthCheckNodePort` de `kong-gateway-proxy`) | Mecanismo estándar de Kubernetes con `externalTrafficPolicy: Local`: solo dice cuántos endpoints locales hay | `nftables` solo desde los nodos |
| `19443` (webhook de MetalLB, `statuscleaner`) | Webhook de admisión: lo llama el API server | `nftables` solo desde los nodos y el API server |
| DNS `53` (BIND) | El DNS no autentica clientes y sirve a toda la red (LAN, otras subredes, VPN) | Sin transferencias de zona y versión oculta; el puerto lo filtra el router (no se reenvía a internet) |
| Ollama `11434` en cada nodo (y en el Mac) | La API de Ollama no tiene autenticación | Firewall del nodo: `11434` desde los nodos de K3s y desde los pods (`host_firewall_ollama_allow_pods`), y desde los equipos que se agreguen a `host_firewall_ollama_extra_cidrs` (el Mac); en el Mac, `allowed_cidrs` del proxy. **El nodo no autentica**: lo que protege la inferencia es el token Bearer del router y las NetworkPolicy del namespace `ai`. Los clientes no hablan con un nodo, solo con el router |
| Servicios internos sin login (Alertmanager, vmsingle/vmui, vmalert, Longhorn UI, VictoriaLogs, Admin API de Kong, `/metrics` del router, kubelet `10250`) | ClusterIP internos sin autenticación nativa (el kubelet sí autentica) | NetworkPolicy `default-deny` con permisos explícitos; para el navegador, `oauth2-proxy` + Dex |
| Salida de Open Terminal (`ai-sandbox`) | Ejecuta código arbitrario y necesita bajar paquetes | NetworkPolicy de egreso solo a internet por 80/443, sin acceso al clúster ni a la red interna; sin `docker.sock` |
| VXLAN de Calico (UDP `4789`), Geneve de OVN (UDP `6081`), etcd (`2379`, `2380`), métricas de calico-node (`9091`), healthz de kube-proxy (`10256`) | Tráfico interno del clúster, sin autenticación de usuario | `nftables`: solo nodos (y pods donde hace falta); Geneve solo entre nodos |
| SSH `22`, API de K3s `6443`, kubelet `10250`, Incus `8443` | Tienen su propia autenticación (llaves y Dex, certificados, authn/authz del kubelet, OIDC), pero escuchan en la red | `nftables`: LAN y estación del operador (SSH), nodos, pods y operador (el resto) |
| Servicio `kong-gateway-proxy` (LoadBalancer `192.168.23.200`) | Es la puerta de entrada del HomeLab; cada ruta lleva su propia autenticación | Los listeners HTTP solo redirigen a HTTPS |
| Dex (`/api/dex`) y los listeners HTTP de Kong | Dex es el propio mecanismo de login; el HTTP solo redirige a HTTPS | Por diseño |

La fuente de verdad de esta lista es
[`ansible/files/exposure-allowlist.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/files/exposure-allowlist.yml),
que lee el script de auditoría; si esta tabla y el archivo difieren, manda el archivo.

!!! info "Alcance de la auditoría"
    La auditoría cubre los servicios de Kubernetes, las rutas del Gateway y los puertos de los nodos. No cubre el
    WireGuard del router, los servicios dentro de las instancias de Incus (`lb01`, `vm01`, `test`) ni el socket de
    Docker de `deborah` (es un socket Unix, no de red).

## Repetir la auditoría

[`ansible/scripts/audit_exposure.sh`](https://github.com/maceosoft/homelab/blob/main/ansible/scripts/audit_exposure.sh)
es un script de **solo lectura**: lista los Services de tipo NodePort y LoadBalancer, las HTTPRoutes (y si su
backend es un proxy de autenticación o una app con OIDC) y las NetworkPolicies de cada namespace, y lo compara con la
[lista de excepciones](https://github.com/maceosoft/homelab/blob/main/ansible/files/exposure-allowlist.yml).
Sale con código `1` si encuentra algo **fuera de esa lista** (y `2` si falta una herramienta; por ejemplo, si el
Python del sistema no tiene PyYAML, usa uno que lo tenga). La lista incluye entradas temporales, con fecha de revisión,
para los namespaces que aún no tienen NetworkPolicy, así que sirve para
detectar regresiones:

```bash
export KUBECONFIG=~/.kube/homelab-k3s.yaml
ansible/scripts/audit_exposure.sh
# 0 = sin sorpresas
echo $?

# Además, los puertos que escucha cada nodo (por SSH, solo lectura):
AUDIT_NODES="deborah invincible oliver" ansible/scripts/audit_exposure.sh
```

Cuando agregues una excepción legítima, actualiza esta tabla **y** la lista del script en el mismo cambio.
El firewall que cierra los puertos de los nodos está descrito en
[Hardening post-incidente](hardening-post-incidente.md).

## Comprobaciones opcionales

- **Calico y las políticas globales.** Por defecto una cuenta de servicio sin permisos no debería poder crear una
  `GlobalNetworkPolicy`. Se comprueba con:

    ```bash
    kubectl --as=system:serviceaccount:default:default create --dry-run=server -f globalnetworkpolicy.yaml
    ```

    (con cualquier `GlobalNetworkPolicy` de prueba). Si responde `created`, esa cuenta puede cambiar el firewall de
    los pods: quita el binding `calico-tiered-policy-passthrough` que se lo permite.
    Los pasos de mitigación están en [`security/calico-policy-edit/`](https://github.com/maceosoft/gitops/tree/main/security/calico-policy-edit).
- **K8sGPT.** Su chart trae un ClusterRole `*/*/*` (en la práctica, administrador del clúster) y su RBAC dinámico lee
  los Secrets de todo el clúster. Por eso está **etapado** (comentado en `root-appset.yaml`). Para activarlo hay tres
  caminos, en [`security/k8sgpt-rbac/`](https://github.com/maceosoft/gitops/tree/main/security/k8sgpt-rbac): aceptar el
  riesgo y descomentar la línea; usar el rol acotado propuesto (no está probado); o activar también la NetworkPolicy del
  namespace.

## Decisiones pendientes

Lo siguiente no se activa solo: cada punto lo decide y lo ejecuta una persona.

1. **Activar las NetworkPolicy `default-deny`** en el orden indicado arriba, comprobando cada namespace antes del
   siguiente. `netpol-longhorn-system` afecta al volumen `arc-cache` de los runners (NFS): probar con un workflow de CI.
2. **K8sGPT**: aceptar el riesgo, acotar su rol o dejarlo apagado.
3. **Mitigación de Calico**: verificar con `--dry-run=server` y, si responde `created`, retirar el binding.
4. **Publicar interfaces internas con `oauth2-proxy`** (Alertmanager, vmui, Longhorn, VictoriaLogs): requiere un cliente de Dex
   confidencial, sus Secrets y un nombre en el DNS.
5. **Réplica del modelo de 7B en `invincible`**: está comentada en su `host_vars`.
6. **Proteger la rama `main`** del repo `gitops` (revisión obligatoria).
7. **K8sGPT en el `-skip` del workflow reutilizable `core-pipelines`** (repo privado, cambio manual) mientras esté
   etapado.

Ver también [Asistente de IA local](../operacion/ia-ollama.md), [Gestión de secretos](../secrets/index.md) y
[Rotar credenciales](../operacion/rotar-credenciales.md).
