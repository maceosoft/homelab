# Glossary

The technical terms used in this documentation, in two tables: [acronyms and
abbreviations](#acronyms-and-abbreviations) and [concepts and tools](#concepts-and-tools).
On any page, underlined acronyms show their meaning when you hover over them
with the mouse, and the first time they appear on each page, their meaning is
given in parentheses.

## Acronyms and abbreviations

| Acronym | Meaning | What it is |
|---|---|---|
| **ACL** | Access Control List | Access control list: who can query a service (in BIND, a `lan` list could restrict queries to certain networks; in this HomeLab, DNS is open to the whole network). |
| **API** | Application Programming Interface | Interface through which a program exposes operations to others (e.g. the Kubernetes API on :6443). |
| **ARC** | [Actions Runner Controller](https://github.com/actions/actions-runner-controller) | Controller that runs GitHub Actions runners inside Kubernetes. |
| **ARM64** | 64-bit ARM architecture | CPU architecture of the Orange Pi (deborah); the other nodes are x86_64. |
| **ARP** | Address Resolution Protocol | Protocol that translates IPs to MAC addresses on the local network. |
| **BD** | database | Where a service stores its data; in the HomeLab, dqlite (Incus), SQLite (K3s), and the VictoriaMetrics and VictoriaLogs volumes. |
| **BGP** | Border Gateway Protocol | Routing protocol; MetalLB/Calico can announce IPs via BGP (L2 is used here). |
| **BIND** | [Berkeley Internet Name Domain](https://www.isc.org/bind/) | DNS server that resolves the HomeLab's internal zones. |
| **BPF** | [Berkeley Packet Filter](https://ebpf.io/) | Linux kernel technology (eBPF) that Cilium uses for networking. |
| **C4** | [C4 model](https://c4model.com/) | Way of drawing architecture at 4 levels: context, containers, components, and deployment. |
| **CA** | certificate authority | Entity that signs TLS certificates. |
| **CAPI** | [Cluster API](https://cluster-api.sigs.k8s.io/) | Kubernetes project for creating and managing clusters declaratively. |
| **CAPN** | [Cluster API Provider for Incus](https://capn.linuxcontainers.org/) | Cluster API provider that creates the nodes of a Kubernetes cluster as Incus instances. |
| **CI** | continuous integration | Automatically building and testing code on every change (GitHub Actions). |
| **CIDR** | Classless Inter-Domain Routing | IP range notation, e.g. 10.42.0.0/16. |
| **CIFS** | Common Internet File System | Windows shared folder protocol (SMB). |
| **CINC** | [CINC Is Not Chef](https://cinc.sh/) | Free distribution of Chef. |
| **CIS** | [Center for Internet Security](https://www.cisecurity.org/benchmark/kubernetes) | Organization that publishes hardening guides (CIS Benchmarks). |
| **CLI** | command-line interface | Tool used from the terminal (e.g. incus, kubectl). |
| **CNCF** | [Cloud Native Computing Foundation](https://www.cncf.io/) | Foundation that hosts Kubernetes and related projects. |
| **CNI** / CNIs | [Container Network Interface](https://www.cni.dev/) | Plugin that provides networking to Kubernetes pods (Flannel, Calico, Cilium…). |
| **CP** | control plane | Part of Kubernetes that manages the cluster (API server, scheduler, etcd). |
| **CPU** | central processing unit |  |
| **CR** / CRs | [Custom Resource](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) | Kubernetes object defined by an operator (e.g. a SUC Plan). |
| **CRD** / CRDs | [Custom Resource Definition](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) | Definition of a new object type in Kubernetes (installed by an operator, e.g. the SUC). |
| **CSR** | [Certificate Signing Request](https://cert-manager.io/docs/usage/certificaterequest/) | Request to sign a certificate: it carries the public key and the names (SANs), never the private key. This is how the Incus S3 certificate is signed without the key ever leaving the node. |
| **CSV** | Comma-Separated Values | Plain-text data file where columns are separated by commas. |
| **Dex** | [Dex](https://dexidp.io/docs/) | The HomeLab's OIDC identity provider: lets you log in to Argo CD, Grafana, Open WebUI, and SSH with your GitHub account (team `devops`). |
| **DHCP** | Dynamic Host Configuration Protocol | Protocol the router uses to assign IPs automatically. |
| **DMZ** | demilitarized zone | Router option that exposes a device directly to the internet. |
| **DNS** | Domain Name System | System that translates names (argocd.homelab.local) to IPs. |
| **DR** | disaster recovery | How to bring a service back up after losing it. |
| **DTB** | Device Tree Blob | Binary description of the hardware that the kernel reads at boot on ARM boards like the Orange Pi. |
| **eBPF** | [extended Berkeley Packet Filter](https://ebpf.io/) | Programs that run inside the Linux kernel; Cilium uses them for networking and policies. |
| **eMMC** | embedded MultiMediaCard | Flash storage soldered to the board; it is deborah's disk and has no SMART. |
| **EOL** | End Of Life | End of life of a component (on the eMMC, a warning that few spare blocks remain). |
| **ESO** | [External Secrets Operator](https://external-secrets.io/) | Kubernetes operator that syncs secrets from external managers. |
| **etcd** | [etcd](https://etcd.io/) | Distributed database where Kubernetes stores its state; K3s can integrate it into the server (embedded etcd). |
| **FRR** | [Free Range Routing](https://frrouting.org/) | Routing software that MetalLB uses to speak BGP; its management port is `2623`. |
| **FTP** | File Transfer Protocol | Protocol for uploading files to hosting (cPanel); also FTPS/SFTP. |
| **GPU** | graphics processing unit | Card or chip designed for parallel computation; it accelerates AI models. The Pi in this HomeLab doesn't use one: the models run on the CPU. |
| **HA** | high availability | Design that keeps a service running if a node goes down. |
| **HDD** | Hard Disk Drive | Mechanical hard drive. |
| **HDMI** | High-Definition Multimedia Interface | Video output; useful for viewing a node's console when the network doesn't respond. |
| **HTTP** | Hypertext Transfer Protocol |  |
| **HTTPS** | secure HTTP (over TLS) |  |
| **IA** | artificial intelligence | Programs that answer questions, summarize texts, or generate exercises; here they serve as a tutor for studying the guide (see [Learn with AI](aprende.md)). |
| **IdP** | Identity Provider | The system that verifies who you are (in the HomeLab, GitHub through Dex). |
| **Incus** | [Incus](https://linuxcontainers.org/incus/) | Container and virtual machine manager (community fork of LXD); it hosts the instances where the HomeLab nodes run. |
| **IP** / IPs | IP address | Address of a device on the network (Internet Protocol). |
| **JEDEC** | Joint Electron Device Engineering Council | Body that standardizes memory; it defines the eMMC wear fields. |
| **journald** | [journald](https://www.freedesktop.org/software/systemd/man/latest/systemd-journald.service.html) | systemd service that stores the logs of each node's services; Vector reads them from there. |
| **JSON** | JavaScript Object Notation | Text format for structured data. |
| **K3s** | [lightweight Kubernetes distribution](https://k3s.io/) | Kubernetes packaged as a single binary, designed for edge and HomeLabs. |
| **K8s** | [Kubernetes](https://kubernetes.io/) | Abbreviation of Kubernetes: the K, the 8 letters in the middle, and the s. |
| **KIC** | [Kong Ingress Controller](https://developer.konghq.com/kubernetes-ingress-controller/) | Kong controller for Kubernetes; here it implements Gateway API. |
| **Kubernetes** | [Kubernetes](https://kubernetes.io/) (K8s) | Platform that orchestrates containers: it decides which node each pod runs on, restarts it if it fails, and provides networking and storage. In this HomeLab it runs as K3s. |
| **KVM** | [Kernel-based Virtual Machine](https://linux-kvm.org/) | Hardware virtualization built into the Linux kernel; Incus VMs use it. |
| **L2** | OSI layer 2 | Data link layer of the OSI model: traffic within the same local network (MAC, ARP). |
| **L3** | OSI layer 3 | Network layer of the OSI model: IPs and routing. |
| **L7** | OSI layer 7 | Application layer of the OSI model: HTTP and similar. |
| **LAN** | local network | Local Area Network: the home network (192.168.20.0/22). |
| **launchd** | [launchd](https://support.apple.com/guide/terminal/apda7b3d2a58-1d40-4d2f-a5d8-9b3a2fd3f36d/mac) | macOS service manager (equivalent to systemd); it socket-activates the Mac's Ollama only when a request arrives. |
| **LB** | load balancer | Kubernetes LoadBalancer-type Service (provided by MetalLB). |
| **LLM** | Large Language Model | The type of AI that understands and writes text (here, the Ollama models). |
| **LogsQL** | [LogsQL](https://docs.victoriametrics.com/victorialogs/logsql/) | VictoriaLogs query language, the one you write in Grafana → Explore. |
| **LVM** | Logical Volume Manager | Linux logical volume manager. |
| **LXC** | [Linux Containers](https://linuxcontainers.org/lxc/) | Full system containers; Incus uses them as instances. |
| **LXD** | [LXD](https://canonical.com/lxd) | Container and VM manager of which Incus is a community fork. |
| **MAC** | MAC address (Media Access Control) | Unique identifier of a network card; the router uses it to always reserve the same IP for a device. |
| **MCP** | [Model Context Protocol](https://modelcontextprotocol.io/) | Standard for giving tools to an AI model (here, read-only queries to the cluster). |
| **MD5** | Message-Digest 5 | Hash algorithm that BGP used to authenticate sessions between routers; here BGP runs without it. |
| **NAT** | Network Address Translation | Address translation performed by the router between the local network and the internet. |
| **NFS** | Network File System | Network shared-folder protocol on Linux. |
| **nftables** | [nftables](https://wiki.nftables.org/) | Linux kernel firewall used by the `host_firewall` role on each node. |
| **NIC** | network card | Network Interface Card. |
| **NRPT** | [Name Resolution Policy Table](https://learn.microsoft.com/en-us/powershell/module/dnsclient/add-dnsclientnrptrule) | Windows table that sends queries for a DNS zone to a specific server; this is how `homelab.local` is resolved with the BIND server at `deborah` without changing the DNS of the whole machine. |
| **NTP** | [Network Time Protocol](https://www.ntp.org/) | Protocol that synchronizes the clocks of machines; without it, TLS certificates may look "not yet valid". |
| **NVMe** | PCIe SSD drive | Non-Volatile Memory Express: high-speed SSD drives. |
| **NXDOMAIN** | [Non-Existent Domain](https://www.rfc-editor.org/rfc/rfc8020) | DNS server response saying the name does not exist; the router returns it for `homelab.local`, which is why pods use only BIND. |
| **OAuth** | [Open Authorization](https://oauth.net/2/) | Standard that lets an application act with the user's permission without knowing their password; OIDC is built on top of it. |
| **oauth2-proxy** | [oauth2-proxy](https://oauth2-proxy.github.io/oauth2-proxy/) | Proxy that puts the Dex login in front of a web interface that has no login of its own. |
| **OCI** | [Open Container Initiative](https://opencontainers.org/) | Standard for images and registries; ARC and NGINX Gateway Fabric publish their Helm chart in an OCI registry. |
| **OIDC** | [OpenID Connect](https://openid.net/developers/how-connect-works/) | Login protocol on top of OAuth 2.0; Dex uses it for the GitHub login. |
| **Open Terminal** | [Open Terminal](https://docs.openwebui.com/features/open-terminal) | Terminal with code execution that Open WebUI uses as an assistant tool; it runs isolated in the `ai-sandbox` namespace. |
| **OpenPubkey** | [OpenPubkey](https://github.com/openpubkey/openpubkey) | Project that turns an OIDC login into a short-lived SSH key; [opkssh](https://github.com/openpubkey/opkssh) uses it to log in to hosts with the Dex identity. |
| **OS** | operating system | Operating System. |
| **OVN** | [Open Virtual Network](https://www.ovn.org/) | Software-defined virtual network that Incus can use. |
| **OVS** | [Open vSwitch](https://www.openvswitch.org/) | Virtual switch that OVN uses to connect Incus instances. |
| **PAT** | [Personal Access Token](https://docs.github.com/es/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) | Personal GitHub token that replaces the password in the API and the CLI. |
| **PDB** | [PodDisruptionBudget](https://kubernetes.io/docs/tasks/run-application/configure-pdb/) | Kubernetes limit on how many pods of an application can be down at the same time during a node drain. |
| **PHP** | [PHP: Hypertext Preprocessor](https://www.php.net/) | Programming language for web applications; the ARC `arc-php-84` scale set comes with it preinstalled (version 8.4). |
| **PKCE** | [Proof Key for Code Exchange](https://oauth.net/2/pkce/) | OAuth extension for public clients (no secret), such as `incus-ui` and `opkssh` in Dex. |
| **PR** / PRs | pull request | A change request on GitHub. |
| **PSA** | [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) | Kubernetes control that applies the Pod Security Standards levels to each namespace (`warn`, `audit` or `enforce`). |
| **PSS** | [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/) | Kubernetes security levels for pods (privileged, baseline, restricted). |
| **PVC** / PVCs | [PersistentVolumeClaim](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) | A pod's request for persistent storage in Kubernetes. |
| **RAG** | Retrieval-Augmented Generation | Giving the model your own documents so it answers from them instead of making things up (here, the HomeLab documentation). |
| **RAM** | RAM | A machine's working memory. |
| **RBAC** | [Role-Based Access Control](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) | Role-based access control: what each user or service account is allowed to do. |
| **RWX** | ReadWriteMany | Access mode for a volume that several pods can mount at the same time, even on different nodes. |
| **S3** | [Simple Storage Service](https://linuxcontainers.org/incus/docs/main/howto/storage_buckets/) | Object storage protocol (buckets) created by Amazon. Incus offers it for its buckets; here it stores the PostgreSQL backups. |
| **SAN** | Subject Alternative Name | Extra name or IP that a TLS certificate accepts (singular of SANs). |
| **SANs** | Subject Alternative Names | Extra names and IPs that a TLS certificate accepts. |
| **SATA** | Serial ATA | Interface for 2.5-inch disks and SSDs (invincible and oliver). |
| **SBC** | Single Board Computer | A computer on a single board, such as the Orange Pi 5 Plus. |
| **SD** | Secure Digital | Memory card; some ARM boards boot from it. |
| **SDK** | Software Development Kit | Library for using a service from code (e.g. the 1Password SDK). |
| **SMART** | Self-Monitoring, Analysis and Reporting Technology | Self-diagnostics built into disks and SSDs; warns you before they fail. |
| **SO** | operating system |  |
| **SOPS** | [Secrets OPerationS](https://github.com/getsops/sops) | Tool for encrypting secrets inside YAML/JSON files. |
| **SPDK** | [Storage Performance Development Kit](https://spdk.io/) | Longhorn v2 storage engine (not used here). |
| **SPI** | Serial Peripheral Interface | Bus for small chips; on the Orange Pi, the SPI flash memory holds the bootloader. |
| **SQLite** | [SQLite](https://www.sqlite.org/) | Single-file database; it is the default datastore for K3s with a single server. |
| **SSD** | solid-state drive |  |
| **SoC** | system on chip | Chip that combines CPU, graphics and other components; deborah's RK3588 is one. |
| **SSH** | Secure Shell | Protocol for connecting to another machine through an encrypted terminal. |
| **SSL** | Secure Sockets Layer | Predecessor of TLS; the name is still used when talking about certificates and encrypted connections. |
| **SSO** | single sign-on | Single Sign-On: logging in to several services with the same account (here, GitHub via Dex). |
| **SUC** | [System Upgrade Controller](https://github.com/rancher/system-upgrade-controller) | Rancher controller that upgrades K3s node by node. |
| **T2** | [Apple T2 chip](https://wiki.t2linux.org/) | Security coprocessor in 2018-2020 Intel Macs; it handles the keyboard, trackpad, audio and Touch ID, and on Linux it requires the `linux-t2` kernel (`eve` node). |
| **TCP** | Transmission Control Protocol | Connection-oriented transport protocol with ordered delivery; HTTP, TLS and SSH run on top of it. |
| **TLS** | Transport Layer Security | Connection encryption (the S in HTTPS). |
| **TTL** | Time To Live | How long a piece of data is cached before it is requested again. |
| **UDP** | User Datagram Protocol | Connectionless transport protocol; used, for example, by DNS and VXLAN. |
| **UEFI** | Unified Extensible Firmware Interface | Boot firmware of modern machines (replaces the BIOS). |
| **UI** | user interface | Web or graphical interface of a tool. |
| **URI** / URIs | Uniform Resource Identifier | Identifier of a resource; a URL is a type of URI. |
| **URL** / URLs | web address | Uniform Resource Locator. |
| **USB** | Universal Serial Bus |  |
| **UUID** | Universally Unique Identifier | 128-bit unique identifier; Linux uses it to name disks and partitions. |
| **Vector** | [Vector](https://vector.dev/) | Log collector that runs on every node and ships logs to VictoriaLogs. |
| **VictoriaLogs** | [VictoriaLogs](https://docs.victoriametrics.com/victorialogs/) | The HomeLab's log database (30-day retention); queried from Grafana. |
| **VIP** | virtual IP | Virtual IP: an IP that doesn't belong to a fixed machine and can move between nodes (kube-vip, MetalLB). |
| **VLAN** / VLANs | virtual local network | Virtual LAN: splitting one physical network into several logical networks. |
| **VM** / VMs | virtual machine | Virtual machine. |
| **VPN** | virtual private network | Virtual Private Network: encrypted access to your home network from outside. |
| **VXLAN** | Virtual Extensible LAN | Layer 2 network encapsulated over UDP; Flannel and Calico use it to connect pods across nodes. |
| **WAL** | [Write-Ahead Log](https://www.postgresql.org/docs/current/wal-intro.html) | Log where PostgreSQL records every change before applying it. Archiving it continuously lets you restore the database to any point in time. |
| **YAML** | YAML Ain't Markup Language | Text configuration format used by Kubernetes and Ansible. |

## Concepts and tools

Terms the guide uses without explaining them each time: Kubernetes components, HomeLab tools and operations jargon. If a word slows you down while reading, look it up here.

| Term | What it is |
|---|---|
| **[1Password](https://1password.com/)** | Password manager. Here it is the vault where the HomeLab's real secrets live (keys, tokens, GitHub Apps); the scripts read them with its SDK. |
| **[age](https://github.com/FiloSottile/age)** | Simple key-based encryption tool; SOPS uses it to encrypt the repo's secrets files. |
| **[Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)** | Receives alerts, groups them, deduplicates them, and sends them to their destination; here, to Discord channels. |
| **[Ansible](https://docs.ansible.com/)** | Tool that configures servers over SSH from YAML files. Here it prepares the nodes and installs the network, Incus, and K3s (Phases 0 to 3). |
| **Application** / **ApplicationSet** | Argo CD resources. An Application says which Git folder to deploy and to which cluster; an ApplicationSet generates many Applications from a template (here the `homelab` ApplicationSet creates one Application for each `bootstrap/components/` file in the `gitops` repo). |
| **apt** | Debian's package manager: installs and updates system software. |
| **[Argo CD](https://argo-cd.readthedocs.io/)** | The HomeLab's GitOps tool: it watches the `gitops` repo and applies its changes to the K3s cluster. It has a web UI where you can see the status of each application. |
| **Bootstrap** | The initial startup: the first manual steps that leave a system ready to manage itself. Here Ansible installs the basics and then Argo CD takes over. |
| **Bridge** | Virtual network interface that works like a switch. The `br0` bridge connects VMs and containers to the LAN as if they were just another machine. |
| **[Calico](https://docs.tigera.io/calico/)** | The cluster's CNI: connects pods across nodes and enforces NetworkPolicies. |
| **[cert-manager](https://cert-manager.io/)** | Automatically issues and renews TLS certificates inside Kubernetes. Here they are signed by the HomeLab's own CA for the `*.homelab.local` domains. |
| **[CloudNativePG](https://cloudnative-pg.io/)** | Kubernetes operator that creates and manages PostgreSQL clusters (instances, users, backups). Here it runs the platform's shared PostgreSQL. |
| **[Cilium](https://cilium.io/)** | eBPF-based CNI. In the guide it appears as an alternative to Calico. |
| **Cluster** | Group of machines that work together as if they were a single system. In this HomeLab there are two on the same 4 nodes: the Incus one and the K3s one. |
| **Container** | Isolated process that brings everything it needs to run but shares the host's kernel; that is why it is lighter than a VM. Incus runs system containers (LXC) and Kubernetes runs application containers inside pods. |
| **Control plane** / **worker** | The control plane is the cluster's "brain": it stores the state and decides which node runs what (here it lives on deborah). Workers only run the applications; K3s calls them *agents* and the control plane the *server*. |
| **Controller** / **operator** | A controller is a cluster program that watches resources and acts until the actual state matches the desired state. An operator is a controller that manages a specific application with its own CRDs (e.g. VictoriaMetrics'). In the guide, "operator" is also sometimes the person who administers the HomeLab. |
| **Cordon** / **drain** | `kubectl cordon` marks a node so it doesn't receive new pods; `kubectl drain` also moves the pods it already has to other nodes. You do this before rebooting or patching a node, and `uncordon` re-enables it. |
| **[CoreDNS](https://coredns.io/)** | Kubernetes' internal DNS: resolves the names of Services and pods inside the cluster. |
| **CronJob** | Kubernetes task that runs on its own on a fixed schedule, like a Linux cron. |
| **DaemonSet** | Kubernetes resource that places a copy of a pod on every node. Vector, which collects the logs, runs this way. |
| **Dashboard** | Grafana panel with several graphs on a topic, e.g. "HomeLab / Ollama". |
| **[Debian](https://www.debian.org/)** | The Linux distribution installed on all four nodes. |
| **Deployment** | Kubernetes resource that keeps N copies (replicas) of a pod running and replaces them if they fail. |
| **[dqlite](https://dqlite.io/)** | Distributed SQLite database where Incus stores the cluster state, replicated across the members: 3 vote and 1 stays on standby. |
| **Docker** | Tool for building and running containers on a computer ([docker.com](https://www.docker.com/)). In the HomeLab it is used by the ARC runners to build images. |
| **Drift** / **self-heal** | Drift is the difference between what Git says and what actually exists in the cluster. With self-heal, Argo CD corrects it automatically. |
| **Exporter** | Small program that publishes metrics so vmagent can collect them: node-exporter provides each node's system metrics and blackbox-exporter probes URLs and DNS from the outside. |
| **Firewall** | Filter that decides which network traffic is allowed and which is blocked (on Linux, ufw or nftables). |
| **[Flannel](https://github.com/flannel-io/flannel)** | The CNI that K3s ships with by default. This HomeLab replaces it with Calico. |
| **Fork** | Copy of a project that continues to be developed separately from the original; e.g. Incus is a fork of LXD and OpenTofu is a fork of Terraform. |
| **[Gateway API](https://gateway-api.sigs.k8s.io/)** / **HTTPRoute** | The Kubernetes standard for exposing web services externally; it replaces Ingress. The Gateway is the entry point (here implemented by Kong) and each HTTPRoute says which domain or path goes to which Service. |
| **[GitHub Actions](https://docs.github.com/actions)** / **workflow** / **runner** | GitHub Actions is GitHub's CI: it runs tasks when you push or open a PR. A workflow is the YAML file that describes those tasks and the runner is the machine that runs them; here the runners are cluster pods, created by ARC. |
| **[GitHub App](https://docs.github.com/apps)** | Application identity on GitHub with scoped permissions, for automating without using a personal account (used by ARC, Argo CD, and OpenTofu). |
| **[GitOps](https://opengitops.dev/)** | A way of operating where Git is the source of truth: you change a file in the repo and a tool (here Argo CD) makes the cluster match it. It's also the name of the `maceosoft/gitops` repo. |
| **[Grafana](https://grafana.com/docs/grafana/latest/)** | The web UI where you view metrics in dashboards and search logs (in "Explore"). |
| **[HAProxy](https://www.haproxy.org/)** | TCP/HTTP proxy and load balancer. On `invincible` it publishes the Incus S3 endpoint with a certificate from the HomeLab CA (role `incus_s3`). |
| **group_vars** / **host_vars** | Ansible folders holding the variables for a group of machines or for one specific machine. |
| **Hardening** | Strengthening a system's security: closing ports, removing unneeded access, and applying secure configurations. |
| **[healthchecks.io](https://healthchecks.io/)** | External service that expects a periodic notification ("ping") and alerts if it stops arriving. It checks that the monitoring itself is still alive. |
| **[Helm](https://helm.sh/)** / **chart** / **values** | Helm is the Kubernetes package manager. A chart is a package of templated manifests, and values are the parameters that tune it. Argo CD installs several HomeLab components as charts. |
| **Idempotent** | You can run it several times and get the same result: if something is already done, it doesn't repeat it or break it. Ansible playbooks are designed this way. |
| **Image** | Read-only template from which a container or VM is created (e.g. `bitnami/kubectl`). It is downloaded from a *registry*. |
| **[Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)** | The classic way to expose HTTP services in Kubernetes. The HomeLab doesn't use it (it uses Gateway API), but it appears for comparison. |
| **Instance** | In Incus, each container or VM it creates. The Kubernetes nodes of CAPN and vCluster are instances. |
| **Inventory** | List of the machines Ansible manages, with their groups and variables. |
| **[K8sGPT](https://k8sgpt.ai/)** | Tool that analyzes cluster problems and explains them in natural language using an LLM (here, from Ollama). |
| **Kernel** | The core of the operating system, the part that talks directly to the hardware. Containers share the host's kernel. |
| **kind** | Kubernetes IN Docker ([kind.sigs.k8s.io](https://kind.sigs.k8s.io/)): spins up a Kubernetes cluster on your computer using Docker containers as nodes. Useful for practicing the guide without multiple machines. |
| **[Kong](https://developer.konghq.com/kubernetes-ingress-controller/)** | The cluster's HTTP/HTTPS entry point: it implements Gateway API (with KIC), receives traffic, and distributes it among the services. |
| **[kube-vip](https://kube-vip.io/)** | Puts a virtual IP (VIP) in front of the Kubernetes API so it doesn't depend on a single node. Optional here; not to be confused with MetalLB. |
| **[kubeconfig](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)** | File with the cluster's address and your credentials; kubectl uses it to know which cluster to connect to and as whom (here, `~/.kube/homelab-k3s.yaml`). |
| **[kubectl](https://kubernetes.io/docs/reference/kubectl/)** | The CLI for talking to Kubernetes: view pods, read logs, apply manifests, or restart things. |
| **kubelet** | Kubernetes agent that runs on each node and starts the pods the control plane assigns to it. |
| **[Kustomize](https://kustomize.io/)** | Tool that builds and tweaks YAML manifests by layering changes over a base, without templates. The `gitops` repo's pipeline uses it to validate it. |
| **Heartbeat** | Short signal that a machine sends at regular intervals to say "I'm still here". Each Ollama node sends one to the router every 60 seconds; if the router goes 3 heartbeats without hearing it (180 s), it considers the node down. |
| **[Longhorn](https://longhorn.io/)** | Distributed storage for Kubernetes: stores each volume with replicas across several nodes so data isn't lost if one goes down (StorageClass `longhorn-mixto`). |
| **Manifest** | YAML file that describes a Kubernetes resource the way you want it to exist. You tell it what you want, not how to do it; Argo CD applies them from Git. |
| **Merge** / **branch** | A branch is a separate line of changes in Git. Merging is combining it into `main`, usually when a PR is approved. |
| **[MetalLB](https://metallb.io/)** | Provides LAN IPs (pool `192.168.23.200–.220`) to LoadBalancer-type Services, something the provider does in the cloud. |
| **Metric** / **scrape** | A metric is a number measured over and over across time (e.g. CPU usage). A scrape is the periodic reading vmagent does of each service's metrics. |
| **Namespace** | Named space within the cluster that separates resources and permissions, like a folder (e.g. `ai`, `kong` or `arc-runners`). Almost every kubectl command takes `-n <namespace>`. |
| **[Netplan](https://netplan.io/)** | Tool that configures networking using YAML files. Here it creates the `br0` bridge and each node's static IP (Phase 1). |
| **[NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/)** | Kubernetes rule that defines which pods can talk to which, like a firewall inside the cluster. It is enforced by the CNI. |
| **Node** | Each machine (physical or VM) that is part of a cluster and contributes CPU, memory, and disk. Here they are deborah, oliver, and invincible. |
| **[Ollama](https://ollama.com/)** | Server that runs language models (LLMs) on your own machines, without sending data outside. Used by Open WebUI and K8sGPT. |
| **[Open WebUI](https://openwebui.com/)** | Chat-style web interface for talking to Ollama models. |
| **[OpenEBS](https://openebs.io/)** | Storage for Kubernetes. Here LocalPV is used (StorageClass `openebs-hostpath`): volumes on the node's local disk, fast but without replicas. |
| **[OpenTofu](https://opentofu.org/)** / **Terraform** | Infrastructure-as-code tools: you describe resources in files and they create them. OpenTofu is the open-source fork of Terraform; here it configures the GitHub organization. |
| **Profile** / **project** / **storage pool** | Incus concepts. A profile is a reusable configuration for instances (disk, network), a project groups and isolates instances, and a storage pool is the place on disk where instances and their snapshots are stored. |
| **Pipeline** | Automatic sequence of steps (validate, build, deploy) that runs when you change the code. |
| **Playbook** | Ansible YAML file with the ordered list of tasks applied to a group of machines (e.g. `playbook-k3s.yml` installs K3s). |
| **Pod** | The smallest unit Kubernetes runs: one or more containers that share network and storage. If a pod dies, Kubernetes creates another one. |
| **port-forward** | `kubectl port-forward` opens a temporary tunnel from your computer to an internal cluster service; that is why some URLs are `http://127.0.0.1:<puerto>`. |
| **Quorum** | Minimum majority of cluster members that must be alive and in agreement to keep making decisions. With 3 voters, 2 have to stay up. That is why Incus, with 4 members, lets only 3 vote in its database: the fourth (`eve`) stays in reserve and replaces the voter that goes down. |
| **Alert rule** | Condition on the metrics (e.g. "disk above 90% for 10 min") that triggers an alert when met. They are evaluated by vmalert. |
| **[Renovate](https://docs.renovatebot.com/)** | Bot that checks for new versions of the components and opens a PR to update them. |
| **Replica** | Identical copy of a pod or a volume that is kept alongside the original, to tolerate failures. |
| **Retention** | How long data is kept before being deleted (e.g. 30 days of logs in VictoriaLogs). |
| **Role** (Ansible) | Reusable package of tasks, templates, and variables with a single purpose, stored in `ansible/roles/` (e.g. `netplan_bridge`). Playbooks combine several roles. |
| **Rollout** / **rollback** | A rollout is deploying or restarting a version gradually (`kubectl rollout restart`); a rollback is returning to the previous version if something failed. |
| **[Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)** | Controller that decrypts encrypted secrets (`SealedSecret`) inside the cluster. This way you can store them in Git: only the cluster has the key. |
| **[Secret](https://kubernetes.io/docs/concepts/configuration/secret/)** | Kubernetes resource for sensitive data (passwords, tokens). Note: by default it is only base64-encoded, not encrypted; that is why here it is encrypted before being pushed to Git. |
| **[Service](https://kubernetes.io/docs/concepts/services-networking/service/)** | Stable address to reach a group of pods. `ClusterIP` is internal only, `NodePort` opens a port on every node, and `LoadBalancer` requests a LAN IP (provided by MetalLB). |
| **Snapshot** | Picture of the state of a disk or an instance at a given moment, which you can go back to if something goes wrong. It does not replace a backup on another machine. |
| **Probe** | Automatic check that visits a URL at regular intervals to find out whether it responds (done by blackbox-exporter). |
| **[StorageClass](https://kubernetes.io/docs/concepts/storage/storage-classes/)** | "Type" of disk that a PVC can request. Here there are `openebs-hostpath` (local, default) and `longhorn-mixto` (with replicas). |
| **sudo** | Command to run something as administrator (root) on Linux. |
| **Sync** / **Synced** / **OutOfSync** / **Healthy** | Argo CD states. Syncing is applying to the cluster what Git says; Synced means they already match, OutOfSync means there are pending differences, and Healthy means the resources are also working properly. |
| **[systemd](https://systemd.io/)** / **timer** | systemd starts and monitors Linux services (such as `k3s` or `incus`). A timer is its way of scheduling periodic tasks, similar to cron. |
| **Token** | Secret key (a long string) that identifies a program or person to a service, instead of a username and password. It is usually sent in the HTTP `Authorization: Bearer …` header. |
| **[Traefik](https://doc.traefik.io/traefik/)** | Ingress proxy that K3s installs by default. Here it is disabled and remains as an alternative to Kong. |
| **[vCluster](https://www.vcluster.com/docs)** | "Virtual" Kubernetes cluster that runs inside a namespace of another cluster: each team gets its own without new machines (Phase 5). |
| **[VictoriaMetrics](https://docs.victoriametrics.com/)** / **vmagent** / **vmalert** | VictoriaMetrics is the HomeLab's metrics database, Prometheus-compatible. vmagent collects the metrics (scrape), and vmalert evaluates the alert rules and passes them to Alertmanager. |
| **Volume** | Disk space mounted into a pod to store data that must survive a restart. It is requested by a PVC and provided by a StorageClass. |
| **Webhook** | URL to which a system sends an automatic message when something happens. Here, alerts reach Discord through webhooks. |
