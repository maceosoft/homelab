import json
import os
import shutil
import unittest

from helpers import ModelsTree, ollama_node, sha256_bytes, tmpdir


class ManifestReaderTest(unittest.TestCase):
    def setUp(self):
        self.root = tmpdir()
        self.t = ModelsTree(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def by_name(self):
        return {m["name"]: m for m in ollama_node.read_models(self.root)}

    def test_v1_basico(self):
        man = self.t.model_manifest(layer_sizes=(1000, 20, 3))
        path, dig = self.t.put("manifests", "registry.ollama.ai/library/llama3.1/8b", man, mtime=1_700_000_000)
        m = self.by_name()["llama3.1:8b"]
        self.assertEqual(m["model"], "llama3.1:8b")
        self.assertEqual(m["digest"], dig)
        self.assertEqual(m["size"], man["config"]["size"] + 1023)
        self.assertEqual(m["modified_at"], "2023-11-14T22:13:20+00:00")
        self.assertEqual(m["details"], {"format": "gguf", "family": "llama", "families": ["llama"],
                                        "parameter_size": "8.0B", "quantization_level": "Q4_K_M"})

    def test_v2_solo(self):
        self.t.put("manifests-v2", "ollama.com/library/qwen2.5/7b", self.t.model_manifest(family="qwen2"))
        self.assertIn("qwen2.5:7b", self.by_name())

    def test_v2_gana_sobre_v1(self):
        self.t.put("manifests", "registry.ollama.ai/library/x/latest", self.t.model_manifest(layer_sizes=(1,)))
        self.t.put("manifests-v2", "ollama.com/library/x/latest", self.t.model_manifest(layer_sizes=(5000,)))
        models = ollama_node.read_models(self.root)
        self.assertEqual(len(models), 1)
        self.assertGreater(models[0]["size"], 5000)

    def test_union_v1_y_v2(self):
        self.t.put("manifests", "registry.ollama.ai/library/a/latest", self.t.model_manifest())
        self.t.put("manifests-v2", "ollama.com/library/b/latest", self.t.model_manifest())
        self.assertEqual(sorted(self.by_name()), ["a:latest", "b:latest"])

    def test_nombres_para_mostrar(self):
        self.t.put("manifests", "registry.ollama.ai/alice/mymodel/v2", self.t.model_manifest())
        self.t.put("manifests", "hf.co/user/repo/Q4_K_M", self.t.model_manifest())
        self.t.put("manifests", "localhost%3A5000/library/m/latest", self.t.model_manifest())
        self.assertEqual(sorted(self.by_name()),
                         ["alice/mymodel:v2", "hf.co/user/repo:Q4_K_M", "localhost:5000/library/m:latest"])

    def test_ignora_ocultos_y_rutas_raras(self):
        self.t.put("manifests", "registry.ollama.ai/library/ok/latest", self.t.model_manifest())
        self.t.put("manifests", "registry.ollama.ai/library/ok/.DS_Store", self.t.model_manifest())
        self.t.put("manifests", ".hidden/library/m/latest", self.t.model_manifest())
        self.t.put("manifests", "registry.ollama.ai/library/solo-tres-niveles", self.t.model_manifest())
        self.assertEqual(list(self.by_name()), ["ok:latest"])

    def test_manifest_corrupto_se_omite(self):
        p, _ = self.t.put("manifests", "registry.ollama.ai/library/bad/latest", {})
        with open(p, "w") as fh:
            fh.write("{no es json")
        self.t.put("manifests", "registry.ollama.ai/library/good/latest", self.t.model_manifest())
        self.assertEqual(list(self.by_name()), ["good:latest"])

    def test_config_blob_ausente(self):
        man = self.t.model_manifest()
        man["config"]["digest"] = "sha256:" + "00" * 32
        self.t.put("manifests", "registry.ollama.ai/library/nocfg/latest", man)
        d = self.by_name()["nocfg:latest"]["details"]
        self.assertEqual(d["format"], "")
        self.assertIsNone(d["families"])

    def test_manifest_list_hijo_en_linea(self):
        child = self.t.model_manifest(family="gemma", layer_sizes=(777,))
        lst = {"schemaVersion": 2, "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
               "manifests": [child]}
        self.t.put("manifests-v2", "ollama.com/library/gem/latest", lst)
        m = self.by_name()["gem:latest"]
        self.assertEqual(m["details"]["family"], "gemma")
        self.assertEqual(m["size"], child["config"]["size"] + 777)

    def test_manifest_list_hijo_por_blob(self):
        child = self.t.model_manifest(family="phi", layer_sizes=(42,))
        cdig, csize = self.t.blob(child)
        lst = {"schemaVersion": 2, "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
               "manifests": [{"mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                              "digest": cdig, "size": csize}]}
        self.t.put("manifests-v2", "ollama.com/library/phi/latest", lst)
        self.assertEqual(self.by_name()["phi:latest"]["details"]["family"], "phi")

    def test_manifest_v2_como_symlink_a_blob(self):
        man = self.t.model_manifest()
        raw = json.dumps(man).encode()
        digest, _ = self.t.blob(man)
        target = os.path.join(self.root, "blobs", digest.replace(":", "-"))
        link = os.path.join(self.root, "manifests-v2", "ollama.com", "library", "lnk", "latest")
        os.makedirs(os.path.dirname(link))
        os.symlink(target, link)
        self.assertEqual(self.by_name()["lnk:latest"]["digest"], sha256_bytes(raw))

    def test_directorios_inexistentes(self):
        self.assertEqual(ollama_node.read_models(os.path.join(self.root, "no-existe")), [])


class DefaultsTest(unittest.TestCase):
    def test_models_dir_config_gana(self):
        self.assertEqual(ollama_node.default_models_dir({"models_dir": "/x/y"}), "/x/y")

    def test_models_dir_por_so(self):
        old = os.environ.pop("OLLAMA_MODELS", None)
        try:
            d = ollama_node.default_models_dir({})
            self.assertTrue(d.endswith(".ollama/models"))
        finally:
            if old is not None:
                os.environ["OLLAMA_MODELS"] = old


if __name__ == "__main__":
    unittest.main()
