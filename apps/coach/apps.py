from django.apps import AppConfig


class CoachConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.coach"
    label = "coach"
    verbose_name = "Coach Chat"

    def ready(self):
        from django.contrib import admin

        admin.site.site_header = "BrandBox Admin"
        admin.site.site_title = "BrandBox"
        admin.site.index_title = "Control panel"
