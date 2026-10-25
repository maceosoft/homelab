<!-- Glosario de siglas: tooltip automático en todas las páginas (abbr).
     Se agrega solo al final de cada página (pymdownx.snippets.auto_append).
     Al agregar una sigla nueva, sumarla también a docs/glosario.md. -->

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
*[DHCP]: Dynamic Host Configuration Protocol — Protocolo con el que el router asigna IPs automáticamente.
*[DMZ]: zona desmilitarizada — Opción del router que expone un equipo directo a internet.
*[DNS]: Domain Name System — Sistema que traduce nombres (argocd.homelab.local) a IPs.
*[DR]: recuperación ante desastres — Disaster recovery: cómo volver a levantar un servicio tras perderlo.
*[ESO]: External Secrets Operator — Operador de Kubernetes que sincroniza secretos desde gestores externos.
*[FTP]: File Transfer Protocol — Protocolo para subir archivos al hosting (cPanel); también FTPS/SFTP.
*[HA]: alta disponibilidad — Diseño para que un servicio siga funcionando si cae un nodo.
*[HTTP]: Hypertext Transfer Protocol
*[HTTPS]: HTTP seguro (sobre TLS)
*[IA]: inteligencia artificial — Programas que responden preguntas, resumen textos o generan ejercicios; aquí sirven de tutor para estudiar la guía.
*[Incus]: Incus — Gestor de contenedores y máquinas virtuales (fork comunitario de LXD); aloja las instancias donde corren los nodos del HomeLab.
*[IP]: dirección IP — Dirección de un equipo en la red (Internet Protocol).
*[IPs]: dirección IP — Dirección de un equipo en la red (Internet Protocol).
*[JSON]: JavaScript Object Notation — Formato de texto para datos estructurados.
*[K3s]: distribución ligera de Kubernetes — Kubernetes empaquetado en un solo binario, pensado para edge y HomeLabs.
*[K8s]: Kubernetes — Plataforma de orquestación de contenedores.
*[KIC]: Kong Ingress Controller — Controlador de Kong para Kubernetes; aquí implementa Gateway API.
*[KVM]: máquina virtual del kernel — Kernel-based Virtual Machine: virtualización por hardware integrada en el kernel de Linux; la usan las VMs de Incus.
*[L2]: capa 2 del modelo OSI — Capa de enlace del modelo OSI: tráfico dentro de la misma red local (MAC, ARP).
*[L3]: capa 3 del modelo OSI — Capa de red del modelo OSI: IPs y ruteo.
*[L7]: capa 7 del modelo OSI — Capa de aplicación del modelo OSI: HTTP y similares.
*[LAN]: red local — Local Area Network: la red de la casa (192.168.20.0/22).
*[LB]: balanceador de carga — Servicio de Kubernetes tipo LoadBalancer (lo provee MetalLB).
*[LVM]: Logical Volume Manager — Gestor de volúmenes lógicos de Linux.
*[LXC]: Linux Containers — Contenedores de sistema completo; Incus los usa como instancias.
*[LXD]: LXD — Gestor de contenedores y VMs del que Incus es un fork comunitario.
*[NAT]: Network Address Translation — Traducción de direcciones que hace el router entre la red local e internet.
*[NFS]: Network File System — Protocolo de carpetas compartidas por red en Linux.
*[NIC]: tarjeta de red — Network Interface Card.
*[NTP]: Network Time Protocol — Protocolo que sincroniza el reloj de los equipos; sin él los certificados TLS pueden parecer "aún no válidos".
*[NVMe]: disco SSD por PCIe — Non-Volatile Memory Express: discos SSD de alta velocidad.
*[OCI]: Open Container Initiative — Estándar de imágenes y registros; ARC y NGINX Gateway Fabric publican su chart de Helm en un registro OCI.
*[OIDC]: OpenID Connect — Protocolo de inicio de sesión sobre OAuth 2.0; Dex lo usa para el login con GitHub.
*[OpenPubkey]: Proyecto que convierte un login OIDC en una llave SSH de corta vida; lo usa opkssh para entrar a los hosts con la identidad de Dex.
*[OS]: sistema operativo — Operating System.
*[OVN]: Open Virtual Network — Red virtual definida por software que Incus puede usar.
*[PKCE]: Proof Key for Code Exchange — Extensión de OAuth para clientes públicos (sin secreto), como incus-ui y opkssh en Dex.
*[PR]: pull request — Solicitud de cambios en GitHub.
*[PRs]: pull request — Solicitud de cambios en GitHub.
*[PSS]: Pod Security Standards — Niveles de seguridad de Kubernetes para pods (privileged, baseline, restricted).
*[PVC]: PersistentVolumeClaim — Pedido de almacenamiento persistente de un pod en Kubernetes.
*[PVCs]: PersistentVolumeClaim — Pedido de almacenamiento persistente de un pod en Kubernetes.
*[RAM]: memoria RAM — Memoria de trabajo del equipo.
*[RWX]: ReadWriteMany — Modo de acceso de un volumen que varios pods pueden montar a la vez, incluso en nodos distintos.
*[SANs]: Subject Alternative Names — Nombres e IPs extra que acepta un certificado TLS.
*[SBC]: Single Board Computer — Computador en una sola placa, como el Orange Pi 5 Plus.
*[SDK]: Software Development Kit — Librería para usar un servicio desde código (p. ej. el SDK de 1Password).
*[SO]: sistema operativo
*[SOPS]: Secrets OPerationS — Herramienta para cifrar secretos dentro de archivos YAML/JSON.
*[SPDK]: Storage Performance Development Kit — Motor de almacenamiento de Longhorn v2 (no se usa aquí).
*[SSD]: disco de estado sólido
*[SoC]: system on chip — Chip que reúne CPU, gráficos y otros componentes; el RK3588 de deborah es uno.
*[SSH]: Secure Shell — Protocolo para conectarse a otro equipo por terminal de forma cifrada.
*[SSO]: inicio de sesión único — Single Sign-On: entrar a varios servicios con la misma cuenta (aquí, GitHub vía Dex).
*[SUC]: System Upgrade Controller — Controlador de Rancher que actualiza K3s nodo por nodo.
*[TLS]: Transport Layer Security — Cifrado de las conexiones (lo que pone la S en HTTPS).
*[UEFI]: Unified Extensible Firmware Interface — Firmware de arranque de los equipos modernos (reemplaza a la BIOS).
*[UI]: interfaz de usuario — Interfaz web o gráfica de una herramienta.
*[URI]: Uniform Resource Identifier — Identificador de un recurso; una URL es un tipo de URI.
*[URIs]: Uniform Resource Identifier — Identificador de un recurso; una URL es un tipo de URI.
*[URL]: dirección web — Uniform Resource Locator.
*[URLs]: dirección web — Uniform Resource Locator.
*[USB]: Universal Serial Bus
*[VIP]: IP virtual — Virtual IP: una IP que no es de un equipo fijo y puede moverse entre nodos (kube-vip, MetalLB).
*[VLAN]: red local virtual — Virtual LAN: separar una red física en varias redes lógicas.
*[VLANs]: red local virtual — Virtual LAN: separar una red física en varias redes lógicas.
*[VM]: máquina virtual — Virtual machine.
*[VMs]: máquina virtual — Virtual machine.
*[VPN]: red privada virtual — Virtual Private Network: acceso cifrado a la red de la casa desde afuera.
*[YAML]: YAML Ain't Markup Language — Formato de texto de configuración que usan Kubernetes y Ansible.
