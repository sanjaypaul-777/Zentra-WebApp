"""
Maintenance mode + error reference middleware.
Maintenance check must not depend on the database.
"""

from __future__ import annotations

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string

from config.error_views import attach_error_reference


class ErrorReferenceMiddleware:
    """Attach a BBX-500-… reference and log the exception before the 500 page."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        attach_error_reference(request, exception)
        return None


class MaintenanceModeMiddleware:
    """
    When MAINTENANCE_MODE is true, serve the maintenance page (503).
    Skips static assets and /admin/ so staff can still reach Django admin.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "MAINTENANCE_MODE", False):
            return self.get_response(request)

        path = request.path or "/"
        static_url = getattr(settings, "STATIC_URL", "/static/") or "/static/"
        media_url = getattr(settings, "MEDIA_URL", "/media/") or "/media/"

        if (
            path.startswith(static_url)
            or path.startswith(media_url)
            or path.startswith("/admin")
        ):
            return self.get_response(request)

        html = render_to_string(
            "maintenance.html",
            {
                "maintenance_eta": getattr(settings, "MAINTENANCE_ETA", "") or "",
                "status_page_url": getattr(settings, "STATUS_PAGE_URL", "") or "",
                "STATIC_URL": static_url,
            },
        )
        return HttpResponse(html, status=503, content_type="text/html; charset=utf-8")
