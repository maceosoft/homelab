"""Helpers 1Password SDK para homelab (DesktopAuth — app local).

Usado por:
  ansible/scripts/test-1password.py
  ansible/scripts/ensure_dex_oauth_secrets.py
  ansible/scripts/apply_dex_oauth_to_argocd.py
  gitops/argocd/secrets/apply-from-1password.py

Configuración vía variables de entorno (ver gitops/argocd/secrets/1password.md):
  ONEPASSWORD_ACCOUNT_NAME — cuenta personal (sidebar); ej. Mi Cuenta
  ONEPASSWORD_VAULT        — bóveda; default HomeLab
  ONEPASSWORD_ITEM         — ítem con los secretos de Dex; default maceosoft-dex
"""
from __future__ import annotations

import os
import secrets

from onepassword import (
    Client,
    DesktopAuth,
    ItemCategory,
    ItemCreateParams,
    ItemField,
    ItemFieldType,
)

# Cuenta personal por defecto (no empresa). Ejemplo: Mi Cuenta
ACCOUNT_NAME = os.getenv("ONEPASSWORD_ACCOUNT_NAME", "Personal")

# Bóveda e ítem de Dex: op://HomeLab/maceosoft-dex/GITHUB_CLIENT_ID
VAULT_NAME = os.getenv("ONEPASSWORD_VAULT", "HomeLab")
ITEM_NAME = os.getenv("ONEPASSWORD_ITEM", "maceosoft-dex")

INTEGRATION_NAME = os.getenv("ONEPASSWORD_INTEGRATION_NAME", "Homelab GitOps")
INTEGRATION_VERSION = os.getenv("ONEPASSWORD_INTEGRATION_VERSION", "1.0.0")

# Campo en 1Password → clave en argocd-secret
DEX_OAUTH_FIELD_MAP: dict[str, str] = {
    "GITHUB_CLIENT_ID": "dex.github.clientId",
    "GITHUB_CLIENT_SECRET": "dex.github.clientSecret",
    "VCLUSTER_CLIENT_SECRET": "dex.vcluster.platform.clientSecret",
}

# Generados por Ansible si faltan en 1Password (lista única — también en group_vars)
DEFAULT_GENERATED_OAUTH_FIELDS = "VCLUSTER_CLIENT_SECRET"


def generated_oauth_fields() -> tuple[str, ...]:
    raw = os.getenv("DEX_OAUTH_GENERATED_FIELDS", DEFAULT_GENERATED_OAUTH_FIELDS)
    return tuple(f.strip() for f in raw.split(",") if f.strip())


# Compat: módulos que importan GENERATED_OAUTH_FIELDS
GENERATED_OAUTH_FIELDS = generated_oauth_fields()


def op_ref(field: str, *, item: str | None = None, vault: str | None = None) -> str:
    """Construye op://vault/item/field."""
    return f"op://{vault or VAULT_NAME}/{item or ITEM_NAME}/{field}"


async def create_client() -> Client:
    try:
        return await Client.authenticate(
            auth=DesktopAuth(account_name=ACCOUNT_NAME),
            integration_name=INTEGRATION_NAME,
            integration_version=INTEGRATION_VERSION,
        )
    except Exception as exc:  # noqa: BLE001 — mensaje accionable para el operador
        if "account not found" in str(exc).lower():
            origen = "ONEPASSWORD_ACCOUNT_NAME" if os.getenv("ONEPASSWORD_ACCOUNT_NAME") else "valor por defecto (sin ONEPASSWORD_ACCOUNT_NAME)"
            raise RuntimeError(
                f"1Password no encuentra la cuenta {ACCOUNT_NAME!r} ({origen}). "
                "Define el nombre de tu cuenta tal como aparece en la barra lateral "
                'de la app de 1Password, p. ej.: export ONEPASSWORD_ACCOUNT_NAME="Mi Cuenta"'
            ) from exc
        raise


def config_summary() -> str:
    return (
        f"cuenta={ACCOUNT_NAME!r} bóveda={VAULT_NAME!r} "
        f"ítem={ITEM_NAME!r}"
    )


async def resolve_field(client: Client, field: str) -> str:
    return await client.secrets.resolve(op_ref(field))


async def resolve_dex_oauth_secrets(client: Client) -> dict[str, str]:
    """Lee todos los campos OAuth Dex y devuelve claves argocd-secret."""
    result: dict[str, str] = {}
    for op_field, secret_key in DEX_OAUTH_FIELD_MAP.items():
        result[secret_key] = await resolve_field(client, op_field)
    return result


def generate_client_secret() -> str:
    """Secret compartido Dex ↔ cliente OIDC (64 hex chars)."""
    return secrets.token_hex(32)


async def find_vault_id(client: Client, vault_name: str | None = None) -> str:
    # Sin distinguir mayúsculas, igual que las referencias op://
    # (op://HomeLab/... encuentra la bóveda "HomeLab").
    name = vault_name or VAULT_NAME
    vaults = await client.vaults.list()
    for vault in vaults:
        if vault.title.lower() == name.lower():
            return vault.id
    visibles = ", ".join(repr(v.title) for v in vaults) or "ninguna"
    raise ValueError(f"Bóveda 1Password no encontrada: {name!r} (bóvedas visibles: {visibles})")


async def get_item_by_title(
    client: Client, *, vault_id: str | None = None, item_title: str | None = None
):
    vid = vault_id or await find_vault_id(client)
    title = item_title or ITEM_NAME
    for overview in await client.items.list(vid):
        if overview.title.lower() == title.lower():
            return await client.items.get(vid, overview.id)
    return None


async def set_item_field(
    client: Client,
    field_title: str,
    value: str,
    *,
    vault_id: str | None = None,
    item_title: str | None = None,
) -> None:
    vid = vault_id or await find_vault_id(client)
    title = item_title or ITEM_NAME
    item = await get_item_by_title(client, vault_id=vid, item_title=title)
    if item is None:
        params = ItemCreateParams(
            title=title,
            category=ItemCategory.SECURENOTE,
            vault_id=vid,
            fields=[
                ItemField(
                    id=field_title.lower(),
                    title=field_title,
                    field_type=ItemFieldType.CONCEALED,
                    value=value,
                )
            ],
        )
        await client.items.create(params)
        return

    for field in item.fields:
        if field.title == field_title:
            field.value = value
            await client.items.put(item)
            return

    item.fields.append(
        ItemField(
            id=field_title.lower(),
            title=field_title,
            field_type=ItemFieldType.CONCEALED,
            value=value,
        )
    )
    await client.items.put(item)


async def ensure_generated_oauth_fields(client: Client) -> dict[str, object]:
    """Genera en 1Password los campos locales si no existen. Idempotente."""
    values: dict[str, str] = {}
    generated: list[str] = []

    for field_name in generated_oauth_fields():
        try:
            values[field_name] = await resolve_field(client, field_name)
        except Exception:  # noqa: BLE001 — campo ausente o referencia inválida
            secret = generate_client_secret()
            await set_item_field(client, field_name, secret)
            values[field_name] = secret
            generated.append(field_name)

    return {"fields": values, "generated": generated}
