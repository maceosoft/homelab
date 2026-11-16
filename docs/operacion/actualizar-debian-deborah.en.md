# Upgrading Debian on deborah (12 → 13)

`deborah` (Orange Pi 5 Plus, ARM64 —64-bit ARM architecture—) runs **Debian 12 (bookworm)**; the other two nodes are already on **Debian 13
(trixie)**. The playbook
[`playbook-upgrade-debian13.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-upgrade-debian13.yml)
upgrades it with a backup, a prior dry run, and a **boot gate** that is validated before rebooting.

!!! danger "This is the most delicate operation in the HomeLab"
    `deborah` is the **K3s control plane**, the **LAN DNS** (BIND), and a member of **Incus**. While it lasts, the
    Kubernetes API and DNS do not respond (pods on the other nodes keep running). And if the machine doesn't boot
    after the reboot, you need **physical access** (HDMI —video output— or serial console). Do this during a maintenance window.

!!! tip "The Kubernetes API goes down while `deborah` reboots"
    `deborah` is the control plane: while it reboots, `kubectl` and Argo CD do not respond, but the pods already running
    on the other nodes keep working. If the control plane were ever on another node
    ([Moving the control plane](mover-control-plane.md)), only the workloads running on `deborah` (the LAN
    DNS, Ollama, and their pods) would go down.

## What changes and what doesn't

| Changes | Doesn't change |
|---|---|
| Debian packages move to trixie (about 600 are upgraded and about 40 old libraries are removed) | **The vendor kernel** (`5.10.160-rockchip-rk3588`) and the u-boot boot process: they don't come from Debian and apt doesn't touch them |
| `systemd`, `glibc`, `openssh`, `bind9`… to the trixie versions | K3s (its binary is independent), Incus (the version is kept), and the pods |
| `/tmp` becomes memory (`tmpfs`) after the reboot | `docker-ce` and `containerd.io` (not from Debian; they stay as they are) |

Kernel 5.10 meets the minimum recommended by `systemd` 257 (5.4), but this is an unusual case: Debian
documents the upgrade for "pure" systems, not for vendor images. That's why the gate exists.

## Before you start

- [ ] **Incus aligned on all nodes.** The cluster requires the same version on all members. If `deborah`
  has a different Incus version from the one offered by the repository, first upgrade Incus on all nodes with
  [`playbook-upgrade-incus.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-upgrade-incus.yml)
  (`-e incus_upgrade_confirm=true`; see [Upgrading or uninstalling Incus](../incus/cluster-setup.md#update-or-uninstall-incus)).
  The playbook stops if they don't match (`upgrade_skip_incus_check=true` skips this check, for rehearsals only).
- [ ] **Physical access** to `deborah` (HDMI or serial console) and, if possible, an **eMMC image** (`dd` from another
  machine). It is the only complete way back.
- [ ] Healthy K3s: `kubectl get nodes` with all `Ready`, and `incus cluster list` with all `ONLINE`.
- [ ] Nobody will need DNS or the Kubernetes API for ~30–60 minutes.

## Step 1 — Preflight and dry run (changes nothing)

```bash
cd ansible
export KUBECONFIG=~/.kube/homelab-k3s.yaml
ansible-playbook -i inventory.ini playbook-upgrade-debian13.yml
```

Without `-e upgrade_confirm=true` it only runs `preflight`: it checks that this is Debian 12 on ARM64, free space
(6 GB on `/`, 300 MB on `/boot`), that `dpkg` has no problems, **the boot setup** (u-boot, gzip `uInitrd`, root
UUID —unique identifier—), and the Incus version. It then downloads the trixie indexes to a separate directory (`/var/tmp`), **simulates** the
upgrade, and **fails if it would remove the kernel, the boot setup, or a HomeLab service** (`linux-image`, `orangepi`,
`k3s`, `incus`, `bind9`, `openssh-server`, `netplan`…). Then it deletes that directory.

## Step 2 — Upgrade

```bash
ansible-playbook -i inventory.ini playbook-upgrade-debian13.yml -e upgrade_confirm=true
```

| Phase (tag) | What it does |
|---|---|
| `backup` | Backs up `/etc`, `/boot`, the state of `dpkg`/`apt`, BIND, and K3s (SQLite, certificates, and token; it **stops K3s** first). Copies the files to `ansible/backups/` (ignored by Git) |
| `upgrade` | Pauses automatic updates, brings Debian 12 up to date, switches the repositories to trixie (Debian and Zabbly), and runs `upgrade` and `full-upgrade` while keeping your configuration files (`--force-confold`) |
| `gate` | **Before rebooting:** regenerates and validates the `initrd`, checks `uInitrd`, `boot.scr`, the DTB, the kernel modules, the root UUID, `sshd -t`, `netplan generate`, and the IP of `br0` |
| `reboot` | Reboots and waits up to 20 minutes |
| `verify` | Confirms Debian 13 with the same kernel, K3s `Ready`, services, DNS, and Incus |
| `cleanup` | Re-enables the apt timers and **lists** obsolete packages (it doesn't delete them) |

If something fails **before** the reboot, the playbook starts K3s again, leaves the machine powered on, and tells you where
the logs (`/var/log/pre-trixie-upgrade-*.log`) and the backup are. To rehearse without rebooting:
`-e upgrade_reboot=false`; you do the reboot and the verification yourself (`--tags reboot,verify`).

### Why the boot gate exists

The board's boot depends on a u-boot script (`boot.scr`) and an `uInitrd` that the
`/etc/initramfs/post-update.d/99-uboot` hook creates by declaring it **gzip**. If the upgrade left the `initrd`
compressed in a different way, u-boot couldn't decompress it and the machine **would not boot**. The playbook requires
`COMPRESS=gzip` in `initramfs.conf` (kept with `--force-confold`) and validates the result with `gzip -t` and
`mkimage -l` before rebooting.

## If the machine doesn't come back

1. Connect a monitor or the serial console and see where it stops (u-boot, kernel, or `systemd`).
2. If it's the boot process: restore the eMMC image you made earlier. With the image, `deborah` goes back to Debian 12.
3. Without an image: reinstall the board's system and restore the backup of `ansible/backups/deborah-<fecha>/`:
   `etc.tgz`, `boot.tgz`, `k3s.tgz` (certificates, token, and control plane database, as long as `deborah` is the control plane) and `bind.tgz`.
   Without the K3s token and certificates you would have to reinstall the cluster.
4. The other two nodes keep working in the meantime, but without a control plane there are no changes or syncing.

## After

- `ansible-playbook -i inventory.ini playbook-upgrade-debian13.yml --tags verify` re-run the verification whenever you want.
- **Don't blindly purge** the list of obsolete packages: it includes `linux-image-legacy-rockchip-rk3588`,
  `orangepi-*` and `linux-u-boot-*`, which are the ones that make the board boot.
- With `deborah` on Debian 13, the OVN and Open vSwitch versions now match those on the other nodes (a
  prerequisite for considering OVN: see [Load balancing and OVN](../incus/cluster-setup.md#load-balancing-and-ovn)).
- **Two units may be left in `failed` after the reboot** (`systemctl --failed`), without affecting the cluster:
  `smartmontools` (the eMMC has no SMART and on Debian 13 the service is enabled by default) and `dnsmasq` (port 53 is already
  taken by BIND, which is the LAN DNS). If you don't use those units, disable them with `systemctl disable --now dnsmasq smartmontools`.
- The `wiringpi` package is held back (`apt-mark hold`) and the `docker-ce` / `containerd.io` are not from Debian: they stay
  as they were; check them if they cause problems.

## Variables

They are passed with `-e nombre=valor` (never with dots).

| Variable | Default | Purpose |
|---|---|---|
| `upgrade_confirm` | `false` | `true` actually runs; `false` only preflight |
| `upgrade_reboot` | `true` | `false` stops before the reboot |
| `upgrade_autoremove` | `false` | `true` runs `apt autoremove` at the end |
| `upgrade_skip_incus_check` | `false` | `true` skips the Incus version check (only for testing) |
| `upgrade_debian_mirror` | `http://ftp.cl.debian.org/debian` | Debian mirror |
| `upgrade_security_mirror` | `http://security.debian.org/debian-security` | Security repository |
