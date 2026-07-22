"""
Resolve admin-editable SEO for public pages.

Marketing paths map to SeoPage keys; everything else gets a safe noindex default.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin

from django.conf import settings
from django.http import HttpRequest

from .models import SeoPage, SiteSeoSettings

# path prefix (normalized, trailing slash) → SeoPage.key
PATH_TO_SEO_KEY: dict[str, str] = {
    "/": "home",
    "/contact/": "contact",
    "/about/": "about",
    "/privacy/": "privacy",
    "/terms/": "terms",
    "/refund/": "refund",
    "/disclaimer/": "disclaimer",
    "/affiliate/": "affiliate",
    "/affiliate/register/": "affiliate_apply",
}

# Paths that should never be indexed (auth, app, admin APIs)
PRIVATE_PREFIXES: tuple[str, ...] = (
    "/admin/",
    "/dashboard/",
    "/checkout/",
    "/onboarding/",
    "/login/",
    "/signup/",
    "/logout/",
    "/forgot/",
    "/password/",
    "/oauth/",
    "/api/",
    "/newsletter/",
)


@dataclass
class ResolvedSeo:
    title: str
    description: str
    keywords: str = ""
    canonical: str = ""
    robots: str = "index, follow"
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    og_type: str = "website"
    twitter_card: str = "summary_large_image"
    twitter_site: str = ""
    site_name: str = "BrandBox"
    google_verification: str = ""
    bing_verification: str = ""
    json_ld: list[dict[str, Any]] = field(default_factory=list)
    page_key: str | None = None

    @property
    def json_ld_script(self) -> str:
        if not self.json_ld:
            return ""
        raw = json.dumps(self.json_ld, ensure_ascii=False, separators=(",", ":"))
        # Prevent </script> breakout in HTML
        return raw.replace("<", "\\u003c")


def marketing_base_url() -> str:
    return (getattr(settings, "MARKETING_URL", "") or "").rstrip("/") + "/"


def absolute_url(path_or_url: str) -> str:
    value = (path_or_url or "").strip()
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value
    return urljoin(marketing_base_url(), value.lstrip("/"))


def seo_key_for_path(path: str) -> str | None:
    if not path:
        return None
    normalized = path if path.endswith("/") or path == "/" else f"{path}/"
    if path == "":
        normalized = "/"
    return PATH_TO_SEO_KEY.get(normalized)


def is_private_path(path: str) -> bool:
    if not path:
        return False
    normalized = path if path.startswith("/") else f"/{path}"
    return any(normalized.startswith(prefix) for prefix in PRIVATE_PREFIXES)


def _default_image(site: SiteSeoSettings) -> str:
    if site.default_og_image_url:
        return absolute_url(site.default_og_image_url)
    # Favicon as last-resort share image
    return absolute_url("/static/images/favicon.png")


def _build_json_ld(
    site: SiteSeoSettings,
    page_key: str | None,
    canonical: str,
    page_title: str,
) -> list[dict]:
    blocks: list[dict] = []
    org_name = (site.organization_name or site.site_name or "BrandBox").strip()
    org: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": org_name,
        "url": marketing_base_url().rstrip("/"),
    }
    logo = absolute_url(site.organization_logo_url) or absolute_url(
        "/static/images/favicon.png"
    )
    if logo:
        org["logo"] = logo
    blocks.append(org)

    if page_key == "home":
        blocks.append(
            {
                "@context": "https://schema.org",
                "@type": "WebSite",
                "name": site.site_name or "BrandBox",
                "url": marketing_base_url().rstrip("/"),
            }
        )
    elif page_key and canonical:
        blocks.append(
            {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": page_title or org_name,
                "url": canonical,
            }
        )
    return blocks


def resolve_seo(request: HttpRequest | None = None, *, page_key: str | None = None) -> ResolvedSeo:
    """
    Build SEO tags for the current request (or an explicit page_key).
    Safe if DB rows are missing — falls back to sensible defaults.
    """
    try:
        site = SiteSeoSettings.load()
    except Exception:
        site = SiteSeoSettings(
            site_name="BrandBox",
            default_title_suffix="BrandBox",
            default_meta_description=(
                "Build a Shopify store by niche with AI Store Builder, "
                "import scored products from the Product Vault, "
                "and get coach chat when you need help."
            ),
        )

    path = ""
    if request is not None:
        path = request.path or "/"

    key = page_key or seo_key_for_path(path)
    page: SeoPage | None = None
    if key:
        page = SeoPage.objects.filter(key=key).first()

    private = is_private_path(path) and key is None

    if page:
        title = (page.meta_title or "").strip()
        description = (page.meta_description or "").strip() or (
            site.default_meta_description or ""
        ).strip()
        keywords = (page.meta_keywords or "").strip()
        robots = page.robots or SeoPage.RobotsChoice.INDEX_FOLLOW
        og_title = (page.og_title or title).strip()
        og_description = (page.og_description or description).strip()
        og_image = absolute_url(page.og_image_url) or _default_image(site)
        if page.canonical_url:
            canonical = absolute_url(page.canonical_url)
        else:
            canonical = absolute_url(path if path.endswith("/") else f"{path}/")
            if key == "home":
                canonical = marketing_base_url().rstrip("/") + "/"
    elif private:
        suffix = (site.default_title_suffix or "BrandBox").strip()
        title = suffix
        description = (site.default_meta_description or "").strip()
        keywords = ""
        robots = SeoPage.RobotsChoice.NOINDEX_NOFOLLOW
        og_title = title
        og_description = description
        og_image = _default_image(site)
        canonical = absolute_url(path)
    else:
        suffix = (site.default_title_suffix or "BrandBox").strip()
        title = suffix
        description = (site.default_meta_description or "").strip()
        keywords = ""
        robots = SeoPage.RobotsChoice.INDEX_FOLLOW
        og_title = title
        og_description = description
        og_image = _default_image(site)
        canonical = absolute_url(path if path else "/")

    twitter = (site.twitter_handle or "").lstrip("@").strip()
    return ResolvedSeo(
        title=title or "BrandBox",
        description=description,
        keywords=keywords,
        canonical=canonical,
        robots=robots,
        og_title=og_title or title or "BrandBox",
        og_description=og_description or description,
        og_image=og_image,
        twitter_site=f"@{twitter}" if twitter else "",
        site_name=(site.site_name or "BrandBox").strip(),
        google_verification=(site.google_site_verification or "").strip(),
        bing_verification=(site.bing_site_verification or "").strip(),
        json_ld=_build_json_ld(site, key, canonical, title or "BrandBox"),
        page_key=key,
    )
