#!/usr/bin/env python3
"""Imprime un campo de un item de 1Password (bóveda HomeLab por defecto).

Lo usan los roles que leen un secreto en la estación del operador (p. ej. wifi_failover). Escribe
SOLO el valor por stdout, sin registrarlo ni mostrarlo en ningún otro lado; los errores van a
stderr y nunca incluyen el valor. Ejecutarlo a mano imprime el secreto en la terminal.

Bóveda y cuenta: ONEPASSWORD_VAULT / ONEPASSWORD_ACCOUNT_NAME (ver onepassword_homelab.py).

Uso:
  python3 ansible/scripts/read_onepassword_field.py --item wifi-homelab --field ssid
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from onepassword_homelab import create_client, op_ref  # noqa: E402


async def read_field(item: str, field: str) -> str:
    client = await create_client()
    value = await client.secrets.resolve(op_ref(field, item=item))
    return value.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--item", required=True)
    parser.add_argument("--field", required=True)
    args = parser.parse_args()
    try:
        value = asyncio.run(read_field(args.item, args.field))
    except Exception as exc:  # noqa: BLE001 — el mensaje de error no contiene el secreto
        print(
            f"No se pudo leer {args.item}/{args.field} de 1Password: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1
    if not value:
        print(f"El campo {args.item}/{args.field} está vacío.", file=sys.stderr)
        return 1
    print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
