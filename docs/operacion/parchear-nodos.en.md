# Patching the Nodes

Debian patches **don't install themselves**: monitoring only alerts you. Each node publishes how many patches it has
pending (and how many are security patches) and whether it needs a reboot; when something has gone unaddressed for too long, an
alert arrives on Discord (`ParchesDeSeguridadPendientes`, `ReinicioPendiente`; see [Monitoring and alerts](monitoreo.md#que-te-puede-llegar)).
This procedure is what you do when you receive it.

## One time only: enable the alert

Apply the role that publishes the metrics on all nodes
([`playbook-apt-metrics.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-apt-metrics.yml)) from `ansible/`:

```bash
ansible-playbook playbook-apt-metrics.yml
```

It installs a timer that updates the apt lists every 6 hours and writes the result where `node-exporter` reads it. It doesn't install
any packages. Once monitoring is deployed, `SinDatosDePaquetes` reminds you of the nodes where it's missing.

## See what's pending

In Grafana, the *Node Exporter Full* dashboard doesn't show it; query `node_apt_upgrades_pending` in *Explore* (label `origin`:
`security` or `other`). Or directly on the node:

```bash
sudo apt-get update && apt list --upgradable
```

## Recommended order

One node at a time, and `deborah` **last**: it's the LAN's DNS server (BIND) and also
the K3s control plane, so rebooting it cuts off DNS and the cluster API for a few minutes.

1. `eve`
2. `oliver`
3. `invincible`
4. `deborah`

## With Ansible (recommended)

[`playbook-parchear.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-parchear.yml) (role
[`node_patch`](https://github.com/maceosoft/homelab/tree/main/ansible/roles/node_patch)) performs the full procedure in
that order, one node at a time. It needs `kubectl` on your machine with `KUBECONFIG` pointing at the cluster (by default
`~/.kube/homelab-k3s.yaml`) and a terminal where you can answer the confirmation prompts. From `ansible/`:

First, a dry run. It doesn't drain or reboot: it shows which packages would be updated on each node and whether a reboot would be needed.

```bash
ansible-playbook -i inventory.ini playbook-parchear.yml --check
```

Then, node by node, or all in a row:

```bash
ansible-playbook -i inventory.ini playbook-parchear.yml -l eve
ansible-playbook -i inventory.ini playbook-parchear.yml -l oliver
ansible-playbook -i inventory.ini playbook-parchear.yml -l invincible
ansible-playbook -i inventory.ini playbook-parchear.yml -l deborah
```

```bash
ansible-playbook -i inventory.ini playbook-parchear.yml
```

On each node:

1. **Pre-check** (tag `precheck`): all nodes are `Ready` and no Longhorn volume is `degraded` or `faulted`. Otherwise, it
   stops without touching anything. Detached volumes (`detached`) show up as `unknown` and don't count as a failure.
2. **Update** (tag `upgrade`): lists the pending packages and runs `apt-get update` and `dist-upgrade`.
3. **Reboot** (tag `reboot`), only if `/var/run/reboot-required` exists: drains the node from your machine, reboots it, waits for
   `Ready` to come back and runs `uncordon`. If a reboot isn't needed, it doesn't drain. If something fails while the node is drained, it tries
   `uncordon` and stops with a message.
4. **Post-check** (tag `postcheck`): waits, up to 15 minutes, for the node to be `Ready` and Longhorn to have no degraded volumes
   before moving on to the next one.

The order is set by the variable `node_patch_order`, not by the inventory. The K3s control plane and `deborah` are always moved to the
end, even if they are listed earlier, and they **ask for confirmation twice**: before updating (if `bind9` is updated, `named`
restarts and DNS is cut off for a few seconds) and before rebooting. On any failure, it doesn't continue to the next node.

Only part of it:

```bash
ansible-playbook -i inventory.ini playbook-parchear.yml --tags precheck
ansible-playbook -i inventory.ini playbook-parchear.yml -l oliver --tags upgrade,postcheck
```

Useful variables (with `-e`): `node_patch_order`, `node_patch_autoremove` (removes unused dependencies; default `false`),
`node_patch_drain_timeout`, `node_patch_reboot_timeout`, `node_patch_postcheck_minutes`.

## By hand

If you can't use Ansible, for each node:

1. Check that the cluster is healthy: `kubectl get nodes` (all `Ready`) and that the Longhorn volumes aren't degraded
   (Longhorn UI, see [URLs and access](urls-y-accesos.md)). If a volume already has only one replica, don't reboot a node that holds the other one.
2. SSH in ([access](acceso-ssh.md)) and install: `sudo apt-get update && sudo apt-get dist-upgrade`.
3. If a reboot is needed (`/var/run/reboot-required` exists, or the `ReinicioPendiente` alert):
   `kubectl drain <nodo> --ignore-daemonsets --delete-emptydir-data`, then `sudo reboot`.
4. When it comes back, `kubectl uncordon <nodo>` and wait for the node to be `Ready` and the Longhorn volumes healthy
   before moving on to the next one.

After a while (up to 6 hours, or run `sudo systemctl start node-apt-metrics.service`), that node's alerts resolve on their own.
