import csv
import json

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.http import HttpResponse
from django.utils import timezone
from django.utils.html import format_html

from .models import CoachAssignment, CoachMessage, CoachProfile, CoachSession

User = get_user_model()

STATUS_COLORS = {
    "bot": "#64748b",
    "waiting": "#b45309",
    "live": "#047857",
    "closed": "#94a3b8",
}


class CoachProfileInline(admin.StackedInline):
    model = CoachProfile
    can_delete = True
    extra = 0
    max_num = 1
    classes = ("collapse",)
    fields = ("is_coach", "is_available", "max_concurrent", "display_name")
    verbose_name = "Coach access"
    verbose_name_plural = "Coach access (staff only)"


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = list(getattr(DjangoUserAdmin, "inlines", ())) + [CoachProfileInline]

    def get_inline_instances(self, request, obj=None):
        instances = super().get_inline_instances(request, obj)
        if obj is not None and not obj.is_staff:
            return [i for i in instances if not isinstance(i, CoachProfileInline)]
        return instances


class CoachMessageInline(admin.TabularInline):
    model = CoachMessage
    extra = 0
    can_delete = False
    show_change_link = False
    ordering = ("created_at",)
    classes = ("collapse",)
    verbose_name = "Message"
    verbose_name_plural = "Chat history"
    fields = ("when", "who", "text")
    readonly_fields = ("when", "who", "text")

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Time")
    def when(self, obj):
        if not obj.created_at:
            return "—"
        return timezone.localtime(obj.created_at).strftime("%d %b %Y, %H:%M")

    @admin.display(description="From")
    def who(self, obj):
        if obj.role == CoachMessage.ROLE_AGENT:
            return "Coach Agent"
        if obj.role == CoachMessage.ROLE_SYSTEM:
            return "System"
        if obj.role == CoachMessage.ROLE_COACH and obj.author_id:
            try:
                return obj.author.coach_profile.public_name
            except CoachProfile.DoesNotExist:
                return obj.author.get_username()
        if obj.role == CoachMessage.ROLE_MERCHANT and obj.author_id:
            return obj.author.get_username()
        return obj.get_role_display()

    @admin.display(description="Message")
    def text(self, obj):
        body = (obj.body or "").strip()
        if len(body) > 220:
            body = body[:217] + "…"
        if obj.guide_title:
            body = f"{body}\n↗ {obj.guide_title}"
        return format_html(
            '<div style="white-space:pre-wrap;max-width:640px;line-height:1.4;">{}</div>',
            body,
        )


class CoachAssignmentInline(admin.TabularInline):
    model = CoachAssignment
    extra = 0
    can_delete = False
    classes = ("collapse",)
    verbose_name_plural = "Assignment history"
    fields = ("when", "reason", "from_coach", "to_coach", "by_user")
    readonly_fields = ("when", "reason", "from_coach", "to_coach", "by_user")

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Time")
    def when(self, obj):
        if not obj.created_at:
            return "—"
        return timezone.localtime(obj.created_at).strftime("%d %b %Y, %H:%M")


@admin.register(CoachProfile)
class CoachProfileAdmin(admin.ModelAdmin):
    list_display = ("coach_name", "user", "is_coach", "is_available", "max_concurrent")
    list_display_links = ("coach_name", "user")
    list_filter = ("is_coach", "is_available")
    search_fields = ("user__username", "user__email", "display_name", "user__first_name")
    list_editable = ("is_coach", "is_available", "max_concurrent")
    ordering = ("user__username",)
    autocomplete_fields = ("user",)
    fields = ("user", "display_name", "is_coach", "is_available", "max_concurrent")

    @admin.display(description="Name", ordering="display_name")
    def coach_name(self, obj):
        return obj.public_name


@admin.register(CoachSession)
class CoachSessionAdmin(admin.ModelAdmin):
    list_display = (
        "session_id",
        "status_badge",
        "merchant_label",
        "coach_label",
        "message_count",
        "updated_at",
    )
    list_display_links = ("session_id", "merchant_label")
    list_filter = ("status",)
    search_fields = (
        "id",
        "merchant__username",
        "merchant__email",
        "assigned_coach__username",
        "assigned_coach__email",
    )
    autocomplete_fields = ("merchant", "assigned_coach")
    readonly_fields = (
        "created_at",
        "updated_at",
        "closed_at",
        "last_merchant_message_at",
        "last_coach_message_at",
    )
    inlines = [CoachMessageInline, CoachAssignmentInline]
    actions = ("export_csv", "export_json")
    date_hierarchy = "updated_at"
    ordering = ("-updated_at",)
    list_per_page = 40
    list_select_related = ("merchant", "assigned_coach")

    fieldsets = (
        (
            "Session",
            {
                "fields": ("status", "merchant", "assigned_coach"),
            },
        ),
        (
            "Timestamps",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                    "closed_at",
                    "last_merchant_message_at",
                    "last_coach_message_at",
                ),
            },
        ),
    )

    @admin.display(description="ID", ordering="id")
    def session_id(self, obj):
        return f"#{obj.pk}"

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        color = STATUS_COLORS.get(obj.status, "#64748b")
        label = obj.get_status_display()
        return format_html(
            '<span style="display:inline-block;min-width:72px;padding:3px 10px;'
            "border-radius:999px;background:{};color:#fff;font-size:11px;"
            'font-weight:600;text-align:center;letter-spacing:0.02em;">{}</span>',
            color,
            label,
        )

    @admin.display(description="Merchant", ordering="merchant__username")
    def merchant_label(self, obj):
        u = obj.merchant
        email = getattr(u, "email", "") or ""
        if email:
            return format_html("{}<br><span style='color:#64748b;font-size:12px;'>{}</span>", u.get_username(), email)
        return u.get_username()

    @admin.display(description="Assigned coach", ordering="assigned_coach__username")
    def coach_label(self, obj):
        if not obj.assigned_coach_id:
            return format_html('<span style="color:#94a3b8;">—</span>')
        try:
            name = obj.assigned_coach.coach_profile.public_name
        except CoachProfile.DoesNotExist:
            name = obj.assigned_coach.get_username()
        return name

    @admin.display(description="Msgs")
    def message_count(self, obj):
        return obj.messages.count()

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("messages")

    @admin.action(description="Export CSV")
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        stamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        response["Content-Disposition"] = f'attachment; filename="coach_sessions_{stamp}.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "session_id",
                "status",
                "merchant",
                "merchant_email",
                "assigned_coach",
                "message_id",
                "role",
                "author",
                "body",
                "guide_title",
                "guide_url",
                "created_at",
            ]
        )
        for session in queryset.select_related("merchant", "assigned_coach").prefetch_related(
            "messages__author"
        ):
            msgs = list(session.messages.all())
            if not msgs:
                writer.writerow(
                    [
                        session.id,
                        session.status,
                        session.merchant.get_username(),
                        getattr(session.merchant, "email", ""),
                        session.assigned_coach.get_username() if session.assigned_coach else "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        session.created_at.isoformat(),
                    ]
                )
                continue
            for msg in msgs:
                writer.writerow(
                    [
                        session.id,
                        session.status,
                        session.merchant.get_username(),
                        getattr(session.merchant, "email", ""),
                        session.assigned_coach.get_username() if session.assigned_coach else "",
                        msg.id,
                        msg.role,
                        msg.author.get_username() if msg.author_id else "",
                        msg.body,
                        msg.guide_title,
                        msg.guide_url,
                        msg.created_at.isoformat(),
                    ]
                )
        return response

    @admin.action(description="Export JSON")
    def export_json(self, request, queryset):
        payload = []
        for session in queryset.select_related("merchant", "assigned_coach").prefetch_related(
            "messages__author"
        ):
            payload.append(
                {
                    "id": session.id,
                    "status": session.status,
                    "merchant": session.merchant.get_username(),
                    "merchant_email": getattr(session.merchant, "email", ""),
                    "assigned_coach": (
                        session.assigned_coach.get_username() if session.assigned_coach else None
                    ),
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "messages": [
                        {
                            "id": m.id,
                            "role": m.role,
                            "author": m.author.get_username() if m.author_id else None,
                            "body": m.body,
                            "guide_title": m.guide_title,
                            "guide_url": m.guide_url,
                            "created_at": m.created_at.isoformat(),
                        }
                        for m in session.messages.all()
                    ],
                }
            )
        stamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        response = HttpResponse(
            json.dumps(payload, indent=2),
            content_type="application/json",
        )
        response["Content-Disposition"] = f'attachment; filename="coach_sessions_{stamp}.json"'
        return response


# Keep Messages / Assignment logs out of the main Admin index —
# open them only from a Chat session (cleaner sidebar).


@admin.register(CoachMessage)
class CoachMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "role", "short_body", "created_at")
    list_filter = ("role",)
    search_fields = ("body", "session__id", "author__username")
    autocomplete_fields = ("session", "author")
    readonly_fields = ("created_at",)

    def has_module_permission(self, request):
        return False

    @admin.display(description="Message")
    def short_body(self, obj):
        return (obj.body or "")[:80]


@admin.register(CoachAssignment)
class CoachAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "reason", "from_coach", "to_coach", "created_at")
    list_filter = ("reason",)
    autocomplete_fields = ("session", "from_coach", "to_coach", "by_user")
    readonly_fields = ("created_at",)

    def has_module_permission(self, request):
        return False
