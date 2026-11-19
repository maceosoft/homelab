<!-- Acronym glossary: automatic tooltip on all pages (abbr).
     Added only at the end of each page (pymdownx.snippets.auto_append).
     When adding a new acronym, also add it to docs/glossary.md. -->

*[ACL]: Access Control List — Access control list: who can query a service (in BIND, a `lan` list could limit queries to certain networks; in this HomeLab DNS is open to the entire network).
*[AKS]: Azure Kubernetes Service — Microsoft Azure managed Kubernetes (has its own kubelogin, different from int128's).
*[API]: Application Programming Interface — Interface through which a program exposes operations to others (e.g. Kubernetes API on :6443).
*[ARC]: Actions Runner Controller — Controller that runs GitHub Actions runners inside Kubernetes.
*[ARM64]: 64-bit ARM architecture — CPU architecture of the Orange Pi (deborah); other nodes are x86_64.
*[ARP]: Address Resolution Protocol — Protocol that translates IPs to MAC addresses on the local network.
*[BD]: database
*[BGP]: Border Gateway Protocol — Routing protocol; MetalLB/Calico can advertise IPs via BGP (L2 is used here).
*[BIND]: Berkeley Internet Name Domain — DNS server that resolves HomeLab internal zones.
*[BPF]: Berkeley Packet Filter — Linux kernel technology (eBPF) used by Cilium for networking.
*[C4]: C4 model — Way to diagram architecture in 4 levels: context, containers, components, and deployment.
*[CA]: certificate authority — Entity that signs TLS certificates.
*[CAPI]: Cluster API — Kubernetes project to create and manage clusters declaratively.
*[CAPN]: Cluster API Provider for Incus — Cluster API provider that creates Kubernetes cluster nodes as Incus instances.
*[CI]: continuous integration — Build and test code automatically on every change (GitHub Actions).
*[CIDR]: Classless Inter-Domain Routing — IP range notation, e.g. 10.42.0.0/16.
*[CIFS]: Common Internet File System — Windows shared folders protocol (SMB).
*[CINC]: CINC Is Not Chef — Free distribution of Chef.
*[CIS]: Center for Internet Security — Organization that publishes hardening guides (CIS Benchmarks).
*[CLI]: command-line interface — Tool used from the terminal (e.g. incus, kubectl).
*[CNCF]: Cloud Native Computing Foundation — Foundation that hosts Kubernetes and related projects.
*[CNI]: Container Network Interface — Plugin that provides networking to Kubernetes pods (Flannel, Calico, Cilium…).
*[CNIs]: Container Network Interface — Plugin that provides networking to Kubernetes pods (Flannel, Calico, Cilium…).
*[CP]: control plane — Part of Kubernetes that manages the cluster (API server, scheduler, etcd).
*[CPU]: central processing unit
*[CR]: Custom Resource — Kubernetes object defined by an operator (e.g. a SUC Plan).
*[CRs]: Custom Resource — Kubernetes object defined by an operator (e.g. a SUC Plan).
*[CRD]: Custom Resource Definition — Definition of a new object type in Kubernetes (installed by an operator, e.g. SUC).
*[CRDs]: Custom Resource Definition — Definition of a new object type in Kubernetes (installed by an operator, e.g. SUC).
*[CSR]: Certificate Signing Request — Certificate signing request: contains the public key and names, never the private key.
*[CSV]: Comma-Separated Values — Text data file where columns are separated by commas.
*[Dex]: Dex — HomeLab OIDC identity provider: allows signing in with GitHub account (team `devops`) to Argo CD, Grafana, Open WebUI, and SSH.
*[DHCP]: Dynamic Host Configuration Protocol — Protocol by which the router assigns IPs automatically.
*[DMZ]: demilitarized zone — Router option that exposes a machine directly to the internet.
*[DNS]: Domain Name System — System that translates names (argocd.homelab.local) to IPs.
*[DR]: disaster recovery — Disaster recovery: how to bring a service back up after losing it.
*[DTB]: Device Tree Blob — Binary hardware description that the kernel reads at boot on ARM boards like the Orange Pi.
*[eBPF]: extended Berkeley Packet Filter — Programs that run inside the Linux kernel; Cilium uses them for networking and policies.
*[eMMC]: embedded MultiMediaCard — Flash storage soldered to the board; it's deborah's disk and has no SMART.
*[EOL]: End Of Life — End of life of a component (in eMMC, warning that few spare blocks remain).
*[ESO]: External Secrets Operator — Kubernetes operator that syncs secrets from external managers.
*[etcd]: etcd — Distributed database where Kubernetes stores its state; K3s can embed it in the server (embedded etcd).
*[FRR]: Free Range Routing — Routing software that MetalLB uses to speak BGP; its management port is `2623`.
*[FTP]: File Transfer Protocol — Protocol for uploading files to hosting (cPanel); also FTPS/SFTP.
*[GPU]: graphics processing unit — Card or chip designed for parallel calculations; accelerates AI models. This HomeLab's Pi doesn't use it: models run on CPU.
*[HA]: high availability — Design for a service to keep running if a node fails.
*[HDD]: Hard Disk Drive — Mechanical hard drive.
*[HDMI]: High-Definition Multimedia Interface — Video output; used to view a node's console when network is unresponsive.
*[HTTP]: Hypertext Transfer Protocol
*[HTTPS]: Secure HTTP (over TLS)
*[IA]: artificial intelligence — Programs that answer questions, summarize text, or generate exercises; here they serve as tutors for studying the guide.
*[IdP]: Identity Provider — Identity provider: the system that verifies who you are (in the HomeLab, GitHub via Dex).
*[Incus]: Incus — Container and virtual machine manager (community fork of LXD); hosts the instances where HomeLab nodes run.
*[IP]: IP address — Address of a machine on the network (Internet Protocol).
*[IPs]: IP address — Address of a machine on the network (Internet Protocol).
*[JEDEC]: Joint Electron Device Engineering Council — Organization that standardizes memory; defines eMMC wear fields.
*[journald]: journald — systemd service that stores logs from each node's services; Vector reads from there.
*[JSON]: JavaScript Object Notation — Text format for structured data.
*[K3s]: lightweight Kubernetes distribution — Kubernetes packaged in a single binary, designed for edge and HomeLabs.
*[K8s]: Kubernetes — Container orchestration platform.
*[KIC]: Kong Ingress Controller — Kong controller for Kubernetes; implements Gateway API here.
*[KVM]: kernel virtual machine — Kernel-based Virtual Machine: hardware virtualization integrated into the Linux kernel; used by Incus VMs.
*[L2]: OSI model layer 2 — Data link layer of the OSI model: traffic within the same local network (MAC, ARP).
*[L3]: OSI model layer 3 — Network layer of the OSI model: IPs and routing.
*[L7]: OSI model layer 7 — Application layer of the OSI model: HTTP and similar.
*[LAN]: local area network — Local Area Network: the home network (192.168.20.0/22).
*[launchd]: launchd — macOS service manager (equivalent to systemd); socket-activates the Mac's Ollama only when a request arrives.
*[LB]: load balancer — Kubernetes LoadBalancer service (provided by MetalLB).
*[LLM]: Large Language Model — Large language model: the type of AI that understands and writes text (here, Ollama models).
*[LogsQL]: LogsQL — VictoriaLogs query language, written in Grafana → Explore.
*[LVM]: Logical Volume Manager — Linux logical volume manager.
*[LXC]: Linux Containers — Full system containers; Incus uses them as instances.
*[LXD]: LXD — Container and VM manager that Incus is a community fork of.
*[MAC]: MAC address — Unique network card identifier; the router uses it to always reserve the same IP for a device.
*[MCP]: Model Context Protocol — Standard for giving tools to an AI model (here, read-only cluster queries).
*[MD5]: Message-Digest 5 — Digest algorithm that BGP used to authenticate sessions between routers; here BGP runs without it.
*[NAT]: Network Address Translation — Address translation the router performs between the local network and the internet.
*[NFS]: Network File System — Network shared folders protocol in Linux.
*[nftables]: nftables — Linux kernel firewall used by the `host_firewall` role on each node.
*[NIC]: network interface card — Network Interface Card.
*[NRPT]: Name Resolution Policy Table — Windows table that sends DNS queries for a zone to a specific server.
*[NTP]: Network Time Protocol — Protocol that synchronizes device clocks; without it TLS certificates can appear "not yet valid".
*[NVMe]: PCIe SSD — Non-Volatile Memory Express: high-speed SSDs.
*[NXDOMAIN]: Non-Existent Domain — DNS response saying the name doesn't exist.
*[OAuth]: Open Authorization — Standard for an application to act with user permission without knowing their password; OIDC is built on it.
*[oauth2-proxy]: oauth2-proxy — Proxy that puts Dex login in front of a web interface that lacks its own login.
*[OCI]: Open Container Initiative — Image and registry standard; ARC and NGINX Gateway Fabric publish their Helm chart to an OCI registry.
*[OIDC]: OpenID Connect — Login protocol over OAuth 2.0; Dex uses it for GitHub login.
*[Open Terminal]: Open Terminal — Terminal with code execution that Open WebUI uses as an assistant tool; runs isolated in the `ai-sandbox` namespace.
*[OpenPubkey]: Project that converts an OIDC login into a short-lived SSH key; opkssh uses it to access hosts with Dex identity.
*[OS]: operating system — Operating System.
*[OVN]: Open Virtual Network — Software-defined virtual network that Incus can use.
*[OVS]: Open vSwitch — Virtual switch that OVN uses to connect Incus instances.
*[PAT]: Personal Access Token — GitHub personal access token that replaces the password in the API and CLI.
*[PDB]: PodDisruptionBudget — Kubernetes limit on how many pods of an application can be down simultaneously during a node drain.
*[PHP]: PHP: Hypertext Preprocessor — Programming language for web applications; the arc-php-84 scale set comes with it preinstalled.
*[PKCE]: Proof Key for Code Exchange — OAuth extension for public clients (no secret), like incus-ui and opkssh in Dex.
*[PR]: pull request — Pull request in GitHub.
*[PRs]: pull request — Pull request in GitHub.
*[PSA]: Pod Security Admission — Kubernetes control that applies Pod Security Standards levels to each namespace (`warn`, `audit` or `enforce`).
*[PSS]: Pod Security Standards — Kubernetes security levels for pods (privileged, baseline, restricted).
*[PVC]: PersistentVolumeClaim — Pod's request for persistent storage in Kubernetes.
*[PVCs]: PersistentVolumeClaim — Pod's request for persistent storage in Kubernetes.
*[RAG]: Retrieval-Augmented Generation — Providing own documents to the model so it answers with them instead of hallucinating (here, the HomeLab documentation).
*[RAM]: RAM — Computer's working memory.
*[RBAC]: Role-Based Access Control — Role-based access control: what each user or service account can do.
*[RWX]: ReadWriteMany — Volume access mode that multiple pods can mount simultaneously, even on different nodes.
*[S3]: Simple Storage Service — Object storage protocol (buckets) created by Amazon; Incus offers it for its buckets.
*[SAN]: Subject Alternative Name — Extra name or IP that a TLS certificate accepts (singular of SANs).
*[SANs]: Subject Alternative Names — Extra names and IPs that a TLS certificate accepts.
*[SATA]: Serial ATA — Interface for 2.5-inch drives and SSDs (invincible and oliver).
*[SBC]: Single Board Computer — Computer on a single board, like the Orange Pi 5 Plus.
*[SD]: Secure Digital — Memory card; some ARM boards boot from it.
*[SDK]: Software Development Kit — Library to use a service from code (e.g., the 1Password SDK).
*[SMART]: Self-Monitoring, Analysis and Reporting Technology — Self-diagnostics built into drives and SSDs; warns before they fail.
*[SO]: operating system
*[SOPS]: Secrets OPerationS — Tool to encrypt secrets inside YAML/JSON files.
*[SPDK]: Storage Performance Development Kit — Longhorn v2 storage engine (not used here).
*[SPI]: Serial Peripheral Interface — Bus for small chips; on the Orange Pi, SPI flash stores the bootloader.
*[SQLite]: SQLite — Database in a single file; it is K3s's default datastore with a single server.
*[SSD]: solid-state drive
*[SoC]: system on chip — Chip that integrates CPU, graphics, and other components; deborah's RK3588 is one.
*[SSH]: Secure Shell — Protocol to connect to another machine via terminal in an encrypted way.
*[SSL]: Secure Sockets Layer — Predecessor of TLS; the name is still used to refer to certificates and encrypted connections.
*[SSO]: single sign-on — Single Sign-On: log into multiple services with the same account (here, GitHub via Dex).
*[SUC]: System Upgrade Controller — Rancher controller that upgrades K3s node by node.
*[T2]: Apple T2 chip — Security coprocessor in 2018-2020 Intel Macs; handles keyboard, trackpad, audio, and Touch ID, and on Linux requires the linux-t2 kernel (eve node).
*[TCP]: Transmission Control Protocol — Connection-oriented transport protocol with ordered delivery; HTTP, TLS, and SSH run on top of it.
*[TLS]: Transport Layer Security — Encryption for connections (what puts the S in HTTPS).
*[TSIG]: Transaction SIGnature — Shared secret used to sign DNS updates (RFC 2845); BIND only accepts those signed with a known key.
*[TTL]: Time To Live — Time a datum is kept in cache before requesting it again.
*[UDP]: User Datagram Protocol — Connectionless transport protocol; used by DNS and VXLAN, for example.
*[UEFI]: Unified Extensible Firmware Interface — Boot firmware on modern computers (replaces BIOS).
*[UI]: user interface — Web or graphical interface of a tool.
*[URI]: Uniform Resource Identifier — Identifier for a resource; a URL is a type of URI.
*[URIs]: Uniform Resource Identifier — Identifier for a resource; a URL is a type of URI.
*[URL]: web address — Uniform Resource Locator.
*[URLs]: web address — Uniform Resource Locator.
*[USB]: Universal Serial Bus
*[UUID]: Universally Unique Identifier — 128-bit unique identifier; Linux uses it to name disks and partitions.
*[Vector]: Vector — Log collector that runs on each node and sends them to VictoriaLogs.
*[VictoriaLogs]: VictoriaLogs — HomeLab log database (30-day retention); queried from Grafana.
*[VIP]: virtual IP — Virtual IP: an IP not tied to a fixed machine that can move between nodes (kube-vip, MetalLB).
*[VLAN]: virtual LAN — Virtual LAN: separate a physical network into multiple logical networks.
*[VLANs]: virtual LAN — Virtual LAN: separate a physical network into multiple logical networks.
*[VM]: virtual machine — Virtual machine.
*[VMs]: virtual machine — Virtual machine.
*[VPN]: virtual private network — Virtual Private Network: encrypted access to the home network from outside.
*[VXLAN]: Virtual Extensible LAN — Layer 2 network encapsulated over UDP; Flannel and Calico use it to connect pods across nodes.
*[WAL]: Write-Ahead Log — Log where PostgreSQL records each change before applying it; archiving it allows point-in-time recovery.
*[YAML]: YAML Ain't Markup Language — Configuration text format used by Kubernetes and Ansible.
