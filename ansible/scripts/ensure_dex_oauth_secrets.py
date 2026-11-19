#!/usr/bin/env python3
"""Asegura secretos OAuth generados localmente en 1Password (idempotente).

Genera cada campo listado en DEX_OAUTH_GENERATED_FIELDS (o
dex_oauth_generated_fields en group_vars) si no existe en el ítem.
Por defecto: ninguno (todos los clientes de Dex salvo GitHub son públicos, con PKCE).
Usado por playbook-dex-oauth-secrets.yml (Ansible).

Uso:
  python3 ansible/scripts/ensure_dex_oauth_secrets.py
  python3 ansible/scripts/ensure_dex_oauth_secrets.py --json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from onepassword_homelab import (  # noqa: E402
    config_summary,
    create_client,
    ensure_generated_oauth_fields,
)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Salida JSON para Ansible (fields + generated)",
    )
    args = parser.parse_args()

    client = await create_client()
    result = await ensure_generated_oauth_fields(client)

    if args.json:
        print(json.dumps(result))
    else:
        print(f"1Password {config_summary()}")
        if result["generated"]:
            print("Generados:", ", ".join(result["generated"]))
        else:
            print("Sin cambios: todos los secretos generados ya existían.")
        for name in result["generated"]:
            print(f"  {name}=<nuevo en 1Password>")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except Exception as exc:  # noqa: BLE001 — script CLI
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
