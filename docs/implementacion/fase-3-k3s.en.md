# Phase 3 — K3s

## Objective

Set up a **K3s (lightweight Kubernetes distribution)** management cluster on 3 nodes (control plane on deborah, workers on invincible and oliver), with **Argo CD** controller ready for GitOps.

## What You Learn

K3s as a lightweight bare-metal Kubernetes: server/agent, CNI (Container Network Interface) configurable
(Flannel by default in K3s; in this homelab, Calico), disable Traefik/ServiceLB to control the Gateway and
LoadBalancer via GitOps later.

!!! abstract "Learn this phase"
    **In simple terms:** Kubernetes is the manager of a restaurant: you tell it "I want three cooks working at all times" and it takes care of replacing any that are missing. The **control plane** is the management (decides) and the **workers** are the kitchen (work). K3s is a version of Kubernetes designed for small teams.

    **Key concepts**

    - **Node:** a machine in the cluster; can be control plane (decides) or worker (executes).
    - **Pod:** the smallest unit of execution: one or more containers that live together.
    - **Deployment:** declares how many copies of a pod should exist and keeps them running.
    - **CNI:** the component that provides network to pods; here, Calico.
    - **`kubectl` and kubeconfig:** the command-line tool and the file with the cluster access data.

    **Practical challenge (safe):** create a test deployment, delete one of its pods, and watch Kubernetes replace it.

    ```bash
    kubectl get nodes -o wide
    kubectl create deployment demo --image=nginx --replicas=2
    kubectl get pods -l app=demo
    kubectl delete pod -l app=demo --wait=false
    # aparecen pods nuevos
    kubectl get pods -l app=demo
    # limpieza
    kubectl delete deployment demo
    ```

    ??? question "What is the difference between a pod and a deployment?"
        A pod is a running copy; a deployment is the rule that says how many copies should exist and recreates them if they disappear.

    ??? question "What happens if a worker fails?"
        Kubernetes detects that the pods have stopped responding and recreates them on other healthy nodes.

    ??? question "Why is a CNI required?"
        Because Kubernetes does not come with its own pod network in this setup: the CNI provides addresses and inter-node communication.

    Have questions? Use the **Learn with AI** button next to each title, or the page [Learn](../aprende.md).

## Stack for this phase

```mermaid
flowchart TB
  subgraph cp [Control_plane]
    DEB[deborah_server]
    VIP[kube_vip_opcional]
  end
  subgraph workers [Workers]
    INV[invincible_agent]
    NOL[oliver_agent]
  end
  DEB --> API[API_6443]
  VIP -.-> API
  INV --> API
  NOL --> API
  DEB --> ArgoCD[ArgoCD_controller]
```

- **[K3s](https://docs.k3s.io/)** — Management cluster; Phase 3.
- **CNI** — [Flannel](https://github.com/flannel-io/flannel) (default), [Canal](https://docs.tigera.io/calico/latest/getting-started/kubernetes/flannel/flannel), [Calico](https://docs.tigera.io/calico/latest/about/), [Cilium](https://docs.cilium.io/); Phase 3.
- **[kube-vip](https://kube-vip.io/)** — Optional VIP (virtual IP) `:6443`; fork Phase 3.
- **[Argo CD](https://argo-cd.readthedocs.io/)** — Controller bootstrap; Phase 3 → GitOps Phase 4.
- **[Ansible](https://docs.ansible.com/)** — `playbook-k3s.yml`.

Further reading: [Playbook options](../k3s/playbook-options.md) · [Ansible role catalog](../ansible/index.md) · [K3s manual (legacy)](../k3s/index.md)

**This decision in other environments**

=== "🏠 At home"

    A single control plane on deborah, with the default K3s datastore (SQLite), and two workers. It is simple, uses little memory, and is sufficient for learning; if deborah goes down, the pods continue running but you cannot make changes until it comes back up. If you want high availability later, K3s can switch to
    [embedded etcd](https://docs.k3s.io/datastore/ha-embedded).

=== "🏢 In a company"

    - **Benefits:** Kubernetes provides a unique way to deploy, scale, and recover applications on any server; a small team operates many services with the same manifests, and K3s achieves this with a lightweight binary that installs and updates in minutes.
    - **High availability:** three control planes are used (an odd number to maintain quorum in etcd), with embedded or [external etcd](https://docs.k3s.io/datastore), behind a virtual IP or a load balancer.
      SQLite does not work with multiple servers.
    - **Zero-downtime updates:** with multiple control planes, one is updated at a time and the API never goes down.
    - **Commercial support:** it is common to pay for a distribution with support and security patches, such as
      [RKE2](https://docs.rke2.io/) within [SUSE Rancher Prime](https://www.suse.com/products/rancher/) or
      [Red Hat OpenShift](https://www.redhat.com/en/technologies/cloud-computing/openshift).
    - **When K3s is suitable:** at the edge (stores, branches, factories, IoT), where there is little hardware, little technical staff on-site, or intermittent connectivity. There, a small and easy-to-replace cluster is worth more than a large one.

=== "☁️ In the cloud"

    | Cloud | Equivalent service |
    |---|---|
    | GCP | [Google Kubernetes Engine (GKE)](https://cloud.google.com/kubernetes-engine) |
    | AWS | [Amazon Elastic Kubernetes Service (EKS)](https://aws.amazon.com/eks/) |
    | Azure | [Azure Kubernetes Service (AKS)](https://azure.microsoft.com/en-us/products/kubernetes-service) |
    | Oracle Cloud (OCI) | [OCI Kubernetes Engine (OKE)](https://www.oracle.com/cloud/cloud-native/kubernetes-engine/) |

    Gain a managed control plane provided by the cloud provider: high availability, patches, and SLA without you having to manage etcd. You lose control over that control plane, pay for the service, and become more tied to that cloud's integrations.

## Before You Start

- [ ] [Phases 0](fase-0-preparacion.md), [1](fase-1-red.md), and [2](fase-2-incus.md) completed.
- [ ] Healthy Incus cluster (optional but recommended before CAPN —Cluster API Provider for Incus—).

## Run

=== "Recommended (Ansible)"

    Playbook options are activated in
    [`group_vars/incus_cluster/k3s_install.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/group_vars/incus_cluster/k3s_install.yml),
    not via command line. Today, Argo CD
    (`gitops_argocd`), node labels (`node_labels`), and local kubeconfig
    (`fetch_kubeconfig`) are enabled, with CNI Calico.
    Review the file and run:

    ```bash
    cd ansible
    ansible-playbook -i inventory.ini playbook-k3s.yml
    ```

    !!! warning "Do not use `-e k3s_install.<opción>=…`"
        Ansible ignores it: `k3s_install` is a dictionary and a key with
        dots in `-e` does not modify it (the default CNI would be installed without warning). Passing `-e`
        with JSON is worse: it replaces the entire dictionary and loses `core.version`,
        `cluster_cidr`, etc. That's why the playbook **fails** in both cases. To change the CNI use
        `-e k3s_cni=canal` (or edit the file); see
        [playbook options](../k3s/playbook-options.md).

=== "Manual alternative"

    Manual curl steps in [K3s — manual installation](../k3s/index.md). Use only if
    Ansible is not available; the supported path is the playbook.

## Options

| If you need… | In `k3s_install.yml` | Today | Doc |
|---|---|---|---|
| Stable API VIP | `kube_vip.enabled: true` | disabled | [playbook-options](../k3s/playbook-options.md) |
| Longhorn/arch labels | `node_labels.enabled: true` | enabled | [playbook-options](../k3s/playbook-options.md) |
| Local kubeconfig | `fetch_kubeconfig.enabled: true` | enabled | [playbook-options](../k3s/playbook-options.md) |
| OS hardening | `os_hardening.enabled: true` | disabled | [playbook-options](../k3s/playbook-options.md) |

| Decision | Option A (default) | Option B |
|---|---|---|
| K3s API | Name `k3s.homelab.local` (variable `k3s_api_endpoint`) to the control plane IP, today deborah `192.168.20.5` | kube-vip `192.168.20.4` |
| CNI | Calico (configured in this repo) | Flannel `vxlan` (default of K3s), Canal or Cilium (`k3s_install.core.cni`) |

### CNI

| CNI | Variable | Notes |
|---|---|---|
| **Flannel** (default of K3s) | `cni: flannel` | Embedded in K3s; `flannel_backend: vxlan` or `host-gw` |
| **Canal** | `cni: canal` | Flannel overlay + Calico policies; role `k3s_cni` |
| **Calico** | `cni: calico` | NetworkPolicy, optional BGP; `--flannel-backend=none` |
| **Cilium** | `cni: cilium` | eBPF, Hubble; validate on ARM64 (deborah) |

The CNI is chosen in `k3s_install.core.cni` (today: `calico`), **before**
installing K3s: changing it in an already installed cluster requires reinstalling K3s.

```yaml
# group_vars/incus_cluster/k3s_install.yml
k3s_install:
  core:
    cni: calico  # flannel | canal | calico | cilium
```

Details: [playbook-options — CNI](../k3s/playbook-options.md#cni).

<div class="card">
  <div class="card-kicker">Trade-off analysis</div>
  <div class="option-grid">
    <div class="card-col">
      <div class="card-title">Ansible (<code>playbook-k3s.yml</code>)</div>
      <div class="text-muted">Flags in <code>group_vars</code>; role <code>k3s_cni</code></div>
      <div class="text-muted">Requires SSH and order server → CNI → agents</div>
    </div>
    <div class="card-col">
      <div class="card-title">Manual curl</div>
      <div class="text-muted">Escape hatch</div>
      <div class="text-muted">No idempotence; easy to forget <code>--disable traefik</code></div>
    </div>
    <div class="card-col">
      <div class="card-title">Fixed IP <code>192.168.20.5</code></div>
      <div class="text-muted">No extra components</div>
      <div class="text-muted">If the CP migrates, agents need reconfiguration</div>
    </div>
    <div class="card-col">
      <div class="card-title">kube-vip <code>192.168.20.4</code></div>
      <div class="text-muted">Stable API VIP</div>
      <div class="text-muted">Additional daemon; different from MetalLB</div>
    </div>
    <div class="card-col">
      <div class="card-title">Flannel</div>
      <div class="text-muted">Zero friction; low consumption</div>
      <div class="text-muted">No native NetworkPolicy</div>
    </div>
    <div class="card-col">
      <div class="card-title">Canal</div>
      <div class="text-muted">Calico policies over overlay</div>
      <div class="text-muted">Legacy project; two stacks</div>
    </div>
    <div class="card-col">
      <div class="card-title">Calico</div>
      <div class="text-muted">Mature NetworkPolicy; BGP at L2</div>
      <div class="text-muted">More pods/RAM; IP pools</div>
    </div>
    <div class="card-col">
      <div class="card-title">Cilium</div>
      <div class="text-muted">eBPF; L3–L7 policies; Hubble</div>
      <div class="text-muted">More CPU; kernel/BPF; test on deborah</div>
    </div>
    <div class="card-col">
      <div class="card-title"><code>node_labels</code> / <code>fetch_kubeconfig</code></div>
      <div class="text-muted">Longhorn and local kubeconfig ready</div>
      <div class="text-muted">Longer play; misapplied labels affect storage</div>
    </div>
  </div>
</div>

## Verify

```bash
# En deborah o con kubeconfig
sudo k3s kubectl get nodes
# 3 nodos Ready
sudo k3s kubectl get pods -n argocd
# argocd-server Running (si gitops_argocd.enabled=true)
```

Wait for pods `argocd-server` in `Running` before Phase 4.

## If it fails

| Symptom | Check |
|---|---|
| Agent does not join | Token, `K3S_URL`, firewall `:6443` |
| Residual Traefik | `--tags traefik` or role `k3s_cleanup_traefik` |
| CP down after reboot | `systemctl enable --now k3s` in deborah |

## Next

**[→ Phase 4 — GitOps](fase-4-gitops.md)**
