"""Coach chat — BrandBox Coach Agent + live staff coaches."""

from django.conf import settings
from django.db import models


class CoachProfile(models.Model):
    """
    Coach capability on a staff/admin User — not a separate user type.
    Enable in Django admin (is_coach) for staff accounts that may join the desk.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coach_profile",
    )
    is_coach = models.BooleanField(
        default=True,
        help_text="Allow this staff user to join the coach desk and live chats.",
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Shown as available for new waiting sessions.",
    )
    max_concurrent = models.PositiveSmallIntegerField(
        default=5,
        help_text="Max live merchant sessions this coach can hold at once.",
    )
    display_name = models.CharField(
        max_length=120,
        blank=True,
        help_text="Optional name shown to merchants (defaults to user full name).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]
        verbose_name = "Coach"
        verbose_name_plural = "Coaches"

    def __str__(self) -> str:
        return f"Coach: {self.public_name}"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.is_coach and self.user_id and not self.user.is_staff:
            raise ValidationError(
                {"is_coach": "Coach feature can only be enabled on staff/admin accounts."}
            )

    @property
    def public_name(self) -> str:
        if self.display_name.strip():
            return self.display_name.strip()
        user = self.user
        full = f"{user.first_name} {user.last_name}".strip()
        return full or user.get_username()

    @classmethod
    def user_is_coach(cls, user) -> bool:
        if not user or not getattr(user, "is_authenticated", False):
            return False
        if not getattr(user, "is_staff", False):
            return False
        try:
            profile = user.coach_profile
        except CoachProfile.DoesNotExist:
            return False
        return bool(profile.is_coach)


class CoachSession(models.Model):
    STATUS_BOT = "bot"
    STATUS_WAITING = "waiting"
    STATUS_LIVE = "live"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_BOT, "Agent"),
        (STATUS_WAITING, "Waiting"),
        (STATUS_LIVE, "Live"),
        (STATUS_CLOSED, "Closed"),
    ]

    merchant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coach_sessions",
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_BOT,
        db_index=True,
    )
    assigned_coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_coach_sessions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    last_merchant_message_at = models.DateTimeField(null=True, blank=True)
    last_coach_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Chat session"
        verbose_name_plural = "Chat sessions"
        indexes = [
            models.Index(fields=["status", "-updated_at"]),
            models.Index(fields=["merchant", "-updated_at"]),
        ]

    def __str__(self) -> str:
        merchant = self.merchant.get_username() if self.merchant_id else "?"
        return f"#{self.pk} · {self.get_status_display()} · {merchant}"

    @property
    def agent_active(self) -> bool:
        return self.status in {self.STATUS_BOT, self.STATUS_WAITING}

    @property
    def status_label(self) -> str:
        from config.product import COACH_STATUS_BOT, COACH_STATUS_CLOSED, COACH_STATUS_WAITING

        if self.status == self.STATUS_LIVE and self.assigned_coach_id:
            name = "Coach"
            try:
                name = self.assigned_coach.coach_profile.public_name
            except Exception:
                full = f"{self.assigned_coach.first_name} {self.assigned_coach.last_name}".strip()
                name = full or self.assigned_coach.get_username()
            return f"Live with {name}"
        labels = {
            self.STATUS_BOT: COACH_STATUS_BOT,
            self.STATUS_WAITING: COACH_STATUS_WAITING,
            self.STATUS_LIVE: "Live with a coach",
            self.STATUS_CLOSED: COACH_STATUS_CLOSED,
        }
        return labels.get(self.status, self.status)


class CoachAssignment(models.Model):
    REASON_CLAIM = "claim"
    REASON_REASSIGN = "reassign"
    REASON_LEAVE = "leave"
    REASON_CHOICES = [
        (REASON_CLAIM, "Claim"),
        (REASON_REASSIGN, "Reassign"),
        (REASON_LEAVE, "Leave"),
    ]

    session = models.ForeignKey(
        CoachSession,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    from_coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    to_coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    reason = models.CharField(max_length=16, choices=REASON_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Assignment log"
        verbose_name_plural = "Assignment logs"

    def __str__(self) -> str:
        return f"{self.get_reason_display()} · session #{self.session_id}"


class CoachMessage(models.Model):
    ROLE_MERCHANT = "merchant"
    ROLE_AGENT = "agent"
    ROLE_COACH = "coach"
    ROLE_SYSTEM = "system"
    ROLE_CHOICES = [
        (ROLE_MERCHANT, "Merchant"),
        (ROLE_AGENT, "Coach Agent"),
        (ROLE_COACH, "Coach"),
        (ROLE_SYSTEM, "System"),
    ]

    session = models.ForeignKey(
        CoachSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coach_messages",
    )
    body = models.TextField()
    guide_title = models.CharField(max_length=255, blank=True)
    guide_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        indexes = [
            models.Index(fields=["session", "id"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_role_display()}: {(self.body or '')[:40]}"
