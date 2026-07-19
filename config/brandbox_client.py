"""
Call BrandBox (Node) internal APIs — install status, niches, builds.

Never request or store Shopify Admin access tokens here.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)

SECRET_HEADER = "X-BrandBox-Internal-Secret"
USER_AGENT = "BrandBox-Web/1.0"
DEFAULT_TIMEOUT = 20


def _config() -> tuple[str, str] | tuple[None, None]:
    base = (settings.SHOPIFY_APP_URL or "").rstrip("/")
    secret = getattr(settings, "BRANDBOX_INTERNAL_API_SECRET", "") or ""
    if not base or not secret:
        return None, None
    return base, secret


def _request(
    method: str,
    path: str,
    *,
    query: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """
    Perform an authenticated request to the Node app.

    Returns a dict that always includes ok: bool.
    On failure: ok=False, error=str, status=int|None, checkable=bool.
    """
    base, secret = _config()
    if not base:
        return {
            "ok": False,
            "checkable": False,
            "error": "SHOPIFY_APP_URL is not set",
            "status": None,
        }
    if not secret:
        return {
            "ok": False,
            "checkable": False,
            "error": "BRANDBOX_INTERNAL_API_SECRET is not set",
            "status": None,
        }

    url = f"{base}{path}"
    if query:
        url = f"{url}?{urlencode(query)}"

    headers = {
        "Accept": "application/json",
        SECRET_HEADER: secret,
        "User-Agent": USER_AGENT,
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = Request(url, data=data, headers=headers, method=method.upper())

    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            payload = json.loads(raw) if raw else {}
    except HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")[:400]
        logger.warning("BrandBox %s %s → HTTP %s: %s", method, path, exc.code, body_text)
        detail = body_text
        try:
            parsed = json.loads(body_text)
            detail = parsed.get("error") or parsed.get("message") or body_text
        except Exception:  # noqa: BLE001
            pass
        return {
            "ok": False,
            "checkable": True,
            "error": str(detail) or f"BrandBox returned HTTP {exc.code}",
            "status": exc.code,
        }
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        logger.warning("BrandBox %s %s failed: %s", method, path, exc)
        return {
            "ok": False,
            "checkable": False,
            "error": str(exc),
            "status": None,
        }

    if isinstance(payload, dict):
        payload.setdefault("ok", True)
        payload["checkable"] = True
        return payload
    return {"ok": True, "checkable": True, "data": payload}


def check_app_installed(shop: str, *, timeout: float = 8) -> dict[str, Any]:
    """
    Ask BrandBox Node GET /api/install-status?shop=...

    productsCount is null when unknown — never treat that as 0.
    Prefer productsCountAvailable / statusKey / statusCopy from Node.
    """
    result = _request(
        "GET", "/api/install-status", query={"shop": shop}, timeout=timeout
    )
    if not result.get("ok"):
        return {
            "shop": shop,
            "installed": False,
            "connected": False,
            "checkable": bool(result.get("checkable")),
            "hasOfflineSession": False,
            "productsCount": None,
            "productsCountAvailable": False,
            "statusKey": "not_connected",
            "statusCopy": "Store not connected — connect to see live products",
            "error": result.get("error"),
        }

    products_count = result.get("productsCount")
    available = bool(result.get("productsCountAvailable"))
    if "productsCountAvailable" not in result:
        # Older Node responses: count is live only when it's a number
        available = products_count is not None

    installed = bool(result.get("installed"))
    has_offline = bool(result.get("hasOfflineSession"))
    connected = bool(result.get("connected")) if "connected" in result else (
        installed and has_offline
    )

    status_key = result.get("statusKey")
    status_copy = result.get("statusCopy")
    if not status_key:
        if not connected:
            status_key = "not_connected"
        elif not available:
            status_key = "connected_count_unavailable"
        elif int(products_count or 0) == 0:
            status_key = "connected_empty"
        else:
            status_key = "connected_with_products"
    if not status_copy:
        if status_key == "not_connected":
            status_copy = "Store not connected — connect to see live products"
        elif status_key == "connected_count_unavailable":
            status_copy = "Product count unavailable"
        elif status_key == "connected_empty":
            status_copy = "0 products — ready for winning products"
        else:
            n = int(products_count or 0)
            status_copy = (
                "1 product live" if n == 1 else f"{n} products live"
            )

    return {
        "shop": result.get("shop") or shop,
        "installed": installed,
        "connected": connected,
        "checkable": True,
        "hasOfflineSession": has_offline,
        "productsCount": products_count if available else None,
        "productsCountAvailable": available,
        "statusKey": status_key,
        "statusCopy": status_copy,
        "checkedAt": result.get("checkedAt"),
        "error": None,
    }


def sync_connection_install_flag(connection, result: dict[str, Any]) -> bool:
    """Update ShopConnection.app_installed (+ cached product count when live)."""
    from django.utils import timezone

    installed = bool(result.get("installed") or result.get("connected"))
    fields: list[str] = []

    if installed and not connection.app_installed:
        connection.app_installed = True
        connection.app_installed_at = timezone.now()
        fields.extend(["app_installed", "app_installed_at"])
    elif (
        not installed
        and connection.app_installed
        and result.get("checkable")
        and not result.get("error")
    ):
        # Only disconnect on a definitive Node answer (installed=false with no
        # transport/HTTP error). 5xx / 401 / timeouts must never clear the flag.
        connection.app_installed = False
        connection.app_installed_at = None
        fields.extend(["app_installed", "app_installed_at"])

    count_ok = bool(result.get("productsCountAvailable")) or (
        result.get("productsCount") is not None
        and "productsCountAvailable" not in result
    )
    if (
        count_ok
        and result.get("productsCount") is not None
        and hasattr(connection, "store_product_count")
    ):
        try:
            connection.store_product_count = int(result["productsCount"])
            connection.store_product_count_at = timezone.now()
            fields.extend(["store_product_count", "store_product_count_at"])
        except (TypeError, ValueError):
            pass

    if fields:
        connection.save(update_fields=list(dict.fromkeys(fields)))
    return bool(connection.app_installed)


def fetch_niches() -> dict[str, Any]:
    """GET /api/niches → { ok, niches: [...] }."""
    return _request("GET", "/api/niches", timeout=12)


def sync_niche_product_counts() -> dict[str, Any]:
    """
    Pull productCount from Node and write onto NichePack.product_count
    (keyed by webSlug). Returns { ok, updated, error? }.
    """
    from apps.builder.models import NichePack

    result = fetch_niches()
    if not result.get("ok"):
        return {
            "ok": False,
            "updated": 0,
            "error": result.get("error") or "Failed to fetch niches",
        }

    niches = result.get("niches") or []
    updated = 0
    for item in niches:
        slug = (item.get("webSlug") or item.get("nicheId") or "").strip().lower()
        if not slug:
            continue
        try:
            count = int(item.get("productCount") or 0)
        except (TypeError, ValueError):
            count = 0
        theme = (item.get("themeName") or "").strip()
        qs = NichePack.objects.filter(slug=slug)
        if not qs.exists():
            continue
        fields: dict[str, Any] = {"product_count": count}
        if theme:
            fields["theme_name"] = theme
        qs.update(**fields)
        updated += 1

    return {"ok": True, "updated": updated}


def start_remote_build(*, shop: str, niche_id: str) -> dict[str, Any]:
    """POST /api/build/start — niche_id may be web slug or engine id."""
    return _request(
        "POST",
        "/api/build/start",
        body={"shop": shop, "nicheId": niche_id},
        timeout=30,
    )


def get_remote_build_status(*, shop: str, build_id: str) -> dict[str, Any]:
    """GET /api/build/status — also advances the Node-side build."""
    return _request(
        "GET",
        "/api/build/status",
        query={"shop": shop, "buildId": build_id},
        timeout=60,
    )


def retry_remote_build(*, shop: str, build_id: str) -> dict[str, Any]:
    """POST /api/build/retry → new buildId for the same niche."""
    return _request(
        "POST",
        "/api/build/retry",
        body={"shop": shop, "buildId": build_id},
        timeout=30,
    )


# —— Shopify bridge (Node) — push + live import status only ——————————
# Catalog browse / My Imports drafts live in Django. Do not add search_products back.


def list_imports(*, shop: str, status: str = "") -> dict[str, Any]:
    """GET /api/imports — sync live in_store / removed_from_store into ShopImport."""
    query: dict[str, str] = {"shop": shop}
    if status:
        query["status"] = status
    return _request("GET", "/api/imports", query=query, timeout=30)


def create_import(*, shop: str, source_id: str, **extra: Any) -> dict[str, Any]:
    """POST /api/imports — upsert Node PendingProduct at push time (for tracker)."""
    body: dict[str, Any] = {"shop": shop, "sourceId": source_id}
    body.update({k: v for k, v in extra.items() if v is not None})
    return _request("POST", "/api/imports", body=body, timeout=30)


def publish_import(*, shop: str, import_id: str) -> dict[str, Any]:
    """POST /api/imports/:id/publish — push to Shopify Admin."""
    return _request(
        "POST",
        f"/api/imports/{import_id}/publish",
        body={"shop": shop},
        timeout=60,
    )
