"""SEO: una meta descripción propia para cada página, tomada de su primer párrafo.

Material escribe `<meta name="description">` con el `description:` del front matter de la página y, si falta,
con `site_description`, que es la misma en todas las páginas. Con la misma descripción en todo el sitio, Google
muestra el mismo texto bajo cada resultado. Este hook completa `description` con el primer párrafo de texto de
las páginas que no la definen; una `description:` escrita a mano en el front matter siempre gana.
"""

import html
import re

# Google corta las descripciones alrededor de 155-160 caracteres.
MAX_CHARS = 155
# Un párrafo más corto que esto (un título suelto, una etiqueta) no sirve como descripción.
MIN_CHARS = 50

# Líneas que no son prosa: encabezados, tablas, listas, admoniciones, pestañas, HTML crudo, snippets, citas.
_STRUCTURAL = re.compile(
    r"^(#|\||>|<|!!!|\?\?\?|===|---|\*\*\*|--8<--|[-*+]\s|\d+[.)]\s|:::|\[\^)"
)


def _clean(text):
    """Quita el formato Markdown/HTML y deja texto plano en una sola línea."""
    text = re.sub(r"<[^>]+>", "", text)  # HTML crudo
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)  # imágenes
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)  # [texto](url) -> texto
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)  # [texto][ref] -> texto
    text = re.sub(r"\{[^}]*\}", "", text)  # attr_list: {: .clase }
    text = re.sub(r"(\*\*|__|`|\*)", "", text)  # negrita, cursiva y código en línea
    text = re.sub(
        r"(?<!\w)_(.+?)_(?!\w)", r"\1", text
    )  # _cursiva_ sin tocar nombres_con_guion_bajo
    return re.sub(r"\s+", " ", text).strip()


def _first_paragraph(markdown):
    """Devuelve el primer párrafo de prosa de la página, ya limpio, o '' si no hay ninguno."""
    in_fence = False
    buffer = []
    for raw in markdown.splitlines():
        line = raw.strip()
        if line.startswith(("```", "~~~")):
            in_fence = not in_fence
            buffer = []
            continue
        if in_fence:
            continue
        # Un párrafo de prosa sigue pegado al anterior: una línea en blanco, indentada (contenido de una
        # admonición o pestaña) o estructural lo cierra.
        if not line or raw.startswith(("    ", "\t")) or _STRUCTURAL.match(line):
            candidate = _clean(" ".join(buffer))
            if len(candidate) >= MIN_CHARS:
                return candidate
            buffer = []
            continue
        buffer.append(line)
    candidate = _clean(" ".join(buffer))
    return candidate if len(candidate) >= MIN_CHARS else ""


def _shorten(text):
    """Recorta a MAX_CHARS, de preferencia al final de una oración."""
    if len(text) <= MAX_CHARS:
        return text
    cut = text[:MAX_CHARS]
    end = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    if end >= 80:
        return cut[: end + 1]
    return cut.rsplit(" ", 1)[0].rstrip(" ,;:—-") + "…"


def on_page_markdown(markdown, page, config, files):
    """Completa la descripción de la página y la fecha que usa el sitemap.

    - page.meta['description']: la del front matter o el primer párrafo, escapada para el atributo HTML.
    - page.meta['seo_description']: el mismo texto sin escapar, para el JSON-LD (overrides/main.html lo
      serializa con tojson, que escapa por su cuenta).
    - page.update_date: fecha del último commit que tocó la página (git-revision-date-localized, que corre
      antes que los hooks). El sitemap la usa como <lastmod>; sin esto todas las URLs llevan la fecha del build
      y Google no puede saber qué páginas cambiaron de verdad.
    """
    description = page.meta.get("description")
    if not description:
        description = _first_paragraph(markdown)
        if description:
            # El Jinja de MkDocs no escapa (autoescape apagado) y Material imprime la descripción tal cual
            # dentro de content="...": se escapan comillas y & para no romper el atributo.
            description = _shorten(description)
            page.meta["description"] = html.escape(description, quote=True)
    if description:
        page.meta["seo_description"] = html.unescape(description)

    git_date = page.meta.get("git_revision_date_localized_raw_iso_date")
    if git_date:
        page.update_date = git_date
    return markdown
