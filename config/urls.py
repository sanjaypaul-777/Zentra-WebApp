"""
Root URL map for BrandBox-Web.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.dashboard.views import (
    address_details,
    address_suggest,
    geo_cities,
    geo_countries,
    geo_phone_meta,
    geo_resolve_timezone,
    geo_states,
    onboarding_page,
)
from apps.home.robots import robots_txt
from apps.home.sitemaps import sitemap_xml
from config import error_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap_xml, name="sitemap_xml"),
    path("", include("apps.home.urls")),
    path("", include("apps.accounts.urls")),
    path("onboarding/", onboarding_page, name="onboarding"),
    path("api/address-suggest/", address_suggest, name="address_suggest"),
    path("api/address-details/", address_details, name="address_details"),
    path("api/geo/countries/", geo_countries, name="geo_countries"),
    path("api/geo/timezone/", geo_resolve_timezone, name="geo_resolve_timezone"),
    path("api/geo/phone-meta/", geo_phone_meta, name="geo_phone_meta"),
    path("api/geo/states/", geo_states, name="geo_states"),
    path("api/geo/cities/", geo_cities, name="geo_cities"),
    path("help/", include("apps.help.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("dashboard/", include("apps.coach.urls")),
    path("checkout/", include("apps.checkout.urls")),
]

handler404 = error_views.page_not_found
handler500 = error_views.server_error

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Preview status pages while DEBUG=True (Django skips custom handler404/500 in DEBUG)
    urlpatterns += [
        path("404/", error_views.page_not_found, name="preview_404"),
        path("500/", error_views.server_error, name="preview_500"),
        path("__debug__/404/", error_views.page_not_found, name="debug_404"),
        path("__debug__/500/", error_views.server_error, name="debug_500"),
        path(
            "__debug__/maintenance/",
            error_views.maintenance_preview,
            name="debug_maintenance",
        ),
    ]
