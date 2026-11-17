#!/usr/bin/env python3
"""Secretos de plataforma de la org maceosoft: 1Password -> clúster.

Crea (o actualiza) los namespaces y Secrets que tienen que existir ANTES de
GitOps, y que no pueden vivir en git:

  argocd/repo-gitops                       App maceosoft-argocd: ArgoCD lee maceosoft/gitops (privado)
  arc-runners/arc-runners-github-app       App de ARC (registro del runner)
  arc-runners-symintel/...                 App de ARC y de OpenTofu de la org antigua (symintel), opcional: ver abajo
  kube-system/sealed-secrets-key-homelab   llave de Sealed Secrets (opcional, ver abajo)
  monitoring/discord-webhooks              webhooks de Discord de Alertmanager (opcional: monitoreo)
  monitoring/healthchecks-ping             ping URL de healthchecks.io (opcional: monitoreo)
  monitoring/grafana-admin                 usuario y contraseña de admin de Grafana (opcional: monitoreo)
  argocd/argocd-notifications-secret       webhooks de Discord de las notificaciones de ArgoCD (opcional:
                                           campo "deployments" de discord-webhooks)
  ai/open-webui-secret                     WEBUI_SECRET_KEY de Open WebUI (opcional: asistente de IA)
  ai/ollama-router-secrets                 tokens del router de Ollama, todos los campos del item (opcional: IA)
  ai/ollama-token-open-webui               token de Open WebUI ante el router (clave "token")
  monitoring/ollama-token-reports          token de los reportes diario/semanal (clave "token")
  monitoring/ollama-token-alert-triage     token de alert-triage ante el router (clave "token")
  k8sgpt-operator-system/ollama-token-k8sgpt   token de K8sGPT ante el router (clave "token")
  monitoring/alert-triage-webhook          token del webhook de alert-triage (opcional; clave "token")
  ai/mcp-api-key                           API key de mcpo, los tool servers MCP (opcional; clave "key")
  monitoring/mcp-api-key                   la misma, para que alert-triage use los tool servers
  monitoring/anthropic-api-key             API key de Claude para alert-triage (opcional; clave "api_key")
  ai/anthropic-api-key                     la misma, para Open WebUI (clave "api_key")
  ai/nvidia-api-key                        API key de NVIDIA para Open WebUI (opcional; clave "api_key")
  ai-sandbox/open-terminal-api-key         API key de Open Terminal (opcional; clave "api_key"; el namespace y su PSA son de GitOps)
  ai/open-terminal-api-key                 el mismo valor, para Open WebUI (clave "api_key")
  postgres/postgres-homelab-agent          rol homelab_agent del PostgreSQL de la plataforma (CloudNativePG):
                                           kubernetes.io/basic-auth, etiqueta cnpg.io/reload
  ai/homelab-agent-postgres                DATABASE_URL de homelab-agent (misma contraseña)
  postgres/postgres-s3                     llave del bucket postgres-backups de Incus (opcional; respaldos)
  postgres/incus-s3-ca                     CA del HomeLab (solo el certificado público, ca.crt de
                                           cert-manager/homelab-ca): valida el S3 de Incus
  namespace terraform                      state de OpenTofu (lo escribe el runner)

Además BORRA de arc-runners los Secrets terraform-app, tofu-vars y argocd-ci si
existen (OBSOLETE_RUNNER_SECRETS). Antes se creaban aquí y el scale set de
maceosoft los cargaba con envFrom en el entorno de TODOS los jobs, incluido el
código de un PR. Ahora una credencial llega solo al paso que la usa, como
secreto de GitHub Actions (el token de ArgoCD del diff: secreto ARGOCD_CI_TOKEN
de maceosoft/gitops; ver docs/operacion/pipeline-gitops.md). Por eso el script
ya no lee los items maceosoft-terraform, ftp-<repo> ni argocd-ci.

Items esperados en la bóveda (ONEPASSWORD_VAULT, default HomeLab); ver
docs/maceosoft/github.md:

  maceosoft-argocd       app_id, installation_id, private_key
  sealed-secrets        (opcional) certificate, private_key: el par de Sealed Secrets
  maceosoft-arc-runners  app_id, installation_id, private_key
  symintel-arc-runners  (opcional) app_id, installation_id, private_key: App de ARC de la org antigua; crea el namespace
                        arc-runners-symintel y su Secret arc-runners-github-app (Application arc-runners-symintel)
  symintel-terraform    (opcional) app_id, installation_id, private_key: App de OpenTofu de la org antigua
  discord-webhooks      (opcional, monitoreo) critical, warnings: URL de un webhook de Discord por canal;
                        deployments (opcional): webhook del canal de despliegues, para las notificaciones de ArgoCD
                        ai (opcional): webhook del canal #ia, para el reporte semanal con IA (clave "ai" del Secret)
  healthchecks-ping     (opcional, monitoreo) url: ping URL del check de healthchecks.io
  grafana-admin         (opcional, monitoreo) password y, si quieres, username (default: admin)
  open-webui            (opcional, asistente de IA) WEBUI_SECRET_KEY: clave aleatoria de 64 caracteres hex
                        (cómo generarla: docs/operacion/ia-ollama.md)
  ollama-router         (opcional, IA) registry_token, open-webui, k8sgpt, reports, alert-triage, translate: un token por
                        cliente del router de Ollama (>= 32 caracteres sin espacios; genéralos con: openssl rand -hex 32)
  alert-triage-webhook  (opcional, IA) token: Bearer con el que Alertmanager llama a alert-triage (openssl rand -hex 32)
  mcp-api-key           (opcional, IA) key: API key de mcpo para los tool servers MCP (openssl rand -hex 32)
  Anthropic-apikey      (opcional, IA) api-key: API key de Claude (console.anthropic.com, workspace con tope de gasto)
  Nvidia-Apikey         (opcional, IA) password: API key de NVIDIA (build.nvidia.com)
  open-terminal         (opcional, IA) api_key: API key de Open Terminal (>= 32 caracteres sin espacios; openssl rand -hex 32)
  postgres-homelab-agent  password: contraseña del rol homelab_agent. Si falta, al aplicar se GENERA (64 hex) y se
                        guarda en el item (con --dry-run no se escribe nada en 1Password)
  postgres-s3           (opcional, respaldos) access_key, secret_key: la llave del bucket postgres-backups de Incus
                        (la crea el operador: docs/storage/postgres.md)

Uso:
  python3 ansible/scripts/apply_platform_secrets.py            # aplica
  python3 ansible/scripts/apply_platform_secrets.py --dry-run  # imprime manifiestos sin secretos
  python3 ansible/scripts/apply_platform_secrets.py --check    # qué campos tiene cada item y qué falta
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import re
import secrets
import subprocess
import sys
import textwrap
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))

from onepassword_homelab import VAULT_NAME, create_client, find_vault_id, set_item_field  # noqa: E402

# Tiene que coincidir con el repoURL de las Applications de maceosoft/gitops.
GITOPS_REPO_URL = "https://github.com/maceosoft/gitops.git"
RUNNER_NAMESPACE = "arc-runners"
# Org antigua (symintel): su scale set corre en otro namespace, con los mismos nombres de Secret. Opcional.
LEGACY_ORG = "symintel"
LEGACY_RUNNER_NAMESPACE = "arc-runners-symintel"
LEGACY_ARC_ITEM = "symintel-arc-runners"
LEGACY_TF_ITEM = "symintel-terraform"
STATE_NAMESPACE = "terraform"
# Secrets que este script creaba en arc-runners y que el scale set cargaba en el entorno de todos los jobs. Ya no se
# crean y, al aplicar, se borran si existen (idempotente). El token de ArgoCD del diff vive ahora en 1Password (item
# argocd-ci) y en el secreto de GitHub Actions ARGOCD_CI_TOKEN de maceosoft/gitops: este script ya no lo lee.
OBSOLETE_RUNNER_SECRETS = ("terraform-app", "tofu-vars", "argocd-ci")
ARGOCD_CI_ITEM = "argocd-ci"
# Par de llaves de Sealed Secrets, generado por el operador (docs/maceosoft/github.md).
# El controlador usa un Secret tls de kube-system con la etiqueta "active" en vez de
# generar su propia llave: así los SealedSecret de git sobreviven a reinstalar K3s.
# Opcional: hasta la Fase 6 (CAPN) nada lo necesita.
SEALED_ITEM = "sealed-secrets"
SEALED_NAMESPACE = "kube-system"
SEALED_SECRET_NAME = "sealed-secrets-key-homelab"
SEALED_LABEL = "sealedsecrets.bitnami.com/sealed-secrets-key"
# Monitoreo (opcional): VictoriaMetrics + Alertmanager + Grafana en el namespace "monitoring". Si no existe
# ninguno de los tres items, no se configura nada; si existe alguno, tienen que estar completos los tres.
# El namespace es "privileged" porque node-exporter usa hostPath/hostNetwork.
MONITORING_NAMESPACE = "monitoring"
# Notificaciones de ArgoCD a Discord: el Secret ya lo crea el manifiesto de ArgoCD (vacío); aquí solo se le añaden
# las claves que leen sus servicios (gitops: addons/argocd/config/notifications). "avisos" reutiliza el webhook "warnings".
ARGOCD_NAMESPACE = "argocd"
ARGOCD_NOTIFICATIONS_SECRET = "argocd-notifications-secret"
DISCORD_ITEM = "discord-webhooks"
# Asistente de IA (opcional): Open WebUI (gitops: bootstrap/components/open-webui.yaml) lee este Secret en el namespace "ai".
AI_NAMESPACE = "ai"
OPEN_WEBUI_ITEM = "open-webui"
OPEN_WEBUI_SECRET_NAME = "open-webui-secret"
# Firma las sesiones de Open WebUI: una clave corta o con patrón sería adivinable.
OPEN_WEBUI_KEY_RE = re.compile(r"^[0-9a-f]{64}$")
# Router de Ollama (gitops: addons/ai/ollama-router): un token Bearer por cliente. El Secret del router lleva todos los campos del
# item; cada cliente recibe solo el suyo (clave "token") en el namespace donde corre.
OLLAMA_ROUTER_ITEM = "ollama-router"
OLLAMA_ROUTER_SECRET = "ollama-router-secrets"
OLLAMA_ROUTER_FIELDS = ("registry_token", "open-webui", "k8sgpt", "reports", "alert-triage", "translate")
# campo del item -> namespace del Secret ollama-token-<campo> (translate y registry_token no tienen Secret propio)
OLLAMA_CLIENT_TOKENS = {
    "open-webui": AI_NAMESPACE,
    "reports": MONITORING_NAMESPACE,
    "alert-triage": MONITORING_NAMESPACE,
    "k8sgpt": "k8sgpt-operator-system",
}
# Items de un solo campo: item -> (campo, [(namespace, Secret, clave), ...]); el mismo valor va a cada destino.
SANDBOX_NAMESPACE = "ai-sandbox"
# Namespaces cuyas etiquetas PSA declara GitOps (ai-sandbox: restricted en gitops addons/ai/open-terminal/namespace.yaml): este script
# solo se asegura de que existan, sin etiqueta PSA, y con la anotación que impide que ArgoCD los pode.
GITOPS_NAMESPACES = (AI_NAMESPACE, SANDBOX_NAMESPACE)
SINGLE_TOKEN_ITEMS = {
    "alert-triage-webhook": ("token", [(MONITORING_NAMESPACE, "alert-triage-webhook", "token")]),
    # mcpo (gitops: addons/ai/tools) la exige; alert-triage (monitoring) la presenta para diagnosticar con las herramientas.
    "mcp-api-key": ("key", [(AI_NAMESPACE, "mcp-api-key", "key"), (MONITORING_NAMESPACE, "mcp-api-key", "key")]),
    # API keys de Claude y NVIDIA: alert-triage (gitops: addons/ai/alert-triage) y Open WebUI (gitops: bootstrap/components/open-webui.yaml).
    "Anthropic-apikey": ("api-key", [(MONITORING_NAMESPACE, "anthropic-api-key", "api_key"), (AI_NAMESPACE, "anthropic-api-key", "api_key")]),
    "Nvidia-Apikey": ("password", [(AI_NAMESPACE, "nvidia-api-key", "api_key")]),
    "open-terminal": ("api_key", [(SANDBOX_NAMESPACE, "open-terminal-api-key", "api_key"), (AI_NAMESPACE, "open-terminal-api-key", "api_key")]),
}
# Un token corto o con espacios sería adivinable o rompería la cabecera Authorization.
TOKEN_MIN_LEN = 32
# PostgreSQL de la plataforma (gitops: addons/storage/postgres, Cluster CNPG "postgres"). El namespace y sus etiquetas
# son de GitOps: aquí solo se asegura que exista para poder crear los Secrets antes que el Cluster.
POSTGRES_NAMESPACE = "postgres"
# Rol y base de homelab-agent. La contraseña vive solo en 1Password; si falta, se genera al aplicar.
POSTGRES_APP_ITEM = "postgres-homelab-agent"
POSTGRES_APP_FIELD = "password"
POSTGRES_APP_USER = "homelab_agent"
POSTGRES_APP_DB = "homelab_agent"
POSTGRES_APP_SECRET = "postgres-homelab-agent"
POSTGRES_RW_HOST = "postgres-rw.postgres.svc:5432"
# La app corre en "ai" y los Secrets no cruzan namespaces: su cadena de conexión va en su propio Secret.
POSTGRES_APP_URL_SECRET = (AI_NAMESPACE, "homelab-agent-postgres")
# Con esta etiqueta CNPG recarga el Secret al cambiar (rotar la contraseña o la llave S3 sin reiniciar).
CNPG_RELOAD_LABELS = {"cnpg.io/reload": "true"}
# Respaldos a S3 (bucket postgres-backups de Incus, rol incus_s3): llave del bucket y CA que firma el endpoint.
POSTGRES_S3_ITEM = "postgres-s3"
POSTGRES_S3_FIELDS = {"access_key": "ACCESS_KEY_ID", "secret_key": "ACCESS_SECRET_KEY"}
POSTGRES_S3_SECRET = "postgres-s3"
INCUS_S3_CA_SECRET = "incus-s3-ca"
S3_KEY_MIN_LEN = 16
# CA del HomeLab: se lee SOLO la clave ca.crt (pública). El mismo Secret guarda la llave de la CA: nunca se pide entera.
HOMELAB_CA = ("cert-manager", "homelab-ca")
# Valor de muestra en --dry-run cuando la contraseña todavía no existe (no se imprime: redact() oculta los valores).
PENDING_PASSWORD = "<se genera al aplicar>"
HEARTBEAT_ITEM = "healthchecks-ping"
GRAFANA_ITEM = "grafana-admin"
# Un webhook de Discord con otro destino mandaría las alertas a un tercero: se valida el formato.
DISCORD_WEBHOOK_RE = re.compile(r"^https://(?:discord|discordapp)\.com/api/webhooks/\d+/[A-Za-z0-9_-]+$")


def normalize_pem(value: str) -> str:
    """Rearma un PEM cuyo cuerpo perdió los saltos de línea (campo de una línea en 1Password)."""
    m = re.search(r"-----BEGIN ([A-Z ]+)-----(.*?)-----END \1-----", value, re.S)
    if not m:
        raise ValueError("el campo no contiene un bloque PEM (-----BEGIN ...-----)")
    label, body = m.group(1), re.sub(r"\s+", "", m.group(2))
    return f"-----BEGIN {label}-----\n" + "\n".join(textwrap.wrap(body, 64)) + f"\n-----END {label}-----\n"


async def resolve(client, ref: str) -> str:
    """client.secrets.resolve, pero el error dice qué referencia falló."""
    try:
        return await client.secrets.resolve(ref)
    except Exception as exc:  # noqa: BLE001 — se re-lanza con contexto
        raise RuntimeError(f"{ref}: {exc} (revisa con --check)") from exc


def namespace(name: str, *, baseline: bool = False, privileged: bool = False, keep: bool = False) -> dict:
    """keep=True: namespace cuyas etiquetas (PSA) son de GitOps: sin etiqueta PSA aquí y ArgoCD no lo poda ni lo borra."""
    level = "privileged" if privileged else "baseline" if baseline else None
    labels = {"pod-security.kubernetes.io/enforce": level} if level else {}
    ns = {"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": name, "labels": labels}}
    if keep:
        ns["metadata"]["annotations"] = {"argocd.argoproj.io/sync-options": "Prune=false,Delete=false"}
    return ns


def secret(ns: str, name: str, data: dict[str, str], labels: dict[str, str] | None = None, type_: str = "Opaque") -> dict:
    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": name, "namespace": ns, "labels": labels or {}},
        "type": type_,
        "stringData": data,
    }


def check_pem(pem: str, ref: str) -> str:
    """Valida que la private key de una GitHub App se pueda leer (sin mostrarla)."""
    from cryptography.hazmat.primitives import serialization

    try:
        serialization.load_pem_private_key(pem.encode(), password=None)
    except Exception as exc:  # noqa: BLE001 — error con contexto
        raise RuntimeError(f"{ref}: no es una private key PEM válida (empieza con {pem.splitlines()[0]!r}): {exc}") from exc
    return pem


def check_sealed_pair(cert_pem: str, key_pem: str) -> None:
    """El certificado tiene que ser X.509 y corresponder a la llave privada."""
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization

    try:
        cert = x509.load_pem_x509_certificate(cert_pem.encode())
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"op://{VAULT_NAME}/{SEALED_ITEM}/certificate: no es un certificado X.509 PEM válido: {exc}") from exc
    try:
        key = serialization.load_pem_private_key(key_pem.encode(), password=None)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"op://{VAULT_NAME}/{SEALED_ITEM}/private_key: no es una llave privada PEM válida: {exc}") from exc
    fmt = (serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    if cert.public_key().public_bytes(*fmt) != key.public_key().public_bytes(*fmt):
        raise RuntimeError(
            f"op://{VAULT_NAME}/{SEALED_ITEM}: el certificado y la llave privada NO son un par "
            "(la llave no corresponde a ese certificado). Revisa que copiaste tls.crt y tls.key del mismo par."
        )


async def read_optional(client, ref: str) -> str:
    """Como resolve(), pero devuelve "" si el item o el campo no existen."""
    try:
        return await client.secrets.resolve(ref)
    except Exception:  # noqa: BLE001 — opcional
        return ""


async def read_app(client, item: str) -> dict[str, str]:
    ref = f"op://{VAULT_NAME}/{item}"
    return {
        "app_id": (await resolve(client, f"{ref}/app_id")).strip(),
        "installation_id": (await resolve(client, f"{ref}/installation_id")).strip(),
        "private_key": check_pem(normalize_pem(await resolve(client, f"{ref}/private_key")), f"{ref}/private_key"),
    }


async def read_app_optional(client, item: str) -> dict[str, str] | None:
    """Como read_app, pero None si el item no existe (opcional). Error si tiene solo parte de los campos."""
    ref = f"op://{VAULT_NAME}/{item}"
    raw = {}
    for f in ("app_id", "installation_id", "private_key"):
        raw[f] = (await read_optional(client, f"{ref}/{f}")).strip()
    if not any(raw.values()):
        return None
    missing = [f for f, v in raw.items() if not v]
    if missing:
        raise RuntimeError(f"{ref}: faltan los campos {', '.join(missing)} (hacen falta app_id, installation_id y private_key).")
    raw["private_key"] = check_pem(normalize_pem(raw["private_key"]), f"{ref}/private_key")
    return raw


async def read_monitoring(client) -> dict[str, str] | None:
    """Valores del monitoreo, o None si no hay ningún item (opcional). Error si están incompletos o mal formados."""
    ref = lambda item, field: f"op://{VAULT_NAME}/{item}/{field}"  # noqa: E731
    wanted = {
        "critical": ref(DISCORD_ITEM, "critical"),
        "warnings": ref(DISCORD_ITEM, "warnings"),
        "url": ref(HEARTBEAT_ITEM, "url"),
        "password": ref(GRAFANA_ITEM, "password"),
    }
    values = {}
    for k, r in wanted.items():
        values[k] = (await read_optional(client, r)).strip()
    if not any(values.values()):
        return None
    missing = [wanted[k] for k, v in values.items() if not v]
    if missing:
        raise RuntimeError(
            "Monitoreo incompleto en 1Password: faltan " + ", ".join(missing) + " (hacen falta los tres items; revisa con --check)."
        )
    for key in ("critical", "warnings"):
        if not DISCORD_WEBHOOK_RE.match(values[key]):
            raise RuntimeError(
                f"{wanted[key]}: no parece un webhook de Discord (https://discord.com/api/webhooks/<id>/<token>). "
                "No se aplica para no enviar alertas a otro destino."
            )
    if not values["url"].startswith("https://"):
        raise RuntimeError(f"{wanted['url']}: la ping URL de healthchecks.io tiene que empezar con https://")
    values["username"] = (await read_optional(client, ref(GRAFANA_ITEM, "username"))).strip() or "admin"
    # Opcional: webhook del canal de despliegues (notificaciones de ArgoCD).
    deployments = (await read_optional(client, ref(DISCORD_ITEM, "deployments"))).strip()
    if deployments and not DISCORD_WEBHOOK_RE.match(deployments):
        raise RuntimeError(
            f"{ref(DISCORD_ITEM, 'deployments')}: no parece un webhook de Discord (https://discord.com/api/webhooks/<id>/<token>). "
            "No se aplica para no enviar notificaciones a otro destino."
        )
    values["deployments"] = deployments
    # Opcional: webhook del canal #ia (reporte semanal con IA).
    ai = (await read_optional(client, ref(DISCORD_ITEM, "ai"))).strip()
    if ai and not DISCORD_WEBHOOK_RE.match(ai):
        raise RuntimeError(
            f"{ref(DISCORD_ITEM, 'ai')}: no parece un webhook de Discord (https://discord.com/api/webhooks/<id>/<token>). "
            "No se aplica para no enviar el reporte a otro destino."
        )
    values["ai"] = ai
    return values


def check_token(value: str, ref: str) -> str:
    """Valida un token de máquina (>= 32 caracteres, sin espacios) sin mostrar su valor."""
    if len(value) < TOKEN_MIN_LEN or re.search(r"\s", value):
        raise RuntimeError(
            f"{ref}: tiene que ser un token de al menos {TOKEN_MIN_LEN} caracteres sin espacios (genéralo con: openssl rand -hex 32)."
        )
    return value


async def read_ollama_tokens(client) -> dict[str, str] | None:
    """Tokens del router de Ollama, o None si no existe el item (opcional). Error si faltan campos o son inválidos."""
    ref = lambda field: f"op://{VAULT_NAME}/{OLLAMA_ROUTER_ITEM}/{field}"  # noqa: E731
    values = {}
    for f in OLLAMA_ROUTER_FIELDS:
        values[f] = (await read_optional(client, ref(f))).strip()
    if not any(values.values()):
        return None
    missing = [ref(f) for f, v in values.items() if not v]
    if missing:
        raise RuntimeError("Item del router de Ollama incompleto en 1Password: faltan " + ", ".join(missing) + " (revisa con --check).")
    return {f: check_token(v, ref(f)) for f, v in values.items()}


def check_public_cert(pem: str, source: str) -> str:
    """Acepta solo certificados PEM públicos: un bloque CERTIFICATE o más y ninguna llave privada."""
    if "PRIVATE KEY" in pem:
        raise RuntimeError(f"{source}: contiene una llave privada; solo se copia el certificado público. No se aplica.")
    blocks = re.findall(r"-----BEGIN CERTIFICATE-----.+?-----END CERTIFICATE-----", pem, re.S)
    leftover = re.sub(r"-----BEGIN CERTIFICATE-----.+?-----END CERTIFICATE-----", "", pem, flags=re.S).strip()
    if not blocks or leftover:
        raise RuntimeError(f"{source}: no es un certificado PEM (-----BEGIN CERTIFICATE-----).")
    return "\n".join(blocks) + "\n"


def read_homelab_ca(run=None) -> str:
    """ca.crt de cert-manager/homelab-ca (solo esa clave, con jsonpath: la llave de la CA no se lee)."""
    ns, name = HOMELAB_CA
    result = (run or subprocess.run)(
        ["kubectl", "-n", ns, "get", "secret", name, "-o", r"jsonpath={.data.ca\.crt}"],
        check=True, capture_output=True, text=True,
    )
    try:
        pem = base64.b64decode(result.stdout.strip(), validate=True).decode()
    except (ValueError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"{ns}/{name}: ca.crt no es base64 válido ({exc}).") from exc
    return check_public_cert(pem, f"{ns}/{name} ca.crt")


async def ensure_generated_password(client, item: str, field: str, *, dry_run: bool) -> str | None:
    """Lee una contraseña de 1Password; si falta, la genera (64 hex) y la guarda en el item. Nunca la imprime.

    Con dry_run no escribe en 1Password y devuelve None si todavía no existe.
    """
    ref = f"op://{VAULT_NAME}/{item}/{field}"
    value = (await read_optional(client, ref)).strip()
    if value:
        return check_token(value, ref)
    if dry_run:
        print(f"Aviso: falta {ref}: al aplicar se genera y se guarda en 1Password (--dry-run no escribe).", file=sys.stderr)
        return None
    value = secrets.token_hex(32)
    await set_item_field(client, field, value, vault_id=await find_vault_id(client), item_title=item)
    print(f"Generado {ref} y guardado en 1Password.", file=sys.stderr)
    return value


async def read_postgres_s3(client) -> dict[str, str] | None:
    """Llave del bucket de respaldos, o None si no existe el item (opcional). Error si está incompleta o mal formada."""
    ref = lambda field: f"op://{VAULT_NAME}/{POSTGRES_S3_ITEM}/{field}"  # noqa: E731
    values = {f: (await read_optional(client, ref(f))).strip() for f in POSTGRES_S3_FIELDS}
    if not any(values.values()):
        return None
    missing = [ref(f) for f, v in values.items() if not v]
    if missing:
        raise RuntimeError("Item de la llave S3 incompleto en 1Password: faltan " + ", ".join(missing) + " (revisa con --check).")
    for f, v in values.items():
        if len(v) < S3_KEY_MIN_LEN or re.search(r"\s", v):
            raise RuntimeError(f"{ref(f)}: tiene que tener al menos {S3_KEY_MIN_LEN} caracteres sin espacios.")
    return {POSTGRES_S3_FIELDS[f]: v for f, v in values.items()}


def database_url(password: str) -> str:
    """Cadena de conexión de homelab-agent (sslmode=require: la CA del servidor es la propia de CNPG)."""
    return (
        f"postgresql://{POSTGRES_APP_USER}:{quote(password, safe='')}@{POSTGRES_RW_HOST}/{POSTGRES_APP_DB}"
        "?sslmode=require"
    )


def ensure_namespace(manifests: list[dict], name: str, **kwargs) -> None:
    """Añade el Namespace solo si todavía no está en la lista (varios bloques comparten namespace)."""
    if not any(m["kind"] == "Namespace" and m["metadata"]["name"] == name for m in manifests):
        manifests.append(namespace(name, **kwargs))


async def build_manifests(dry_run: bool = False) -> list[dict]:
    client = await create_client()

    argocd = await read_app(client, "maceosoft-argocd")
    arc = await read_app(client, "maceosoft-arc-runners")

    manifests: list[dict] = [
        namespace("argocd"),
        # privileged: los runners llevan un sidecar dind (gitops: addons/ci/arc/values-scaleset.yaml).
        namespace(RUNNER_NAMESPACE, privileged=True),
        namespace(STATE_NAMESPACE),
    ]

    manifests.append(
        secret(
            "argocd",
            "repo-gitops",
            {
                "type": "git",
                "url": GITOPS_REPO_URL,
                "githubAppID": argocd["app_id"],
                "githubAppInstallationID": argocd["installation_id"],
                "githubAppPrivateKey": argocd["private_key"],
            },
            labels={"argocd.argoproj.io/secret-type": "repository"},
        )
    )
    manifests.append(
        secret(
            RUNNER_NAMESPACE,
            "arc-runners-github-app",
            {
                "github_app_id": arc["app_id"],
                "github_app_installation_id": arc["installation_id"],
                "github_app_private_key": arc["private_key"],
            },
        )
    )

    legacy_arc = await read_app_optional(client, LEGACY_ARC_ITEM)
    legacy_tf = await read_app_optional(client, LEGACY_TF_ITEM)
    if legacy_arc:
        # Org antigua: sin cambios. Su scale set (arc-runners-symintel) todavía carga terraform-app con envFrom.
        manifests.append(namespace(LEGACY_RUNNER_NAMESPACE, privileged=True))
        manifests.append(
            secret(
                LEGACY_RUNNER_NAMESPACE,
                "arc-runners-github-app",
                {
                    "github_app_id": legacy_arc["app_id"],
                    "github_app_installation_id": legacy_arc["installation_id"],
                    "github_app_private_key": legacy_arc["private_key"],
                },
            )
        )
        if legacy_tf:
            manifests.append(
                secret(
                    LEGACY_RUNNER_NAMESPACE,
                    "terraform-app",
                    {
                        "TF_VAR_github_app_id": legacy_tf["app_id"],
                        "TF_VAR_github_app_installation_id": legacy_tf["installation_id"],
                        "TF_VAR_github_app_private_key": legacy_tf["private_key"],
                    },
                )
            )
    elif legacy_tf:
        raise RuntimeError(f"El item {LEGACY_TF_ITEM!r} existe pero falta {LEGACY_ARC_ITEM!r}: sin él no hay scale set para la org {LEGACY_ORG}.")
    else:
        print(f"Aviso: sin item {LEGACY_ARC_ITEM!r}: no se prepara el scale set de la org {LEGACY_ORG} (opcional).", file=sys.stderr)

    sealed_cert = await read_optional(client, f"op://{VAULT_NAME}/{SEALED_ITEM}/certificate")
    sealed_key = await read_optional(client, f"op://{VAULT_NAME}/{SEALED_ITEM}/private_key")
    if sealed_cert and sealed_key:
        cert_pem, key_pem = normalize_pem(sealed_cert), normalize_pem(sealed_key)
        check_sealed_pair(cert_pem, key_pem)
        manifests.append(
            secret(
                SEALED_NAMESPACE,
                SEALED_SECRET_NAME,
                {"tls.crt": cert_pem, "tls.key": key_pem},
                labels={SEALED_LABEL: "active"},
                type_="kubernetes.io/tls",
            )
        )
    elif sealed_cert or sealed_key:
        raise RuntimeError(f"El item {SEALED_ITEM!r} tiene solo uno de los campos: hacen falta 'certificate' y 'private_key'.")
    else:
        print(f"Aviso: sin item {SEALED_ITEM!r} en 1Password: Sealed Secrets generará su propia llave (se pierde si reinstalas K3s).", file=sys.stderr)

    monitoring = await read_monitoring(client)
    if monitoring:
        manifests.append(namespace(MONITORING_NAMESPACE, privileged=True))
        manifests.append(
            secret(
                MONITORING_NAMESPACE,
                "discord-webhooks",
                {"critical": monitoring["critical"], "warnings": monitoring["warnings"], **({"ai": monitoring["ai"]} if monitoring["ai"] else {})},
            )
        )
        if not monitoring["ai"]:
            print(f"Aviso: sin el campo 'ai' en {DISCORD_ITEM!r}: el reporte semanal con IA no tendrá canal en Discord.", file=sys.stderr)
        manifests.append(secret(MONITORING_NAMESPACE, "healthchecks-ping", {"url": monitoring["url"]}))
        manifests.append(
            secret(MONITORING_NAMESPACE, "grafana-admin", {"admin-user": monitoring["username"], "admin-password": monitoring["password"]})
        )
        if monitoring["deployments"]:
            manifests.append(
                secret(
                    ARGOCD_NAMESPACE,
                    ARGOCD_NOTIFICATIONS_SECRET,
                    {"discord-despliegues-url": monitoring["deployments"], "discord-avisos-url": monitoring["warnings"]},
                )
            )
        else:
            print(
                f"Aviso: sin el campo 'deployments' en {DISCORD_ITEM!r}: ArgoCD no enviará notificaciones a Discord.",
                file=sys.stderr,
            )
    else:
        print(
            f"Aviso: sin items {DISCORD_ITEM!r}, {HEARTBEAT_ITEM!r} y {GRAFANA_ITEM!r} en 1Password: el monitoreo no se configura.",
            file=sys.stderr,
        )

    webui_key = (await read_optional(client, f"op://{VAULT_NAME}/{OPEN_WEBUI_ITEM}/WEBUI_SECRET_KEY")).strip()
    if webui_key:
        if not OPEN_WEBUI_KEY_RE.match(webui_key):
            raise RuntimeError(
                f"op://{VAULT_NAME}/{OPEN_WEBUI_ITEM}/WEBUI_SECRET_KEY: tiene que ser un valor aleatorio de 64 caracteres "
                "hexadecimales (genéralo con: openssl rand -hex 32)."
            )
        manifests.append(namespace(AI_NAMESPACE, keep=True))
        manifests.append(secret(AI_NAMESPACE, OPEN_WEBUI_SECRET_NAME, {"WEBUI_SECRET_KEY": webui_key}))
    else:
        print(f"Aviso: sin item {OPEN_WEBUI_ITEM!r} en 1Password: Open WebUI no arrancará (opcional: asistente de IA).", file=sys.stderr)

    ollama = await read_ollama_tokens(client)
    if ollama:
        # ai y k8sgpt-operator-system sin etiqueta PSS; monitoring "privileged" como en el bloque del monitoreo.
        ensure_namespace(manifests, AI_NAMESPACE, keep=True)
        manifests.append(secret(AI_NAMESPACE, OLLAMA_ROUTER_SECRET, dict(ollama)))
        for field, ns in OLLAMA_CLIENT_TOKENS.items():
            ensure_namespace(manifests, ns, privileged=(ns == MONITORING_NAMESPACE), keep=(ns in GITOPS_NAMESPACES))
            manifests.append(secret(ns, f"ollama-token-{field}", {"token": ollama[field]}))
    else:
        print(f"Aviso: sin item {OLLAMA_ROUTER_ITEM!r} en 1Password: el router de Ollama y sus clientes no arrancarán (opcional: IA).", file=sys.stderr)
    for item, (field, targets) in SINGLE_TOKEN_ITEMS.items():
        ref = f"op://{VAULT_NAME}/{item}/{field}"
        value = (await read_optional(client, ref)).strip()
        if value:
            check_token(value, ref)
            for ns, name, key in targets:
                ensure_namespace(manifests, ns, privileged=(ns == MONITORING_NAMESPACE), keep=(ns in GITOPS_NAMESPACES))
                manifests.append(secret(ns, name, {key: value}))
        else:
            print(f"Aviso: sin item {item!r} en 1Password: no se crean sus Secrets (opcional: IA).", file=sys.stderr)

    # PostgreSQL de la plataforma: rol de homelab-agent (contraseña generada si falta) y su cadena de conexión.
    ensure_namespace(manifests, POSTGRES_NAMESPACE, keep=True)
    password = await ensure_generated_password(client, POSTGRES_APP_ITEM, POSTGRES_APP_FIELD, dry_run=dry_run)
    password = password or PENDING_PASSWORD
    manifests.append(
        secret(
            POSTGRES_NAMESPACE,
            POSTGRES_APP_SECRET,
            {"username": POSTGRES_APP_USER, "password": password},
            labels=dict(CNPG_RELOAD_LABELS),
            type_="kubernetes.io/basic-auth",
        )
    )
    url_ns, url_name = POSTGRES_APP_URL_SECRET
    ensure_namespace(manifests, url_ns, keep=True)
    manifests.append(secret(url_ns, url_name, {"DATABASE_URL": database_url(password)}))
    # CA pública del endpoint S3 (siempre: no es secreta) y llave del bucket (si el operador ya la creó).
    manifests.append(secret(POSTGRES_NAMESPACE, INCUS_S3_CA_SECRET, {"ca.crt": read_homelab_ca()}))
    s3 = await read_postgres_s3(client)
    if s3:
        manifests.append(secret(POSTGRES_NAMESPACE, POSTGRES_S3_SECRET, s3, labels=dict(CNPG_RELOAD_LABELS)))
    else:
        print(f"Aviso: sin item {POSTGRES_S3_ITEM!r} en 1Password: PostgreSQL queda sin respaldos a S3 (opcional).", file=sys.stderr)
    return manifests


def delete_obsolete_secrets(run=None) -> list[str]:
    """Borra de arc-runners los Secrets que ya no se crean (OBSOLETE_RUNNER_SECRETS). Idempotente.

    Devuelve los Secrets borrados como los imprime kubectl -o name ("secret/<nombre>"); vacía si no había ninguno.
    """
    result = (run or subprocess.run)(
        ["kubectl", "delete", "secret", "-n", RUNNER_NAMESPACE, *OBSOLETE_RUNNER_SECRETS, "--ignore-not-found", "-o", "name"],
        check=True, capture_output=True, text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def redact(manifest: dict) -> dict:
    if manifest["kind"] != "Secret":
        return manifest
    return {**manifest, "stringData": {k: "<redacted>" for k in manifest["stringData"]}}


# Items y campos que el script espera (ver docs/maceosoft/github.md).
EXPECTED = {
    "maceosoft-arc-runners": ["app_id", "installation_id", "private_key"],
    "maceosoft-argocd": ["app_id", "installation_id", "private_key"],
}


async def check() -> int:
    """Muestra, sin valores, qué campos tiene cada item esperado y qué falta."""
    client = await create_client()
    vault_id = await find_vault_id(client)
    overviews = await client.items.list(vault_id)
    by_title = {o.title.lower(): o for o in overviews}
    expected = dict(EXPECTED)
    ok = True
    print(f"Bóveda {VAULT_NAME!r}:")
    for title, fields in expected.items():
        if title not in by_title:
            print(f"  ✗ {title}: NO EXISTE el item")
            ok = False
            continue
        item = await client.items.get(vault_id, by_title[title].id)
        sections = {sec.id: sec.title for sec in (item.sections or [])}
        found = {f.title: sections.get(f.section_id) for f in item.fields}
        found_ci = {k.lower(): k for k in found}
        print(f"  {title}  (tipo: {item.category})")
        for name in fields:
            real = found_ci.get(name.lower())
            if real is not None and real != name:
                print(f"    ✗ {name}: existe como {real!r} (el nombre tiene que ser exacto)")
                ok = False
                continue
            if name not in found:
                print(f"    ✗ {name}: falta")
                ok = False
            elif found[name]:
                print(f"    ✗ {name}: está dentro de la sección {found[name]!r} (sácalo de la sección)")
                ok = False
            else:
                print(f"    ✓ {name}")
        extra = sorted(set(found) - set(fields))
        if extra:
            print(f"    · otros campos en el item: {', '.join(repr(x) for x in extra)}")
    # Ya no se leen (solo informativo, sin abrir el item): el token de ArgoCD del diff va como secreto de GitHub Actions.
    print(
        f"  · {ARGOCD_CI_ITEM}: este script ya no lo lee; el token va en el secreto ARGOCD_CI_TOKEN de maceosoft/gitops "
        "(docs/operacion/pipeline-gitops.md)"
    )
    # Opcional: las Apps de la org antigua (scale set arc-runners-symintel).
    for title in (LEGACY_ARC_ITEM, LEGACY_TF_ITEM):
        if title in by_title:
            item = await client.items.get(vault_id, by_title[title].id)
            found = {f.title: f.value for f in item.fields}
            print(f"  {title}  (opcional: org {LEGACY_ORG})")
            for name in ("app_id", "installation_id", "private_key"):
                good = bool((found.get(name) or "").strip())
                print(f"    {'✓' if good else '✗'} {name}")
                ok = ok and good
        else:
            print(f"  · sin item {title} (opcional: org {LEGACY_ORG})")
    # Opcional: el par de llaves de Sealed Secrets.
    if SEALED_ITEM in by_title:
        item = await client.items.get(vault_id, by_title[SEALED_ITEM].id)
        found = {f.title: f.value for f in item.fields}
        print(f"  {SEALED_ITEM}  (opcional)")
        for name in ("certificate", "private_key"):
            good = bool(found.get(name))
            print(f"    {'✓' if good else '✗'} {name}")
            ok = ok and good
        if found.get("certificate") and found.get("private_key"):
            try:
                check_sealed_pair(normalize_pem(found["certificate"]), normalize_pem(found["private_key"]))
                print("    ✓ el certificado corresponde a la llave privada")
            except RuntimeError as exc:
                print(f"    ✗ {exc}")
                ok = False
    else:
        print(f"  · sin item {SEALED_ITEM} (opcional: Sealed Secrets generará su propia llave)")
    # Opcional: monitoreo (los tres items juntos).
    monitoring_fields = {DISCORD_ITEM: ("critical", "warnings"), HEARTBEAT_ITEM: ("url",), GRAFANA_ITEM: ("password",)}
    present = [t for t in monitoring_fields if t in by_title]
    if not present:
        print(f"  · sin items de monitoreo ({', '.join(monitoring_fields)}): opcional, no se configura")
    else:
        for title, names in monitoring_fields.items():
            if title not in by_title:
                print(f"  ✗ {title}: NO EXISTE el item (el monitoreo necesita los tres)")
                ok = False
                continue
            item = await client.items.get(vault_id, by_title[title].id)
            found = {f.title: f.value for f in item.fields}
            print(f"  {title}  (monitoreo)")
            for name in names:
                value = (found.get(name) or "").strip()
                good = bool(value)
                if good and title == DISCORD_ITEM:
                    good = bool(DISCORD_WEBHOOK_RE.match(value))
                    print(f"    {'✓' if good else '✗'} {name}" + ("" if good else " (no parece un webhook de Discord)"))
                else:
                    print(f"    {'✓' if good else '✗'} {name}" + ("" if good else " (falta o está vacío)"))
                ok = ok and good
            if title == DISCORD_ITEM:
                # Opcional: no hace fallar la comprobación, pero si existe tiene que tener el formato correcto.
                dep = (found.get("deployments") or "").strip()
                ai = (found.get("ai") or "").strip()
                if not ai:
                    print("    · ai (opcional): sin él, el reporte semanal con IA no tiene canal")
                elif DISCORD_WEBHOOK_RE.match(ai):
                    print("    ✓ ai (opcional)")
                else:
                    print("    ✗ ai (opcional): no parece un webhook de Discord")
                    ok = False
                if not dep:
                    print("    · deployments (opcional): sin él, ArgoCD no notifica a Discord")
                elif DISCORD_WEBHOOK_RE.match(dep):
                    print("    ✓ deployments (opcional)")
                else:
                    print("    ✗ deployments (opcional): no parece un webhook de Discord")
                    ok = False
    # Opcional: clave de sesión de Open WebUI (asistente de IA).
    if OPEN_WEBUI_ITEM in by_title:
        item = await client.items.get(vault_id, by_title[OPEN_WEBUI_ITEM].id)
        found = {f.title: f.value for f in item.fields}
        value = (found.get("WEBUI_SECRET_KEY") or "").strip()
        good = bool(OPEN_WEBUI_KEY_RE.match(value))
        print(f"  {OPEN_WEBUI_ITEM}  (opcional: asistente de IA)")
        print(f"    {'✓' if good else '✗'} WEBUI_SECRET_KEY" + ("" if good else " (falta o no son 64 caracteres hexadecimales)"))
        ok = ok and good
    else:
        print(f"  · sin item {OPEN_WEBUI_ITEM} (opcional: Open WebUI no arrancará sin él)")
    # Opcional: tokens de IA (router de Ollama, alert-triage, mcpo): campos presentes y con formato de token.
    token_items = {OLLAMA_ROUTER_ITEM: OLLAMA_ROUTER_FIELDS, **{i: (v[0],) for i, v in SINGLE_TOKEN_ITEMS.items()}}
    for title, names in token_items.items():
        if title.lower() not in by_title:
            print(f"  · sin item {title} (opcional: IA)")
            continue
        item = await client.items.get(vault_id, by_title[title.lower()].id)
        found = {f.title: f.value for f in item.fields}
        print(f"  {title}  (opcional: IA)")
        for name in names:
            value = (found.get(name) or "").strip()
            good = len(value) >= TOKEN_MIN_LEN and not re.search(r"\s", value)
            print(f"    {'✓' if good else '✗'} {name}" + ("" if good else f" (falta o no es un token de {TOKEN_MIN_LEN}+ caracteres sin espacios)"))
            ok = ok and good
    # PostgreSQL de la plataforma: la contraseña se genera si falta; la llave S3 es opcional (respaldos).
    if POSTGRES_APP_ITEM in by_title:
        item = await client.items.get(vault_id, by_title[POSTGRES_APP_ITEM].id)
        value = (({f.title: f.value for f in item.fields}).get(POSTGRES_APP_FIELD) or "").strip()
        good = not value or (len(value) >= TOKEN_MIN_LEN and not re.search(r"\s", value))
        state = "✓" if value and good else "·" if not value else "✗"
        note = "" if value and good else " (falta: se genera al aplicar)" if not value else f" ({TOKEN_MIN_LEN}+ caracteres sin espacios)"
        print(f"  {POSTGRES_APP_ITEM}\n    {state} {POSTGRES_APP_FIELD}{note}")
        ok = ok and good
    else:
        print(f"  · sin item {POSTGRES_APP_ITEM} (se crea con la contraseña generada al aplicar)")
    if POSTGRES_S3_ITEM in by_title:
        item = await client.items.get(vault_id, by_title[POSTGRES_S3_ITEM].id)
        found = {f.title: f.value for f in item.fields}
        print(f"  {POSTGRES_S3_ITEM}  (opcional: respaldos de PostgreSQL)")
        for name in POSTGRES_S3_FIELDS:
            value = (found.get(name) or "").strip()
            good = len(value) >= S3_KEY_MIN_LEN and not re.search(r"\s", value)
            print(f"    {'✓' if good else '✗'} {name}" + ("" if good else f" (falta o no tiene {S3_KEY_MIN_LEN}+ caracteres sin espacios)"))
            ok = ok and good
    else:
        print(f"  · sin item {POSTGRES_S3_ITEM} (opcional: PostgreSQL sin respaldos a S3)")
    return 0 if ok else 1


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="imprime los manifiestos (sin valores) y no aplica")
    parser.add_argument("--check", action="store_true", help="lista los campos de cada item esperado (sin valores) y qué falta")
    args = parser.parse_args()

    if args.check:
        return await check()

    manifests = await build_manifests(dry_run=args.dry_run)
    if args.dry_run:
        print(json.dumps([redact(m) for m in manifests], indent=2))
        obsolete = ", ".join(f"{RUNNER_NAMESPACE}/{n}" for n in OBSOLETE_RUNNER_SECRETS)
        print(f"Al aplicar se borran, si existen: {obsolete}.", file=sys.stderr)
        return 0

    doc = {"apiVersion": "v1", "kind": "List", "items": manifests}
    # Server-side: los stringData no quedan en la anotación last-applied-configuration (que es legible en claro).
    subprocess.run(["kubectl", "apply", "--server-side", "--force-conflicts", "--field-manager=platform-secrets", "-f", "-"],
                   input=json.dumps(doc), text=True, check=True)
    # Secrets creados antes con apply del lado cliente: quita esa anotación (best effort; sin ella no pasa nada).
    for m in manifests:
        if m["kind"] == "Secret":
            subprocess.run(["kubectl", "annotate", "secret", m["metadata"]["name"], "-n", m["metadata"]["namespace"],
                            "kubectl.kubernetes.io/last-applied-configuration-"], check=False, capture_output=True)
    deleted = delete_obsolete_secrets()
    monitoring_note = " (monitoreo configurado)" if any(m["metadata"]["name"] == "discord-webhooks" for m in manifests) else ""
    print(f"Secretos de plataforma aplicados{monitoring_note}.")
    print(f"Borrados de {RUNNER_NAMESPACE}: {', '.join(deleted)}." if deleted else f"Nada obsoleto que borrar en {RUNNER_NAMESPACE}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except Exception as exc:  # noqa: BLE001 — script CLI
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
