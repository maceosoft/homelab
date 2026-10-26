"""Ajustes para que el sitio bilingüe (mkdocs-static-i18n) conviva con el resto de la config."""

import logging
from pathlib import Path

INCLUDES = Path("includes")


class _DropLlmstxtMissingPage(logging.Filter):
    """mkdocs-llmstxt corre en cada build de idioma, pero sus `sections` nombran los .md en español.

    En el build en inglés esas páginas se llaman *.en.md y viceversa, y el plugin avisa
    "Page URI ... not found" (rompe `--strict`). llms.txt se genera solo desde el español, así que
    el aviso es ruido.
    """

    def filter(self, record):
        return "not found in the generated pages" not in record.getMessage()


logging.getLogger("mkdocs.plugins.mkdocs_llmstxt._internal.plugin").addFilter(_DropLlmstxtMissingPage())


def on_page_markdown(markdown, page, config, files):
    """Agrega el glosario de siglas (tooltips abbr) en el idioma del build.

    Reemplaza a `pymdownx.snippets: auto_append`, que es global y metería las definiciones en
    español en las páginas en inglés. Si falta includes/abbreviations.<idioma>.md se usa el español.
    """
    lang = config.theme.get("language") or "es"
    name = f"abbreviations.{lang}.md"
    if lang == "es" or not (INCLUDES / name).exists():
        name = "abbreviations.md"
    return f'{markdown}\n\n--8<-- "includes/{name}"\n'
