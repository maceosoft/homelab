<!-- Glosario de siglas: tooltip automático en todas las páginas (abbr).
     Se agrega solo al final de cada página (pymdownx.snippets.auto_append).
     Al agregar una sigla nueva, sumarla también a docs/glosario.md. -->

*[ACL]: Access Control List — Lista de control de acceso: quién puede consultar un servicio (en BIND, una lista `lan` podría limitar las consultas a ciertas redes; en este HomeLab el DNS queda abierto a toda la red).
*[API]: Application Programming Interface — Interfaz por la que un programa expone operaciones a otros (p. ej. la API de Kubernetes en :6443).
*[ARC]: Actions Runner Controller — Controlador que corre runners de GitHub Actions dentro de Kubernetes.
*[ARM64]: arquitectura ARM de 64 bits — Arquitectura de CPU del Orange Pi (deborah); los otros nodos son x86_64.
*[ARP]: Address Resolution Protocol — Protocolo que traduce IPs a direcciones MAC en la red local.
*[BD]: base de datos
*[BGP]: Border Gateway Protocol — Protocolo de enrutamiento; MetalLB/Calico pueden anunciar IPs por BGP (aquí se usa L2).
*[BIND]: Berkeley Internet Name Domain — Servidor DNS que resuelve las zonas internas del HomeLab.
*[BPF]: Berkeley Packet Filter — Tecnología del kernel Linux (eBPF) que usa Cilium para la red.
*[C4]: modelo C4 — Forma de dibujar arquitectura en 4 niveles: contexto, contenedores, componentes y despliegue.
*[CA]: autoridad certificadora — Entidad que firma los certificados TLS.
*[CAPI]: Cluster API — Proyecto de Kubernetes para crear y administrar clústeres de forma declarativa.
*[CAPN]: Cluster API Provider for Incus — Proveedor de Cluster API que crea los nodos de un clúster Kubernetes como instancias de Incus.
*[CI]: integración continua — Compilar y probar el código automáticamente en cada cambio (GitHub Actions).
*[CIDR]: Classless Inter-Domain Routing — Notación de rangos de IPs, p. ej. 10.42.0.0/16.
*[CIFS]: Common Internet File System — Protocolo de carpetas compartidas de Windows (SMB).
*[CINC]: CINC Is Not Chef — Distribución libre de Chef.
*[CIS]: Center for Internet Security — Organización que publica guías de endurecimiento (CIS Benchmarks).
*[CLI]: interfaz de línea de comandos — Herramienta que se usa desde la terminal (p. ej. incus, kubectl).
*[CNCF]: Cloud Native Computing Foundation — Fundación que aloja Kubernetes y proyectos relacionados.
*[CNI]: Container Network Interface — Plugin que da red a los pods de Kubernetes (Flannel, Calico, Cilium…).
*[CNIs]: Container Network Interface — Plugin que da red a los pods de Kubernetes (Flannel, Calico, Cilium…).
*[CP]: control plane — Parte de Kubernetes que administra el clúster (API server, scheduler, etcd).
*[CPU]: unidad central de procesamiento
*[CR]: Custom Resource — Objeto de Kubernetes definido por un operador (p. ej. un Plan de SUC).
*[CRs]: Custom Resource — Objeto de Kubernetes definido por un operador (p. ej. un Plan de SUC).
*[CRD]: Custom Resource Definition — Definición de un tipo de objeto nuevo en Kubernetes (la instala un operador, p. ej. el SUC).
*[CRDs]: Custom Resource Definition — Definición de un tipo de objeto nuevo en Kubernetes (la instala un operador, p. ej. el SUC).
*[CSV]: Comma-Separated Values — Archivo de datos en texto donde las columnas se separan con comas.
*[Dex]: Dex — Proveedor de identidad OIDC del HomeLab: permite entrar con la cuenta de GitHub (team `devops`) a Argo CD, Grafana, Open WebUI y SSH.
*[DHCP]: Dynamic Host Configuration Protocol — Protocolo con el que el router asigna IPs automáticamente.
*[DMZ]: zona desmilitarizada — Opción del router que expone un equipo directo a internet.
*[DNS]: Domain Name System — Sistema que traduce nombres (argocd.homelab.local) a IPs.
*[DR]: recuperación ante desastres — Disaster recovery: cómo volver a levantar un servicio tras perderlo.
*[DTB]: Device Tree Blob — Descripción binaria del hardware que el kernel lee al arrancar en placas ARM como el Orange Pi.
*[eBPF]: extended Berkeley Packet Filter — Programas que corren dentro del kernel de Linux; Cilium los usa para la red y las políticas.
*[eMMC]: embedded MultiMediaCard — Almacenamiento flash soldado a la placa; es el disco de deborah y no tiene SMART.
*[EOL]: End Of Life — Fin de vida de un componente (en la eMMC, aviso de que quedan pocos bloques de reserva).
*[ESO]: External Secrets Operator — Operador de Kubernetes que sincroniza secretos desde gestores externos.
*[etcd]: etcd — Base de datos distribuida donde Kubernetes guarda su estado; K3s puede integrarla en el servidor (etcd embebido).
*[FRR]: Free Range Routing — Software de enrutamiento que MetalLB usa para hablar BGP; su puerto de administración es `2623`.
*[FTP]: File Transfer Protocol — Protocolo para subir archivos al hosting (cPanel); también FTPS/SFTP.
*[GPU]: unidad de procesamiento gráfico — Tarjeta o chip pensado para cálculos en paralelo; acelera los modelos de IA. La Pi de este HomeLab no la usa: los modelos corren en la CPU.
*[HA]: alta disponibilidad — Diseño para que un servicio siga funcionando si cae un nodo.
*[HDD]: Hard Disk Drive — Disco duro mecánico.
*[HDMI]: High-Definition Multimedia Interface — Salida de video; sirve para ver la consola de un nodo cuando la red no responde.
*[HTTP]: Hypertext Transfer Protocol
*[HTTPS]: HTTP seguro (sobre TLS)
*[IA]: inteligencia artificial — Programas que responden preguntas, resumen textos o generan ejercicios; aquí sirven de tutor para estudiar la guía.
*[IdP]: Identity Provider — Proveedor de identidad: el sistema que verifica quién eres (en el HomeLab, GitHub a través de Dex).
*[Incus]: Incus — Gestor de contenedores y máquinas virtuales (fork comunitario de LXD); aloja las instancias donde corren los nodos del HomeLab.
*[IP]: dirección IP — Dirección de un equipo en la red (Internet Protocol).
*[IPs]: dirección IP — Dirección de un equipo en la red (Internet Protocol).
*[JEDEC]: Joint Electron Device Engineering Council — Organismo que estandariza las memorias; define los campos de desgaste de la eMMC.
*[journald]: journald — Servicio de systemd que guarda los registros (logs) de los servicios de cada nodo; Vector los lee desde ahí.
*[JSON]: JavaScript Object Notation — Formato de texto para datos estructurados.
*[K3s]: distribución ligera de Kubernetes — Kubernetes empaquetado en un solo binario, pensado para edge y HomeLabs.
*[K8s]: Kubernetes — Plataforma de orquestación de contenedores.
*[KIC]: Kong Ingress Controller — Controlador de Kong para Kubernetes; aquí implementa Gateway API.
*[KVM]: máquina virtual del kernel — Kernel-based Virtual Machine: virtualización por hardware integrada en el kernel de Linux; la usan las VMs de Incus.
*[L2]: capa 2 del modelo OSI — Capa de enlace del modelo OSI: tráfico dentro de la misma red local (MAC, ARP).
*[L3]: capa 3 del modelo OSI — Capa de red del modelo OSI: IPs y ruteo.
*[L7]: capa 7 del modelo OSI — Capa de aplicación del modelo OSI: HTTP y similares.
*[LAN]: red local — Local Area Network: la red de la casa (192.168.20.0/22).
*[launchd]: launchd — Gestor de servicios de macOS (equivale a systemd); activa por socket el Ollama del Mac solo cuando llega una petición.
*[LB]: balanceador de carga — Servicio de Kubernetes tipo LoadBalancer (lo provee MetalLB).
*[LLM]: Large Language Model — Modelo de lenguaje de gran tamaño: el tipo de IA que entiende y escribe texto (aquí, los modelos de Ollama).
*[LogsQL]: LogsQL — Lenguaje de consultas de VictoriaLogs, el que se escribe en Grafana → Explore.
*[LVM]: Logical Volume Manager — Gestor de volúmenes lógicos de Linux.
*[LXC]: Linux Containers — Contenedores de sistema completo; Incus los usa como instancias.
*[LXD]: LXD — Gestor de contenedores y VMs del que Incus es un fork comunitario.
*[MAC]: dirección MAC — Identificador único de una tarjeta de red; el router lo usa para reservar siempre la misma IP a un equipo.
*[MCP]: Model Context Protocol — Estándar para darle herramientas a un modelo de IA (aquí, consultas de solo lectura al clúster).
*[MD5]: Message-Digest 5 — Algoritmo de resumen que BGP usaba para autenticar sesiones entre routers; aquí BGP corre sin él.
*[NAT]: Network Address Translation — Traducción de direcciones que hace el router entre la red local e internet.
*[NFS]: Network File System — Protocolo de carpetas compartidas por red en Linux.
*[nftables]: nftables — Firewall del kernel de Linux que usa el rol `host_firewall` en cada nodo.
*[NIC]: tarjeta de red — Network Interface Card.
*[NTP]: Network Time Protocol — Protocolo que sincroniza el reloj de los equipos; sin él los certificados TLS pueden parecer "aún no válidos".
*[NVMe]: disco SSD por PCIe — Non-Volatile Memory Express: discos SSD de alta velocidad.
*[NXDOMAIN]: Non-Existent Domain — Respuesta de un DNS que dice que el nombre no existe.
*[OAuth]: Open Authorization — Estándar para que una aplicación actúe con permiso del usuario sin conocer su contraseña; OIDC se construye sobre él.
*[oauth2-proxy]: oauth2-proxy — Proxy que pone el inicio de sesión de Dex delante de una interfaz web que no trae login propio.
*[OCI]: Open Container Initiative — Estándar de imágenes y registros; ARC y NGINX Gateway Fabric publican su chart de Helm en un registro OCI.
*[OIDC]: OpenID Connect — Protocolo de inicio de sesión sobre OAuth 2.0; Dex lo usa para el login con GitHub.
*[Open Terminal]: Open Terminal — Terminal con ejecución de código que Open WebUI usa como herramienta del asistente; corre aislado en el namespace `ai-sandbox`.
*[OpenPubkey]: Proyecto que convierte un login OIDC en una llave SSH de corta vida; lo usa opkssh para entrar a los hosts con la identidad de Dex.
*[OS]: sistema operativo — Operating System.
*[OVN]: Open Virtual Network — Red virtual definida por software que Incus puede usar.
*[OVS]: Open vSwitch — Switch virtual que usa OVN para conectar las instancias de Incus.
*[PAT]: Personal Access Token — Token personal de GitHub que reemplaza la contraseña en la API y en la CLI.
*[PDB]: PodDisruptionBudget — Límite de Kubernetes sobre cuántos pods de una aplicación pueden estar caídos a la vez durante un vaciado de nodo.
*[PKCE]: Proof Key for Code Exchange — Extensión de OAuth para clientes públicos (sin secreto), como incus-ui y opkssh en Dex.
*[PR]: pull request — Solicitud de cambios en GitHub.
*[PRs]: pull request — Solicitud de cambios en GitHub.
*[PSA]: Pod Security Admission — Control de Kubernetes que aplica los niveles de Pod Security Standards a cada namespace (`warn`, `audit` o `enforce`).
*[PSS]: Pod Security Standards — Niveles de seguridad de Kubernetes para pods (privileged, baseline, restricted).
*[PVC]: PersistentVolumeClaim — Pedido de almacenamiento persistente de un pod en Kubernetes.
*[PVCs]: PersistentVolumeClaim — Pedido de almacenamiento persistente de un pod en Kubernetes.
*[RAG]: Retrieval-Augmented Generation — Dar documentos propios al modelo para que responda con ellos en vez de inventar (aquí, la documentación del HomeLab).
*[RAM]: memoria RAM — Memoria de trabajo del equipo.
*[RBAC]: Role-Based Access Control — Control de acceso por roles: qué puede hacer cada usuario o cuenta de servicio.
*[RWX]: ReadWriteMany — Modo de acceso de un volumen que varios pods pueden montar a la vez, incluso en nodos distintos.
*[SAN]: Subject Alternative Name — Nombre o IP extra que acepta un certificado TLS (singular de SANs).
*[SANs]: Subject Alternative Names — Nombres e IPs extra que acepta un certificado TLS.
*[SATA]: Serial ATA — Interfaz de los discos y SSD de 2,5 pulgadas (invincible y oliver).
*[SBC]: Single Board Computer — Computador en una sola placa, como el Orange Pi 5 Plus.
*[SD]: Secure Digital — Tarjeta de memoria; algunas placas ARM arrancan desde ella.
*[SDK]: Software Development Kit — Librería para usar un servicio desde código (p. ej. el SDK de 1Password).
*[SMART]: Self-Monitoring, Analysis and Reporting Technology — Autodiagnóstico que traen los discos y SSD; avisa antes de que fallen.
*[SO]: sistema operativo
*[SOPS]: Secrets OPerationS — Herramienta para cifrar secretos dentro de archivos YAML/JSON.
*[SPDK]: Storage Performance Development Kit — Motor de almacenamiento de Longhorn v2 (no se usa aquí).
*[SPI]: Serial Peripheral Interface — Bus para chips pequeños; en el Orange Pi, la memoria flash SPI guarda el cargador de arranque.
*[SQLite]: SQLite — Base de datos en un solo archivo; es el almacén de datos por defecto de K3s con un solo servidor.
*[SSD]: disco de estado sólido
*[SoC]: system on chip — Chip que reúne CPU, gráficos y otros componentes; el RK3588 de deborah es uno.
*[SSH]: Secure Shell — Protocolo para conectarse a otro equipo por terminal de forma cifrada.
*[SSL]: Secure Sockets Layer — Antecesor de TLS; el nombre se sigue usando para hablar de certificados y conexiones cifradas.
*[SSO]: inicio de sesión único — Single Sign-On: entrar a varios servicios con la misma cuenta (aquí, GitHub vía Dex).
*[SUC]: System Upgrade Controller — Controlador de Rancher que actualiza K3s nodo por nodo.
*[TLS]: Transport Layer Security — Cifrado de las conexiones (lo que pone la S en HTTPS).
*[TTL]: Time To Live — Tiempo que se guarda un dato en caché antes de volver a pedirlo.
*[UDP]: User Datagram Protocol — Protocolo de transporte sin conexión; lo usan, por ejemplo, el DNS y VXLAN.
*[UEFI]: Unified Extensible Firmware Interface — Firmware de arranque de los equipos modernos (reemplaza a la BIOS).
*[UI]: interfaz de usuario — Interfaz web o gráfica de una herramienta.
*[URI]: Uniform Resource Identifier — Identificador de un recurso; una URL es un tipo de URI.
*[URIs]: Uniform Resource Identifier — Identificador de un recurso; una URL es un tipo de URI.
*[URL]: dirección web — Uniform Resource Locator.
*[URLs]: dirección web — Uniform Resource Locator.
*[USB]: Universal Serial Bus
*[UUID]: Universally Unique Identifier — Identificador único de 128 bits; Linux lo usa para nombrar discos y particiones.
*[Vector]: Vector — Recolector de logs que corre en cada nodo y los envía a VictoriaLogs.
*[VictoriaLogs]: VictoriaLogs — Base de datos de logs del HomeLab (retención de 30 días); se consulta desde Grafana.
*[VIP]: IP virtual — Virtual IP: una IP que no es de un equipo fijo y puede moverse entre nodos (kube-vip, MetalLB).
*[VLAN]: red local virtual — Virtual LAN: separar una red física en varias redes lógicas.
*[VLANs]: red local virtual — Virtual LAN: separar una red física en varias redes lógicas.
*[VM]: máquina virtual — Virtual machine.
*[VMs]: máquina virtual — Virtual machine.
*[VPN]: red privada virtual — Virtual Private Network: acceso cifrado a la red de la casa desde afuera.
*[VXLAN]: Virtual Extensible LAN — Red de capa 2 encapsulada sobre UDP; con ella Flannel y Calico conectan los pods entre nodos.
*[YAML]: YAML Ain't Markup Language — Formato de texto de configuración que usan Kubernetes y Ansible.
