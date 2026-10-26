# Update Debian on deborah (12 → 13)

`deborah` (Orange Pi 5 Plus, ARM64 —64-bit ARM architecture—) runs **Debian 12 (bookworm)**; the other two nodes are already on **Debian 13
(trixie)**. The playbook
[`playbook-upgrade-debian13.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-upgrade-debian13.yml)
updates it with backup, a prior simulation, and a **boot gate** that validates before rebooting.

!!! danger "It's the most delicate operation in the Homelab"
    `deborah` is the **K3s control plane**, the **LAN DNS** (BIND) and a member of **Incus**. During this process, the
    Kubernetes API and DNS do not respond (the pods on the other nodes continue running). If the machine does not boot
    after the reboot, physical access (HDMI —video output— or serial console) is required. Do this during maintenance windows.

!!! tip "Simpler if the control plane has already moved"
    Once the control plane is on `oliver` ([Move the control plane](mover-control-plane.md)), `deborah` is
    just a worker: the Kubernetes API continues responding during the update and only its part of the load (LAN DNS, Ollama, and the pods that live on it) falls. It's advisable to do the move **before** this update.

## What Changes and What Doesn't

| Changes | Doesn't Change |
|---|---|
| Debian packages move to trixie (around 600 are updated and about 40 old libraries are removed) | **The manufacturer's kernel** (`5.10.160-rockchip-rk3588`) and the boot with u-boot: they don't come from Debian and apt doesn't touch them |
| `systemd`, `glibc`, `openssh`, `bind9`… to their trixie versions | K3s (its binary is independent), Incus (keeps the same version), and the pods |
| `/tmp` becomes memory (`tmpfs`) after the reboot | `docker-ce` and `containerd.io` (not from Debian; remain as they are) |

Kernel 5.10 meets the minimum recommended by `systemd` 257 (5.4), but this is an unusual case: Debian
documents the update for "pure" systems, not for manufacturer images. That's why the boot gate exists.

## Before You Start

- [ ] **Incus aligned on all three nodes.** The cluster requires the same version on all members. If `deborah`
  has a different Incus version than the repository offers, update Incus on all three nodes first with
  [`playbook-upgrade-incus.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-upgrade-incus.yml)
  (`-e incus_upgrade_confirm=true`; see [Update or Uninstall Incus](../incus/cluster-setup.md#update-or-uninstall-incus)).
  The playbook stops if they don't match (`upgrade_skip_incus_check=true` skips it, only for testing).
- [ ] **Physical access** to `deborah` (HDMI or serial console) and, if possible, an **eMMC image** (`dd` from another
  machine). This is the only complete rollback.
- [ ] Healthy K3s: `kubectl get nodes` with the three `Ready`, and `incus cluster list` with the three `ONLINE`.
- [ ] No one will need the DNS or the Kubernetes API for ~30–60 minutes.

## Step 1 — Preflight and Simulation (Nothing Changes)

```bash
cd ansible
export KUBECONFIG=~/.kube/homelab-k3s.yaml
ansible-playbook -i inventory.ini playbook-upgrade-debian13.yml
```

Without `-e upgrade_confirm=true` it only runs `preflight`: checks that it's Debian 12 on ARM64, free space
(6 GB in `/`, 300 MB in `/boot`), that `dpkg` doesn't have issues, **boot** (u-boot, `uInitrd` in gzip, UUID —unique identifier— of the
root), and the Incus version. Then it downloads the trixie indexes to a separate directory (`/var/tmp`), **simulates** the
update, and **fails if it would remove the kernel, boot, or a Homelab service** (`linux-image`, `orangepi`,
`k3s`, `incus`, `bind9`, `openssh-server`, `netplan`…). Then it deletes that directory.

## Step 2 — Update

```bash
ansible-playbook -i inventory.ini playbook-upgrade-debian13.yml -e upgrade_confirm=true
```

| Phase (tag) | What It Does |
|---|---|
| `backup` | Backs up `/etc`, `/boot`, the state of `dpkg`/`apt`, BIND, and K3s (SQLite, certificates, and token; **stops K3s** before). Brings the files to `ansible/backups/` (ignored by Git) |
| `upgrade` | Pauses automatic updates, keeps Debian 12 up to date, changes the repositories to trixie (Debian and Zabbly), and does `upgrade` and `full-upgrade` while preserving your configuration files (`--force-confold`) |
| `gate` | **Before rebooting:** regenerates and validates the `initrd`, checks `uInitrd`, `boot.scr`, the DTB, kernel modules, the UUID of the root, `sshd -t`, `netplan generate`, and the IP of `br0` |
| `reboot` | Reboots and waits up to 20 minutes |
| `verify` | Confirms Debian 13 with the same kernel, K3s `Ready`, services, DNS, and Incus |
| `cleanup` | Reactivates apt timers and **lists** obsolete packages (doesn't remove them) |

If something fails **before** the reboot, the playbook restarts K3s, leaves the machine powered on, and tells you where
the logs (`/var/log/pre-trixie-upgrade-*.log`) and backup are. To test without rebooting:
`-e upgrade_reboot=false`; the reboot and verification you do manually (`--tags reboot,verify`).

### Why the Boot Gate Exists

The board's boot depends on a u-boot script (`boot.scr`) and a `uInitrd` that the hook
`/etc/initramfs/post-update.d/99-uboot` creates by declaring it **gzip**. If the update left the `initrd`
compressed differently, u-boot couldn't decompress it, and the machine **wouldn't boot**. The playbook requires
`COMPRESS=gzip` in `initramfs.conf` (it's preserved with `--force-confold`) and validates the result with `gzip -t` and
`mkimage -l` before rebooting.

## If the Machine Doesn't Boot

1. Connect a screen or serial console and see where it stops (u-boot, kernel, or `systemd`).
2. If it's the boot: restore the eMMC image you made earlier. With the image, `deborah` returns to Debian 12.
3. Without an image: reinstall the board's system and restore the backup of `ansible/backups/deborah-<fecha>/`:
   `etc.tgz`, `boot.tgz`, `k3s.tgz` (certificates, token, and control plane database, while `deborah` is the control plane) and `bind.tgz`.
   Without the K3s token and certificates, you'd have to reinstall the cluster.
4. The other two nodes continue working, but without a control plane, there are no changes or synchronization.

## Next Steps

- `ansible-playbook -i inventory.ini playbook-upgrade-debian13.yml --tags verify` repeat the verification when you want to.
- **Do not blindly purge** the list of obsolete packages: it includes `linux-image-legacy-rockchip-rk3588`,
  `orangepi-*` and `linux-u-boot-*`, which are what make the board boot.
- With `deborah` in Debian 13, the versions of OVN and Open vSwitch now match those of the other nodes (a prerequisite for considering OVN: see [Load Balancing and OVN](../incus/cluster-setup.md#load-balancing-and-ovn)).
- **Two units may end up in `failed` after a reboot** (`systemctl --failed`), without affecting the cluster:
  `smartmontools` (the eMMC does not have SMART and in Debian 13 the service is enabled by default) and `dnsmasq` (port 53 is already occupied by BIND, which is the LAN DNS). If you do not use those units, disable them with `systemctl disable --now dnsmasq smartmontools`.
- The package `wiringpi` is held back (`apt-mark hold`) and the `docker-ce` / `containerd.io` are not from Debian: they remain as they were; review them if they cause issues.

## Variables

Passed with `-e nombre=valor` (never with dots).

| Variable | Default | Purpose |
|---|---|---|
| `upgrade_confirm` | `false` | `true` runs for real; `false` only preflight |
| `upgrade_reboot` | `true` | `false` stops before reboot |
| `upgrade_autoremove` | `false` | `true` runs `apt autoremove` at the end |
| `upgrade_skip_incus_check` | `false` | `true` skips the Incus version check (for testing only) |
| `upgrade_debian_mirror` | `http://ftp.cl.debian.org/debian` | Debian mirror |
| `upgrade_security_mirror` | `http://security.debian.org/debian-security` | Security repository |
