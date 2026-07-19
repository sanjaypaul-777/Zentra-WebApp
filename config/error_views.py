"""
Custom error views — keep 500 path extremely simple (no DB / heavy context).
"""

from __future__ import annotations

import logging
import secrets
import time

from django.conf import settings
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import render
from django.template import Context, Engine
from django.template.loader import render_to_string

logger = logging.getLogger("brandbox.errors")


def _error_reference() -> str:
    """Short support lookup id, e.g. BBX-500-A3F9."""
    stamp = format(int(time.time()) % 0xFFFF, "X").zfill(4)
    rand = secrets.token_hex(1).upper()
    return f"BBX-500-{stamp}{rand}"[:14]


def page_not_found(request, exception=None):
    """handler404 — full-screen glass card."""
    return render(request, "404.html", status=404)


def server_error(request):
    """
    handler500 — minimal template context only.
    Prefer reference attached by ErrorReferenceMiddleware.
    """
    ref = getattr(request, "error_reference", None) or _error_reference()
    if not getattr(request, "error_reference", None):
        request.error_reference = ref
        logger.error("Server error page rendered with reference=%s", ref)

    try:
        template = Engine.get_default().get_template("500.html")
        html = template.render(
            Context(
                {
                    "error_reference": ref,
                    "STATIC_URL": settings.STATIC_URL,
                }
            )
        )
    except Exception:
        logger.exception("Failed rendering 500.html (ref=%s)", ref)
        html = (
            "<!DOCTYPE html><html><head><title>Server error · BrandBox</title></head>"
            "<body style='background:#0a0a0c;color:#dde4dd;font-family:system-ui;"
            "display:grid;place-items:center;min-height:100vh;margin:0;padding:2rem;text-align:center'>"
            "<div><h1>Something went wrong on our end</h1>"
            f"<p>Error reference: {ref}</p>"
            "<p><a href='/dashboard/' style='color:#4edea3'>Back to Dashboard</a></p>"
            "</div></body></html>"
        )
    return HttpResponseServerError(html)


def attach_error_reference(request, exception) -> str:
    """Create + log a support reference for an unhandled exception."""
    ref = _error_reference()
    request.error_reference = ref
    logger.exception(
        "Unhandled server error reference=%s path=%s",
        ref,
        getattr(request, "path", "?"),
        exc_info=exception,
    )
    return ref


def maintenance_preview(request):
    """DEBUG-only preview of the maintenance page."""
    html = render_to_string(
        "maintenance.html",
        {
            "maintenance_eta": getattr(settings, "MAINTENANCE_ETA", "")
            or "a few minutes",
            "status_page_url": getattr(settings, "STATUS_PAGE_URL", "") or "",
            "STATIC_URL": settings.STATIC_URL,
        },
    )
    return HttpResponse(html, status=503, content_type="text/html; charset=utf-8")
