#!/usr/bin/env python3
"""Rota la password de root de los nodos del homelab y la guarda en 1Password.

Genera una password nueva por host (no es idempotente a proposito: cada
corrida rota), la guarda en la boveda HomeLab en un item dedicado por host
(`root@<hostname>`, campo `password`), y la imprime para que
playbook-rotate-root-passwords.yml la aplique de verdad en el host via
`ansible.builtin.user` + `become`. Este script SOLO habla con 1Password —
nunca toca los nodos por SSH directamente (ver el playbook para eso).

Motivo (2026-09): tras el incidente de deborah (DMZ + password default de
la imagen Orange Pi), tambien vale la pena rotar la password local de root
en los 3 nodos como defensa en profundidad (consola/`su -`, no SSH: PermitRootLogin
ya esta en "no" via host_hardening).

Uso:
  export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"
  export ONEPASSWORD_VAULT="HomeLab"

  # Los 3 nodos por defecto:
  python3 ansible/scripts/rotate_root_passwords.py --json

  # Uno solo (asi lo invoca el playbook, un host por vez):
  python3 ansible/scripts/rotate_root_passwords.py --json deborah
"""
from __future__ import annotations

import asyncio
import json
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from onepassword_homelab import (  # noqa: E402
    config_summary,
    create_client,
    find_vault_id,
    set_item_field,
)

DEFAULT_HOSTS = ("invincible", "oliver", "deborah")
PASSWORD_FIELD = "password"


def generate_root_password() -> str:
    """Password nueva, alfabeto URL-safe (sin caracteres raros para shell/YAML)."""
    return secrets.token_urlsafe(24)


async def rotate_host(client, vault_id: str, host: str) -> str:
    new_password = generate_root_password()
    await set_item_field(
        client,
        PASSWORD_FIELD,
        new_password,
        vault_id=vault_id,
        item_title=f"root@{host}",
    )
    return new_password


async def main() -> int:
    args = sys.argv[1:]
    as_json = "--json" in args
    hosts = tuple(a for a in args if a != "--json") or DEFAULT_HOSTS

    if not as_json:
        print(f"1Password {config_summary()} hosts={hosts!r}", file=sys.stderr)

    client = await create_client()
    vault_id = await find_vault_id(client)

    passwords: dict[str, str] = {}
    for host in hosts:
        passwords[host] = await rotate_host(client, vault_id, host)

    if as_json:
        print(json.dumps(passwords))
    else:
        for host in hosts:
            print(f"{host}: guardado en 1Password (item root@{host})")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except Exception as exc:  # noqa: BLE001 — script CLI
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
