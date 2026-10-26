# Glossary

Acronyms and abbreviations used in this documentation. On any page, underlined
acronyms show their meaning on hover, and the first time they appear on each
page they include the meaning in parentheses.

| Abbreviation | Meaning | What It Is |
|---|---|---|
| **ACL** | Access Control List | Access Control List: who can query a service (in BIND, an ACL `lan` might limit queries to certain networks; in this homelab, DNS is open to the entire network). |
| **API** | Application Programming Interface | Interface through which a program exposes operations to others (e.g., the Kubernetes API on :6443). |
| **ARC** | [Actions Runner Controller](https://github.com/actions/actions-runner-controller) | Controller that runs GitHub Actions runners inside Kubernetes. |
| **ARM64** | 64-bit ARM architecture | CPU architecture of the Orange Pi (deborah); the other nodes are x86_64. |
| **ARP** | Address Resolution Protocol | Protocol that translates IPs to MAC addresses on the local network. |
| **BD** | database | Where a service stores its data; in the HomeLab, dqlite (Incus), SQLite (K3s) and the VictoriaMetrics and VictoriaLogs volumes. |
| **BGP** | Border Gateway Protocol | Routing protocol; MetalLB/Calico can announce IPs via BGP (L2 is used here). |
| **BIND** | [Berkeley Internet Name Domain](https://www.isc.org/bind/) | DNS server that resolves internal zones in the homelab. |
| **BPF** | [Berkeley Packet Filter](https://ebpf.io/) | Linux kernel technology (eBPF) used by Cilium for networking. |
| **C4** | [C4 model](https://c4model.com/) | Way of drawing architecture in 4 levels: context, containers, components, and deployment. |
| **CA** | certificate authority | Entity that signs TLS certificates. |
| **CAPI** | [Cluster API](https://cluster-api.sigs.k8s.io/) | Kubernetes project to create and manage clusters declaratively. |
| **CAPN** | [Cluster API Provider for Incus](https://capn.linuxcontainers.org/) | Cluster API provider that creates Kubernetes nodes as Incus instances. |
| **CI** | continuous integration | Automatically compile and test code on every change (GitHub Actions). |
| **CIDR** | Classless Inter-Domain Routing | Notation for IP ranges, e.g., 10.42.0.0/16. |
| **CIFS** | Common Internet File System | Windows shared folder protocol (SMB). |
| **CINC** | [CINC Is Not Chef](https://cinc.sh/) | Free distribution of Chef. |
| **CIS** | [Center for Internet Security](https://www.cisecurity.org/benchmark/kubernetes) | Organization that publishes hardening guides (CIS Benchmarks). |
| **CLI** | command-line interface | Tool used from the terminal (e.g., incus, kubectl). |
| **CNCF** | [Cloud Native Computing Foundation](https://www.cncf.io/) | Foundation that hosts Kubernetes and related projects. |
| **CNI** / CNIs | [Container Network Interface](https://www.cni.dev/) | Plugin that provides networking to Kubernetes pods (Flannel, Calico, Cilium…). |
| **CP** | control plane | Part of Kubernetes that manages the cluster (API server, scheduler, etcd). |
| **CPU** | central processing unit |  |
| **CR** / CRs | [Custom Resource](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) | Kubernetes object defined by an operator (e.g., a SUC plan). |
| **CRD** / CRDs | [Custom Resource Definition](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) | Definition of a new Kubernetes object type (installed by an operator, e.g., the SUC). |
| **CSV** | Comma-Separated Values | Text file of data where columns are separated by commas. |
| **Dex** | [Dex](https://dexidp.io/docs/) | HomeLab's OIDC identity provider: allows login with the GitHub account (team `devops`) to Argo CD, Grafana, Open WebUI, and SSH. |
| **DHCP** | Dynamic Host Configuration Protocol | Protocol by which the router assigns IPs automatically. |
| **DMZ** | demilitarized zone | Router option that exposes a device directly to the internet. |
| **DNS** | Domain Name System | System that translates names (argocd.homelab.local) to IPs. |
| **DR** | disaster recovery | Disaster recovery: how to bring a service back up after losing it. |
| **DTB** | Device Tree Blob | Binary description of the hardware that the kernel reads on boot on ARM boards like the Orange Pi. |
| **eBPF** | [extended Berkeley Packet Filter](https://ebpf.io/) | Programs that run inside the Linux kernel; Cilium uses them for networking and policies. |
| **eMMC** | embedded MultiMediaCard | Flash storage soldered to the board; it's the disk of deborah and does not have SMART. |
| **EOL** | End Of Life | End of life of a component (on the eMMC, warning that few reserve blocks remain). |
| **ESO** | [External Secrets Operator](https://external-secrets.io/) | Kubernetes operator that synchronizes secrets from external managers. |
| **etcd** | [etcd](https://etcd.io/) | Distributed database where Kubernetes stores its state; K3s can integrate it into the server (embedded etcd). |
| **FRR** | [Free Range Routing](https://frrouting.org/) | Routing software that MetalLB uses to speak BGP; its management port is `2623`. |
| **FTP** | File Transfer Protocol | Protocol for uploading files to hosting (cPanel); also FTPS/SFTP. |
| **GPU** | graphics processing unit | Card or chip designed for parallel calculations; accelerates AI models. The Pi in this homelab does not use it: the models run on the CPU. |
| **HA** | high availability | Design to keep a service running if a node fails. |
| **HDD** | Hard Disk Drive | Mechanical hard disk. |
| **HDMI** | High-Definition Multimedia Interface | Video output; useful to see the console of a node when the network is down. |
| **HTTP** | Hypertext Transfer Protocol |  |
| **HTTPS** | HTTP secure (over TLS) |  |
| **IA** | artificial intelligence | Programs that answer questions, summarize text, or generate exercises; here they serve as a tutor to study the guide (see [Learn with AI](aprende.md)). |
| **IdP** | Identity Provider | Identity Provider: the system that verifies who you are (in the homelab, GitHub through Dex). |
| **Incus** | [Incus](https://linuxcontainers.org/incus/) | Container and virtual machine manager (community fork of LXD); hosts the instances where the homelab nodes run. |
| **IP** / IPs | IP address | Address of a device on the network (Internet Protocol). |
| **JEDEC** | Joint Electron Device Engineering Council | Organization that standardizes memory; defines the wear fields of the eMMC. |
| **journald** | [journald](https://www.freedesktop.org/software/systemd/man/latest/systemd-journald.service.html) | systemd service that stores the logs of each node's services; Vector reads them from there. |
| **JSON** | JavaScript Object Notation | Text format for structured data. |
| **K3s** | [lightweight Kubernetes distribution](https://k3s.io/) | Kubernetes packaged into a single binary, designed for edge and homelabs. |
| **K8s** | [Kubernetes](https://kubernetes.io/) | Container orchestration platform. |
| **KIC** | [Kong Ingress Controller](https://developer.konghq.com/kubernetes-ingress-controller/) | Kong controller for Kubernetes; here it implements Gateway API. |
| **KVM** | [Kernel-based Virtual Machine](https://linux-kvm.org/) | Hardware-integrated virtualization in the Linux kernel; used by Incus VMs. |
| **L2** | layer 2 of the OSI model | OSI model's data link layer: traffic within the same local network (MAC, ARP). |
| **L3** | layer 3 of the OSI model | OSI model's network layer: IPs and routing. |
| **L7** | layer 7 of the OSI model | OSI model's application layer: HTTP and similar. |
| **LAN** | local area network | Local Area Network: the home network (192.168.20.0/22). |
| **launchd** | [launchd](https://support.apple.com/guide/terminal/apda7b3d2a58-1d40-4d2f-a5d8-9b3a2fd3f36d/mac) | macOS service manager (equivalent to systemd); activates the Ollama socket on the Mac only when a request arrives. |
| **LB** | load balancer | Kubernetes service of type LoadBalancer (provided by MetalLB). |
| **LLM** | Large Language Model | Large language model: the type of AI that understands and writes text (here, the Ollama models). |
| **LogsQL** | [LogsQL](https://docs.victoriametrics.com/victorialogs/logsql/) | VictoriaLogs query language, written in Grafana → Explore. |
| **LVM** | Logical Volume Manager | Linux logical volume manager. |
| **LXC** | [Linux Containers](https://linuxcontainers.org/lxc/) | Full system containers; Incus uses them as instances. |
| **LXD** | [LXD](https://canonical.com/lxd) | Container and VM manager from which Incus is a community fork. |
| **MAC** | MAC address (Media Access Control) | Unique identifier of a network card; the router uses it to always reserve the same IP for a device. |
| **MCP** | [Model Context Protocol](https://modelcontextprotocol.io/) | Standard to give tools to an AI model (here, read-only queries to the cluster). |
| **MD5** | Message-Digest 5 | Algorithm that BGP used to authenticate sessions between routers; here BGP runs without it. |
| **NAT** | Network Address Translation | Network translation that the router does between the local network and the internet. |
| **NFS** | Network File System | Protocol for shared folders over the network in Linux. |
| **nftables** | [nftables](https://wiki.nftables.org/) | Linux kernel firewall that uses the `host_firewall` role on each node. |
| **NIC** | network interface card | Network Interface Card. |
| **NTP** | [Network Time Protocol](https://www.ntp.org/) | Protocol that synchronizes the clock of devices; without it TLS certificates may appear "not yet valid". |
| **NVMe** | SSD over PCIe | Non-Volatile Memory Express: high-speed SSDs. |
| **NXDOMAIN** | [Non-Existent Domain](https://www.rfc-editor.org/rfc/rfc8020) | DNS server response that says the name does not exist; the router gives it for `homelab.local`, so the pods use only BIND. |
| **OAuth** | [Open Authorization](https://oauth.net/2/) | Standard for an application to act on behalf of a user without knowing their password; OIDC is built on top of it. |
| **oauth2-proxy** | [oauth2-proxy](https://oauth2-proxy.github.io/oauth2-proxy/) | Proxy that puts the Dex login in front of a web interface that does not have its own login. |
| **OCI** | [Open Container Initiative](https://opencontainers.org/) | Standard for images and registries; ARC and NGINX Gateway Fabric publish their Helm chart in an OCI registry. |
| **OIDC** | [OpenID Connect](https://openid.net/developers/how-connect-works/) | Login protocol over OAuth 2.0; Dex uses it for GitHub login. |
| **Open Terminal** | [Open Terminal](https://docs.openwebui.com/features/open-terminal) | Terminal with code execution that Open WebUI uses as a tool for the assistant; runs isolated in the `ai-sandbox` namespace. |
| **OpenPubkey** | [OpenPubkey](https://github.com/openpubkey/openpubkey) | Project that converts an OIDC login into a short-lived SSH key; used by [opkssh](https://github.com/openpubkey/opkssh) to log into hosts with the Dex identity. |
| **OS** | operating system | Operating System. |
| **OVN** | [Open Virtual Network](https://www.ovn.org/) | Software-defined virtual network that Incus can use. |
| **OVS** | [Open vSwitch](https://www.openvswitch.org/) | Virtual switch that OVN uses to connect Incus instances. |
| **PAT** | [Personal Access Token](https://docs.github.com/es/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) | GitHub personal access token that replaces the password in the API and CLI. |
| **PDB** | [PodDisruptionBudget](https://kubernetes.io/docs/tasks/run-application/configure-pdb/) | Kubernetes limit on how many pods of an application can be down at once during a node drain. |
| **PKCE** | [Proof Key for Code Exchange](https://oauth.net/2/pkce/) | OAuth extension for public clients (without a secret), such as `incus-ui` and `opkssh` in Dex. |
| **PR** / PRs | pull request | GitHub change request. |
| **PSA** | [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) | Kubernetes control that applies Pod Security Standards levels to each namespace (`warn`, `audit` or `enforce`). |
| **PSS** | [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/) | Kubernetes pod security levels (privileged, baseline, restricted). |
| **PVC** / PVCs | [PersistentVolumeClaim](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) | Kubernetes pod request for persistent storage. |
| **RAG** | Retrieval-Augmented Generation | Feeding documents to the model so it responds with them instead of inventing (here, the HomeLab documentation). |
| **RAM** | memory RAM | Working memory of the computer. |
| **RBAC** | [Role-Based Access Control](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) | Role-based access control: what each user or service account can do. |
| **RWX** | ReadWriteMany | Volume access mode that multiple pods can mount at once, even on different nodes. |
| **SAN** | Subject Alternative Name | Extra name or IP that a TLS certificate accepts (singular of SANs). |
| **SANs** | Subject Alternative Names | Extra names and IPs that a TLS certificate accepts. |
| **SATA** | Serial ATA | Interface for 2.5-inch disks and SSDs (invincible and oliver). |
| **SBC** | Single Board Computer | Computer on a single board, such as the Orange Pi 5 Plus. |
| **SD** | Secure Digital | Memory card; some ARM boards boot from it. |
| **SDK** | Software Development Kit | Library to use a service from code (e.g., the 1Password SDK). |
| **SMART** | Self-Monitoring, Analysis and Reporting Technology | Self-diagnosis that comes with disks and SSDs; warns before they fail. |
| **SO** | operating system |  |
| **SOPS** | [Secrets OPerationS](https://github.com/getsops/sops) | Tool to encrypt secrets within YAML/JSON files. |
| **SPDK** | [Storage Performance Development Kit](https://spdk.io/) | Longhorn v2 storage engine (not used here). |
| **SPI** | Serial Peripheral Interface | Bus for small chips; on the Orange Pi, the SPI flash memory stores the boot loader. |
| **SQLite** | [SQLite](https://www.sqlite.org/) | Single-file database; it is the default data store for K3s with a single server. |
| **SSD** | solid-state drive |  |
| **SoC** | system on chip | Chip that integrates CPU, graphics, and other components; the RK3588 of deborah is one. |
| **SSH** | Secure Shell | Protocol to connect to another computer via terminal in an encrypted way. |
| **SSL** | Secure Sockets Layer | Predecessor of TLS; the name is still used to refer to certificates and encrypted connections. |
| **SSO** | single sign-on | Single Sign-On: sign in to multiple services with the same account (here, GitHub via Dex). |
| **SUC** | [System Upgrade Controller](https://github.com/rancher/system-upgrade-controller) | Rancher controller that updates K3s node by node. |
| **TLS** | Transport Layer Security | Connection encryption (the S in HTTPS). |
| **TTL** | Time To Live | Time a data is cached before it is requested again. |
| **UDP** | User Datagram Protocol | Connectionless transport protocol; it is used, for example, by DNS and VXLAN. |
| **UEFI** | Unified Extensible Firmware Interface | Modern computer boot firmware (replaces BIOS). |
| **UI** | user interface | Web or graphical interface of a tool. |
| **URI** / URIs | Uniform Resource Identifier | Identifier of a resource; a URL is a type of URI. |
| **URL** / URLs | web address | Uniform Resource Locator. |
| **USB** | Universal Serial Bus |  |
| **UUID** | Universally Unique Identifier | 128-bit unique identifier; Linux uses it to name disks and partitions. |
| **Vector** | [Vector](https://vector.dev/) | Log collector that runs on each node and sends logs to VictoriaLogs. |
| **VictoriaLogs** | [VictoriaLogs](https://docs.victoriametrics.com/victorialogs/) | HomeLab log database (30-day retention); queried from Grafana. |
| **VIP** | virtual IP | Virtual IP: an IP that is not fixed to a machine and can move between nodes (kube-vip, MetalLB). |
| **VLAN** / VLANs | virtual local network | Virtual LAN: splitting a physical network into several logical networks. |
| **VM** / VMs | virtual machine | Virtual machine. |
| **VPN** | virtual private network | Virtual Private Network: encrypted access to the home network from outside. |
| **VXLAN** | Virtual Extensible LAN | Layer 2 network encapsulated over UDP; with it, Flannel and Calico connect pods between nodes. |
| **YAML** | YAML Ain't Markup Language | Text configuration format used by Kubernetes and Ansible. |
