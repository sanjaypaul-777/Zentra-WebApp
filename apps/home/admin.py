from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    AffiliateApplication,
    ContactMessage,
    LegalPage,
    NewsletterSubscriber,
    SeoPage,
    SiteSeoSettings,
)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("created_at",)
    list_editable = ("is_read",)


@admin.register(AffiliateApplication)
class AffiliateApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "primary_platform",
        "audience_size",
        "status",
        "created_at",
    )
    list_filter = (
        "status",
        "current_activity",
        "primary_platform",
        "audience_size",
        "content_focus",
        "has_affiliate_experience",
        "created_at",
    )
    search_fields = ("name", "email", "promo_url", "notes", "activity_other")
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("status",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "status",
                    "name",
                    "email",
                    "current_activity",
                    "activity_other",
                    "primary_platform",
                    "promo_url",
                    "audience_size",
                    "content_focus",
                    "promotion_plan",
                    "promotion_other",
                    "has_affiliate_experience",
                )
            },
        ),
        ("Notes", {"fields": ("notes",)}),
        ("Internal", {"fields": ("admin_notes", "created_at", "updated_at")}),
    )


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("email",)
    readonly_fields = ("created_at",)


@admin.register(LegalPage)
class LegalPageAdmin(admin.ModelAdmin):
    list_display = ("title", "key", "is_published", "updated_at")
    list_filter = ("is_published", "key")
    search_fields = ("title", "body")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": ("key", "title", "is_published"),
            },
        ),
        (
            "Content",
            {
                "fields": ("body",),
                "description": "Use simple HTML: &lt;h2&gt;, &lt;p&gt;, &lt;ul&gt;, &lt;li&gt;, &lt;a&gt;, &lt;strong&gt;.",
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at")},
        ),
    )


@admin.register(SiteSeoSettings)
class SiteSeoSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Site identity",
            {
                "fields": (
                    "site_name",
                    "default_title_suffix",
                    "organization_name",
                    "organization_logo_url",
                ),
            },
        ),
        (
            "Default search & social",
            {
                "fields": (
                    "default_meta_description",
                    "default_og_image_url",
                    "twitter_handle",
                ),
                "description": (
                    "Used when a page has no override. "
                    "Share image: 1200×630 px, absolute https URL."
                ),
            },
        ),
        (
            "Search Console verification",
            {
                "fields": ("google_site_verification", "bing_site_verification"),
                "description": "Paste the token only — not the full HTML meta tag.",
            },
        ),
        (
            "robots.txt extras",
            {
                "fields": ("robots_extra",),
                "description": (
                    "Optional extra lines. Core Allow/Disallow and Sitemap are generated automatically. "
                    "Preview at /robots.txt"
                ),
            },
        ),
        ("Timestamps", {"fields": ("updated_at",)}),
    )
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return not SiteSeoSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SeoPage)
class SeoPageAdmin(admin.ModelAdmin):
    list_display = (
        "key",
        "meta_title",
        "title_len_badge",
        "desc_len_badge",
        "robots",
        "include_in_sitemap",
        "updated_at",
    )
    list_filter = ("robots", "include_in_sitemap", "key")
    search_fields = ("meta_title", "meta_description", "meta_keywords")
    readonly_fields = ("created_at", "updated_at", "title_len_badge", "desc_len_badge")
    fieldsets = (
        (
            "Page",
            {
                "fields": ("key",),
                "description": (
                    "One SEO record per public marketing page. "
                    "Fix titles/descriptions here when Search Console reports issues."
                ),
            },
        ),
        (
            "Search engines",
            {
                "fields": (
                    "meta_title",
                    "title_len_badge",
                    "meta_description",
                    "desc_len_badge",
                    "meta_keywords",
                    "canonical_url",
                    "robots",
                ),
                "description": (
                    "Title ≈ 50–60 chars. Description ≈ 150–160 chars. "
                    "Leave canonical blank unless you need to force a specific URL."
                ),
            },
        ),
        (
            "Social share (Open Graph / Twitter)",
            {
                "fields": ("og_title", "og_description", "og_image_url"),
                "description": "Blank fields inherit from Search engines (or site defaults).",
            },
        ),
        (
            "Sitemap",
            {
                "fields": (
                    "include_in_sitemap",
                    "sitemap_priority",
                    "sitemap_changefreq",
                ),
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Title length")
    def title_len_badge(self, obj: SeoPage):
        n = obj.title_length
        if n <= 60:
            color = "#0a7a32"
            note = "ok"
        elif n <= 70:
            color = "#a15c00"
            note = "long"
        else:
            color = "#b42318"
            note = "too long"
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span> <span style="opacity:.7;">({})</span>',
            color,
            n,
            note,
        )

    @admin.display(description="Description length")
    def desc_len_badge(self, obj: SeoPage):
        n = obj.description_length
        if not n:
            color = "#a15c00"
            note = "empty"
        elif 120 <= n <= 160:
            color = "#0a7a32"
            note = "ok"
        elif n < 120:
            color = "#a15c00"
            note = "short"
        else:
            color = "#a15c00"
            note = "long"
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span> <span style="opacity:.7;">({})</span>',
            color,
            n,
            note,
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        try:
            extra_context["seo_help_links"] = {
                "robots": reverse("robots_txt"),
                "sitemap": reverse("sitemap_xml"),
            }
        except Exception:
            extra_context["seo_help_links"] = {}
        return super().changelist_view(request, extra_context=extra_context)
