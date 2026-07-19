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
