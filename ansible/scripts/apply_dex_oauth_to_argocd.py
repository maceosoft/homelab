#!/usr/bin/env python3
"""Inyecta secretos Dex OAuth desde 1Password en argocd-secret.

Invocado por playbook-dex-oauth-secrets.yml. Ejecutar ensure_dex_oauth_secrets
antes si faltan VCLUSTER_CLIENT_SECRET.
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from onepassword_homelab import (  # noqa: E402
    config_summary,
    create_client,
    ensure_generated_oauth_fields,
    resolve_dex_oauth_secrets,
)

SECRET_NAME = "argocd-secret"
NAMESPACE = "argocd"


def patch_argocd_secret(string_data: dict[str, str]) -> None:
    # El parche va por stdin: en argv quedaría visible en `ps` y en el mensaje de error de CalledProcessError.
    subprocess.run(
        [
            "kubectl",
            "patch",
            "secret",
            SECRET_NAME,
            "-n",
            NAMESPACE,
            "--type",
            "merge",
            "--patch-file",
            "/dev/stdin",
        ],
        input=json.dumps({"stringData": string_data}),
        text=True,
        check=True,
    )


async def main() -> int:
    print(f"1Password {config_summary()}")
    client = await create_client()
    await ensure_generated_oauth_fields(client)
    secrets = await resolve_dex_oauth_secrets(client)
    patch_argocd_secret(secrets)
    print("argocd-secret actualizado.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except Exception as exc:  # noqa: BLE001 — script CLI
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
