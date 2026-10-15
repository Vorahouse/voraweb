#!/usr/bin/env python3
"""Genera las versiones EN y CA a partir de las páginas en español (*.dc.html).

Uso:  python3 i18n/build.py
Las páginas ES son la fuente: edita el español y vuelve a ejecutar el script.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from translations import T, FORM_NAMES  # noqa: E402

DOMAIN = "https://vorahouse.com"
LANGS = ["es", "en", "ca"]
SUFFIX = {"es": "", "en": "-EN", "ca": "-CA"}
HTML_LANG = {"es": "es", "en": "en", "ca": "ca"}
OG_LOCALE = {"es": "es_ES", "en": "en_US", "ca": "ca_ES"}
LANG_NAME = {"es": "Español", "en": "English", "ca": "Català"}

# Página base (ES) -> URL pública en cada idioma
PAGES = {
    "Vora-House":              {"es": "/es/", "en": "/", "ca": "/ca/"},
    "Productos":               {"es": "/es/productos", "en": "/products", "ca": "/ca/productes"},
    "Servicios":               {"es": "/es/servicios", "en": "/services", "ca": "/ca/serveis"},
    "Nosotros":                {"es": "/es/nosotros", "en": "/about", "ca": "/ca/nosaltres"},
    "Contacto":                {"es": "/es/contacto", "en": "/contact", "ca": "/ca/contacte"},
    "Producto-Terra":          {"es": "/es/productos/terra", "en": "/products/terra", "ca": "/ca/productes/terra"},
    "Producto-Mar":            {"es": "/es/productos/mar", "en": "/products/mar", "ca": "/ca/productes/mar"},
    "Producto-Voira":          {"es": "/es/productos/voira", "en": "/products/voira", "ca": "/ca/productes/voira"},
    "Producto-Brisa":          {"es": "/es/productos/brisa", "en": "/products/brisa", "ca": "/ca/productes/brisa"},
    "Aviso-Legal":             {"es": "/es/aviso-legal", "en": "/legal-notice", "ca": "/ca/avis-legal"},
    "Politica-de-Privacidad":  {"es": "/es/politica-de-privacidad", "en": "/privacy-policy", "ca": "/ca/politica-de-privacitat"},
    "Politica-de-Cookies":     {"es": "/es/politica-de-cookies", "en": "/cookie-policy", "ca": "/ca/politica-de-galetes"},
    "Devoluciones-y-Garantia": {"es": "/es/devoluciones-y-garantia", "en": "/returns-warranty", "ca": "/ca/devolucions-i-garantia"},
}
URL_MAP = {lang: {p["es"]: p[lang] for p in PAGES.values()} for lang in LANGS}
IDX = {"en": 1, "ca": 2}


def fname(page, lang):
    return f"{page}{SUFFIX[lang]}.dc.html"


def lang_switcher(s, page, lang):
    urls = PAGES[page]
    # Desplegable de escritorio
    def menu_item(m):
        l = {v: k for k, v in LANG_NAME.items()}[m.group(2)]
        bold = " font-weight: 600;" if l == lang else ""
        return (f'<a href="{urls[l]}" style="display: block; padding: 8px 14px; white-space: nowrap;{bold}" '
                f'style-hover="{m.group(1)}">{LANG_NAME[l]}</a>')
    s = re.sub(r'<a href="[^"]*" style="display: block; padding: 8px 14px; white-space: nowrap;(?: font-weight: 600;)?" '
               r'style-hover="([^"]*)">(Español|English|Català)</a>', menu_item, s)
    # Botón que muestra el idioma actual
    s = re.sub(r'</svg>(Español|English|Català)<svg', f'</svg>{LANG_NAME[lang]}<svg', s)
    # Menú móvil
    def mob_item(m):
        l = m.group(1).lower()
        bold = ' style="font-weight: 600;"' if l == lang else ""
        return f'<a href="{urls[l]}"{bold}>{m.group(1)}</a>'
    s = re.sub(r'<a href="[^"]*"(?: style="font-weight: 600;")?>(ES|EN|CA)</a>', mob_item, s)
    # Pie: enlaces a los otros dos idiomas
    others = "".join(f'<a href="{urls[l]}" style="text-decoration: underline;" hreflang="{l}">{l.upper()}</a>'
                     for l in LANGS if l != lang)
    foot = r'<a href="[^"]*" style="text-decoration: underline;"(?: hreflang="[a-z]+")?>(?:ES|EN|CA)</a>'
    s = re.sub(rf'<span style="display: flex; gap: 14px;">(?:{foot})+</span>|{foot}',
               lambda m: f'<span style="display: flex; gap: 14px;">{others}</span>', s)
    return s


def head_links(s, page, lang):
    urls = PAGES[page]
    s = re.sub(r'<html lang="[a-z]+">', f'<html lang="{HTML_LANG[lang]}">', s, count=1)
    s = re.sub(r'\n<link rel="(?:canonical|alternate)"[^>]*>', "", s)
    block = [f'<link rel="canonical" href="{DOMAIN}{urls[lang]}">']
    block += [f'<link rel="alternate" hreflang="{l}" href="{DOMAIN}{urls[l]}">' for l in LANGS]
    block.append(f'<link rel="alternate" hreflang="x-default" href="{DOMAIN}{urls["en"]}">')
    s = s.replace('<link rel="icon"', "\n".join(block) + '\n<link rel="icon"', 1)
    s = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{DOMAIN}{urls[lang]}">', s)
    s = re.sub(r'\n<meta property="og:locale(?::alternate)?" content="[^"]*">', "", s)
    locs = [f'<meta property="og:locale" content="{OG_LOCALE[lang]}">']
    locs += [f'<meta property="og:locale:alternate" content="{OG_LOCALE[l]}">' for l in LANGS if l != lang]
    s = s.replace('<meta name="twitter:card"', "\n".join(locs) + '\n<meta name="twitter:card"', 1)
    return s


def translate(s, lang):
    d = {es: tr[IDX[lang] - 1] for es, *tr in T}
    head_end = s.index("<x-dc>")
    head, rest = s[:head_end], s[head_end:]
    head = re.sub(r"<title>(.*?)</title>", lambda m: f"<title>{d.get(m.group(1), m.group(1))}</title>", head)
    head = re.sub(r'content="([^"]*)"', lambda m: f'content="{d.get(m.group(1), m.group(1))}"', head)

    js_start = rest.index("</x-dc>")
    body, js = rest[:js_start], rest[js_start:]

    def text_node(m):
        raw = m.group(1)
        core = raw.strip()
        if core in d:
            lead = raw[: len(raw) - len(raw.lstrip())]
            trail = raw[len(raw.rstrip()):]
            return f">{lead}{d[core]}{trail}<"
        return m.group(0)
    body = re.sub(r">([^<>]+)<", text_node, body)
    body = re.sub(r'\b(alt|placeholder|aria-label|title)="([^"]*)"',
                  lambda m: f'{m.group(1)}="{d.get(m.group(2), m.group(2))}"', body)
    i = IDX[lang] - 1
    body = re.sub(r'\bname="([a-z]+)"', lambda m: f'name="{FORM_NAMES[m.group(1)][i]}"' if m.group(1) in FORM_NAMES else m.group(0), body)

    jsq = lambda v: d.get(v, v).replace("\\", "\\\\").replace("'", "\\'")
    js = re.sub(r"\b(label|alt|desc): '([^']*)'", lambda m: f"{m.group(1)}: '{jsq(m.group(2))}'", js)
    js = re.sub(r"encodeURIComponent\('([^']*)'\)", lambda m: f"encodeURIComponent('{jsq(m.group(1))}')", js)
    return head + body + js


def map_urls(s, lang):
    m = URL_MAP[lang]
    s = re.sub(r'href="(/es/[^"#]*)(#[^"]*)?"', lambda x: f'href="{m.get(x.group(1), x.group(1))}{x.group(2) or ""}"', s)
    s = re.sub(r"href: '(/es/[^']*)'", lambda x: f"href: '{m.get(x.group(1), x.group(1))}'", s)
    return s


LOADER = ("<script>document.write('<script src=\"' + (location.protocol === 'file:' ? 'support.js' : '/support.js') "
          "+ '\"><\\/script>');</script>")


def local_preview(s):
    """Permite abrir los .dc.html con doble clic (file://). En un servidor no cambia nada."""
    s = s.replace('<script src="/support.js"></script>', LOADER)
    s = re.sub(r'\n<script data-local-preview>.*?</script>', "", s, flags=re.S)
    files = {urls[l]: fname(page, l) for page, urls in PAGES.items() for l in LANGS}
    fix = (
        "<script data-local-preview>if (location.protocol === 'file:') (function () {\n"
        "  var dir = location.href.replace(/[^/]*$/, ''), map = " + json.dumps(files) + ";\n"
        "  function fix(t, q) { return t.replace(/([\"'(])\\/assets\\//g, '$1' + dir + 'assets/')\n"
        "    .replace(q === '\"' ? /href=\"(\\/[^\"#]*)(#[^\"]*)?\"/g : /href: '(\\/[^'#]*)(#[^']*)?'/g, function (m, u, h) {\n"
        "      return map[u] ? m.replace(u + (h || ''), dir + map[u] + (h || '')) : m; }); }\n"
        "  var x = document.querySelector('x-dc'); if (x) x.innerHTML = fix(x.innerHTML, '\"');\n"
        "  var j = document.querySelector('script[data-dc-script]'); if (j) j.textContent = fix(j.textContent, \"'\");\n"
        "})();</script>"
    )
    return s.replace("</body>", "\n" + fix + "\n</body>", 1)


def build():
    for page in PAGES:
        src_path = os.path.join(ROOT, fname(page, "es"))
        with open(src_path, encoding="utf-8") as f:
            src = f.read()
        for lang in LANGS:
            s = head_links(src, page, lang)
            if lang != "es":
                s = translate(s, lang)
                s = map_urls(s, lang)
            s = lang_switcher(s, page, lang)
            s = local_preview(s)
            out = os.path.join(ROOT, fname(page, lang))
            if lang == "es" and s == src:
                continue
            with open(out, "w", encoding="utf-8") as f:
                f.write(s)
            print("escrito", fname(page, lang))
    write_vercel()
    write_sitemap()


def write_vercel():
    rewrites, redirects = [], []
    for page, urls in PAGES.items():
        for lang in LANGS:
            url, dest = urls[lang], "/" + fname(page, lang)
            rewrites.append({"source": url, "destination": dest})
            if url.endswith("/") and url != "/":
                rewrites.append({"source": url.rstrip("/"), "destination": dest})
            redirects.append({"source": dest, "destination": url, "permanent": True})
    # URLs antiguas sin prefijo de idioma y con prefijo /en
    for page, urls in PAGES.items():
        if page == "Vora-House":
            redirects += [{"source": "/en", "destination": "/", "permanent": True},
                          {"source": "/en/", "destination": "/", "permanent": True}]
            continue
        redirects.append({"source": urls["es"].replace("/es", "", 1), "destination": urls["es"], "permanent": True})
        redirects.append({"source": "/en" + urls["en"], "destination": urls["en"], "permanent": True})
    config = {
        "cleanUrls": False,
        "rewrites": rewrites,
        "redirects": redirects,
        "headers": [
            {"source": "/assets/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=31536000, immutable"}]},
        ],
    }
    with open(os.path.join(ROOT, "vercel.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("escrito vercel.json")


def write_sitemap():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for urls in PAGES.values():
        for lang in LANGS:
            lines.append("  <url>")
            lines.append(f"    <loc>{DOMAIN}{urls[lang]}</loc>")
            for l in LANGS:
                lines.append(f'    <xhtml:link rel="alternate" hreflang="{l}" href="{DOMAIN}{urls[l]}"/>')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{DOMAIN}{urls["en"]}"/>')
            lines.append("  </url>")
    lines.append("</urlset>")
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
    print("escrito sitemap.xml y robots.txt")


if __name__ == "__main__":
    build()
