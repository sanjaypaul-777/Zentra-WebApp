from django.contrib import admin

from .models import (
    HelpArticle,
    HelpArticleAttachment,
    HelpArticleFeedback,
    HelpCategory,
)


class HelpArticleAttachmentInline(admin.TabularInline):
    model = HelpArticleAttachment
    extra = 1
    fields = ("image", "caption", "sort_order")


@admin.register(HelpCategory)
class HelpCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order", "is_published", "article_count")
    list_editable = ("sort_order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Articles")
    def article_count(self, obj):
        return obj.articles.count()


@admin.register(HelpArticle)
class HelpArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "is_published",
        "is_coming_soon",
        "sort_order",
        "updated_at",
    )
    list_filter = ("category", "is_published", "is_coming_soon")
    list_editable = ("sort_order", "is_published", "is_coming_soon")
    search_fields = ("title", "summary", "body", "slug")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    inlines = [HelpArticleAttachmentInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "category",
                    "title",
                    "slug",
                    "summary",
                    "body",
                    "is_published",
                    "is_coming_soon",
                    "sort_order",
                )
            },
        ),
        (
            "Media",
            {
                "fields": ("hero_image", "video_url", "video_file"),
                "description": "Optional screenshot, image, or video for this article.",
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(HelpArticleFeedback)
class HelpArticleFeedbackAdmin(admin.ModelAdmin):
    list_display = ("article", "was_helpful", "user", "created_at")
    list_filter = ("was_helpful", "created_at")
    search_fields = ("article__title", "session_key", "user__email")
    readonly_fields = ("article", "was_helpful", "user", "session_key", "created_at")

    def has_add_permission(self, request):
        return False
