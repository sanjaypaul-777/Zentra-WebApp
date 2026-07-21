from django.contrib import admin

from .models import (
    ActivityEvent,
    CallSlot,
    MerchantProfile,
    NotificationPreferences,
    ScheduledCall,
    ShopConnection,
    UserPlan,
)


@admin.register(ShopConnection)
class ShopConnectionAdmin(admin.ModelAdmin):
    list_display = ("shop", "user", "app_installed", "installed_at", "app_installed_at")
    search_fields = ("shop", "user__username", "user__email")
    list_filter = ("app_installed",)
    readonly_fields = ("installed_at", "app_installed_at")


@admin.register(UserPlan)
class UserPlanAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "renews_on", "updated_at")
    list_filter = ("plan",)
    search_fields = ("user__username", "user__email")


@admin.register(MerchantProfile)
class MerchantProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "full_name",
        "company",
        "phone",
        "vertical_industry",
        "desired_niche",
        "onboarding_completed",
        "onboarding_step",
        "updated_at",
    )
    list_filter = (
        "onboarding_completed",
        "vertical_industry",
        "desired_niche",
        "has_existing_shopify_store",
        "current_revenue",
    )
    search_fields = (
        "user__username",
        "user__email",
        "full_name",
        "company",
        "phone",
        "vertical_industry",
        "desired_niche",
    )
    raw_id_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Account link",
            {"fields": ("user", "full_name", "company", "phone")},
        ),
        (
            "Address",
            {
                "fields": (
                    "address_street",
                    "address_city",
                    "address_state",
                    "address_zip",
                    "address_country",
                    "address",
                )
            },
        ),
        (
            "Business",
            {
                "fields": (
                    "vertical_industry",
                    "vertical_other",
                    "desired_niche",
                    "bio",
                    "has_existing_shopify_store",
                    "current_revenue",
                )
            },
        ),
        (
            "Goals & resources",
            {
                "fields": (
                    "ecommerce_goal",
                    "previous_experience",
                    "success_definition",
                    "weekly_time_investment",
                    "ad_budget",
                    "biggest_challenges",
                    "biggest_challenges_other",
                    "additional_comments",
                )
            },
        ),
        (
            "Onboarding",
            {"fields": ("onboarding_step", "onboarding_completed", "created_at", "updated_at")},
        ),
    )


@admin.register(NotificationPreferences)
class NotificationPreferencesAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "email_build_success",
        "email_build_failed",
        "email_winning_products",
        "email_tips",
        "default_niche_slug",
    )
    search_fields = ("user__username", "user__email")


@admin.register(CallSlot)
class CallSlotAdmin(admin.ModelAdmin):
    list_display = ("starts_at", "duration_minutes", "topic", "is_open", "created_at")
    list_filter = ("is_open",)
    search_fields = ("topic",)
    readonly_fields = ("created_at",)


@admin.register(ScheduledCall)
class ScheduledCallAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "starts_at",
        "duration_minutes",
        "topic",
        "status",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("user__username", "user__email", "topic")
    readonly_fields = ("created_at",)
    raw_id_fields = ("user", "slot")


@admin.register(ActivityEvent)
class ActivityEventAdmin(admin.ModelAdmin):
    list_display = ("message", "event_type", "user", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("message", "user__username", "user__email")
    readonly_fields = ("created_at",)
