# Glossary

The technical terms in this documentation, in two tables: [acronyms and
abbreviations](#acronyms-and-abbreviations) and [concepts and tools](#concepts-and-tools).
On any page, underlined acronyms show their meaning on hover, and the first
time they appear on each page they include the meaning in parentheses.

## Acronyms and abbreviations

| Acronym | Meaning | What is |
|---|---|---|
| **AKS** | [Azure Kubernetes Service](https://learn.microsoft.com/azure/aks/) | Microsoft Azure's managed Kubernetes. Its `kubelogin` plugin shares the name with int128's used in this HomeLab, but doesn't work with Dex. |
| **ACL** | Access Control List | Access control list: who can query a service (in BIND, an `lan` list could limit queries to certain networks; in this HomeLab DNS is open to the whole network). |
| **API** | Application Programming Interface | Interface through which a program exposes operations to others (e.g., the Kubernetes API on :6443). |
| **ARC** | [Actions Runner Controller](https://github.com/actions/actions-runner-controller) | Controller that runs GitHub Actions runners inside Kubernetes. |
| **ARM64** | 64-bit ARM architecture | CPU architecture of the Orange Pi (deborah); the other nodes are x86_64. |
| **ARP** | Address Resolution Protocol | Protocol that translates IPs to MAC addresses on the local network. |
| **BD** | database | Where a service stores its data; in the HomeLab, dqlite (Incus), SQLite (K3s), and the VictoriaMetrics and VictoriaLogs volumes. |
| **BGP** | Border Gateway Protocol | Routing protocol; MetalLB/Calico can announce IPs via BGP (here L2 is used). |
| **BIND** | [Berkeley Internet Name Domain](https://www.isc.org/bind/) | DNS server that resolves the HomeLab's internal zones. |
| **BPF** | [Berkeley Packet Filter](https://ebpf.io/) | Linux kernel technology (eBPF) that Cilium uses for networking. |
| **C4** | [C4 model](https://c4model.com/) | Way to diagram architecture in 4 levels: context, containers, components, and deployment. |
| **CA** | certificate authority | Entity that signs TLS certificates. |
| **CAPI** | [Cluster API](https://cluster-api.sigs.k8s.io/) | Kubernetes project to create and manage clusters declaratively. |
| **CAPN** | [Cluster API Provider for Incus](https://capn.linuxcontainers.org/) | Cluster API provider that creates Kubernetes cluster nodes as Incus instances. |
| **CI** | continuous integration | Automatically build and test code on every change (GitHub Actions). |
| **CIDR** | Classless Inter-Domain Routing | IP range notation, e.g., 10.42.0.0/16. |
| **CIFS** | Common Internet File System | Windows shared folders protocol (SMB). |
| **CINC** | [CINC Is Not Chef](https://cinc.sh/) | Free distribution of Chef. |
| **CIS** | [Center for Internet Security](https://www.cisecurity.org/benchmark/kubernetes) | Organization that publishes hardening guides (CIS Benchmarks). |
| **CLI** | command-line interface | Tool used from the terminal (e.g., incus, kubectl). |
| **CNCF** | [Cloud Native Computing Foundation](https://www.cncf.io/) | Foundation that hosts Kubernetes and related projects. |
| **CNI** / CNIs | [Container Network Interface](https://www.cni.dev/) | Plugin that provides networking to Kubernetes pods (Flannel, Calico, Cilium…). |
| **CP** | control plane | Part of Kubernetes that manages the cluster (API server, scheduler, etcd). |
| **CPU** | central processing unit |  |
| **CR** / CRs | [Custom Resource](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) | Kubernetes object defined by an operator (e.g., a SUC Plan). |
| **CRD** / CRDs | [Custom Resource Definition](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) | Definition of a new object type in Kubernetes (installed by an operator, e.g., the SUC). |
| **CSR** | [Certificate Signing Request](https://cert-manager.io/docs/usage/certificaterequest/) | Certificate signing request: carries the public key and names (SANs), never the private key. This is how the Incus S3 certificate is signed without removing its key from the node. |
| **CSV** | Comma-Separated Values | Text data file where columns are separated by commas. |
| **Dex** | [Dex](https://dexidp.io/docs/) | HomeLab's OIDC identity provider: allows login with a GitHub account (team `devops`) to Argo CD, Grafana, Open WebUI, and SSH. |
| **DHCP** | Dynamic Host Configuration Protocol | Protocol by which the router assigns IPs automatically. |
| **DMZ** | demilitarized zone | Router option that exposes a machine directly to the internet. |
| **DNS** | Domain Name System | System that translates names (argocd.homelab.local) to IPs. |
| **DR** | disaster recovery | Disaster recovery: how to bring a service back up after losing it. |
| **DTB** | Device Tree Blob | Binary hardware description that the kernel reads at boot on ARM boards like the Orange Pi. |
| **eBPF** | [extended Berkeley Packet Filter](https://ebpf.io/) | Programs that run inside the Linux kernel; Cilium uses them for networking and policies. |
| **eMMC** | embedded MultiMediaCard | Flash storage soldered to the board; it's deborah's disk and has no SMART. |
| **EOL** | End Of Life | End of life of a component (in the eMMC, warning that few spare blocks remain). |
| **ESO** | [External Secrets Operator](https://external-secrets.io/) | Kubernetes operator that syncs secrets from external managers. |
| **etcd** | [etcd](https://etcd.io/) | Distributed database where Kubernetes stores its state; K3s can integrate it into the server (embedded etcd). |
| **FRR** | [Free Range Routing](https://frrouting.org/) | Routing software that MetalLB uses to speak BGP; its management port is `2623`. |
| **FTP** | File Transfer Protocol | Protocol for uploading files to hosting (cPanel); also FTPS/SFTP. |
| **GPU** | graphics processing unit | Card or chip designed for parallel calculations; accelerates AI models. The Pi in this HomeLab doesn't use it: models run on the CPU. |
| **HA** | high availability | Design for a service to keep working if a node fails. |
| **HDD** | Hard Disk Drive | Mechanical hard drive. |
| **HDMI** | High-Definition Multimedia Interface | Video output; useful for viewing a node's console when the network doesn't respond. |
| **HTTP** | Hypertext Transfer Protocol |  |
| **HTTPS** | HTTP secure (over TLS) |  |
| **IA** | artificial intelligence | Programs that answer questions, summarize texts, or generate exercises; here they serve as tutors for studying the guide (see [Learn with AI](aprende.md)). |
| **IdP** | Identity Provider | Identity provider: the system that verifies who you are (in the HomeLab, GitHub via Dex). |
| **Incus** | [Incus](https://linuxcontainers.org/incus/) | Container and virtual machine manager (community fork of LXD); hosts the instances where the HomeLab nodes run. |
| **IP** / IPs | dirección IP | Address of a device on the network (Internet Protocol). |
| **JEDEC** | Joint Electron Device Engineering Council | Body that standardizes memory; defines eMMC wear fields. |
| **journald** | [journald](https://www.freedesktop.org/software/systemd/man/latest/systemd-journald.service.html) | systemd service that stores the logs of each node's services; Vector reads them from there. |
| **JSON** | JavaScript Object Notation | Text format for structured data. |
| **K3s** | [distribución ligera de Kubernetes](https://k3s.io/) | Kubernetes packaged in a single binary, designed for edge and HomeLabs. |
| **K8s** | [Kubernetes](https://kubernetes.io/) | Abbreviation for Kubernetes: the K, the 8 middle letters, and the s. |
| **KIC** | [Kong Ingress Controller](https://developer.konghq.com/kubernetes-ingress-controller/) | Kong controller for Kubernetes; here it implements Gateway API. |
| **Kubernetes** | [Kubernetes](https://kubernetes.io/) (K8s) | Platform that orchestrates containers: decides which node runs each pod, restarts it if it fails, and gives it network and storage. In this HomeLab it runs as K3s. |
| **KVM** | [Kernel-based Virtual Machine](https://linux-kvm.org/) | Hardware virtualization built into the Linux kernel; used by Incus VMs. |
| **L2** | capa 2 del modelo OSI | OSI model link layer: traffic within the same local network (MAC, ARP). |
| **L3** | capa 3 del modelo OSI | OSI model network layer: IPs and routing. |
| **L7** | capa 7 del modelo OSI | OSI model application layer: HTTP and similar. |
| **LAN** | red local | Local Area Network: the home network (192.168.20.0/22). |
| **launchd** | [launchd](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html) | macOS service manager (equivalent to systemd); socket-activates the Mac's Ollama only when a request arrives. |
| **LB** | balanceador de carga | Kubernetes LoadBalancer service (provided by MetalLB). |
| **LLM** | Large Language Model | Large Language Model: the type of AI that understands and writes text (here, the Ollama models). |
| **LogsQL** | [LogsQL](https://docs.victoriametrics.com/victorialogs/logsql/) | VictoriaLogs query language, the one written in Grafana → Explore. |
| **LVM** | Logical Volume Manager | Linux Logical Volume Manager. |
| **LXC** | [Linux Containers](https://linuxcontainers.org/lxc/) | Full system containers; Incus uses them as instances. |
| **LXD** | [LXD](https://canonical.com/lxd) | Container and VM manager that Incus is a community fork of. |
| **MAC** | dirección MAC (Media Access Control) | Unique identifier of a network card; the router uses it to always reserve the same IP for a device. |
| **MCP** | [Model Context Protocol](https://modelcontextprotocol.io/) | Standard for giving tools to an AI model (here, read-only queries to the cluster). |
| **MD5** | Message-Digest 5 | Digest algorithm that BGP used to authenticate sessions between routers; here BGP runs without it. |
| **NAT** | Network Address Translation | Address translation that the router performs between the local network and the internet. |
| **NFS** | Network File System | Network file sharing protocol in Linux. |
| **nftables** | [nftables](https://wiki.nftables.org/) | Linux kernel firewall used by the `host_firewall` role on each node. |
| **NIC** | tarjeta de red | Network Interface Card. |
| **NRPT** | [Name Resolution Policy Table](https://learn.microsoft.com/en-us/powershell/module/dnsclient/add-dnsclientnrptrule) | Windows table that sends DNS zone queries to a specific server; this resolves `homelab.local` with the BIND of `deborah` without changing the DNS of the whole machine. |
| **NTP** | [Network Time Protocol](https://www.ntp.org/) | Protocol that synchronizes the clock of devices; without it TLS certificates may appear "not yet valid". |
| **NVMe** | disco SSD por PCIe | Non-Volatile Memory Express: high-speed SSD disks. |
| **NXDOMAIN** | [Non-Existent Domain](https://www.rfc-editor.org/rfc/rfc8020) | Response from a DNS server saying the name does not exist; the router gives it for `homelab.local`, which is why pods use only BIND. |
| **OAuth** | [Open Authorization](https://oauth.net/2/) | Standard for an application to act with user permission without knowing their password; OIDC is built on it. |
| **oauth2-proxy** | [oauth2-proxy](https://oauth2-proxy.github.io/oauth2-proxy/) | Proxy that puts the Dex login in front of a web interface that lacks its own login. |
| **OCI** | [Open Container Initiative](https://opencontainers.org/) | Image and registry standard; ARC and NGINX Gateway Fabric publish their Helm chart in an OCI registry. |
| **OIDC** | [OpenID Connect](https://openid.net/developers/how-connect-works/) | Login protocol over OAuth 2.0; Dex uses it for GitHub login. |
| **Open Terminal** | [Open Terminal](https://docs.openwebui.com/features/open-terminal) | Terminal with code execution that Open WebUI uses as an assistant tool; runs isolated in the `ai-sandbox` namespace. |
| **OpenPubkey** | [OpenPubkey](https://github.com/openpubkey/openpubkey) | Project that turns an OIDC login into a short-lived SSH key; used by [opkssh](https://github.com/openpubkey/opkssh) to access hosts with the Dex identity. |
| **OS** | sistema operativo | Operating System. |
| **OVN** | [Open Virtual Network](https://www.ovn.org/) | Software-defined virtual network that Incus can use. |
| **OVS** | [Open vSwitch](https://www.openvswitch.org/) | Virtual switch that OVN uses to connect Incus instances. |
| **PAT** | [Personal Access Token](https://docs.github.com/es/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) | GitHub personal access token that replaces the password in the API and CLI. |
| **PDB** | [PodDisruptionBudget](https://kubernetes.io/docs/tasks/run-application/configure-pdb/) | Kubernetes limit on how many pods of an application can be down at once during a node drain. |
| **PHP** | [PHP: Hypertext Preprocessor](https://www.php.net/) | Programming language for web applications; the ARC `arc-php-84` scale set comes with it preinstalled (version 8.4). |
| **PKCE** | [Proof Key for Code Exchange](https://oauth.net/2/pkce/) | OAuth extension for public clients (no secret), such as `incus-ui` and `opkssh` in Dex. |
| **PR** / PRs | pull request | Pull request in GitHub. |
| **PSA** | [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) | Kubernetes control that applies Pod Security Standards levels to each namespace (`warn`, `audit`, or `enforce`). |
| **PSS** | [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/) | Kubernetes security levels for pods (privileged, baseline, restricted). |
| **PVC** / PVCs | [PersistentVolumeClaim](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) | A pod's request for persistent storage in Kubernetes. |
| **RAG** | Retrieval-Augmented Generation | Provide custom documents to the model so it answers with them instead of making things up (here, the HomeLab documentation). |
| **RAM** | memoria RAM | The computer's working memory. |
| **RBAC** | [Role-Based Access Control](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) | Role-based access control: what each user or service account can do. |
| **RWX** | ReadWriteMany | Volume access mode that multiple pods can mount simultaneously, even on different nodes. |
| **S3** | [Simple Storage Service](https://linuxcontainers.org/incus/docs/main/howto/storage_buckets/) | Object storage protocol (buckets) created by Amazon. Incus offers it for its buckets; here it stores PostgreSQL backups. |
| **SAN** | Subject Alternative Name | Extra name or IP that a TLS certificate accepts (singular of SANs). |
| **SANs** | Subject Alternative Names | Extra names and IPs that a TLS certificate accepts. |
| **SATA** | Serial ATA | Interface for 2.5-inch drives and SSDs (invincible and oliver). |
| **SBC** | Single Board Computer | Computer on a single board, like the Orange Pi 5 Plus. |
| **SD** | Secure Digital | Memory card; some ARM boards boot from it. |
| **SDK** | Software Development Kit | Library to use a service from code (e.g., the 1Password SDK). |
| **SMART** | Self-Monitoring, Analysis and Reporting Technology | Self-diagnostics built into drives and SSDs; warns before they fail. |
| **SO** | sistema operativo |  |
| **SOPS** | [Secrets OPerationS](https://github.com/getsops/sops) | Tool to encrypt secrets inside YAML/JSON files. |
| **SPDK** | [Storage Performance Development Kit](https://spdk.io/) | Longhorn v2 storage engine (not used here). |
| **SPI** | Serial Peripheral Interface | Bus for small chips; on the Orange Pi, SPI flash stores the bootloader. |
| **SQLite** | [SQLite](https://www.sqlite.org/) | Database in a single file; it is K3s's default datastore with a single server. |
| **SSD** | disco de estado sólido |  |
| **SoC** | system on chip | Chip that integrates CPU, graphics, and other components; deborah's RK3588 is one. |
| **SSH** | Secure Shell | Encrypted terminal protocol for connecting to another machine. |
| **SSL** | Secure Sockets Layer | Predecessor of TLS; the name is still used to refer to certificates and encrypted connections. |
| **SSO** | inicio de sesión único | Single Sign-On: log in to multiple services with the same account (here, GitHub via Dex). |
| **SUC** | [System Upgrade Controller](https://github.com/rancher/system-upgrade-controller) | Rancher controller that updates K3s node by node. |
| **T2** | [chip Apple T2](https://wiki.t2linux.org/) | Security coprocessor in 2018-2020 Intel Macs; handles keyboard, trackpad, audio, and Touch ID, and on Linux requires kernel `linux-t2` (node `eve`). |
| **TCP** | Transmission Control Protocol | Connection-oriented transport protocol with ordered delivery; HTTP, TLS, and SSH run over it. |
| **TLS** | Transport Layer Security | Connection encryption (what puts the S in HTTPS). |
| **TSIG** | [Transaction SIGnature](https://datatracker.ietf.org/doc/html/rfc8945) | Shared secret used to sign DNS changes. ExternalDNS and Ansible each write to BIND with their own key. |
| **TTL** | Time To Live | Time a piece of data is kept in cache before being requested again. |
| **UDP** | User Datagram Protocol | Connectionless transport protocol; used by DNS and VXLAN, for example. |
| **UEFI** | Unified Extensible Firmware Interface | Boot firmware on modern computers (replaces BIOS). |
| **UI** | interfaz de usuario | Web or graphical interface of a tool. |
| **URI** / URIs | Uniform Resource Identifier | Identifier for a resource; a URL is a type of URI. |
| **URL** / URLs | dirección web | Uniform Resource Locator. |
| **USB** | Universal Serial Bus |  |
| **UUID** | Universally Unique Identifier | 128-bit unique identifier; Linux uses it to name disks and partitions. |
| **Vector** | [Vector](https://vector.dev/) | Log collector that runs on each node and sends them to VictoriaLogs. |
| **VictoriaLogs** | [VictoriaLogs](https://docs.victoriametrics.com/victorialogs/) | HomeLab log database (30-day retention); queried from Grafana. |
| **VIP** | IP virtual | Virtual IP: an IP not tied to a fixed machine that can move between nodes (kube-vip, MetalLB). |
| **VLAN** / VLANs | red local virtual | Virtual LAN: separate a physical network into multiple logical networks. |
| **VM** / VMs | máquina virtual | Virtual machine. |
| **VPN** | red privada virtual | Virtual Private Network: encrypted access to the home network from outside. |
| **VXLAN** | Virtual Extensible LAN | Layer 2 network encapsulated over UDP; Flannel and Calico use it to connect pods across nodes. |
| **WAL** | [Write-Ahead Log](https://www.postgresql.org/docs/current/wal-intro.html) | Log where PostgreSQL records each change before applying it. Continuously archiving it allows restoring the database to any point in time. |
| **YAML** | YAML Ain't Markup Language | Configuration text format used by Kubernetes and Ansible. |

## Concepts and tools

Terms the guide uses without explaining each time: Kubernetes components, HomeLab tools, and ops jargon. If a word trips you up while reading, look it up here.

| Term | What it is |
|---|---|
| **[1Password](https://1password.com/)** | Password manager. Here it's the vault where the HomeLab's real secrets live (keys, tokens, GitHub Apps); scripts read them with its SDK. |
| **[age](https://github.com/FiloSottile/age)** | Simple encryption tool with keys; SOPS uses it to encrypt the repo's secret files. |
| **[Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)** | Receives alerts, groups them, avoids duplicates, and sends them to their destination; here, to Discord channels. |
| **[Ansible](https://docs.ansible.com/)** | Tool that configures servers via SSH from YAML files. Here it prepares nodes and installs the network, Incus, and K3s (Phases 0 to 3). |
| **Application** / **ApplicationSet** | Argo CD resources. An Application defines which Git folder to deploy and in which cluster; an ApplicationSet generates many Applications from a template (here the ApplicationSet `homelab` creates one Application for each `bootstrap/components/` file in the `gitops` repo). |
| **apt** | Debian package manager: installs and updates system software. |
| **[Argo CD](https://argo-cd.readthedocs.io/)** | The HomeLab's GitOps tool: watches the `gitops` repo and applies its changes to the K3s cluster. Has a web UI where you see each application's status. |
| **Bootstrap** | The initial boot: the first manual steps that leave a system ready to manage itself. Here Ansible installs the basics and then Argo CD takes over. |
| **Bridge** | Virtual network interface that works like a switch. The `br0` bridge connects VMs and containers to the LAN as if they were another machine. |
| **[Calico](https://docs.tigera.io/calico/)** | The cluster's CNI: connects pods across nodes and enforces NetworkPolicy. |
| **[cert-manager](https://cert-manager.io/)** | Issues and renews TLS certificates inside Kubernetes only. Here they are signed by the HomeLab's own CA for the `*.homelab.local` domains. |
| **[CloudNativePG](https://cloudnative-pg.io/)** | Kubernetes operator that creates and manages PostgreSQL clusters (instances, users, backups). Here it runs the platform's shared PostgreSQL. |
| **[Cilium](https://cilium.io/)** | eBPF-based CNI. Appears in the guide as an alternative to Calico. |
| **Cluster** | Group of machines working together as a single system. In this HomeLab there are two on the same 4 nodes: the Incus cluster and the K3s cluster. |
| **Container** | Isolated process that brings everything it needs to run but shares the host's kernel; that's why it's lighter than a VM. Incus runs system containers (LXC) and Kubernetes runs application containers inside pods. |
| **Control plane** / **worker** | The control plane is the cluster's "brain": stores state and decides which node runs what (here it's on deborah). Workers only run applications; K3s calls them *agents* and the control plane *server*. |
| **Controller** / **operator** | A controller is a cluster program that watches resources and acts until the real state matches the desired state. An operator is a controller that manages a specific application with its own CRDs (e.g., VictoriaMetrics'). In the guide, "operator" also sometimes means the person who administers the HomeLab. |
| **Cordon** / **drain** | `kubectl cordon` marks a node so it receives no new pods; `kubectl drain` also evicts existing ones to other nodes. Done before rebooting or patching a node, and `uncordon` re-enables it. |
| **[CoreDNS](https://coredns.io/)** | Kubernetes' internal DNS: resolves Service and pod names inside the cluster. |
| **CronJob** | Kubernetes task that runs on a fixed schedule, like a Linux cron. |
| **DaemonSet** | Kubernetes resource that runs a copy of a pod on every node. Vector, which collects logs, runs this way. |
| **Dashboard** | Grafana dashboard with multiple charts on a topic, e.g., "HomeLab / Ollama". |
| **[Debian](https://www.debian.org/)** | The Linux distribution installed on the four nodes. |
| **Deployment** | Kubernetes resource that keeps N copies (replicas) of a pod running and replaces them if they fail. |
| **[dqlite](https://dqlite.io/)** | Distributed SQLite database where Incus stores cluster state, replicated among members: 3 vote and 1 stands by. |
| **Docker** | Tool to create and run containers on a computer ([docker.com](https://www.docker.com/)). In the HomeLab, ARC runners use it to build images. |
| **Drift** / **self-heal** | Drift is the difference between what Git says and what is actually in the cluster. With self-heal, Argo CD corrects it automatically. |
| **[ExternalDNS](https://kubernetes-sigs.github.io/external-dns/)** | Kubernetes controller that publishes `HTTPRoute` and Service names to a DNS, and deletes them when they disappear. In the HomeLab it writes to BIND: [Automatic DNS](networking/dns-automatico.md). |
| **Exporter** | Small program that publishes metrics for vmagent to scrape: node-exporter exposes each node's system metrics and blackbox-exporter probes URLs and DNS from outside. |
| **Firewall** | Filter that decides what network traffic is allowed and what is blocked (on Linux, ufw or nftables). |
| **[Flannel](https://github.com/flannel-io/flannel)** | The CNI that K3s includes by default. This HomeLab replaces it with Calico. |
| **Fork** | Copy of a project developed separately from the original; e.g., Incus is a fork of LXD and OpenTofu of Terraform. |
| **[Gateway API](https://gateway-api.sigs.k8s.io/)** / **HTTPRoute** | Kubernetes standard for exposing web services externally; replaces Ingress. The Gateway is the entry point (here implemented by Kong) and each HTTPRoute defines which domain or path goes to which Service. |
| **[GitHub Actions](https://docs.github.com/actions)** / **workflow** / **runner** | GitHub Actions is GitHub's CI: runs tasks when you push or open a PR. A workflow is the YAML file describing those tasks and the runner is the machine that runs them; here runners are cluster pods created by ARC. |
| **[GitHub App](https://docs.github.com/apps)** | GitHub App identity with scoped permissions, to automate without using a personal account (used by ARC, Argo CD, and OpenTofu). |
| **[GitOps](https://opengitops.dev/)** | Way of operating where Git is the source of truth: you change a file in the repo and a tool (here Argo CD) makes the cluster match. Also the name of the repo `maceosoft/gitops`. |
| **[Grafana](https://grafana.com/docs/grafana/latest/)** | The web UI where you view metrics in dashboards and search logs (in «Explore»). |
| **[HAProxy](https://www.haproxy.org/)** | TCP/HTTP proxy and load balancer. In `invincible` it exposes Incus S3 with a certificate from the HomeLab CA (role `incus_s3`). |
| **group_vars** / **host_vars** | Ansible folders with variables for a group of machines or a specific machine. |
| **Hardening** | Hardening a system's security: closing ports, removing unnecessary access, and applying secure configurations. |
| **[healthchecks.io](https://healthchecks.io/)** | External service that expects a periodic «ping» and alerts if it stops arriving. Monitors that monitoring itself stays alive. |
| **[Helm](https://helm.sh/)** / **chart** / **values** | Helm is the Kubernetes package manager. A chart is a package of manifests with templates and values are the parameters that tune it. Argo CD installs several HomeLab components as charts. |
| **Idempotente** | Something you can run multiple times with the same result: if something is already done, it doesn't repeat or break it. Ansible playbooks are designed this way. |
| **Imagen** | Read-only template from which a container or VM is created (e.g. `bitnami/kubectl`). Downloaded from a *registry*. |
| **[Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)** | The classic way to expose HTTP services in Kubernetes. The HomeLab doesn't use it (uses Gateway API), but it appears for comparison. |
| **Instancia** | In Incus, each container or VM it creates. CAPN and vCluster Kubernetes nodes are instances. |
| **Inventario** | List of machines managed by Ansible, with their groups and variables. |
| **[K8sGPT](https://k8sgpt.ai/)** | Tool that analyzes cluster problems and explains them in natural language with an LLM (here, from Ollama). |
| **Kernel** | The operating system kernel, which talks directly to hardware. Containers share the host's kernel. |
| **kind** | Kubernetes IN Docker ([kind.sigs.k8s.io](https://kind.sigs.k8s.io/)): spins up a Kubernetes cluster on your computer using Docker containers as nodes. Useful for practicing the guide without multiple machines. |
| **[Kong](https://developer.konghq.com/kubernetes-ingress-controller/)** | The cluster's HTTP/HTTPS gateway: implements Gateway API (with KIC), receives traffic and routes it to services. |
| **[kube-vip](https://kube-vip.io/)** | Places a virtual IP (VIP) in front of the Kubernetes API so it doesn't depend on a single node. Optional here; don't confuse with MetalLB. |
| **[kubeconfig](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)** | File with the cluster address and your credentials; kubectl uses it to know which cluster to connect to and as whom (here, `~/.kube/homelab-k3s.yaml`). |
| **[kubectl](https://kubernetes.io/docs/reference/kubectl/)** | The CLI to talk to Kubernetes: view pods, read logs, apply manifests, or restart things. |
| **kubelet** | Kubernetes agent that runs on each node and starts the pods assigned by the control plane. |
| **[Kustomize](https://kustomize.io/)** | Tool that builds and tweaks YAML manifests by overlaying changes on a base, without templates. The repo `gitops` pipeline uses it for validation. |
| **Latido** (heartbeat) | Short signal a machine sends periodically to say «I'm here». Each Ollama node sends it to the router every 60 seconds; if the router misses 3 heartbeats (180 s), it marks it as down. |
| **[Longhorn](https://longhorn.io/)** | Distributed storage for Kubernetes: stores each volume with replicas across multiple nodes so data isn't lost if one goes down (StorageClass `longhorn-mixto`). |
| **Manifiesto** | YAML file describing a Kubernetes resource as you want it to exist. You declare what you want, not how to do it; Argo CD applies them from Git. |
| **Merge** / **rama** | A branch is a separate line of changes in Git. Merging joins it to `main`, typically when approving a PR. |
| **[MetalLB](https://metallb.io/)** | Gives LAN IPs (pool `192.168.23.200–.220`) to LoadBalancer-type Services, something the cloud provider does in the cloud. |
| **Métrica** / **scrape** | A metric is a number measured repeatedly over time (e.g. CPU usage). The scrape is the periodic read vmagent makes of each service's metrics. |
| **Namespace** | Named space inside the cluster that separates resources and permissions, like a folder (e.g. `ai`, `kong`, or `arc-runners`). Almost all kubectl commands take `-n <namespace>`. |
| **[Netplan](https://netplan.io/)** | Tool that configures networking with YAML files. Here it creates the bridge `br0` and each node's static IP (Phase 1). |
| **[NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/)** | Kubernetes rule that says which pods can talk to which, like a firewall inside the cluster. Enforced by the CNI. |
| **Nodo** | Each machine (physical or VM) that's part of a cluster and contributes CPU, memory, and disk. Here they are deborah, oliver, and invincible. |
| **[Ollama](https://ollama.com/)** | Server that runs language models (LLMs) on your own machines, without sending data outside. Used by Open WebUI and K8sGPT. |
| **[Open WebUI](https://openwebui.com/)** | Chat-style web UI to converse with Ollama models. |
| **[OpenEBS](https://openebs.io/)** | Storage for Kubernetes. Here LocalPV is used (StorageClass `openebs-hostpath`): volumes on the node's local disk, fast but without replicas. |
| **[OpenTofu](https://opentofu.org/)** / **Terraform** | Infrastructure-as-code tools: you describe resources in files and they create them. OpenTofu is the free fork of Terraform; here it configures the GitHub organization. |
| **Perfil** / **proyecto** / **storage pool** | Incus concepts. A profile is a reusable configuration for instances (disk, network), a project groups and isolates instances, and a storage pool is the disk location where instances and their snapshots are stored. |
| **Pipeline** | Automatic sequence of steps (validate, build, deploy) that runs when you change code. |
| **Playbook** | Ansible YAML file with the ordered list of tasks applied to a group of machines (e.g. `playbook-k3s.yml` installs K3s). |
| **Pod** | The minimum unit that runs in Kubernetes: one or more containers sharing network and storage. If a pod dies, Kubernetes creates another. |
| **port-forward** | `kubectl port-forward` opens a temporary tunnel from your computer to an internal cluster service; that's why some URLs are `http://127.0.0.1:<puerto>`. |
| **Quórum** | Minimum majority of cluster members that must be alive and in agreement to continue making decisions. With 3 voters, 2 must stay up. That's why Incus, with 4 members, lets only 3 vote in its database: the fourth (`eve`) stays as reserve and replaces the voter that falls. |
| **Regla de alerta** | Condition on metrics (e.g. "disk over 90% for 10 min") that, if met, triggers an alert. Evaluated by vmalert. |
| **[Renovate](https://docs.renovatebot.com/)** | Bot that checks for new versions of components and opens a PR to update them. |
| **Réplica** | Identical copy of a pod or volume kept alongside the original to tolerate failures. |
| **Retención** | How long data is kept before deletion (e.g. 30 days of logs in VictoriaLogs). |
| **Rol** (Ansible) | Reusable package of tasks, templates and variables with a single purpose, stored in `ansible/roles/` (e.g. `netplan_bridge`). Playbooks combine several roles. |
| **Rollout** / **rollback** | Rollout is deploying or restarting a version gradually (`kubectl rollout restart`); rollback is reverting to the previous version if something failed. |
| **[Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)** | Controller that decrypts inside the cluster the encrypted secrets (`SealedSecret`). This way you can store them in Git: only the cluster has the key. |
| **[Secret](https://kubernetes.io/docs/concepts/configuration/secret/)** | Kubernetes resource for sensitive data (passwords, tokens). Note: by default it's only base64 encoded, not encrypted; that's why here it's encrypted before pushing to Git. |
| **[Service](https://kubernetes.io/docs/concepts/services-networking/service/)** | Stable address to reach a group of pods. `ClusterIP` is internal only, `NodePort` opens a port on each node and `LoadBalancer` requests a LAN IP (provided by MetalLB). |
| **Snapshot** | Snapshot of a disk or instance state at a given moment, to which you can revert if something goes wrong. Does not replace a backup on another machine. |
| **Sonda** | Automated check that visits a URL periodically to know if it responds (done by blackbox-exporter). |
| **[StorageClass](https://kubernetes.io/docs/concepts/storage/storage-classes/)** | "Type" of disk that a PVC can request. Here there are `openebs-hostpath` (local, default) and `longhorn-mixto` (with replicas). |
| **sudo** | Command to run something as administrator (root) on Linux. |
| **Sync** / **Synced** / **OutOfSync** / **Healthy** | Argo CD states. Syncing (sync) is applying to the cluster what Git says; Synced means they already match, OutOfSync that there are pending differences and Healthy that resources also work properly. |
| **[systemd](https://systemd.io/)** / **timer** | systemd starts and monitors Linux services (like `k3s` or `incus`). A timer is its way of scheduling periodic tasks, similar to cron. |
| **Token** | Secret key (a long string) that identifies a program or person to a service, instead of username and password. Usually sent in the HTTP `Authorization: Bearer …` header. |
| **[Traefik](https://doc.traefik.io/traefik/)** | Ingress proxy that K3s installs by default. Here it's disabled and remains as an alternative to Kong. |
| **[vCluster](https://www.vcluster.com/docs)** | Virtual Kubernetes cluster running inside a namespace of another cluster: each team gets theirs without new machines (Phase 5). |
| **[VictoriaMetrics](https://docs.victoriametrics.com/)** / **vmagent** / **vmalert** | VictoriaMetrics is the HomeLab metrics database, Prometheus-compatible. vmagent collects metrics (scrape) and vmalert evaluates alert rules and passes them to Alertmanager. |
| **Volumen** | Disk space mounted in a pod to store data that must survive a restart. Requested by a PVC and provided by a StorageClass. |
| **Webhook** | URL to which a system sends an automatic message when something happens. Here alerts arrive at Discord via webhooks. |
