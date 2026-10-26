# Apéndice — Desinstalar K3s

Fuera del recorrido normal de [implementación](index.md). Usar para reset completo
del management cluster antes de reinstalar Fase 3.

## Objetivo

Eliminar K3s (distribución ligera de Kubernetes) server y agents en los 3 nodos de forma ordenada.

## Stack

- **[K3s](https://docs.k3s.io/)** — Scripts de desinstalación en `/usr/local/bin/k3s-uninstall.sh` y `k3s-agent-uninstall.sh`.
- **[Ansible](https://docs.ansible.com/)** — `playbook-k3s-uninstall.yml`.

## Ejecutar

```bash
cd ansible
ansible-playbook -i inventory.ini playbook-k3s-uninstall.yml
```

## Verificar

```bash
ansible -i ansible/inventory.ini incus_cluster -m command -a "systemctl is-active k3s" || true
# inactive / failed en todos
```

## Siguiente

Reinstalar: **[Fase 3 — K3s](fase-3-k3s.md)**
