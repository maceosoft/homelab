# Glosario

Siglas y abreviaturas que aparecen en esta documentación. En cualquier página,
las siglas subrayadas muestran su significado al pasar el mouse, y la primera
vez que aparecen en cada página llevan el significado entre paréntesis.

| Sigla | Significado | Qué es |
|---|---|---|
| **API** | Application Programming Interface | Interfaz por la que un programa expone operaciones a otros (p. ej. la API de Kubernetes en :6443). |
| **ARC** | [Actions Runner Controller](https://github.com/actions/actions-runner-controller) | Controlador que corre runners de GitHub Actions dentro de Kubernetes. |
| **ARM64** | arquitectura ARM de 64 bits | Arquitectura de CPU del Orange Pi (deborah); los otros nodos son x86_64. |
| **ARP** | Address Resolution Protocol | Protocolo que traduce IPs a direcciones MAC en la red local. |
| **BD** | base de datos |  |
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
| **DHCP** | Dynamic Host Configuration Protocol | Protocolo con el que el router asigna IPs automáticamente. |
| **DMZ** | zona desmilitarizada | Opción del router que expone un equipo directo a internet. |
| **DNS** | Domain Name System | Sistema que traduce nombres (argocd.homelab.local) a IPs. |
| **DR** | recuperación ante desastres | Disaster recovery: cómo volver a levantar un servicio tras perderlo. |
| **ESO** | [External Secrets Operator](https://external-secrets.io/) | Operador de Kubernetes que sincroniza secretos desde gestores externos. |
| **FTP** | File Transfer Protocol | Protocolo para subir archivos al hosting (cPanel); también FTPS/SFTP. |
| **HA** | alta disponibilidad | Diseño para que un servicio siga funcionando si cae un nodo. |
| **HTTP** | Hypertext Transfer Protocol |  |
| **HTTPS** | HTTP seguro (sobre TLS) |  |
| **IA** | inteligencia artificial | Programas que responden preguntas, resumen textos o generan ejercicios; aquí sirven de tutor para estudiar la guía (ver [Aprende con IA](aprende.md)). |
| **Incus** | [Incus](https://linuxcontainers.org/incus/) | Gestor de contenedores y máquinas virtuales (fork comunitario de LXD); aloja las instancias donde corren los nodos del HomeLab. |
| **IP** / IPs | dirección IP | Dirección de un equipo en la red (Internet Protocol). |
| **JSON** | JavaScript Object Notation | Formato de texto para datos estructurados. |
| **K3s** | [distribución ligera de Kubernetes](https://k3s.io/) | Kubernetes empaquetado en un solo binario, pensado para edge y HomeLabs. |
| **K8s** | [Kubernetes](https://kubernetes.io/) | Plataforma de orquestación de contenedores. |
| **KIC** | [Kong Ingress Controller](https://developer.konghq.com/kubernetes-ingress-controller/) | Controlador de Kong para Kubernetes; aquí implementa Gateway API. |
| **KVM** | [Kernel-based Virtual Machine](https://linux-kvm.org/) | Virtualización por hardware integrada en el kernel de Linux; la usan las VMs de Incus. |
| **L2** | capa 2 del modelo OSI | Capa de enlace del modelo OSI: tráfico dentro de la misma red local (MAC, ARP). |
| **L3** | capa 3 del modelo OSI | Capa de red del modelo OSI: IPs y ruteo. |
| **L7** | capa 7 del modelo OSI | Capa de aplicación del modelo OSI: HTTP y similares. |
| **LAN** | red local | Local Area Network: la red de la casa (192.168.20.0/22). |
| **LB** | balanceador de carga | Servicio de Kubernetes tipo LoadBalancer (lo provee MetalLB). |
| **LVM** | Logical Volume Manager | Gestor de volúmenes lógicos de Linux. |
| **LXC** | [Linux Containers](https://linuxcontainers.org/lxc/) | Contenedores de sistema completo; Incus los usa como instancias. |
| **LXD** | [LXD](https://canonical.com/lxd) | Gestor de contenedores y VMs del que Incus es un fork comunitario. |
| **NAT** | Network Address Translation | Traducción de direcciones que hace el router entre la red local e internet. |
| **NFS** | Network File System | Protocolo de carpetas compartidas por red en Linux. |
| **NIC** | tarjeta de red | Network Interface Card. |
| **NTP** | [Network Time Protocol](https://www.ntp.org/) | Protocolo que sincroniza el reloj de los equipos; sin él los certificados TLS pueden parecer "aún no válidos". |
| **NVMe** | disco SSD por PCIe | Non-Volatile Memory Express: discos SSD de alta velocidad. |
| **OCI** | [Open Container Initiative](https://opencontainers.org/) | Estándar de imágenes y registros; ARC y NGINX Gateway Fabric publican su chart de Helm en un registro OCI. |
| **OIDC** | [OpenID Connect](https://openid.net/developers/how-connect-works/) | Protocolo de inicio de sesión sobre OAuth 2.0; Dex lo usa para el login con GitHub. |
| **OpenPubkey** | [OpenPubkey](https://github.com/openpubkey/openpubkey) | Proyecto que convierte un login OIDC en una llave SSH de corta vida; lo usa [opkssh](https://github.com/openpubkey/opkssh) para entrar a los hosts con la identidad de Dex. |
| **OS** | sistema operativo | Operating System. |
| **OVN** | [Open Virtual Network](https://www.ovn.org/) | Red virtual definida por software que Incus puede usar. |
| **PKCE** | [Proof Key for Code Exchange](https://oauth.net/2/pkce/) | Extensión de OAuth para clientes públicos (sin secreto), como `incus-ui` y `opkssh` en Dex. |
| **PR** / PRs | pull request | Solicitud de cambios en GitHub. |
| **PSS** | [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/) | Niveles de seguridad de Kubernetes para pods (privileged, baseline, restricted). |
| **PVC** / PVCs | [PersistentVolumeClaim](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) | Pedido de almacenamiento persistente de un pod en Kubernetes. |
| **RAM** | memoria RAM | Memoria de trabajo del equipo. |
| **RWX** | ReadWriteMany | Modo de acceso de un volumen que varios pods pueden montar a la vez, incluso en nodos distintos. |
| **SANs** | Subject Alternative Names | Nombres e IPs extra que acepta un certificado TLS. |
| **SBC** | Single Board Computer | Computador en una sola placa, como el Orange Pi 5 Plus. |
| **SDK** | Software Development Kit | Librería para usar un servicio desde código (p. ej. el SDK de 1Password). |
| **SO** | sistema operativo |  |
| **SOPS** | [Secrets OPerationS](https://github.com/getsops/sops) | Herramienta para cifrar secretos dentro de archivos YAML/JSON. |
| **SPDK** | [Storage Performance Development Kit](https://spdk.io/) | Motor de almacenamiento de Longhorn v2 (no se usa aquí). |
| **SSD** | disco de estado sólido |  |
| **SoC** | system on chip | Chip que reúne CPU, gráficos y otros componentes; el RK3588 de deborah es uno. |
| **SSH** | Secure Shell | Protocolo para conectarse a otro equipo por terminal de forma cifrada. |
| **SSO** | inicio de sesión único | Single Sign-On: entrar a varios servicios con la misma cuenta (aquí, GitHub vía Dex). |
| **SUC** | [System Upgrade Controller](https://github.com/rancher/system-upgrade-controller) | Controlador de Rancher que actualiza K3s nodo por nodo. |
| **TLS** | Transport Layer Security | Cifrado de las conexiones (lo que pone la S en HTTPS). |
| **UEFI** | Unified Extensible Firmware Interface | Firmware de arranque de los equipos modernos (reemplaza a la BIOS). |
| **UI** | interfaz de usuario | Interfaz web o gráfica de una herramienta. |
| **URI** / URIs | Uniform Resource Identifier | Identificador de un recurso; una URL es un tipo de URI. |
| **URL** / URLs | dirección web | Uniform Resource Locator. |
| **USB** | Universal Serial Bus |  |
| **VIP** | IP virtual | Virtual IP: una IP que no es de un equipo fijo y puede moverse entre nodos (kube-vip, MetalLB). |
| **VLAN** / VLANs | red local virtual | Virtual LAN: separar una red física en varias redes lógicas. |
| **VM** / VMs | máquina virtual | Virtual machine. |
| **VPN** | red privada virtual | Virtual Private Network: acceso cifrado a la red de la casa desde afuera. |
| **YAML** | YAML Ain't Markup Language | Formato de texto de configuración que usan Kubernetes y Ansible. |
