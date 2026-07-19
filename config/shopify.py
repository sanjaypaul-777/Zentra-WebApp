"""
Shopify helpers — normalize shop domain and build OAuth install URL.
OAuth itself runs in the sibling BrandBox (Node) app.
"""

from __future__ import annotations

import re
from urllib.parse import urlencode, urljoin

from django.conf import settings


def normalize_shop_domain(raw: str) -> str | None:
    """Turn pasted input into store.myshopify.com."""
    value = (raw or "").strip().lower()
    if not value:
        return None

    admin = re.search(r"admin\.shopify\.com/store/([a-z0-9][a-z0-9-]*)", value)
    if admin:
        return f"{admin.group(1)}.myshopify.com"

    host = re.sub(r"^https?://", "", value)
    host = host.split("/")[0].rstrip(".")

    if "." not in host:
        host = f"{host}.myshopify.com"

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*\.myshopify\.com", host):
        return None
    return host


def build_shopify_install_url(shop: str, state: str | None = None) -> str:
    """Redirect browser to BrandBox Node /auth/login?shop=... (starts OAuth)."""
    base = (settings.SHOPIFY_APP_URL or "").rstrip("/")
    if not base:
        raise ValueError(
            "Set SHOPIFY_APP_URL in .env.local to your BrandBox tunnel "
            "(from ../BrandBoxApp → npm run dev), e.g. https://xxxx.trycloudflare.com"
        )

    # Block known placeholders that look configured but are unreachable
    host = base.lower().replace("https://", "").replace("http://", "").split("/")[0]
    if host in {"app.brandbox.co", "example.com", "localhost", "127.0.0.1"}:
        raise ValueError(
            f"SHOPIFY_APP_URL is set to “{base}”, which isn’t a live BrandBox tunnel. "
            "Run `npm run dev` in ../BrandBoxApp and paste the Cloudflare URL into .env.local."
        )

    query = {"shop": shop}
    if state:
        query["state"] = state
    # /auth/login?shop=… — shopify.login() starts OAuth when shop is present.
    # Plain /auth?shop=… often lands on an empty login form (route mismatch).
    return f"{base}/auth/login?{urlencode(query)}"
