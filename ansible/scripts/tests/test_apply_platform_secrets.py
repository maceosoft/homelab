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
)
aps = importlib.import_module("apply_platform_secrets")

APP = {"app_id": "1", "installation_id": "2", "private_key": "-----BEGIN RSA PRIVATE KEY-----\nx\n-----END RSA PRIVATE KEY-----\n"}


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


def run_build(values=None, legacy=None):
    """build_manifests con un cliente falso; read_app/read_app_optional no validan el PEM (sin cryptography)."""
    client = types.SimpleNamespace(secrets=FakeSecrets(values or {}), items=FakeItems())
    apps_read = []

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
        contextlib.redirect_stderr(io.StringIO()),
    ):
        manifests = asyncio.run(aps.build_manifests())
    return manifests, client.secrets.asked, apps_read


def names(manifests, ns):
    return {m["metadata"]["name"] for m in manifests if m["kind"] == "Secret" and m["metadata"]["namespace"] == ns}


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
        async def build():
            return manifests

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
