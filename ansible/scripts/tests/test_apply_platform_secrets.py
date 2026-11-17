"""Prueba apply_platform_secrets.py con un 1Password y un kubectl simulados (sin red, sin 1Password, sin clúster).

    python3 -m unittest discover -s ansible/scripts/tests
"""

import asyncio
import contextlib
import importlib
import io
import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
# El SDK de 1Password no hace falta (ni se instala en la CI): se reemplaza el módulo que lo importa.
sys.modules["onepassword_homelab"] = types.SimpleNamespace(
    VAULT_NAME="HomeLab",
    create_client=None,
    find_vault_id=None,
    set_item_field=None,
)
aps = importlib.import_module("apply_platform_secrets")

APP = {"app_id": "1", "installation_id": "2", "private_key": "-----BEGIN RSA PRIVATE KEY-----\nx\n-----END RSA PRIVATE KEY-----\n"}
CA_PEM = "-----BEGIN CERTIFICATE-----\nMIIBfake\n-----END CERTIFICATE-----\n"
PG_REF = "op://HomeLab/postgres-homelab-agent/password"
S3_REFS = {"access_key": "op://HomeLab/postgres-s3/access_key", "secret_key": "op://HomeLab/postgres-s3/secret_key"}


class FakeSecrets:
    """client.secrets.resolve: solo existen las referencias de `values`; registra todo lo que se pide."""

    def __init__(self, values):
        self.values = values
        self.asked = []

    async def resolve(self, ref):
        self.asked.append(ref)
        if ref not in self.values:
            raise LookupError(ref)
        return self.values[ref]


class FakeItems:
    async def list(self, vault_id):  # noqa: ARG002
        raise AssertionError("build_manifests ya no tiene que listar items (eran los ftp-<repo>)")


def run_build(values=None, legacy=None, dry_run=False, stored=None):
    """build_manifests con un cliente falso; read_app/read_app_optional no validan el PEM (sin cryptography).

    stored: lista donde quedan las escrituras en 1Password (set_item_field) como (item, campo, valor).
    """
    client = types.SimpleNamespace(secrets=FakeSecrets(values or {}), items=FakeItems())
    apps_read = []
    writes = stored if stored is not None else []

    async def set_item_field(_client, field, value, *, vault_id, item_title):
        assert vault_id == "vault-id"
        writes.append((item_title, field, value))

    async def find_vault_id(_client):
        return "vault-id"

    async def create_client():
        return client

    async def read_app(_client, item):
        apps_read.append(item)
        return dict(APP)

    async def read_app_optional(_client, item):
        apps_read.append(item)
        return dict(APP) if legacy and item in legacy else None

    with (
        mock.patch.object(aps, "create_client", create_client),
        mock.patch.object(aps, "read_app", read_app),
        mock.patch.object(aps, "read_app_optional", read_app_optional),
        mock.patch.object(aps, "set_item_field", set_item_field),
        mock.patch.object(aps, "find_vault_id", find_vault_id),
        mock.patch.object(aps, "read_homelab_ca", lambda: CA_PEM),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        manifests = asyncio.run(aps.build_manifests(dry_run=dry_run))
    return manifests, client.secrets.asked, apps_read


def names(manifests, ns):
    return {m["metadata"]["name"] for m in manifests if m["kind"] == "Secret" and m["metadata"]["namespace"] == ns}


def find(manifests, ns, name):
    (m,) = [m for m in manifests if m["kind"] == "Secret" and m["metadata"]["namespace"] == ns and m["metadata"]["name"] == name]
    return m


class BuildManifestsTest(unittest.TestCase):
    def test_runners_solo_reciben_el_secret_de_registro(self):
        manifests, _, _ = run_build()
        self.assertEqual(names(manifests, "arc-runners"), {"arc-runners-github-app"})
        self.assertIn("repo-gitops", names(manifests, "argocd"))

    def test_no_crea_los_secrets_obsoletos_aunque_existan_los_items(self):
        # Aunque 1Password todavía tenga argocd-ci, no se lleva al clúster.
        manifests, asked, apps_read = run_build({"op://HomeLab/argocd-ci/token": "t" * 40})
        for name in aps.OBSOLETE_RUNNER_SECRETS:
            self.assertNotIn(name, names(manifests, "arc-runners"))
        self.assertFalse([r for r in asked if "/argocd-ci/" in r or "/ftp-" in r], asked)
        self.assertNotIn("maceosoft-terraform", apps_read)
        self.assertEqual(apps_read[:2], ["maceosoft-argocd", "maceosoft-arc-runners"])

    def test_org_antigua_sin_cambios(self):
        manifests, _, _ = run_build(legacy={aps.LEGACY_ARC_ITEM, aps.LEGACY_TF_ITEM})
        self.assertEqual(names(manifests, aps.LEGACY_RUNNER_NAMESPACE), {"arc-runners-github-app", "terraform-app"})

    def test_check_ya_no_pide_maceosoft_terraform(self):
        self.assertNotIn("maceosoft-terraform", aps.EXPECTED)


class PostgresTest(unittest.TestCase):
    def test_contrasena_existente_no_se_regenera(self):
        writes = []
        manifests, _, _ = run_build({PG_REF: "a" * 64}, stored=writes)
        self.assertEqual(writes, [])
        app = find(manifests, "postgres", "postgres-homelab-agent")
        self.assertEqual(app["type"], "kubernetes.io/basic-auth")
        self.assertEqual(app["metadata"]["labels"], {"cnpg.io/reload": "true"})
        self.assertEqual(app["stringData"], {"username": "homelab_agent", "password": "a" * 64})
        url = find(manifests, "ai", "homelab-agent-postgres")["stringData"]["DATABASE_URL"]
        self.assertEqual(url, "postgresql://homelab_agent:" + "a" * 64 + "@postgres-rw.postgres.svc:5432/homelab_agent?sslmode=require")

    def test_contrasena_faltante_se_genera_y_se_guarda_en_1password(self):
        writes = []
        manifests, _, _ = run_build(stored=writes)
        ((item, field, value),) = writes
        self.assertEqual((item, field), ("postgres-homelab-agent", "password"))
        self.assertRegex(value, r"^[0-9a-f]{64}$")
        self.assertEqual(find(manifests, "postgres", "postgres-homelab-agent")["stringData"]["password"], value)
        self.assertIn(value, find(manifests, "ai", "homelab-agent-postgres")["stringData"]["DATABASE_URL"])

    def test_dry_run_no_escribe_en_1password(self):
        writes = []
        manifests, _, _ = run_build(dry_run=True, stored=writes)
        self.assertEqual(writes, [])
        self.assertEqual(find(manifests, "postgres", "postgres-homelab-agent")["stringData"]["password"], aps.PENDING_PASSWORD)

    def test_contrasena_corta_se_rechaza(self):
        with self.assertRaises(RuntimeError):
            run_build({PG_REF: "corta"})

    def test_llave_s3_y_ca(self):
        values = {PG_REF: "a" * 64, S3_REFS["access_key"]: "k" * 20, S3_REFS["secret_key"]: "s" * 40}
        manifests, _, _ = run_build(values)
        s3 = find(manifests, "postgres", "postgres-s3")
        self.assertEqual(s3["stringData"], {"ACCESS_KEY_ID": "k" * 20, "ACCESS_SECRET_KEY": "s" * 40})
        self.assertEqual(s3["metadata"]["labels"], {"cnpg.io/reload": "true"})
        self.assertEqual(find(manifests, "postgres", "incus-s3-ca")["stringData"], {"ca.crt": CA_PEM})
        namespaces = [m["metadata"] for m in manifests if m["kind"] == "Namespace" and m["metadata"]["name"] == "postgres"]
        self.assertEqual(len(namespaces), 1)
        # El namespace es de GitOps: sin etiqueta PSA y sin que ArgoCD lo pode.
        self.assertEqual(namespaces[0]["labels"], {})
        self.assertIn("Prune=false", namespaces[0]["annotations"]["argocd.argoproj.io/sync-options"])

    def test_sin_item_s3_no_hay_secret_de_llave_pero_si_ca(self):
        manifests, _, _ = run_build({PG_REF: "a" * 64})
        self.assertEqual(names(manifests, "postgres"), {"postgres-homelab-agent", "incus-s3-ca"})

    def test_llave_s3_incompleta_falla(self):
        with self.assertRaises(RuntimeError):
            run_build({PG_REF: "a" * 64, S3_REFS["access_key"]: "k" * 20})

    def test_database_url_escapa_la_contrasena(self):
        self.assertIn("homelab_agent:a%40b%2Fc%3A@", aps.database_url("a@b/c:"))


class HomelabCaTest(unittest.TestCase):
    def _read(self, pem):
        import base64

        calls = []

        def run(cmd, **kwargs):  # noqa: ARG001
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout=base64.b64encode(pem.encode()).decode(), stderr="")

        return aps.read_homelab_ca(run=run), calls

    def test_lee_solo_ca_crt(self):
        pem, calls = self._read(CA_PEM)
        self.assertEqual(pem, CA_PEM)
        ((cmd),) = calls
        self.assertEqual(cmd[-2:], ["-o", r"jsonpath={.data.ca\.crt}"])
        self.assertEqual(cmd[1:6], ["-n", "cert-manager", "get", "secret", "homelab-ca"])

    def test_rechaza_una_llave_privada(self):
        with self.assertRaises(RuntimeError):
            self._read(CA_PEM + "-----BEGIN EC PRIVATE KEY-----\nx\n-----END EC PRIVATE KEY-----\n")

    def test_rechaza_lo_que_no_es_certificado(self):
        for bad in ("", "hola", CA_PEM + "basura"):
            with self.subTest(bad=bad), self.assertRaises(RuntimeError):
                aps.check_public_cert(bad, "prueba")


class DeleteObsoleteTest(unittest.TestCase):
    def test_borra_los_tres_en_arc_runners_idempotente(self):
        calls = []

        def run(cmd, **kwargs):
            calls.append((cmd, kwargs))
            return subprocess.CompletedProcess(cmd, 0, stdout="secret/terraform-app\nsecret/argocd-ci\n", stderr="")

        deleted = aps.delete_obsolete_secrets(run=run)
        self.assertEqual(deleted, ["secret/terraform-app", "secret/argocd-ci"])
        (cmd, kwargs), = calls
        self.assertEqual(cmd[:5], ["kubectl", "delete", "secret", "-n", "arc-runners"])
        self.assertEqual(set(cmd[5:8]), {"terraform-app", "tofu-vars", "argocd-ci"})
        self.assertIn("--ignore-not-found", cmd)
        self.assertTrue(kwargs["check"])

    def test_nada_que_borrar(self):
        def run(cmd, **kwargs):  # noqa: ARG001
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        self.assertEqual(aps.delete_obsolete_secrets(run=run), [])

    def test_solo_toca_arc_runners(self):
        self.assertEqual(aps.OBSOLETE_RUNNER_SECRETS, ("terraform-app", "tofu-vars", "argocd-ci"))
        self.assertEqual(aps.RUNNER_NAMESPACE, "arc-runners")


class MainTest(unittest.TestCase):
    def _main(self, argv, manifests):
        async def build(dry_run=False):
            seen.append(dry_run)
            return manifests

        seen = []
        self.seen = seen

        calls = []

        def run(cmd, **kwargs):
            calls.append(cmd)
            out = "secret/tofu-vars\n" if cmd[:2] == ["kubectl", "delete"] else ""
            return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")

        out = io.StringIO()
        with (
            mock.patch.object(sys, "argv", ["apply_platform_secrets.py", *argv]),
            mock.patch.object(aps, "build_manifests", build),
            mock.patch.object(aps.subprocess, "run", run),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            rc = asyncio.run(aps.main())
        return rc, calls, out.getvalue()

    def test_dry_run_no_toca_el_cluster(self):
        rc, calls, _ = self._main(["--dry-run"], [aps.secret("arc-runners", "arc-runners-github-app", {"a": "b"})])
        self.assertEqual(rc, 0)
        self.assertEqual(calls, [])
        # --dry-run llega a build_manifests: así no se genera ni guarda la contraseña en 1Password.
        self.assertEqual(self.seen, [True])

    def test_aplicar_borra_los_obsoletos_despues_del_apply(self):
        manifests = [aps.secret("arc-runners", "arc-runners-github-app", {"a": "b"})]
        rc, calls, out = self._main([], manifests)
        self.assertEqual(rc, 0)
        verbs = [c[1] for c in calls]
        self.assertEqual(verbs[0], "apply")
        self.assertEqual(verbs[-1], "delete")
        self.assertIn("secret/tofu-vars", out)


if __name__ == "__main__":
    unittest.main()
