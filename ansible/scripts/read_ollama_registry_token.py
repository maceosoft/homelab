#!/usr/bin/env python3
"""Imprime el token del registro de Ollama guardado en 1Password.

Lo usa el rol ollama_node (tarea local en la estación del operador). Escribe SOLO el valor
por stdout, sin registrarlo ni mostrarlo en ningún otro lado; los errores van a stderr y nunca
incluyen el valor. Ejecutarlo a mano imprime el secreto en la terminal.

Referencia por defecto: op://HomeLab/ollama-router/registry_token
(bóveda y cuenta: ONEPASSWORD_VAULT / ONEPASSWORD_ACCOUNT_NAME, ver onepassword_homelab.py).

Uso:
  python3 ansible/scripts/read_ollama_registry_token.py [--item ollama-router] [--field registry_token] [--fallback-field registry_token]
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from onepassword_homelab import create_client, op_ref  # noqa: E402

DEFAULT_ITEM = "ollama-router"
DEFAULT_FIELD = "registry_token"


async def read_token(item: str, field: str, fallback: str | None) -> str:
    client = await create_client()
    try:
        value = await client.secrets.resolve(op_ref(field, item=item))
    except Exception:  # noqa: BLE001 — campo ausente: se prueba el compartido
        if not fallback or fallback == field:
            raise
        value = await client.secrets.resolve(op_ref(fallback, item=item))
    return value.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--item", default=DEFAULT_ITEM)
    parser.add_argument("--field", default=DEFAULT_FIELD)
    parser.add_argument("--fallback-field", default=None, help="campo a usar si --field no existe")
    args = parser.parse_args()
    try:
        token = asyncio.run(read_token(args.item, args.field, args.fallback_field))
    except Exception as exc:  # noqa: BLE001 — el mensaje de error no contiene el secreto
        print(
            f"No se pudo leer {args.item}/{args.field} de 1Password: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1
    if not token:
        print(f"El campo {args.item}/{args.field} está vacío.", file=sys.stderr)
        return 1
    print(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
