# Glosario

Las palabras técnicas de esta documentación, en dos tablas: [siglas y
abreviaturas](#siglas-y-abreviaturas) y [conceptos y herramientas](#conceptos-y-herramientas).
En cualquier página, las siglas subrayadas muestran su significado al pasar el
mouse, y la primera vez que aparecen en cada página llevan el significado entre
paréntesis.

## Siglas y abreviaturas

| Sigla | Significado | Qué es |
|---|---|---|
| **ACL** | Access Control List | Lista de control de acceso: quién puede consultar un servicio (en BIND, una lista `lan` podría limitar las consultas a ciertas redes; en este HomeLab el DNS queda abierto a toda la red). |
| **API** | Application Programming Interface | Interfaz por la que un programa expone operaciones a otros (p. ej. la API de Kubernetes en :6443). |
| **ARC** | [Actions Runner Controller](https://github.com/actions/actions-runner-controller) | Controlador que corre runners de GitHub Actions dentro de Kubernetes. |
| **ARM64** | arquitectura ARM de 64 bits | Arquitectura de CPU del Orange Pi (deborah); los otros nodos son x86_64. |
| **ARP** | Address Resolution Protocol | Protocolo que traduce IPs a direcciones MAC en la red local. |
| **BD** | base de datos | Donde un servicio guarda su información; en el HomeLab, dqlite (Incus), SQLite (K3s) y los volúmenes de VictoriaMetrics y VictoriaLogs. |
| **BGP** | Border Gateway Protocol | Protocolo de enrutamiento; MetalLB/Calico pueden anunciar IPs por BGP (aquí se usa L2). |
| **BIND** | [Berkeley Internet Name Domain](https://www.isc.org/bind/) | Servidor DNS que resuelve las zonas internas del HomeLab. |
| **BPF** | [Berkeley Packet Filter](https://ebpf.io/) | Tecnología del kernel Linux (eBPF) que usa Cilium para la red. |
| **C4** | [modelo C4](https://c4model.com/) | Forma de dibujar arquitectura en 4 niveles: contexto, contenedores, componentes y despliegue. |
| **CA** | autoridad certificadora | Entidad que firma los certificados TLS. |
| **CAPI** | [Cluster API](https://cluster-api.sigs.k8s.io/) | Proyecto de Kubernetes para crear y administrar clústeres de forma declarativa. |
| **CAPN** | [Cluster API Provider for Incus](https://capn.linuxcontainers.org/) | Proveedor de Cluster API que crea los nodos de un clúster Kubernetes como instancias de Incus. |
| **CI** | integración continua | Compilar y probar el código automáticamente en cada cambio (GitHub Actions). |
| **CIDR** | Classless Inter-Domain Routing | Notación de rangos de IPs, p. ej. 10.42.0.0/16. |
| **CIFS** | Common Internet File System | Protocolo de carpetas compartidas de Windows (SMB). |
| **CINC** | [CINC Is Not Chef](https://cinc.sh/) | Distribución libre de Chef. |
| **CIS** | [Center for Internet Security](https://www.cisecurity.org/benchmark/kubernetes) | Organización que publica guías de endurecimiento (CIS Benchmarks). |
| **CLI** | interfaz de línea de comandos | Herramienta que se usa desde la terminal (p. ej. incus, kubectl). |
| **CNCF** | [Cloud Native Computing Foundation](https://www.cncf.io/) | Fundación que aloja Kubernetes y proyectos relacionados. |
| **CNI** / CNIs | [Container Network Interface](https://www.cni.dev/) | Plugin que da red a los pods de Kubernetes (Flannel, Calico, Cilium…). |
| **CP** | control plane | Parte de Kubernetes que administra el clúster (API server, scheduler, etcd). |
| **CPU** | unidad central de procesamiento |  |
| **CR** / CRs | [Custom Resource](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) | Objeto de Kubernetes definido por un operador (p. ej. un Plan de SUC). |
| **CRD** / CRDs | [Custom Resource Definition](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) | Definición de un tipo de objeto nuevo en Kubernetes (la instala un operador, p. ej. el SUC). |
| **CSV** | Comma-Separated Values | Archivo de datos en texto donde las columnas se separan con comas. |
| **Dex** | [Dex](https://dexidp.io/docs/) | Proveedor de identidad OIDC del HomeLab: permite entrar con la cuenta de GitHub (team `devops`) a Argo CD, Grafana, Open WebUI y SSH. |
| **DHCP** | Dynamic Host Configuration Protocol | Protocolo con el que el router asigna IPs automáticamente. |
| **DMZ** | zona desmilitarizada | Opción del router que expone un equipo directo a internet. |
| **DNS** | Domain Name System | Sistema que traduce nombres (argocd.homelab.local) a IPs. |
| **DR** | recuperación ante desastres | Disaster recovery: cómo volver a levantar un servicio tras perderlo. |
| **DTB** | Device Tree Blob | Descripción binaria del hardware que el kernel lee al arrancar en placas ARM como el Orange Pi. |
| **eBPF** | [extended Berkeley Packet Filter](https://ebpf.io/) | Programas que corren dentro del kernel de Linux; Cilium los usa para la red y las políticas. |
| **eMMC** | embedded MultiMediaCard | Almacenamiento flash soldado a la placa; es el disco de deborah y no tiene SMART. |
| **EOL** | End Of Life | Fin de vida de un componente (en la eMMC, aviso de que quedan pocos bloques de reserva). |
| **ESO** | [External Secrets Operator](https://external-secrets.io/) | Operador de Kubernetes que sincroniza secretos desde gestores externos. |
| **etcd** | [etcd](https://etcd.io/) | Base de datos distribuida donde Kubernetes guarda su estado; K3s puede integrarla en el servidor (etcd embebido). |
| **FRR** | [Free Range Routing](https://frrouting.org/) | Software de enrutamiento que MetalLB usa para hablar BGP; su puerto de administración es `2623`. |
| **FTP** | File Transfer Protocol | Protocolo para subir archivos al hosting (cPanel); también FTPS/SFTP. |
| **GPU** | unidad de procesamiento gráfico | Tarjeta o chip pensado para cálculos en paralelo; acelera los modelos de IA. La Pi de este HomeLab no la usa: los modelos corren en la CPU. |
| **HA** | alta disponibilidad | Diseño para que un servicio siga funcionando si cae un nodo. |
| **HDD** | Hard Disk Drive | Disco duro mecánico. |
| **HDMI** | High-Definition Multimedia Interface | Salida de video; sirve para ver la consola de un nodo cuando la red no responde. |
| **HTTP** | Hypertext Transfer Protocol |  |
| **HTTPS** | HTTP seguro (sobre TLS) |  |
| **IA** | inteligencia artificial | Programas que responden preguntas, resumen textos o generan ejercicios; aquí sirven de tutor para estudiar la guía (ver [Aprende con IA](aprende.md)). |
| **IdP** | Identity Provider | Proveedor de identidad: el sistema que verifica quién eres (en el HomeLab, GitHub a través de Dex). |
| **Incus** | [Incus](https://linuxcontainers.org/incus/) | Gestor de contenedores y máquinas virtuales (fork comunitario de LXD); aloja las instancias donde corren los nodos del HomeLab. |
| **IP** / IPs | dirección IP | Dirección de un equipo en la red (Internet Protocol). |
| **JEDEC** | Joint Electron Device Engineering Council | Organismo que estandariza las memorias; define los campos de desgaste de la eMMC. |
| **journald** | [journald](https://www.freedesktop.org/software/systemd/man/latest/systemd-journald.service.html) | Servicio de systemd que guarda los registros (logs) de los servicios de cada nodo; Vector los lee desde ahí. |
| **JSON** | JavaScript Object Notation | Formato de texto para datos estructurados. |
| **K3s** | [distribución ligera de Kubernetes](https://k3s.io/) | Kubernetes empaquetado en un solo binario, pensado para edge y HomeLabs. |
| **K8s** | [Kubernetes](https://kubernetes.io/) | Abreviatura de Kubernetes: la K, las 8 letras del medio y la s. |
| **KIC** | [Kong Ingress Controller](https://developer.konghq.com/kubernetes-ingress-controller/) | Controlador de Kong para Kubernetes; aquí implementa Gateway API. |
| **Kubernetes** | [Kubernetes](https://kubernetes.io/) (K8s) | Plataforma que orquesta contenedores: decide en qué nodo corre cada pod, lo reinicia si falla y le da red y almacenamiento. En este HomeLab corre como K3s. |
| **KVM** | [Kernel-based Virtual Machine](https://linux-kvm.org/) | Virtualización por hardware integrada en el kernel de Linux; la usan las VMs de Incus. |
| **L2** | capa 2 del modelo OSI | Capa de enlace del modelo OSI: tráfico dentro de la misma red local (MAC, ARP). |
| **L3** | capa 3 del modelo OSI | Capa de red del modelo OSI: IPs y ruteo. |
| **L7** | capa 7 del modelo OSI | Capa de aplicación del modelo OSI: HTTP y similares. |
| **LAN** | red local | Local Area Network: la red de la casa (192.168.20.0/22). |
| **launchd** | [launchd](https://support.apple.com/guide/terminal/apda7b3d2a58-1d40-4d2f-a5d8-9b3a2fd3f36d/mac) | Gestor de servicios de macOS (equivale a systemd); activa por socket el Ollama del Mac solo cuando llega una petición. |
| **LB** | balanceador de carga | Servicio de Kubernetes tipo LoadBalancer (lo provee MetalLB). |
| **LLM** | Large Language Model | Modelo de lenguaje de gran tamaño: el tipo de IA que entiende y escribe texto (aquí, los modelos de Ollama). |
| **LogsQL** | [LogsQL](https://docs.victoriametrics.com/victorialogs/logsql/) | Lenguaje de consultas de VictoriaLogs, el que se escribe en Grafana → Explore. |
| **LVM** | Logical Volume Manager | Gestor de volúmenes lógicos de Linux. |
| **LXC** | [Linux Containers](https://linuxcontainers.org/lxc/) | Contenedores de sistema completo; Incus los usa como instancias. |
| **LXD** | [LXD](https://canonical.com/lxd) | Gestor de contenedores y VMs del que Incus es un fork comunitario. |
| **MAC** | dirección MAC (Media Access Control) | Identificador único de una tarjeta de red; el router lo usa para reservar siempre la misma IP a un equipo. |
| **MCP** | [Model Context Protocol](https://modelcontextprotocol.io/) | Estándar para darle herramientas a un modelo de IA (aquí, consultas de solo lectura al clúster). |
| **MD5** | Message-Digest 5 | Algoritmo de resumen que BGP usaba para autenticar sesiones entre routers; aquí BGP corre sin él. |
| **NAT** | Network Address Translation | Traducción de direcciones que hace el router entre la red local e internet. |
| **NFS** | Network File System | Protocolo de carpetas compartidas por red en Linux. |
| **nftables** | [nftables](https://wiki.nftables.org/) | Firewall del kernel de Linux que usa el rol `host_firewall` en cada nodo. |
| **NIC** | tarjeta de red | Network Interface Card. |
| **NTP** | [Network Time Protocol](https://www.ntp.org/) | Protocolo que sincroniza el reloj de los equipos; sin él los certificados TLS pueden parecer "aún no válidos". |
| **NVMe** | disco SSD por PCIe | Non-Volatile Memory Express: discos SSD de alta velocidad. |
| **NXDOMAIN** | [Non-Existent Domain](https://www.rfc-editor.org/rfc/rfc8020) | Respuesta de un servidor DNS que dice que el nombre no existe; el router la da para `homelab.local`, por eso los pods usan solo el BIND. |
| **OAuth** | [Open Authorization](https://oauth.net/2/) | Estándar para que una aplicación actúe con permiso del usuario sin conocer su contraseña; OIDC se construye sobre él. |
| **oauth2-proxy** | [oauth2-proxy](https://oauth2-proxy.github.io/oauth2-proxy/) | Proxy que pone el inicio de sesión de Dex delante de una interfaz web que no trae login propio. |
| **OCI** | [Open Container Initiative](https://opencontainers.org/) | Estándar de imágenes y registros; ARC y NGINX Gateway Fabric publican su chart de Helm en un registro OCI. |
| **OIDC** | [OpenID Connect](https://openid.net/developers/how-connect-works/) | Protocolo de inicio de sesión sobre OAuth 2.0; Dex lo usa para el login con GitHub. |
| **Open Terminal** | [Open Terminal](https://docs.openwebui.com/features/open-terminal) | Terminal con ejecución de código que Open WebUI usa como herramienta del asistente; corre aislado en el namespace `ai-sandbox`. |
| **OpenPubkey** | [OpenPubkey](https://github.com/openpubkey/openpubkey) | Proyecto que convierte un login OIDC en una llave SSH de corta vida; lo usa [opkssh](https://github.com/openpubkey/opkssh) para entrar a los hosts con la identidad de Dex. |
| **OS** | sistema operativo | Operating System. |
| **OVN** | [Open Virtual Network](https://www.ovn.org/) | Red virtual definida por software que Incus puede usar. |
| **OVS** | [Open vSwitch](https://www.openvswitch.org/) | Switch virtual que usa OVN para conectar las instancias de Incus. |
| **PAT** | [Personal Access Token](https://docs.github.com/es/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) | Token personal de GitHub que reemplaza la contraseña en la API y en la CLI. |
| **PDB** | [PodDisruptionBudget](https://kubernetes.io/docs/tasks/run-application/configure-pdb/) | Límite de Kubernetes sobre cuántos pods de una aplicación pueden estar caídos a la vez durante un vaciado de nodo. |
| **PKCE** | [Proof Key for Code Exchange](https://oauth.net/2/pkce/) | Extensión de OAuth para clientes públicos (sin secreto), como `incus-ui` y `opkssh` en Dex. |
| **PR** / PRs | pull request | Solicitud de cambios en GitHub. |
| **PSA** | [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) | Control de Kubernetes que aplica los niveles de Pod Security Standards a cada namespace (`warn`, `audit` o `enforce`). |
| **PSS** | [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/) | Niveles de seguridad de Kubernetes para pods (privileged, baseline, restricted). |
| **PVC** / PVCs | [PersistentVolumeClaim](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) | Pedido de almacenamiento persistente de un pod en Kubernetes. |
| **RAG** | Retrieval-Augmented Generation | Dar documentos propios al modelo para que responda con ellos en vez de inventar (aquí, la documentación del HomeLab). |
| **RAM** | memoria RAM | Memoria de trabajo del equipo. |
| **RBAC** | [Role-Based Access Control](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) | Control de acceso por roles: qué puede hacer cada usuario o cuenta de servicio. |
| **RWX** | ReadWriteMany | Modo de acceso de un volumen que varios pods pueden montar a la vez, incluso en nodos distintos. |
| **SAN** | Subject Alternative Name | Nombre o IP extra que acepta un certificado TLS (singular de SANs). |
| **SANs** | Subject Alternative Names | Nombres e IPs extra que acepta un certificado TLS. |
| **SATA** | Serial ATA | Interfaz de los discos y SSD de 2,5 pulgadas (invincible y oliver). |
| **SBC** | Single Board Computer | Computador en una sola placa, como el Orange Pi 5 Plus. |
| **SD** | Secure Digital | Tarjeta de memoria; algunas placas ARM arrancan desde ella. |
| **SDK** | Software Development Kit | Librería para usar un servicio desde código (p. ej. el SDK de 1Password). |
| **SMART** | Self-Monitoring, Analysis and Reporting Technology | Autodiagnóstico que traen los discos y SSD; avisa antes de que fallen. |
| **SO** | sistema operativo |  |
| **SOPS** | [Secrets OPerationS](https://github.com/getsops/sops) | Herramienta para cifrar secretos dentro de archivos YAML/JSON. |
| **SPDK** | [Storage Performance Development Kit](https://spdk.io/) | Motor de almacenamiento de Longhorn v2 (no se usa aquí). |
| **SPI** | Serial Peripheral Interface | Bus para chips pequeños; en el Orange Pi, la memoria flash SPI guarda el cargador de arranque. |
| **SQLite** | [SQLite](https://www.sqlite.org/) | Base de datos en un solo archivo; es el almacén de datos por defecto de K3s con un solo servidor. |
| **SSD** | disco de estado sólido |  |
| **SoC** | system on chip | Chip que reúne CPU, gráficos y otros componentes; el RK3588 de deborah es uno. |
| **SSH** | Secure Shell | Protocolo para conectarse a otro equipo por terminal de forma cifrada. |
| **SSL** | Secure Sockets Layer | Antecesor de TLS; el nombre se sigue usando para hablar de certificados y conexiones cifradas. |
| **SSO** | inicio de sesión único | Single Sign-On: entrar a varios servicios con la misma cuenta (aquí, GitHub vía Dex). |
| **SUC** | [System Upgrade Controller](https://github.com/rancher/system-upgrade-controller) | Controlador de Rancher que actualiza K3s nodo por nodo. |
| **TLS** | Transport Layer Security | Cifrado de las conexiones (lo que pone la S en HTTPS). |
| **TTL** | Time To Live | Tiempo que se guarda un dato en caché antes de volver a pedirlo. |
| **UDP** | User Datagram Protocol | Protocolo de transporte sin conexión; lo usan, por ejemplo, el DNS y VXLAN. |
| **UEFI** | Unified Extensible Firmware Interface | Firmware de arranque de los equipos modernos (reemplaza a la BIOS). |
| **UI** | interfaz de usuario | Interfaz web o gráfica de una herramienta. |
| **URI** / URIs | Uniform Resource Identifier | Identificador de un recurso; una URL es un tipo de URI. |
| **URL** / URLs | dirección web | Uniform Resource Locator. |
| **USB** | Universal Serial Bus |  |
| **UUID** | Universally Unique Identifier | Identificador único de 128 bits; Linux lo usa para nombrar discos y particiones. |
| **Vector** | [Vector](https://vector.dev/) | Recolector de logs que corre en cada nodo y los envía a VictoriaLogs. |
| **VictoriaLogs** | [VictoriaLogs](https://docs.victoriametrics.com/victorialogs/) | Base de datos de logs del HomeLab (retención de 30 días); se consulta desde Grafana. |
| **VIP** | IP virtual | Virtual IP: una IP que no es de un equipo fijo y puede moverse entre nodos (kube-vip, MetalLB). |
| **VLAN** / VLANs | red local virtual | Virtual LAN: separar una red física en varias redes lógicas. |
| **VM** / VMs | máquina virtual | Virtual machine. |
| **VPN** | red privada virtual | Virtual Private Network: acceso cifrado a la red de la casa desde afuera. |
| **VXLAN** | Virtual Extensible LAN | Red de capa 2 encapsulada sobre UDP; con ella Flannel y Calico conectan los pods entre nodos. |
| **YAML** | YAML Ain't Markup Language | Formato de texto de configuración que usan Kubernetes y Ansible. |

## Conceptos y herramientas

Términos que la guía usa sin explicarlos cada vez: piezas de Kubernetes, herramientas del HomeLab y jerga de
operación. Si una palabra te frena al leer, búscala aquí.

| Término | Qué es |
|---|---|
| **[1Password](https://1password.com/)** | Gestor de contraseñas. Aquí es la bóveda donde viven los secretos reales del HomeLab (llaves, tokens, GitHub Apps); los scripts los leen con su SDK. |
| **[age](https://github.com/FiloSottile/age)** | Herramienta sencilla de cifrado con llaves; SOPS la usa para cifrar los archivos de secretos del repo. |
| **[Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)** | Recibe las alertas, las agrupa, evita repetirlas y las envía a su destino; aquí, a canales de Discord. |
| **[Ansible](https://docs.ansible.com/)** | Herramienta que configura servidores por SSH a partir de archivos YAML. Aquí prepara los nodos e instala la red, Incus y K3s (Fases 0 a 3). |
| **Application** / **ApplicationSet** | Recursos de Argo CD. Una Application dice qué carpeta de Git desplegar y en qué clúster; un ApplicationSet genera muchas Applications desde una plantilla (aquí `homelab-root` crea todas las demás). |
| **apt** | Gestor de paquetes de Debian: instala y actualiza el software del sistema. |
| **[Argo CD](https://argo-cd.readthedocs.io/)** | La herramienta de GitOps del HomeLab: vigila el repo `gitops` y aplica sus cambios al clúster K3s. Tiene una web donde ves el estado de cada aplicación. |
| **Bootstrap** | El arranque inicial: los primeros pasos manuales que dejan un sistema listo para gestionarse solo. Aquí Ansible instala lo básico y después Argo CD toma el relevo. |
| **Bridge** (puente) | Interfaz de red virtual que funciona como un switch. El bridge `br0` conecta las VMs y los contenedores a la LAN como si fueran un equipo más. |
| **[Calico](https://docs.tigera.io/calico/)** | El CNI del clúster: conecta los pods entre nodos y hace cumplir las NetworkPolicy. |
| **[cert-manager](https://cert-manager.io/)** | Emite y renueva solo los certificados TLS dentro de Kubernetes. Aquí los firma la CA propia del HomeLab para los dominios `*.homelab.local`. |
| **[Cilium](https://cilium.io/)** | CNI basado en eBPF. En la guía aparece como alternativa a Calico. |
| **Clúster** | Grupo de máquinas que trabajan juntas como si fueran un solo sistema. En este HomeLab hay dos sobre los mismos 3 nodos: el de Incus y el de K3s. |
| **Contenedor** | Proceso aislado que trae todo lo que necesita para funcionar pero comparte el kernel del equipo anfitrión; por eso es más liviano que una VM. Incus corre contenedores de sistema (LXC) y Kubernetes corre contenedores de aplicación dentro de los pods. |
| **Control plane** / **worker** | El control plane es el «cerebro» del clúster: guarda el estado y decide en qué nodo corre cada cosa (aquí está en deborah). Los workers solo ejecutan las aplicaciones; K3s los llama *agents* y al control plane, *server*. |
| **Controlador** / **operador** | Un controlador es un programa del clúster que vigila recursos y actúa hasta que el estado real coincide con el deseado. Un operador es un controlador que administra una aplicación concreta con sus propios CRD (p. ej. el de VictoriaMetrics). En la guía «operador» también es, a veces, la persona que administra el HomeLab. |
| **Cordon** / **drain** | `kubectl cordon` marca un nodo para que no reciba pods nuevos; `kubectl drain` además mueve los que ya tiene a otros nodos. Se hace antes de reiniciar o parchear un nodo, y `uncordon` lo vuelve a habilitar. |
| **[CoreDNS](https://coredns.io/)** | El DNS interno de Kubernetes: resuelve los nombres de los Services y los pods dentro del clúster. |
| **CronJob** | Tarea de Kubernetes que se ejecuta sola en un horario fijo, como un cron de Linux. |
| **DaemonSet** | Recurso de Kubernetes que pone una copia de un pod en cada nodo. Vector, que recoge los logs, corre así. |
| **Dashboard** | Panel de Grafana con varios gráficos sobre un tema, p. ej. «HomeLab / Ollama». |
| **[Debian](https://www.debian.org/)** | La distribución de Linux instalada en los tres nodos. |
| **Deployment** | Recurso de Kubernetes que mantiene corriendo N copias (réplicas) de un pod y las reemplaza si fallan. |
| **[dqlite](https://dqlite.io/)** | Base de datos SQLite distribuida donde Incus guarda el estado del clúster, replicada entre los 3 nodos. |
| **Drift** / **self-heal** | Drift es la diferencia entre lo que dice Git y lo que hay de verdad en el clúster. Con self-heal, Argo CD la corrige solo. |
| **Exporter** | Programa pequeño que publica métricas para que vmagent las recoja: node-exporter da las del sistema de cada nodo y blackbox-exporter prueba URLs y DNS desde afuera. |
| **Firewall** | Filtro que decide qué tráfico de red se permite y cuál se bloquea (en Linux, ufw o nftables). |
| **[Flannel](https://github.com/flannel-io/flannel)** | El CNI que trae K3s por defecto. Este HomeLab lo reemplaza por Calico. |
| **Fork** | Copia de un proyecto que se sigue desarrollando por separado del original; p. ej. Incus es un fork de LXD y OpenTofu, de Terraform. |
| **[Gateway API](https://gateway-api.sigs.k8s.io/)** / **HTTPRoute** | El estándar de Kubernetes para publicar servicios web hacia afuera; reemplaza a Ingress. El Gateway es la puerta de entrada (aquí la implementa Kong) y cada HTTPRoute dice qué dominio o ruta va a qué Service. |
| **[GitHub Actions](https://docs.github.com/actions)** / **workflow** / **runner** | GitHub Actions es la CI de GitHub: ejecuta tareas cuando haces push o abres un PR. Un workflow es el archivo YAML que describe esas tareas y el runner es la máquina que las corre; aquí los runners son pods del clúster, creados por ARC. |
| **[GitHub App](https://docs.github.com/apps)** | Identidad de aplicación en GitHub con permisos acotados, para automatizar sin usar una cuenta personal (la usan ARC, Argo CD y OpenTofu). |
| **[GitOps](https://opengitops.dev/)** | Forma de operar en la que Git es la fuente de verdad: cambias un archivo en el repo y una herramienta (aquí Argo CD) hace que el clúster coincida. También es el nombre del repo `maceosoft/gitops`. |
| **[Grafana](https://grafana.com/docs/grafana/latest/)** | La web donde ves las métricas en dashboards y buscas logs (en «Explore»). |
| **group_vars** / **host_vars** | Carpetas de Ansible con las variables de un grupo de máquinas o de una máquina concreta. |
| **Hardening** | Endurecer la seguridad de un sistema: cerrar puertos, quitar accesos que sobran y aplicar configuraciones seguras. |
| **[healthchecks.io](https://healthchecks.io/)** | Servicio externo que espera un aviso («ping») periódico y alerta si deja de llegar. Vigila que el propio monitoreo siga vivo. |
| **[Helm](https://helm.sh/)** / **chart** / **values** | Helm es el gestor de paquetes de Kubernetes. Un chart es un paquete de manifiestos con plantillas y los values son los parámetros que lo ajustan. Argo CD instala varios componentes del HomeLab como charts. |
| **Idempotente** | Que puedes ejecutarlo varias veces y el resultado es el mismo: si algo ya está hecho, no lo repite ni lo rompe. Los playbooks de Ansible están pensados así. |
| **Imagen** | Plantilla de solo lectura desde la que se crea un contenedor o una VM (p. ej. `bitnami/kubectl`). Se descarga de un *registry*. |
| **[Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)** | La forma clásica de exponer servicios HTTP en Kubernetes. El HomeLab no lo usa (usa Gateway API), pero aparece para comparar. |
| **Instancia** | En Incus, cada contenedor o VM que crea. Los nodos de Kubernetes de CAPN y vCluster son instancias. |
| **Inventario** | Lista de las máquinas que gestiona Ansible, con sus grupos y variables. |
| **[K8sGPT](https://k8sgpt.ai/)** | Herramienta que analiza problemas del clúster y los explica en lenguaje natural con un LLM (aquí, de Ollama). |
| **Kernel** | El núcleo del sistema operativo, el que habla directamente con el hardware. Los contenedores comparten el kernel del equipo anfitrión. |
| **[Kong](https://developer.konghq.com/kubernetes-ingress-controller/)** | La puerta de entrada HTTP/HTTPS del clúster: implementa Gateway API (con KIC), recibe el tráfico y lo reparte entre los servicios. |
| **[kube-vip](https://kube-vip.io/)** | Pone una IP virtual (VIP) delante de la API de Kubernetes para que no dependa de un solo nodo. Aquí es opcional; no confundir con MetalLB. |
| **[kubeconfig](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)** | Archivo con la dirección del clúster y tus credenciales; kubectl lo usa para saber a qué clúster conectarse y como quién (aquí, `~/.kube/homelab-k3s.yaml`). |
| **[kubectl](https://kubernetes.io/docs/reference/kubectl/)** | La CLI para hablar con Kubernetes: ver pods, leer logs, aplicar manifiestos o reiniciar cosas. |
| **kubelet** | Agente de Kubernetes que corre en cada nodo y arranca los pods que el control plane le asigna. |
| **[Kustomize](https://kustomize.io/)** | Herramienta que arma y ajusta manifiestos YAML superponiendo cambios sobre una base, sin plantillas. El pipeline del repo `gitops` la usa para validarlo. |
| **Latido** (heartbeat) | Aviso corto que un equipo manda cada cierto tiempo para decir «sigo aquí». Cada nodo de Ollama se lo manda al router cada 60 segundos; si el router pasa 3 latidos sin oírlo (180 s), lo da por apagado. |
| **[Longhorn](https://longhorn.io/)** | Almacenamiento distribuido para Kubernetes: guarda cada volumen con réplicas en varios nodos para que no se pierdan datos si cae uno (StorageClass `longhorn-mixto`). |
| **Manifiesto** | Archivo YAML que describe un recurso de Kubernetes tal como quieres que exista. Le dices qué quieres, no cómo hacerlo; Argo CD los aplica desde Git. |
| **Merge** / **rama** | Una rama es una línea de cambios separada en Git. Hacer merge es unirla a `main`, normalmente al aprobar un PR. |
| **[MetalLB](https://metallb.io/)** | Da IPs de la LAN (pool `192.168.23.200–.220`) a los Services de tipo LoadBalancer, algo que en la nube hace el proveedor. |
| **Métrica** / **scrape** | Una métrica es un número que se mide una y otra vez en el tiempo (p. ej. el uso de CPU). El scrape es la lectura periódica que hace vmagent de las métricas de cada servicio. |
| **Namespace** | Espacio con nombre dentro del clúster que separa recursos y permisos, como una carpeta (p. ej. `ai`, `kong` o `arc-runners`). Casi todos los comandos de kubectl llevan `-n <namespace>`. |
| **[Netplan](https://netplan.io/)** | Herramienta que configura la red con archivos YAML. Aquí crea el bridge `br0` y la IP fija de cada nodo (Fase 1). |
| **[NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/)** | Regla de Kubernetes que dice qué pods pueden hablar con cuáles, como un firewall dentro del clúster. La hace cumplir el CNI. |
| **Nodo** | Cada máquina (física o VM) que forma parte de un clúster y aporta CPU, memoria y disco. Aquí son deborah, oliver e invincible. |
| **[Ollama](https://ollama.com/)** | Servidor que ejecuta modelos de lenguaje (LLM) en tus propias máquinas, sin mandar datos afuera. Lo usan Open WebUI y K8sGPT. |
| **[Open WebUI](https://openwebui.com/)** | Interfaz web tipo chat para conversar con los modelos de Ollama. |
| **[OpenEBS](https://openebs.io/)** | Almacenamiento para Kubernetes. Aquí se usa LocalPV (StorageClass `openebs-hostpath`): volúmenes en el disco local del nodo, rápidos pero sin réplicas. |
| **[OpenTofu](https://opentofu.org/)** / **Terraform** | Herramientas de infraestructura como código: describes recursos en archivos y ellas los crean. OpenTofu es el fork libre de Terraform; aquí configura la organización de GitHub. |
| **Perfil** / **proyecto** / **storage pool** | Conceptos de Incus. Un perfil es una configuración reutilizable para instancias (disco, red), un proyecto agrupa y aísla instancias y un storage pool es el lugar del disco donde se guardan las instancias y sus snapshots. |
| **Pipeline** | Secuencia automática de pasos (validar, construir, desplegar) que se ejecuta cuando cambias el código. |
| **Playbook** | Archivo YAML de Ansible con la lista ordenada de tareas que se aplican a un grupo de máquinas (p. ej. `playbook-k3s.yml` instala K3s). |
| **Pod** | La unidad mínima que ejecuta Kubernetes: uno o varios contenedores que comparten red y almacenamiento. Si un pod muere, Kubernetes crea otro. |
| **port-forward** | `kubectl port-forward` abre un túnel temporal desde tu computador a un servicio interno del clúster; por eso algunas URLs son `http://127.0.0.1:<puerto>`. |
| **Quórum** | Mayoría mínima de miembros de un clúster que deben estar vivos y de acuerdo para seguir tomando decisiones. Con 3 nodos, 2 tienen que seguir arriba; por eso Incus y K3s usan tres. |
| **Regla de alerta** | Condición sobre las métricas (p. ej. «disco sobre 90 % durante 10 min») que, si se cumple, dispara una alerta. Las evalúa vmalert. |
| **[Renovate](https://docs.renovatebot.com/)** | Bot que revisa si hay versiones nuevas de los componentes y abre un PR para actualizarlos. |
| **Réplica** | Copia idéntica de un pod o de un volumen que se mantiene a la vez que el original, para tolerar fallos. |
| **Retención** | Cuánto tiempo se guardan los datos antes de borrarse (p. ej. 30 días de logs en VictoriaLogs). |
| **Rol** (Ansible) | Paquete reutilizable de tareas, plantillas y variables con un solo propósito, guardado en `ansible/roles/` (p. ej. `netplan_bridge`). Los playbooks combinan varios roles. |
| **Rollout** / **rollback** | Rollout es desplegar o reiniciar una versión de forma gradual (`kubectl rollout restart`); rollback es volver a la versión anterior si algo falló. |
| **[Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)** | Controlador que descifra dentro del clúster los secretos cifrados (`SealedSecret`). Así puedes guardarlos en Git: solo el clúster tiene la llave. |
| **[Secret](https://kubernetes.io/docs/concepts/configuration/secret/)** | Recurso de Kubernetes para datos sensibles (contraseñas, tokens). Ojo: por defecto solo va codificado en base64, no cifrado; por eso aquí se cifra antes de subirlo a Git. |
| **[Service](https://kubernetes.io/docs/concepts/services-networking/service/)** | Dirección estable para llegar a un grupo de pods. `ClusterIP` es solo interna, `NodePort` abre un puerto en cada nodo y `LoadBalancer` pide una IP de la LAN (la da MetalLB). |
| **Snapshot** | Foto del estado de un disco o de una instancia en un momento dado, a la que puedes volver si algo sale mal. No reemplaza un respaldo en otro equipo. |
| **Sonda** | Comprobación automática que visita una URL cada cierto tiempo para saber si responde (la hace blackbox-exporter). |
| **[StorageClass](https://kubernetes.io/docs/concepts/storage/storage-classes/)** | «Tipo» de disco que un PVC puede pedir. Aquí hay `openebs-hostpath` (local, por defecto) y `longhorn-mixto` (con réplicas). |
| **sudo** | Comando para ejecutar algo como administrador (root) en Linux. |
| **Sync** / **Synced** / **OutOfSync** / **Healthy** | Estados de Argo CD. Sincronizar (sync) es aplicar al clúster lo que dice Git; Synced significa que ya coinciden, OutOfSync que hay diferencias pendientes y Healthy que los recursos además funcionan bien. |
| **[systemd](https://systemd.io/)** / **timer** | systemd arranca y vigila los servicios de Linux (como `k3s` o `incus`). Un timer es su forma de programar tareas periódicas, parecida a cron. |
| **Token** | Clave secreta (una cadena larga) que identifica a un programa o persona ante un servicio, en lugar de usuario y contraseña. Se suele enviar en la cabecera HTTP `Authorization: Bearer …`. |
| **[Traefik](https://doc.traefik.io/traefik/)** | Proxy de entrada que K3s instala por defecto. Aquí se desactiva y queda como alternativa a Kong. |
| **[vCluster](https://www.vcluster.com/docs)** | Clúster de Kubernetes «virtual» que corre dentro de un namespace de otro clúster: cada equipo tiene el suyo sin máquinas nuevas (Fase 5). |
| **[VictoriaMetrics](https://docs.victoriametrics.com/)** / **vmagent** / **vmalert** | VictoriaMetrics es la base de datos de métricas del HomeLab, compatible con Prometheus. vmagent recoge las métricas (scrape) y vmalert evalúa las reglas de alerta y se las pasa a Alertmanager. |
| **Volumen** | Espacio de disco que se monta en un pod para guardar datos que deben sobrevivir a un reinicio. Lo pide un PVC y lo entrega una StorageClass. |
| **Webhook** | URL a la que un sistema envía un mensaje automático cuando pasa algo. Aquí las alertas llegan a Discord por webhooks. |
