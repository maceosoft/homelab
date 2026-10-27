# Glossary

The technical words in this documentation, in two tables: [acronyms and
abbreviations](#acronyms-and-abbreviations) and [concepts and tools](#concepts-and-tools).
On any page, underlined acronyms show their meaning on hover, and the first time
they appear on each page they include the meaning in parentheses.

## Acronyms and Abbreviations

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
| **K8s** | [Kubernetes](https://kubernetes.io/) | Abbreviation of Kubernetes: the K, the 8 letters in the middle and the s. |
| **KIC** | [Kong Ingress Controller](https://developer.konghq.com/kubernetes-ingress-controller/) | Kong controller for Kubernetes; here it implements Gateway API. |
| **Kubernetes** | [Kubernetes](https://kubernetes.io/) (K8s) | Platform that orchestrates containers: it decides which node runs each pod, restarts it if it fails and gives it networking and storage. In this homelab it runs as K3s. |
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

## Concepts and Tools

Terms the guide uses without explaining them every time: Kubernetes building blocks, homelab tools and operations
jargon. If a word slows you down while reading, look it up here.

| Term | What It Is |
|---|---|
| **[1Password](https://1password.com/)** | Password manager. Here it is the vault that holds the homelab's real secrets (keys, tokens, GitHub Apps); scripts read them with its SDK. |
| **[age](https://github.com/FiloSottile/age)** | Simple key-based encryption tool; SOPS uses it to encrypt the repo's secret files. |
| **Alert rule** | Condition on the metrics (e.g. "disk over 90 % for 10 min") that fires an alert when it holds. vmalert evaluates them. |
| **[Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)** | Receives alerts, groups them, avoids repeats and sends them to their destination; here, Discord channels. |
| **[Ansible](https://docs.ansible.com/)** | Tool that configures servers over SSH from YAML files. Here it prepares the nodes and installs the network, Incus and K3s (Phases 0 to 3). |
| **Application** / **ApplicationSet** | Argo CD resources. An Application says which Git folder to deploy and to which cluster; an ApplicationSet generates many Applications from a template (here `homelab-root` creates all the others). |
| **apt** | Debian's package manager: installs and updates system software. |
| **[Argo CD](https://argo-cd.readthedocs.io/)** | The homelab's GitOps tool: it watches the `gitops` repo and applies its changes to the K3s cluster. It has a web UI that shows the state of each application. |
| **Bootstrap** | The initial startup: the first manual steps that leave a system ready to manage itself. Here Ansible installs the basics and then Argo CD takes over. |
| **Bridge** | Virtual network interface that works like a switch. The `br0` bridge connects VMs and containers to the LAN as if they were one more machine. |
| **[Calico](https://docs.tigera.io/calico/)** | The cluster's CNI: it connects pods across nodes and enforces NetworkPolicies. |
| **[cert-manager](https://cert-manager.io/)** | Issues and renews TLS certificates inside Kubernetes on its own. Here the homelab's own CA signs them for the `*.homelab.local` domains. |
| **[Cilium](https://cilium.io/)** | eBPF-based CNI. The guide mentions it as an alternative to Calico. |
| **Cluster** | Group of machines that work together as if they were a single system. This homelab has two on the same 3 nodes: the Incus one and the K3s one. |
| **Container** | Isolated process that brings everything it needs to run but shares the host's kernel, which makes it lighter than a VM. Incus runs system containers (LXC) and Kubernetes runs application containers inside pods. |
| **Control plane** / **worker** | The control plane is the cluster's "brain": it stores the state and decides which node runs what (here it is on deborah). Workers only run the applications; K3s calls them *agents* and calls the control plane the *server*. |
| **Controller** / **operator** | A controller is a program in the cluster that watches resources and acts until the real state matches the desired one. An operator is a controller that manages a specific application through its own CRDs (e.g. the VictoriaMetrics one). In the guide, "operator" sometimes also means the person who runs the homelab. |
| **Cordon** / **drain** | `kubectl cordon` marks a node so it gets no new pods; `kubectl drain` also moves the pods it already has to other nodes. You do it before rebooting or patching a node, and `uncordon` enables it again. |
| **[CoreDNS](https://coredns.io/)** | Kubernetes' internal DNS: it resolves the names of Services and pods inside the cluster. |
| **CronJob** | Kubernetes task that runs by itself on a fixed schedule, like a Linux cron job. |
| **DaemonSet** | Kubernetes resource that puts one copy of a pod on every node. Vector, which collects the logs, runs this way. |
| **Dashboard** | Grafana panel with several charts about one topic, e.g. "HomeLab / Ollama". |
| **[Debian](https://www.debian.org/)** | The Linux distribution installed on the three nodes. |
| **Deployment** | Kubernetes resource that keeps N copies (replicas) of a pod running and replaces them if they fail. |
| **[dqlite](https://dqlite.io/)** | Distributed SQLite database where Incus stores the cluster state, replicated across the 3 nodes. |
| **Drift** / **self-heal** | Drift is the difference between what Git says and what is actually in the cluster. With self-heal, Argo CD fixes it on its own. |
| **Exporter** | Small program that publishes metrics for vmagent to collect: node-exporter provides each node's system metrics and blackbox-exporter tests URLs and DNS from the outside. |
| **Firewall** | Filter that decides which network traffic is allowed and which is blocked (on Linux, ufw or nftables). |
| **[Flannel](https://github.com/flannel-io/flannel)** | The CNI that K3s ships by default. This homelab replaces it with Calico. |
| **Fork** | Copy of a project that keeps being developed separately from the original; e.g. Incus is a fork of LXD and OpenTofu of Terraform. |
| **[Gateway API](https://gateway-api.sigs.k8s.io/)** / **HTTPRoute** | The Kubernetes standard for publishing web services to the outside; it replaces Ingress. The Gateway is the entry point (implemented here by Kong) and each HTTPRoute says which domain or path goes to which Service. |
| **[GitHub Actions](https://docs.github.com/actions)** / **workflow** / **runner** | GitHub Actions is GitHub's CI: it runs tasks when you push or open a PR. A workflow is the YAML file that describes those tasks and the runner is the machine that runs them; here the runners are pods in the cluster, created by ARC. |
| **[GitHub App](https://docs.github.com/apps)** | Application identity on GitHub with scoped permissions, used to automate without a personal account (ARC, Argo CD and OpenTofu use them). |
| **[GitOps](https://opengitops.dev/)** | Way of operating in which Git is the source of truth: you change a file in the repo and a tool (here Argo CD) makes the cluster match. It is also the name of the `maceosoft/gitops` repo. |
| **[Grafana](https://grafana.com/docs/grafana/latest/)** | The web UI where you view metrics in dashboards and search logs (in "Explore"). |
| **group_vars** / **host_vars** | Ansible folders with the variables for a group of machines or for one specific machine. |
| **Hardening** | Tightening a system's security: closing ports, removing unneeded access and applying secure settings. |
| **[healthchecks.io](https://healthchecks.io/)** | External service that expects a periodic "ping" and alerts if it stops arriving. It watches that the monitoring itself is still alive. |
| **Heartbeat** | Short message a machine sends every so often to say "I'm still here". Each Ollama node sends one to the router every 60 seconds; if the router misses 3 heartbeats (180 s), it considers the node off. |
| **[Helm](https://helm.sh/)** / **chart** / **values** | Helm is Kubernetes' package manager. A chart is a package of templated manifests and the values are the parameters that adjust it. Argo CD installs several homelab components as charts. |
| **Idempotent** | You can run it several times and the result is the same: if something is already done, it doesn't repeat it or break it. Ansible playbooks are designed this way. |
| **Image** | Read-only template from which a container or a VM is created (e.g. `bitnami/kubectl`). It is downloaded from a *registry*. |
| **[Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)** | The classic way to expose HTTP services in Kubernetes. The homelab doesn't use it (it uses Gateway API), but it comes up for comparison. |
| **Instance** | In Incus, each container or VM it creates. The Kubernetes nodes of CAPN and vCluster are instances. |
| **Inventory** | List of the machines Ansible manages, with their groups and variables. |
| **[K8sGPT](https://k8sgpt.ai/)** | Tool that analyzes cluster problems and explains them in natural language with an LLM (here, from Ollama). |
| **Kernel** | The core of the operating system, the part that talks directly to the hardware. Containers share the host's kernel. |
| **[Kong](https://developer.konghq.com/kubernetes-ingress-controller/)** | The cluster's HTTP/HTTPS entry point: it implements Gateway API (through KIC), receives the traffic and spreads it across the services. |
| **[kube-vip](https://kube-vip.io/)** | Puts a virtual IP (VIP) in front of the Kubernetes API so it doesn't depend on a single node. Optional here; don't confuse it with MetalLB. |
| **[kubeconfig](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)** | File with the cluster address and your credentials; kubectl uses it to know which cluster to connect to and as whom (here, `~/.kube/homelab-k3s.yaml`). |
| **[kubectl](https://kubernetes.io/docs/reference/kubectl/)** | The CLI for talking to Kubernetes: list pods, read logs, apply manifests or restart things. |
| **kubelet** | Kubernetes agent that runs on every node and starts the pods the control plane assigns to it. |
| **[Kustomize](https://kustomize.io/)** | Tool that builds and adjusts YAML manifests by layering changes over a base, without templates. The `gitops` repo pipeline uses it to validate the repo. |
| **[Longhorn](https://longhorn.io/)** | Distributed storage for Kubernetes: it keeps each volume with replicas on several nodes so no data is lost if one goes down (StorageClass `longhorn-mixto`). |
| **Manifest** | YAML file that describes a Kubernetes resource the way you want it to exist. You say what you want, not how to do it; Argo CD applies them from Git. |
| **Merge** / **branch** | A branch is a separate line of changes in Git. Merging joins it into `main`, usually when a PR is approved. |
| **[MetalLB](https://metallb.io/)** | Gives LAN IPs (pool `192.168.23.200–.220`) to Services of type LoadBalancer, something the provider does in the cloud. |
| **Metric** / **scrape** | A metric is a number measured over and over in time (e.g. CPU usage). A scrape is vmagent's periodic read of each service's metrics. |
| **Namespace** | Named space inside the cluster that separates resources and permissions, like a folder (e.g. `ai`, `kong` or `arc-runners`). Almost every kubectl command takes `-n <namespace>`. |
| **[Netplan](https://netplan.io/)** | Tool that configures the network from YAML files. Here it creates the `br0` bridge and each node's static IP (Phase 1). |
| **[NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/)** | Kubernetes rule that says which pods can talk to which, like a firewall inside the cluster. The CNI enforces it. |
| **Node** | Each machine (physical or VM) that is part of a cluster and contributes CPU, memory and disk. Here they are deborah, oliver and invincible. |
| **[Ollama](https://ollama.com/)** | Server that runs language models (LLMs) on your own machines, without sending data out. Open WebUI and K8sGPT use it. |
| **[Open WebUI](https://openwebui.com/)** | Chat-style web interface for talking to Ollama's models. |
| **[OpenEBS](https://openebs.io/)** | Storage for Kubernetes. Here LocalPV is used (StorageClass `openebs-hostpath`): volumes on the node's local disk, fast but without replicas. |
| **[OpenTofu](https://opentofu.org/)** / **Terraform** | Infrastructure-as-code tools: you describe resources in files and they create them. OpenTofu is the open-source fork of Terraform; here it configures the GitHub organization. |
| **Pipeline** | Automatic sequence of steps (validate, build, deploy) that runs when you change the code. |
| **Playbook** | Ansible YAML file with the ordered list of tasks applied to a group of machines (e.g. `playbook-k3s.yml` installs K3s). |
| **Pod** | The smallest unit Kubernetes runs: one or more containers that share network and storage. If a pod dies, Kubernetes creates another. |
| **port-forward** | `kubectl port-forward` opens a temporary tunnel from your computer to a service inside the cluster; that's why some URLs are `http://127.0.0.1:<port>`. |
| **Probe** | Automatic check that visits a URL every so often to see whether it responds (done by blackbox-exporter). |
| **Profile** / **project** / **storage pool** | Incus concepts. A profile is a reusable configuration for instances (disk, network), a project groups and isolates instances and a storage pool is the place on disk where instances and their snapshots are stored. |
| **Quorum** | Minimum majority of a cluster's members that must be alive and in agreement to keep making decisions. With 3 nodes, 2 must stay up; that's why Incus and K3s use three. |
| **[Renovate](https://docs.renovatebot.com/)** | Bot that checks for new versions of the components and opens a PR to update them. |
| **Replica** | Identical copy of a pod or a volume kept alongside the original to tolerate failures. |
| **Retention** | How long data is kept before it is deleted (e.g. 30 days of logs in VictoriaLogs). |
| **Role** (Ansible) | Reusable package of tasks, templates and variables with a single purpose, stored in `ansible/roles/` (e.g. `netplan_bridge`). Playbooks combine several roles. |
| **Rollout** / **rollback** | A rollout deploys or restarts a version gradually (`kubectl rollout restart`); a rollback goes back to the previous version if something failed. |
| **[Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)** | Controller that decrypts encrypted secrets (`SealedSecret`) inside the cluster. That way you can keep them in Git: only the cluster has the key. |
| **[Secret](https://kubernetes.io/docs/concepts/configuration/secret/)** | Kubernetes resource for sensitive data (passwords, tokens). Careful: by default it is only base64-encoded, not encrypted; that's why here it is encrypted before going into Git. |
| **[Service](https://kubernetes.io/docs/concepts/services-networking/service/)** | Stable address for reaching a group of pods. `ClusterIP` is internal only, `NodePort` opens a port on every node and `LoadBalancer` requests a LAN IP (MetalLB provides it). |
| **Snapshot** | Picture of the state of a disk or an instance at a given moment, which you can go back to if something goes wrong. It doesn't replace a backup on another machine. |
| **[StorageClass](https://kubernetes.io/docs/concepts/storage/storage-classes/)** | "Kind" of disk a PVC can request. Here there are `openebs-hostpath` (local, default) and `longhorn-mixto` (replicated). |
| **sudo** | Command to run something as administrator (root) on Linux. |
| **Sync** / **Synced** / **OutOfSync** / **Healthy** | Argo CD states. Syncing is applying what Git says to the cluster; Synced means they already match, OutOfSync that there are pending differences and Healthy that the resources also work fine. |
| **[systemd](https://systemd.io/)** / **timer** | systemd starts and watches Linux services (such as `k3s` or `incus`). A timer is its way of scheduling periodic tasks, similar to cron. |
| **Token** | Secret key (a long string) that identifies a program or person to a service instead of a username and password. It is usually sent in the HTTP header `Authorization: Bearer …`. |
| **[Traefik](https://doc.traefik.io/traefik/)** | Ingress proxy that K3s installs by default. Here it is disabled and kept as an alternative to Kong. |
| **[vCluster](https://www.vcluster.com/docs)** | "Virtual" Kubernetes cluster that runs inside a namespace of another cluster: each team gets its own without new machines (Phase 5). |
| **[VictoriaMetrics](https://docs.victoriametrics.com/)** / **vmagent** / **vmalert** | VictoriaMetrics is the homelab's metrics database, compatible with Prometheus. vmagent collects the metrics (scrape) and vmalert evaluates the alert rules and passes them to Alertmanager. |
| **Volume** | Disk space mounted into a pod to keep data that must survive a restart. A PVC requests it and a StorageClass provides it. |
| **Webhook** | URL that a system sends an automatic message to when something happens. Here alerts reach Discord through webhooks. |
