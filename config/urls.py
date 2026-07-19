"""
Root URL map for BrandBox-Web.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from config import error_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.home.urls")),
    path("", include("apps.accounts.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("checkout/", include("apps.checkout.urls")),
    path("builder/", include("apps.builder.urls")),
]

handler404 = error_views.page_not_found
handler500 = error_views.server_error

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Preview status pages while DEBUG=True (Django skips custom 404/500 in DEBUG)
    urlpatterns += [
        path("__debug__/404/", error_views.page_not_found, name="debug_404"),
        path("__debug__/500/", error_views.server_error, name="debug_500"),
        path(
            "__debug__/maintenance/",
            error_views.maintenance_preview,
            name="debug_maintenance",
        ),
    ]
