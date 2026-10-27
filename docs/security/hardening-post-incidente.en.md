# Post-incident hardening

!!! danger "What happened (2026-09)"
    `deborah` (Orange Pi 5 Plus, K3s control plane) was left exposed
    directly to the internet — DMZ (demilitarized zone)/port-forward on the router to its IP —
    still with the manufacturer image's default password. It was
    compromised and had to be reinstalled from scratch.

This page is the guide to rebuild `deborah` securely and to
prevent this incident from recurring on `invincible`/`oliver`. The playbook and the
role that accompany it are in
[`ansible/roles/host_hardening/`](https://github.com/maceosoft/homelab/blob/main/ansible/roles/host_hardening/README.md).

## Root cause (and why order matters)

Two independent failures, either one alone was already enough:

1. **Direct internet exposure.** A port-forward/DMZ on the router
   sends internet traffic straight to a LAN (local area network) host, without any
   intermediate control. Any service with a vulnerability, or
   any administration port (SSH included), becomes reachable
   by anyone on the internet.
2. **Unchanged default password.** SBC —Single Board Computer— images (Orange Pi,
   Raspberry Pi, etc.) ship with publicly documented
   username/password in the manufacturer's repo — it's the first thing
   an automated scanner tries.

The combination is lethal: no zero-day vulnerability is needed,
a cheap scanner sweeping internet IPs for SSH (Secure Shell) with
default credentials is enough.

## The principle that replaces the DMZ: remote access only via the router's VPN

The WireGuard server is the router. This repo stores no
WireGuard configuration or keys.

- **Never** forward an administration port (SSH, Incus UI,
  K3s API) on the router directly to a LAN host.
- The **only** traffic that should reach your network from the internet is the
  router's VPN (virtual private network) traffic. Everything else (SSH, Incus, K3s, BIND) is administered
  *through* the tunnel or from the LAN — never directly from the internet.
- If you ever need to genuinely publish something to the internet (a
  web service, not an administration service), the standard practice is a reverse
  proxy in a real, isolated DMZ — not the host running the service, and
  never the same host that manages the cluster.

Exposure is limited at the router **and on each node** (see the next
section). `roles/host_hardening` does not configure the host firewall: ufw conflicts
with kube-proxy's iptables rules and is not compatible with
K8s (Kubernetes); that's handled by the `host_firewall` role, which uses `nftables`.

## Host firewall, exposed services, and authentication

An audit of the repo and the live cluster found that, in addition to the incident's DMZ, the nodes had the `INPUT` chain in `ACCEPT` and several services accessible from the entire LAN and WiFi without authentication. The outcome, and what was done for each finding, is summarized here; the general rule and the exception list live in [Authentication model](modelo-de-autenticacion.md). The "Fix" column describes the design; what gets rolled out in stages (NetworkPolicy `default-deny`, PSA —Pod Security Admission— labels, `oauth2-proxy`) is marked as "to enable".

| Finding | Fix |
|---|---|
| No managed host firewall: LAN and WiFi reached `22`, `6443`, `8443`, `10250`, `9100`, `11434`... | `host_firewall` role with `nftables`: own table, evaluated before kube-proxy and without touching Calico chains |
| Ollama without authentication, with `/api/pull`, `/api/create`, and `/api/delete` | Socket only on the node IP, `nftables` with port `11434` only from K3s nodes and pods, Kong only via HTTPS and Bearer auth on the router, which also blocks management verbs. The node's Ollama remains unauthenticated: the real protection is the router token plus NetworkPolicy |
| Kong Manager (ports `8002` and `8445`, NodePort) and Admin API without authentication | Kong Manager disabled; Admin API internal only (its NetworkPolicy is to enable) |
| Argo CD with local `admin` user and its initial secret | `admin.enabled: "false"` and delete the initial secret; the pipeline uses a `ci` token with expiration |
| No NetworkPolicy in `kong`, `monitoring`, `ai`, `longhorn-system`, `gateway`, and `arc-*` | `default-deny` manifests and explicit per-namespace permissions, **to enable** one by one (those for logs, `ai/tools`, `alert-triage`, and Open Terminal already ship with their application) |
| Open WebUI with open registration and no Dex | Dex with the `devops` team, registration closed |
| Incus (`8443`) open to LAN | Restricted by `nftables`; specific OIDC group |
| `adbd` (Android Debug Bridge, no credentials) listening on `deborah:5555`, launched by `usbdevice.service` | Disable and mask that unit and verify the port closes |
| node-exporter and MetalLB and FRR metrics open to LAN | Listen only on the node IP and `nftables` toward the collector |
| `alert-triage` and `mcpo` without token | Bearer token or API key, NetworkPolicy |
| BIND without zone transfers and with visible version | `allow-transfer { none; }` and version hidden. DNS serves the whole network (other router subnets, VPN): not limited by source nor rate limit enabled (opt-in with `bind_dns_restrict_clients` and `bind_dns_rate_limit_enabled`) |
| K3s without Dex or Secrets encryption | Flags `oidc-*` toward Dex, `--secrets-encryption`, and installer with checksum, configured in `k3s_install` (`group_vars/incus_cluster/k3s_install.yml`); the server picks them up on reinstall or when [moving the control plane](../operacion/mover-control-plane.md) |
| `rpcbind`, `dnsmasq`, SSH with `AllowUsers` undefined, minimum `auditd` | Disable what is not used, `AllowUsers devops amaceo`, and `auditd` rules sent to [VictoriaLogs](../operacion/logs.md) |

!!! danger "Firewall applies with auto-rollback"
    A `nftables` mistake can lock you out of SSH. The role applies rules with a **300-second (5-minute) auto-rollback**: new connections (SSH, K3s API) are tested and must be confirmed manually; if not, a systemd timer removes the rules. It is applied node by node (`playbook-firewall.yml`): first `--check` on `oliver`, then `invincible`, and finally `deborah`. To remove it in an emergency on the node: `sudo systemctl disable --now homelab-firewall`. The role details are in its [README](https://github.com/maceosoft/homelab/blob/main/ansible/roles/host_firewall/README.md).

SSH access with the Dex identity (opkssh) only works if the policy deployed on each node matches the current team organization (`maceosoft:devops`); if the organization changes, `playbook-opkssh.yml` must be reapplied.

The shared `devops` account (with passwordless `sudo`) is kept as an SSO (single sign-on) account by explicit decision; control is `AllowUsers` and the audit trail is `auditd`.

## What the hardening does (summary)

Full detail in the [role README](https://github.com/maceosoft/homelab/blob/main/ansible/roles/host_hardening/README.md).
In short: SSH without password (key only), removal of known default accounts (`orangepi`, `pi`, `ubuntu`, `debian`) with their home directories, basic network sysctl, and auditd to have a trail if something happens again. On `deborah`, **SSH host keys are also regenerated** — factory SBC images sometimes repeat both the password and the host keys across all units of the same model.

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-hardening.yml --check --diff
ansible-playbook -i inventory.ini playbook-hardening.yml --limit deborah
```

## `deborah` rebuild order

`deborah` is the K3s control plane (`k3s_api_ip` in
`group_vars/all.yml`) — it must be rebuilt in order before
it becomes useful again. The complete order, step by step with the exact
commands, lives in a single place to avoid duplication (and prevent it from
going out of sync in two different places):

**→ [`ansible/bootstrap/README.md`](https://github.com/maceosoft/homelab/blob/main/ansible/bootstrap/README.md)**

Use `--limit deborah` at each step. The static IP (`playbook-set-static-ip.yml`) goes
**before** hardening.

Specific notes:

- **Manual, before any Ansible step:** when flashing the image,
  change the default password and load your SSH key *before* connecting the
  machine to any network with internet access. `playbook-hardening.yml`
  assumes a key already exists in `authorized_keys` (aborts if not
  found) — it does not replace this manual step.
- **Hardening goes before re-adding `deborah` to the cluster** (after
  the static IP): there is no point in re-exposing an unhardened host
  while rebuilding.
- **The CA (certificate authority) and K3s certificates (lightweight Kubernetes distribution) regenerate automatically** when doing a clean `k3s server` on the
  reinstalled `deborah` (no etcd backup/snapshot to restore) —
  this is, in effect, a full rotation of the cluster's root of trust. If you happen to have an etcd snapshot from before the incident, **do not restore it** — it would bring back potentially compromised certificates.

## Rotate the root password

In addition to SSH hardening, it is advisable to rotate the local
`root` password on all 3 nodes (defense in depth for console/`su -` —
  `root` login via SSH is already disabled). There is a dedicated playbook
  that generates a new password per host and stores it in 1Password (vault
  `HomeLab`): see [Secrets management](../secrets/index.md#rotacion-de-password-de-root-1password-sdk-local).

```bash
ansible-playbook -i inventory.ini playbook-rotate-root-passwords.yml \
  --limit deborah
```

## On the router

- Delete any DMZ/port-forward rule pointing to `192.168.20.5`
  (or any other node).
- Leave **only** the router's WireGuard server exposed.
- If the router supports it, this is also the time to evaluate VLANs (virtual local area networks)
  (see [Next hardening level](#next-hardening-level)) instead of a single flat LAN.

These changes are made **only from the router's web interface**; menus depend on the model.

## Next hardening level

- **Segmentation with VLANs** — separate the HomeLab cluster VLAN (virtual local area network) from
  anything else on the LAN (IoT, guests, etc.), instead of trusting
  a single flat LAN. Requires network hardware/config not yet declared
  in this repo.
- **CIS (Center for Internet Security) Kubernetes / `kube-bench` Benchmark** on K3s — K3s already passes
  several CIS controls by default; for those it doesn't, you must
  opt in explicitly (`protect-kernel-defaults`, `secrets-encryption`,
  `NetworkPolicy`, Pod Security Admission). See
  [official K3s guide](https://docs.k3s.io/security/hardening-guide) and
  [`kube-bench`](https://github.com/aquasecurity/kube-bench).
- **Encryption of secrets at rest** in K3s (`--secrets-encryption`): already in `k3s_install`; the server picks it up on
  reinstall (or when [moving the control plane](../operacion/mover-control-plane.md), if ever done).
- **NetworkPolicies** `default-deny` between namespaces (`ai`, `monitoring`, `longhorn-system`,
  `kong`, `gateway`, `arc-*`): manifests are ready but enabled in stages,
  namespace by namespace. See [What is active](modelo-de-autenticacion.md#que-esta-activo-y-que-esta-por-activar).
- **Pod Security Admission** (PSA) in `warn` and `audit` mode with the `restricted` level
  before making it mandatory (labels ready, pending activation).

## References consulted

- [Linux Server Hardening Checklist for 2026 — SysWard](https://sysward.com/blog/2026-05-06-linux-server-hardening-checklist/)
- [SSH Hardening Checklist for 2026 (Ubuntu/Debian) — Let's Secure Me](https://letsecure.me/ssh-hardening-checklist-2026-ubuntu-debian/)
- [CIS Hardening Guide — K3s docs](https://docs.k3s.io/security/hardening-guide)
- [CIS Self Assessment Guide — K3s docs](https://docs.k3s.io/security/self-assessment)
- [Kubernetes hardening with kube-bench — CNCF blog](https://www.cncf.io/blog/2025/04/08/kubernetes-hardening-made-easy-running-cis-benchmarks-with-kube-bench/)
- [How to Secure Remote Access to a Homelab — HomelabAddiction](https://homelabaddiction.com/homelab-security/)
