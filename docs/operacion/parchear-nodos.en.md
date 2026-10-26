# Patch the nodes

Debian patches **are not installed automatically**: monitoring only warns. Each node publishes how many patches are
pending (and how many are security patches) and whether it needs a reboot; when something has gone unattended for too long, an
alert arrives on Discord (`ParchesDeSeguridadPendientes`, `ReinicioPendiente`; see [Monitoring and alerts](monitoreo.md#que-te-puede-llegar)).
This procedure is what you do when you receive it.

## Once: enable the notice

Apply the role that publishes the metrics on the three nodes
([`playbook-apt-metrics.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-apt-metrics.yml)) from `ansible/`:

```bash
ansible-playbook playbook-apt-metrics.yml
```

It installs a timer that refreshes the apt lists every 6 hours and writes the result where `node-exporter` reads it. It does not install
any package. With monitoring already deployed, `SinDatosDePaquetes` reminds you of the nodes where it is missing.

## See what is pending

In Grafana, the *Node Exporter Full* dashboard does not show it; query `node_apt_upgrades_pending` in *Explore* (`origin` label:
`security` or `other`). Or directly on the node:

```bash
sudo apt-get update && apt list --upgradable
```

## Recommended order

One node at a time, with `deborah` **last**: it is the LAN DNS server (BIND) and, until the control plane move, also
the K3s one, so rebooting it cuts the DNS and the cluster API for a few minutes.

1. `oliver`
2. `invincible`
3. `deborah`

## With Ansible (recommended)

[`playbook-parchear.yml`](https://github.com/maceosoft/homelab/blob/main/ansible/playbook-parchear.yml) (role
[`node_patch`](https://github.com/maceosoft/homelab/tree/main/ansible/roles/node_patch)) runs the whole procedure in
that order, one node at a time. It needs `kubectl` on your machine with `KUBECONFIG` pointing to the cluster (by default
`~/.kube/homelab-k3s.yaml`) and a terminal where you can answer the confirmations. From `ansible/`:

First, a dry run. It does not drain or reboot: it shows which packages would be upgraded on each node and whether a reboot would be needed.

```bash
ansible-playbook -i inventory.ini playbook-parchear.yml --check
```

Then, node by node, or all in a row:

```bash
ansible-playbook -i inventory.ini playbook-parchear.yml -l oliver
ansible-playbook -i inventory.ini playbook-parchear.yml -l invincible
ansible-playbook -i inventory.ini playbook-parchear.yml -l deborah
```

```bash
ansible-playbook -i inventory.ini playbook-parchear.yml
```

On each node:

1. **Pre-check** (tag `precheck`): all nodes `Ready` and no Longhorn volume `degraded` or `faulted`. Otherwise it
   stops without touching anything. Disconnected volumes (`detached`) show up as `unknown` and do not count as a failure.
2. **Upgrade** (tag `upgrade`): lists the pending packages and runs `apt-get update` and `dist-upgrade`.
3. **Reboot** (tag `reboot`), only if `/var/run/reboot-required` exists: drains the node from your machine, reboots it, waits for
   it to come back `Ready` and runs `uncordon`. If no reboot is needed, it does not drain. If something fails with the node drained, it tries the
   `uncordon` and stops with a message.
4. **Post-check** (tag `postcheck`): waits, up to 15 minutes, for the node to be `Ready` and Longhorn to have no degraded
   volumes before moving on to the next one.

The order is set by the `node_patch_order` variable, not by the inventory. The K3s control plane and `deborah` are always moved to the
end, even if written earlier, and **ask for confirmation twice**: before upgrading (if `bind9` is upgraded, `named`
restarts and the DNS goes down for a few seconds) and before rebooting. On any failure, it does not continue with the next node.

Only part of it:

```bash
ansible-playbook -i inventory.ini playbook-parchear.yml --tags precheck
ansible-playbook -i inventory.ini playbook-parchear.yml -l oliver --tags upgrade,postcheck
```

Useful variables (with `-e`): `node_patch_order`, `node_patch_autoremove` (removes unused dependencies; `false` by default),
`node_patch_drain_timeout`, `node_patch_reboot_timeout`, `node_patch_postcheck_minutes`.

## By hand

If you cannot use Ansible, for each node:

1. Check that the cluster is healthy: `kubectl get nodes` (all `Ready`) and that the Longhorn volumes are not degraded
   (Longhorn UI, see [URLs and access](urls-y-accesos.md)). If a volume already has a single replica, do not reboot a node that holds the other one.
2. SSH in ([access](acceso-ssh.md)) and install: `sudo apt-get update && sudo apt-get dist-upgrade`.
3. If a reboot is needed (`/var/run/reboot-required` exists, or the `ReinicioPendiente` alert):
   `kubectl drain <nodo> --ignore-daemonsets --delete-emptydir-data`, then `sudo reboot`.
4. When it comes back, `kubectl uncordon <nodo>` and wait for the node to be `Ready` and the Longhorn volumes healthy
   before moving on to the next one.

After a while (up to 6 hours, or run `sudo systemctl start node-apt-metrics.service`), that node's alerts resolve themselves.
