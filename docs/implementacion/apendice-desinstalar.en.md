# Appendix — Uninstall K3s

Outside the normal [implementation](index.md) path. Use it for a full reset
of the management cluster before reinstalling Phase 3.

## Goal

Remove the K3s (lightweight Kubernetes distribution) server and agents on the 3 nodes in an orderly way.

## Stack

- **[K3s](https://docs.k3s.io/)** — Uninstall scripts in `/usr/local/bin/k3s-uninstall.sh` and `k3s-agent-uninstall.sh`.
- **[Ansible](https://docs.ansible.com/)** — `playbook-k3s-uninstall.yml`.

## Run

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
