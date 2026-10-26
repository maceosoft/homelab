# ollama_node

Agente de registro de Ollama para nodos Linux. Se ejecuta tras `ollama_ondemand` (mismo play, tag `register`) y reutiliza sus
variables (usuario, socket y `ollama_ondemand_models_dir`).

- Copia `ollama-node/ollama_node.py` del repo a `/usr/local/lib/ollama-node/`.
- Escribe `/etc/ollama-node/config.json` (`name`, `url`, `registry_url`, `token_file`, `ca_file`, `priority`, `tags`, `models_dir`, `interval`).
- Instala el token del registro en `/etc/ollama-node/registry-token` (0600), leído en la estación del operador con
  [`scripts/read_ollama_registry_token.py`](../../scripts/read_ollama_registry_token.py) (1Password, item `ollama-router`, campo `registry_token`).
- Instala la CA del HomeLab (cert-manager `homelab-ca`, misma fuente que `opkssh`) en `/etc/ollama-node/homelab-ca.crt`.
- Habilita `ollama-node-register.service` (`Restart=always`, `register --loop`) con el usuario `ollama-node` (distinto del que sirve los modelos; lee los manifests por el grupo `ollama`).

Variables en `defaults/main.yml`: `ollama_node_enabled`, `_user`, `_name`, `_url`, `_registry_url`, `_priority`, `_tags`, `_interval`,
`_read_group`, `_token_item`, `_token_field`, `_token_fallback_field`, `_install_homelab_ca`. Detalle y procedimiento en el README de `ollama_ondemand`.
