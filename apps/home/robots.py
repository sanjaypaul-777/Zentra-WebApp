"""robots.txt for BrandBox marketing site."""

from django.http import HttpResponse
from django.views.decorators.http import require_GET

from .models import SiteSeoSettings
from .seo import marketing_base_url


@require_GET
def robots_txt(request):
    sitemap = marketing_base_url().rstrip("/") + "/sitemap.xml"
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /dashboard/",
        "Disallow: /checkout/",
        "Disallow: /onboarding/",
        "Disallow: /login/",
        "Disallow: /signup/",
        "Disallow: /logout/",
        "Disallow: /forgot/",
        "Disallow: /password/",
        "Disallow: /oauth/",
        "Disallow: /api/",
        "Disallow: /newsletter/",
        f"Sitemap: {sitemap}",
    ]
    try:
        extra = (SiteSeoSettings.load().robots_extra or "").strip()
    except Exception:
        extra = ""
    if extra:
        lines.append("")
        lines.extend(line.rstrip() for line in extra.splitlines() if line.strip())

    body = "\n".join(lines) + "\n"
    return HttpResponse(body, content_type="text/plain; charset=utf-8")
