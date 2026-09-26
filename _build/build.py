"""Generate the service / city pages and sitemap.xml.

Run from the repo root:  python _build/build.py
Folders starting with "_" are not published by GitHub Pages.
"""
import html
import json
import os
import sys
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(__file__))
from common import BASE, PHONE, PHONE_DISPLAY, EMAIL, WA, PRICING, PORTFOLIO, STEPS, UI, WILAYAS, LASTMOD
from services import SERVICES
from cities import CITIES, HUB

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = SERVICES + [HUB] + CITIES
HOME = {"ar": "/", "fr": "/?lang=fr"}

e = html.escape


def url(page, lang):
    return BASE + page["slug"][lang]


def rich(text):
    # content strings may contain <strong>/<a> markup written by us
    return text


def blocks_html(blocks):
    out = []
    for b in blocks:
        if isinstance(b, list):
            out.append("<ul>" + "".join(f"<li>{rich(i)}</li>" for i in b) + "</ul>")
        else:
            out.append(f"<p>{rich(b)}</p>")
    return "\n".join(out)


def pricing_html(kind, lang):
    t = UI[lang]
    cards = []
    for p in PRICING[kind]:
        feats = "".join(f"<li>{e(f)}</li>" for f in p["features"][lang])
        cls = "price-card featured" if p.get("featured") else "price-card"
        badge = f'<span class="price-badge">{t["popular"]}</span>' if p.get("featured") else ""
        cards.append(
            f'<div class="{cls}">{badge}<div class="price-tier">{e(p["tier"][lang])}</div>'
            f'<div class="price-amount">{e(p["price"][lang])}</div>'
            f'<div class="price-for">{e(p["for"][lang])}</div><ul>{feats}</ul></div>'
        )
    note = t["price_note_apps"] if kind == "apps" else t["price_note_web"]
    return f'<div class="price-grid">{"".join(cards)}</div><p class="note">{note}</p>'


def portfolio_html(keys, lang):
    t = UI[lang]
    cards = []
    for k in keys:
        p = PORTFOLIO[k]
        cards.append(
            f'<a class="pf-card" href="{p["url"]}" target="_blank" rel="noopener">'
            f'<span class="pf-tag">{e(p["tag"][lang])}</span>'
            f'<strong>{e(p["name"][lang])}</strong><span>{e(p["desc"][lang])}</span>'
            f'<em>{t["view_live"]}</em></a>'
        )
    return f'<div class="pf-grid">{"".join(cards)}</div>'


def steps_html(lang):
    return '<ol class="steps">' + "".join(
        f"<li><strong>{e(s[0])}</strong><span>{e(s[1])}</span></li>" for s in STEPS[lang]
    ) + "</ol>"


def faq_html(faq):
    return '<div class="faq">' + "".join(
        f"<details><summary>{e(q)}</summary><p>{rich(a)}</p></details>" for q, a in faq
    ) + "</div>"


def wilayas_html(lang):
    return '<ul class="wilayas">' + "".join(
        f"<li><span>{n:02d}</span>{e(w[0] if lang == 'ar' else w[1])}</li>" for n, w in enumerate(WILAYAS, 1)
    ) + "</ul>"


def related_html(page, lang):
    t = UI[lang]
    def links(items):
        return "".join(
            f'<a href="{p["slug"][lang]}">{e(p[lang]["short"])}</a>' for p in items if p is not page
        )
    return (
        f'<div class="related"><h2>{t["other_services"]}</h2><div class="chips">{links(SERVICES)}</div>'
        f'<h2>{t["cities"]}</h2><div class="chips">{links([HUB] + CITIES)}</div></div>'
    )


def schema(page, lang):
    c = page[lang]
    t = UI[lang]
    graph = [
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": t["home"], "item": BASE + HOME[lang]},
                {"@type": "ListItem", "position": 2, "name": c["short"], "item": url(page, lang)},
            ],
        },
        {
            "@type": "Service",
            "name": c["h1"],
            "description": c["desc"],
            "url": url(page, lang),
            "inLanguage": lang,
            "serviceType": c["short"],
            "provider": {"@id": BASE + "/#business"},
            "areaServed": (
                {"@type": "City", "name": page["city"][lang]} if page.get("city")
                else {"@type": "Country", "name": "Algeria"}
            ),
        },
    ]
    if c.get("faq"):
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}}
                for q, a in c["faq"]
            ],
        })
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=1)


def strip_tags(s):
    import re
    return re.sub(r"<[^>]+>", "", s)


def render(page, lang):
    c = page[lang]
    t = UI[lang]
    other = "fr" if lang == "ar" else "ar"
    d = "rtl" if lang == "ar" else "ltr"
    wa_text = quote(t["wa_msg"].format(c["short"]))
    wa_link = f"https://wa.me/{WA}?text={wa_text}"
    fonts = (
        "family=Cairo:wght@400;700;900" if lang == "ar" else "family=Inter:wght@400;600;800"
    )

    sections = "\n".join(
        f'<section class="block"><h2>{e(h)}</h2>{blocks_html(b)}</section>' for h, b in c["sections"]
    )
    extra = ""
    if page.get("wilayas"):
        extra += f'<section class="block"><h2>{t["wilayas_title"]}</h2>{wilayas_html(lang)}</section>'
    if page.get("portfolio"):
        extra += f'<section class="block"><h2>{t["portfolio_title"]}</h2>{portfolio_html(page["portfolio"], lang)}</section>'
    if page.get("pricing"):
        for kind in page["pricing"]:
            extra += f'<section class="block wide"><h2>{t["pricing_title_" + kind]}</h2>{pricing_html(kind, lang)}</section>'
    extra += f'<section class="block"><h2>{t["steps_title"]}</h2>{steps_html(lang)}</section>'
    if c.get("faq"):
        extra += f'<section class="block"><h2>{t["faq_title"]}</h2>{faq_html(c["faq"])}</section>'

    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{d}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(c["title"])}</title>
<meta name="description" content="{e(c["desc"])}">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{url(page, lang)}">
<link rel="alternate" hreflang="ar" href="{url(page, 'ar')}">
<link rel="alternate" hreflang="fr" href="{url(page, 'fr')}">
<link rel="alternate" hreflang="x-default" href="{url(page, 'ar')}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#e8431a">
<meta property="og:type" content="website">
<meta property="og:site_name" content="SnetProDz">
<meta property="og:url" content="{url(page, lang)}">
<meta property="og:title" content="{e(c["title"])}">
<meta property="og:description" content="{e(c["desc"])}">
<meta property="og:image" content="{BASE}/og-image.png">
<meta property="og:locale" content="{'ar_DZ' if lang == 'ar' else 'fr_DZ'}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?{fonts}&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
<script type="application/ld+json">
{schema(page, lang)}
</script>
</head>
<body>
<div class="topbar"><a href="{page["slug"][other]}" hreflang="{other}" lang="{other}">{t["switch"]}</a></div>
<header class="nav">
  <a href="{HOME[lang]}" class="logo">Snet<span>ProDz</span></a>
  <nav aria-label="{t["menu"]}">
    <a href="{HOME[lang].split('?')[0]}{'?lang=fr' if lang == 'fr' else ''}#services">{t["services"]}</a>
    <a href="{HUB["slug"][lang]}">{t["cities"]}</a>
    <a href="#pricing-anchor">{t["pricing"]}</a>
    <a href="{wa_link}" class="nav-cta" target="_blank" rel="noopener">{t["quote"]}</a>
  </nav>
</header>

<main>
<div class="hero">
  <ol class="crumbs"><li><a href="{HOME[lang]}">{t["home"]}</a></li><li>{e(c["short"])}</li></ol>
  <span class="kicker">{page["icon"]} {e(c["kicker"])}</span>
  <h1>{e(c["h1"])}</h1>
  <p class="lead">{rich(c["lead"])}</p>
  <div class="actions">
    <a class="btn" href="{wa_link}" target="_blank" rel="noopener">{t["cta_wa"]}</a>
    <a class="btn-ghost" href="tel:{PHONE}">{t["call"]} <bdi dir="ltr">{PHONE_DISPLAY}</bdi></a>
  </div>
  <ul class="trust">{"".join(f"<li>{x}</li>" for x in t["trust"])}</ul>
</div>

<div class="content">
{sections}
<span id="pricing-anchor"></span>
{extra}
</div>

<section class="cta">
  <h2>{e(c.get("cta", t["cta_title"]))}</h2>
  <p>{t["cta_text"]}</p>
  <div class="actions">
    <a class="btn" href="{wa_link}" target="_blank" rel="noopener">{t["cta_wa"]}</a>
    <a class="btn-ghost light" href="{HOME[lang].split('?')[0]}{'?lang=fr' if lang == 'fr' else ''}#contact">{t["cta_form"]}</a>
  </div>
</section>

<div class="content">{related_html(page, lang)}</div>
</main>

<footer class="footer">
  <div>
    <a href="{HOME[lang]}" class="logo light">Snet<span>ProDz</span></a>
    <p>{t["footer_desc"]}</p>
  </div>
  <div>
    <h3>{t["contact"]}</h3>
    <p><a href="{wa_link}" target="_blank" rel="noopener">WhatsApp: <bdi dir="ltr">{PHONE_DISPLAY}</bdi></a><br>
    <a href="mailto:{EMAIL}">{EMAIL}</a><br>{t["address"]}</p>
  </div>
</footer>
<div class="copy">© 2026 SnetProDz — {t["copy"]}</div>
<a href="{wa_link}" class="wa-float" target="_blank" rel="noopener" aria-label="WhatsApp">💬</a>
</body>
</html>
"""


def sitemap():
    def entry(loc_ar, loc_fr, lang):
        loc = loc_ar if lang == "ar" else loc_fr
        return (
            f"  <url>\n    <loc>{e(loc)}</loc>\n"
            f'    <xhtml:link rel="alternate" hreflang="ar" href="{e(loc_ar)}"/>\n'
            f'    <xhtml:link rel="alternate" hreflang="fr" href="{e(loc_fr)}"/>\n'
            f'    <xhtml:link rel="alternate" hreflang="x-default" href="{e(loc_ar)}"/>\n'
            f"    <lastmod>{LASTMOD}</lastmod>\n  </url>\n"
        )
    body = entry(BASE + "/", BASE + "/?lang=fr", "ar") + entry(BASE + "/", BASE + "/?lang=fr", "fr")
    for p in PAGES:
        for lang in ("ar", "fr"):
            body += entry(url(p, "ar"), url(p, "fr"), lang)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + body + "</urlset>\n"
    )


def main():
    for p in PAGES:
        for lang in ("ar", "fr"):
            path = os.path.join(ROOT, p["slug"][lang].strip("/"), "index.html")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(render(p, lang))
            print("wrote", p["slug"][lang])
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(sitemap())
    print("wrote sitemap.xml with", 2 + 2 * len(PAGES), "urls")


if __name__ == "__main__":
    main()
