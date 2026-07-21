from django.contrib import admin

from .models import ContactMessage, LegalPage, NewsletterSubscriber


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("created_at",)
    list_editable = ("is_read",)


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
    prepopulated_fields = {}
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
