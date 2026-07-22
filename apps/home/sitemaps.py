"""sitemap.xml for public marketing pages (controlled via Page SEO in admin)."""

from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_GET
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

from .models import LegalPage, SeoPage
from .seo import marketing_base_url

PAGE_URL_NAMES: dict[str, str] = {
    "home": "home:index",
    "contact": "home:contact",
    "about": "home:about",
    "privacy": "home:privacy",
    "terms": "home:terms",
    "refund": "home:refund",
    "disclaimer": "home:disclaimer",
    "affiliate": "home:affiliate",
    "affiliate_apply": "home:affiliate_register",
}


def _published_legal_keys() -> set[str]:
    return {
        p.key
        for p in LegalPage.objects.filter(is_published=True)
        if (p.body or "").strip()
    }


def _sitemap_entries() -> list[dict]:
    base = marketing_base_url().rstrip("/")
    legal_keys = _published_legal_keys()
    entries: list[dict] = []
    pages = SeoPage.objects.filter(include_in_sitemap=True).exclude(
        robots__startswith="noindex"
    )
    for page in pages:
        if page.key in (
            "about",
            "privacy",
            "terms",
            "refund",
            "disclaimer",
        ) and page.key not in legal_keys:
            continue
        name = PAGE_URL_NAMES.get(page.key)
        if not name:
            continue
        path = reverse(name)
        loc = f"{base}{path}" if path.startswith("/") else f"{base}/{path}"
        entries.append(
            {
                "loc": loc,
                "lastmod": page.updated_at.date().isoformat() if page.updated_at else "",
                "changefreq": page.sitemap_changefreq,
                "priority": f"{float(page.sitemap_priority):.1f}",
            }
        )
    return entries


@require_GET
def sitemap_xml(request):
    urlset = Element(
        "urlset",
        xmlns="http://www.sitemaps.org/schemas/sitemap/0.9",
    )
    for entry in _sitemap_entries():
        url_el = SubElement(urlset, "url")
        SubElement(url_el, "loc").text = entry["loc"]
        if entry["lastmod"]:
            SubElement(url_el, "lastmod").text = entry["lastmod"]
        SubElement(url_el, "changefreq").text = entry["changefreq"]
        SubElement(url_el, "priority").text = entry["priority"]

    raw = tostring(urlset, encoding="utf-8", xml_declaration=True)
    try:
        pretty = minidom.parseString(raw).toprettyxml(indent="  ", encoding="utf-8")
    except Exception:
        pretty = raw
    return HttpResponse(pretty, content_type="application/xml; charset=utf-8")
