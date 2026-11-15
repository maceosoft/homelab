# Appendix — Uninstall K3s

Outside the normal [deployment](index.md) path. Use to completely reset the management cluster before reinstalling Phase 3.

## Objective

Remove K3s (lightweight Kubernetes distribution) server and agents from all nodes in an orderly manner.

## Stack

- **[K3s](https://docs.k3s.io/)** — Uninstallation scripts in `/usr/local/bin/k3s-uninstall.sh` and `k3s-agent-uninstall.sh`.
- **[Ansible](https://docs.ansible.com/)** — `playbook-k3s-uninstall.yml`.

## Execute

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-k3s-uninstall.yml
```

## Verify

```bash
ansible -i ansible/inventory.ini incus_cluster -m command -a "systemctl is-active k3s" || true
# inactive / failed en todos
```

## Next

Reinstall: **[Phase 3 — K3s](fase-3-k3s.md)**
