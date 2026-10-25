#!/usr/bin/env python3
"""Prueba lectura 1Password SDK (DesktopAuth, app local).

Lee los secretos de Dex del ítem maceosoft-dex (bóveda HomeLab):
  op://HomeLab/maceosoft-dex/GITHUB_CLIENT_ID

Uso:
  export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"   # si tu cuenta no se llama Personal
  python3 ansible/scripts/test-1password.py

  # Un solo campo:
  python3 ansible/scripts/test-1password.py GITHUB_CLIENT_ID
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Importar onepassword_homelab desde este directorio
sys.path.insert(0, str(Path(__file__).resolve().parent))

from onepassword_homelab import (  # noqa: E402
    config_summary,
    create_client,
    resolve_field,
)

DEFAULT_TEST_FIELD = "GITHUB_CLIENT_ID"


async def main() -> int:
    field = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TEST_FIELD
    print(f"1Password {config_summary()} campo={field!r}")
    client = await create_client()
    value = await resolve_field(client, field)
    print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
