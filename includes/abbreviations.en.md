<!-- Abbreviation glossary: automatic tooltip on all pages (abbr).
     Add only at the end of each page (pymdownx.snippets.auto_append).
     When adding a new acronym, also add it to docs/glossary.md. -->

*[ACL]: Access Control List — List of who can query a service (in BIND, an ACL `lan` could limit queries to certain networks; in this homelab, the DNS is open to the entire network).
*[API]: Application Programming Interface — Interface through which a program exposes operations to others (e.g., the Kubernetes API on :6443).
*[ARC]: Actions Runner Controller — Controller that runs GitHub Actions runners inside Kubernetes.
*[ARM64]: 64-bit ARM architecture — CPU architecture of the Orange Pi (deborah); the other nodes are x86_64.
*[ARP]: Address Resolution Protocol — Protocol that translates IPs to MAC addresses on the local network.
*[BD]: database
*[BGP]: Border Gateway Protocol — Routing protocol; MetalLB/Calico can announce IPs via BGP (here L2 is used).
*[BIND]: Berkeley Internet Name Domain — DNS server that resolves internal zones in the homelab.
*[BPF]: Berkeley Packet Filter — Linux kernel technology (eBPF) used by Cilium for networking.
*[C4]: C4 model — Method of drawing architecture in four levels: context, containers, components, and deployment.
*[CA]: certificate authority — Entity that signs TLS certificates.
*[CAPI]: Cluster API — Kubernetes project for creating and managing clusters declaratively.
*[CAPN]: Cluster API Provider for Incus — Cluster API provider that creates Kubernetes nodes as Incus instances.
*[CI]: continuous integration — Automatically compile and test code on each change (GitHub Actions).
*[CIDR]: Classless Inter-Domain Routing — Notation for IP ranges, e.g., 10.42.0.0/16.
*[CIFS]: Common Internet File System — Windows shared folder protocol (SMB).
*[CINC]: CINC Is Not Chef — Free distribution of Chef.
*[CIS]: Center for Internet Security — Organization that publishes hardening guides (CIS Benchmarks).
*[CLI]: command-line interface — Tool used from the terminal (e.g., incus, kubectl).
*[CNCF]: Cloud Native Computing Foundation — Foundation that hosts Kubernetes and related projects.
*[CNI]: Container Network Interface — Plugin that provides networking to Kubernetes pods (Flannel, Calico, Cilium…).
*[CNIs]: Container Network Interface — Plugin that provides networking to Kubernetes pods (Flannel, Calico, Cilium…).
*[CP]: control plane — Part of Kubernetes that manages the cluster (API server, scheduler, etcd).
*[CPU]: central processing unit
*[CR]: Custom Resource — Kubernetes object defined by an operator (e.g., a SUC plan).
*[CRs]: Custom Resource — Kubernetes object defined by an operator (e.g., a SUC plan).
*[CRD]: Custom Resource Definition — Definition of a new Kubernetes object type (installed by an operator, e.g., the SUC).
*[CRDs]: Custom Resource Definition — Definition of a new Kubernetes object type (installed by an operator, e.g., the SUC).
*[CSV]: Comma-Separated Values — Text file where columns are separated by commas.
*[Dex]: Dex — OIDC identity provider for the homelab: allows login with the GitHub team `devops` to Argo CD, Grafana, Open WebUI, and SSH.
*[DHCP]: Dynamic Host Configuration Protocol — Protocol used by the router to assign IPs automatically.
*[DMZ]: demilitarized zone — Router option that exposes a device directly to the internet.
*[DNS]: Domain Name System — System that translates names (argocd.homelab.local) to IPs.
*[DR]: disaster recovery — How to bring a service back up after it fails.
*[DTB]: Device Tree Blob — Binary description of the hardware that the kernel reads on boot on ARM boards like the Orange Pi.
*[eBPF]: extended Berkeley Packet Filter — Programs that run inside the Linux kernel; Cilium uses them for networking and policies.
*[eMMC]: embedded MultiMediaCard — Flash storage soldered to the board; it is the disk of deborah and does not have SMART.
*[EOL]: End Of Life — End of life of a component (on the eMMC, warning that few spare blocks remain).
*[ESO]: External Secrets Operator — Kubernetes operator that synchronizes secrets from external managers.
*[etcd]: etcd — Distributed database where Kubernetes stores its state; K3s can integrate it into the server (embedded etcd).
*[FRR]: Free Range Routing — Routing software that MetalLB uses to speak BGP; its management port is `2623`.
*[FTP]: File Transfer Protocol — Protocol for uploading files to hosting (cPanel); also FTPS/SFTP.
*[GPU]: graphics processing unit — Card or chip designed for parallel calculations; accelerates AI models. The Pi in this homelab does not use it: the models run on the CPU.
*[HA]: high availability — Design to keep a service running if a node fails.
*[HDD]: Hard Disk Drive — Mechanical hard disk.
*[HDMI]: High-Definition Multimedia Interface — Video output; useful for viewing the console of a node when the network is down.
*[HTTP]: Hypertext Transfer Protocol
*[HTTPS]: HTTP secure (over TLS)
*[IA]: artificial intelligence — Programs that respond to questions, summarize text, or generate exercises; here they serve as tutors to study the guide.
*[IdP]: Identity Provider — System that verifies who you are (in the homelab, GitHub through Dex).
*[Incus]: Incus — Container and virtual machine manager (community fork of LXD); hosts the instances where the homelab nodes run.
*[IP]: IP address — Address of a device on the network (Internet Protocol).
*[IPs]: IP address — Address of a device on the network (Internet Protocol).
*[JEDEC]: Joint Electron Device Engineering Council — Organization that standardizes memory; defines the wear fields of the eMMC.
*[journald]: journald — systemd service that logs the logs of each node’s services; Vector reads from there.
*[JSON]: JavaScript Object Notation — Text format for structured data.
*[K3s]: lightweight Kubernetes distribution — Kubernetes packaged into a single binary, designed for edge and HomeLabs.
*[K8s]: Kubernetes — Container orchestration platform.
*[KIC]: Kong Ingress Controller — Kong controller for Kubernetes; here it implements Gateway API.
*[KVM]: kernel-based virtual machine — Kernel-based Virtual Machine: hardware-integrated virtualization in the Linux kernel; used by Incus VMs.
*[L2]: layer 2 of the OSI model — OSI data link layer: traffic within the same local network (MAC, ARP).
*[L3]: layer 3 of the OSI model — OSI network layer: IPs and routing.
*[L7]: layer 7 of the OSI model — OSI application layer: HTTP and similar protocols.
*[LAN]: local area network — Home network (192.168.20.0/22).
*[launchd]: launchd — macOS service manager (equivalent to systemd); activates the Ollama socket on the Mac only when a request arrives.
*[LB]: load balancer — Kubernetes service of type LoadBalancer (provided by MetalLB).
*[LLM]: Large Language Model — Large-scale language model: the type of AI that understands and writes text (here, Ollama models).
*[LogsQL]: LogsQL — VictoriaLogs query language, written in Grafana → Explore.
*[LVM]: Logical Volume Manager — Linux logical volume manager.
*[LXC]: Linux Containers — Full system containers; Incus uses them as instances.
*[LXD]: LXD — Container and VM manager from which Incus is a community fork.
*[MAC]: MAC address — Unique identifier for a network card; the router uses it to always reserve the same IP for a device.
*[MCP]: Model Context Protocol — Standard to give tools to an AI model (here, read-only queries to the cluster).
*[MD5]: Message-Digest 5 — Digest algorithm that BGP used to authenticate sessions between routers; here BGP runs without it.
*[NAT]: Network Address Translation — Network translation that the router performs between the local network and the internet.
*[NFS]: Network File System — Linux protocol for shared network folders.
*[nftables]: nftables — Linux kernel firewall that uses the `host_firewall` role on each node.
*[NIC]: network interface card — Network Interface Card.
*[NTP]: Network Time Protocol — Protocol that synchronizes the clock of devices; without it TLS certificates may appear "not yet valid".
*[NVMe]: PCIe SSD — Non-Volatile Memory Express: high-speed SSDs.
*[NXDOMAIN]: Non-Existent Domain — DNS response that says the domain does not exist.
*[OAuth]: Open Authorization — Standard for an application to act on behalf of a user without knowing their password; OIDC is built on top of it.
*[oauth2-proxy]: oauth2-proxy — Proxy that puts Dex login in front of a web interface that does not have its own login.
*[OCI]: Open Container Initiative — Standard for images and registries; ARC and NGINX Gateway Fabric publish their Helm chart in an OCI registry.
*[OIDC]: OpenID Connect — Login protocol over OAuth 2.0; Dex uses it for GitHub login.
*[Open Terminal]: Open Terminal — Code-executing terminal that Open WebUI uses as a tool for the assistant; runs isolated in the `ai-sandbox` namespace.
*[OpenPubkey]: Project that converts an OIDC login into a short-lived SSH key; used by opkssh to log into hosts with the Dex identity.
*[OS]: operating system — Operating System.
*[OVN]: Open Virtual Network — Software-defined virtual network that Incus can use.
*[OVS]: Open vSwitch — Virtual switch that OVN uses to connect Incus instances.
*[PAT]: Personal Access Token — GitHub personal token that replaces the password in the API and CLI.
*[PDB]: PodDisruptionBudget — Kubernetes limit on how many pods of an application can be down at once during a node drain.
*[PKCE]: Proof Key for Code Exchange — OAuth extension for public clients (without a secret), such as incus-ui and opkssh in Dex.
*[PR]: pull request — GitHub change request.
*[PRs]: pull request — GitHub change request.
*[PSA]: Pod Security Admission — Kubernetes control that applies Pod Security Standards levels to each namespace (`warn`, `audit`, or `enforce`).
*[PSS]: Pod Security Standards — Kubernetes security levels for pods (privileged, baseline, restricted).
*[PVC]: PersistentVolumeClaim — Persistent storage claim of a pod in Kubernetes.
*[PVCs]: PersistentVolumeClaim — Persistent storage claim of a pod in Kubernetes.
*[RAG]: Retrieval-Augmented Generation — Feeding documents to the model so it responds with them instead of inventing (here, the HomeLab documentation).
*[RAM]: random access memory — Working memory of the device.
*[RBAC]: Role-Based Access Control — Role-based access control: what each user or service account can do.
*[RWX]: ReadWriteMany — Access mode of a volume that multiple pods can mount at once, even on different nodes.
*[SAN]: Subject Alternative Name — Additional name or IP accepted by a TLS certificate (singular of SANs).
*[SANs]: Subject Alternative Names — Additional names and IPs accepted by a TLS certificate.
*[SATA]: Serial ATA — Interface for 2.5-inch disks and SSDs (invincible and oliver).
*[SBC]: Single Board Computer — Single-board computer, such as the Orange Pi 5 Plus.
*[SD]: Secure Digital — Memory card; some ARM boards boot from it.
*[SDK]: Software Development Kit — Library to use a service from code (e.g., the 1Password SDK).
*[SMART]: Self-Monitoring, Analysis and Reporting Technology — Self-diagnosis that comes with disks and SSDs; warns before they fail.
*[SO]: operating system
*[SOPS]: Secrets OPerationS — Tool to encrypt secrets within YAML/JSON files.
*[SPDK]: Storage Performance Development Kit — Longhorn v2 storage engine (not used here).
*[SPI]: Serial Peripheral Interface — Bus for small chips; on the Orange Pi, the SPI flash memory stores the boot loader.
*[SQLite]: SQLite — Single-file database; it is the default data store for a single-server K3s installation.
*[SSD]: solid-state drive
*[SoC]: system on chip — Chip that integrates CPU, graphics, and other components; the RK3588 in deborah is one.
*[SSH]: Secure Shell — Protocol for encrypted terminal connections to another machine.
*[SSL]: Secure Sockets Layer — Predecessor to TLS; the name is still used to refer to certificates and encrypted connections.
*[SSO]: single sign-on — Single Sign-On: log in to multiple services with the same account (here, GitHub via Dex).
*[SUC]: System Upgrade Controller — Rancher controller that updates K3s node by node.
*[TLS]: Transport Layer Security — Encryption for connections (the S in HTTPS).
*[TTL]: Time To Live — Time a data item is cached before it is refreshed.
*[UDP]: User Datagram Protocol — Connectionless transport protocol; used, for example, by DNS and VXLAN.
*[UEFI]: Unified Extensible Firmware Interface — Modern boot firmware for computers (replaces BIOS).
*[UI]: user interface — Web or graphical interface for a tool.
*[URI]: Uniform Resource Identifier — Identifier for a resource; a URL is a type of URI.
*[URIs]: Uniform Resource Identifier — Identifier for a resource; a URL is a type of URI.
*[URL]: web address — Uniform Resource Locator.
*[URLs]: web address — Uniform Resource Locator.
*[USB]: Universal Serial Bus
*[UUID]: Universally Unique Identifier — 128-bit unique identifier; Linux uses it to name disks and partitions.
*[Vector]: Vector — Log collector running on each node that sends logs to VictoriaLogs.
*[VictoriaLogs]: VictoriaLogs — HomeLab log database (30-day retention); queried from Grafana.
*[VIP]: virtual IP — Virtual IP: an IP address that is not tied to a fixed machine and can move between nodes (kube-vip, MetalLB).
*[VLAN]: virtual local area network — Virtual LAN: splitting a physical network into multiple logical networks.
*[VLANs]: virtual local area network — Virtual LAN: splitting a physical network into multiple logical networks.
*[VM]: virtual machine — Virtual machine.
*[VMs]: virtual machine — Virtual machine.
*[VPN]: virtual private network — Virtual Private Network: encrypted access to the home network from outside.
*[VXLAN]: Virtual Extensible LAN — Layer 2 network encapsulated over UDP; used by Flannel and Calico to connect pods between nodes.
*[YAML]: YAML Ain't Markup Language — Text configuration format used by Kubernetes and Ansible.
