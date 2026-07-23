"""
Template context: public settings for Shopify / product URLs.
"""

from django.conf import settings


def brandbox_settings(request):
    return {
        "SHOPIFY_APP_URL": settings.SHOPIFY_APP_URL,
        "SHOPIFY_PARTNER_SIGNUP_URL": settings.SHOPIFY_PARTNER_SIGNUP_URL,
        "MARKETING_URL": settings.MARKETING_URL,
        "DASHBOARD_URL": settings.DASHBOARD_URL,
    }


def product_settings(request):
    """Homepage offer % and affiliate % — edit config/product.py."""
    from config.product import as_template_context

    return {"product": as_template_context()}


def seo_meta(request):
    """Admin-editable SEO tags for the current path."""
    from apps.home.seo import resolve_seo

    try:
        return {"seo": resolve_seo(request)}
    except Exception:
        return {"seo": None}
