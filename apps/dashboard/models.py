"""
Dashboard models — shop link, plan, and activity feed.

ShopConnection lifecycle:
  pending  — user entered a *.myshopify.com domain (Section A); no valid token yet.
             Must NOT count as "connected" anywhere in the app.
  active   — OAuth completed and install confirmed (app_installed=True).
             This is View B / Case A on Overview.
"""

from django.conf import settings
from django.db import models


class ShopConnection(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shop_connections",
    )
    shop = models.CharField(max_length=255, unique=True)
    app_installed = models.BooleanField(default=False)
    installed_at = models.DateTimeField(auto_now_add=True)
    app_installed_at = models.DateTimeField(null=True, blank=True)
    # Cached live Shopify product count (from Node install-status)
    store_product_count = models.PositiveIntegerField(null=True, blank=True)
    store_product_count_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-installed_at"]

    def __str__(self) -> str:
        state = "active" if self.app_installed else "pending"
        return f"{self.user_id} → {self.shop} ({state})"

    @property
    def storefront_url(self) -> str:
        return f"https://{self.shop}"

    @property
    def is_preview(self) -> bool:
        """Staff-only demo shop — not a real Shopify storefront."""
        return self.shop.startswith("admin-preview-")

    @property
    def is_connected(self) -> bool:
        """True only when OAuth/install confirmed a valid session/token."""
        return bool(self.app_installed) and not self.is_preview

    @classmethod
    def active_for_user(cls, user) -> "ShopConnection | None":
        return (
            cls.objects.filter(user=user, app_installed=True)
            .exclude(shop__startswith="admin-preview-")
            .first()
        )

    @classmethod
    def pending_for_user(cls, user) -> "ShopConnection | None":
        return (
            cls.objects.filter(user=user, app_installed=False)
            .order_by("-installed_at")
            .first()
        )

    @classmethod
    def user_is_connected(cls, user) -> bool:
        return cls.active_for_user(user) is not None

    @classmethod
    def for_builder(cls, user) -> "ShopConnection | None":
        """
        Active shop for AI Store Builder.
        Customers must have a real connected store.
        Staff/superusers may use a local preview shop when it is marked installed.
        """
        active = cls.active_for_user(user)
        if active:
            return active
        if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
            preview = cls.ensure_staff_preview(user)
            if preview.app_installed:
                return preview
        return None

    @classmethod
    def staff_preview_for_user(cls, user) -> "ShopConnection | None":
        """Existing admin-preview shop for this user, if any (does not create)."""
        return (
            cls.objects.filter(user=user, shop__startswith="admin-preview-")
            .order_by("-id")
            .first()
        )

    @classmethod
    def ensure_staff_preview(cls, user) -> "ShopConnection":
        """
        Demo connection for Django admin/staff — not a real Shopify OAuth link.

        Creates a preview shop only when missing. Does NOT force app_installed
        back to True — staff can uncheck it in admin to test the connect UI.
        """
        from django.utils import timezone

        shop = f"admin-preview-{user.pk}.myshopify.com"
        connection, created = cls.objects.get_or_create(
            shop=shop,
            defaults={
                "user": user,
                "app_installed": True,
                "app_installed_at": timezone.now(),
            },
        )
        if connection.user_id != user.pk:
            # Shop uniqueness collision — attach a unique slug
            shop = f"admin-preview-{user.pk}-{timezone.now().timestamp():.0f}.myshopify.com"
            connection = cls.objects.create(
                user=user,
                shop=shop,
                app_installed=True,
                app_installed_at=timezone.now(),
            )
        return connection


class UserPlan(models.Model):
    class Plan(models.TextChoices):
        FREE = "free", "Free"
        PRO = "pro", "Pro"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="plan_profile",
    )
    plan = models.CharField(
        max_length=16,
        choices=Plan.choices,
        default=Plan.FREE,
    )
    renews_on = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user_id} · {self.plan}"

    @property
    def is_pro(self) -> bool:
        return self.plan == self.Plan.PRO

    @property
    def label(self) -> str:
        return self.get_plan_display()


class NotificationPreferences(models.Model):
    """Per-user email notification toggles (Settings → Notifications)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_prefs",
    )
    email_build_success = models.BooleanField(default=True)
    email_build_failed = models.BooleanField(default=True)
    email_winning_products = models.BooleanField(default=True)
    email_tips = models.BooleanField(default=False)
    # Preferred niche slug for AI Store Builder pre-select
    default_niche_slug = models.SlugField(max_length=64, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    NOTIFICATION_FIELDS = (
        "email_build_success",
        "email_build_failed",
        "email_winning_products",
        "email_tips",
    )

    def __str__(self) -> str:
        return f"notifications · user {self.user_id}"

    @classmethod
    def for_user(cls, user) -> "NotificationPreferences":
        prefs, _ = cls.objects.get_or_create(user=user)
        return prefs


class MerchantProfile(models.Model):
    """Customer profile — onboarding + Settings → Account (same fields)."""

    class Vertical(models.TextChoices):
        FASHION = "fashion", "Fashion"
        BEAUTY = "beauty", "Beauty"
        FITNESS = "fitness", "Fitness"
        HOME_DECOR = "home_decor", "Home Decor"
        ELECTRONICS = "electronics", "Electronics"
        PET = "pet", "Pet"
        KIDS_BABY = "kids_baby", "Kids & Baby"
        JEWELRY = "jewelry", "Jewelry"
        GENERAL = "general", "General"
        OTHER = "other", "Other"

    class Niche(models.TextChoices):
        LIVING = "living", "Living"
        PEAK = "peak", "Peak"
        VOGUE = "vogue", "Vogue"
        LUX = "lux", "Lux"
        PAWS = "paws", "Paws"
        JUNIOR = "junior", "Junior"
        CARE = "care", "Care"
        TECH = "tech", "Tech"
        MART = "mart", "Mart"
        POD = "pod", "Pod"
        NOT_SURE = "not_sure", "Not sure yet — recommend one for me"

    class Revenue(models.TextChoices):
        ZERO_1K = "0_1k", "$0 - $1K"
        ONE_5K = "1_5k", "$1-5K/mo"
        FIVE_10K = "5_10k", "$5K-10K/mo"
        TEN_PLUS = "10k_plus", "$10K+/mo"

    class EcommerceGoal(models.TextChoices):
        REPLACE_JOB = "replace_job", "Replace my job income"
        SIDE_INCOME = "side_income", "Build a side income"
        TEST_IDEA = "test_idea", "Test a business idea"
        SCALE_BRAND = "scale_brand", "Scale an existing brand"
        EXPLORING = "exploring", "Just exploring"

    class PreviousExperience(models.TextChoices):
        NEVER = "never", "Never sold online"
        TRIED = "tried", "Tried, didn't work out"
        CURRENTLY = "currently", "Currently selling"
        EXPERIENCED = "experienced", "Experienced seller"

    class SuccessDefinition(models.TextChoices):
        QUIT_JOB = "quit_job", "Quit my day job"
        EXTRA_1_2K = "extra_1_2k", "Extra $1-2K/month"
        SELL_BRAND = "sell_brand", "Build a brand I can eventually sell"
        LEARN = "learn", "Just want to learn"

    class WeeklyTime(models.TextChoices):
        UNDER_5 = "under_5", "<5 hrs"
        FIVE_10 = "5_10", "5-10 hrs"
        TEN_20 = "10_20", "10-20 hrs"
        FULL_TIME = "full_time", "20+ hrs (full-time)"

    class AdBudget(models.TextChoices):
        ZERO_100 = "0_100", "$0-100/mo"
        ONE_HUNDRED_500 = "100_500", "$100-500/mo"
        FIVE_HUNDRED_2K = "500_2k", "$500-2K/mo"
        TWO_K_PLUS = "2k_plus", "$2K+/mo"

    CHALLENGE_CHOICES = (
        ("finding_products", "Finding good products"),
        ("building_store", "Building the store"),
        ("running_ads", "Running ads"),
        ("getting_sales", "Getting sales"),
        ("time", "Time"),
        ("technical_skills", "Technical skills"),
        ("other", "Other"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="merchant_profile",
    )
    full_name = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True)
    address_street = models.CharField(max_length=255, blank=True)
    address_city = models.CharField(max_length=128, blank=True)
    address_state = models.CharField(max_length=128, blank=True)
    address_zip = models.CharField(max_length=32, blank=True)
    address_country = models.CharField(max_length=128, blank=True)
    phone = models.CharField(max_length=64, blank=True)
    vertical_industry = models.CharField(max_length=64, blank=True)
    vertical_other = models.CharField(max_length=255, blank=True)
    desired_niche = models.CharField(max_length=64, blank=True)
    bio = models.TextField(blank=True)
    has_existing_shopify_store = models.BooleanField(null=True, blank=True)
    current_revenue = models.CharField(max_length=32, blank=True)
    ecommerce_goal = models.CharField(max_length=32, blank=True)
    previous_experience = models.CharField(max_length=32, blank=True)
    success_definition = models.CharField(max_length=32, blank=True)
    weekly_time_investment = models.CharField(max_length=32, blank=True)
    ad_budget = models.CharField(max_length=32, blank=True)
    biggest_challenges = models.JSONField(default=list, blank=True)
    biggest_challenges_other = models.CharField(max_length=255, blank=True)
    additional_comments = models.TextField(blank=True, null=True)
    onboarding_step = models.PositiveSmallIntegerField(default=1)
    onboarding_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"profile · user {self.user_id}"

    @classmethod
    def for_user(cls, user) -> "MerchantProfile":
        profile, _ = cls.objects.get_or_create(user=user)
        return profile

    def sync_address_text(self) -> None:
        """Keep legacy `address` in sync for Settings display."""
        parts = [
            self.address_street.strip(),
            ", ".join(
                p
                for p in (
                    self.address_city.strip(),
                    self.address_state.strip(),
                    self.address_zip.strip(),
                )
                if p
            ),
            self.address_country.strip(),
        ]
        self.address = "\n".join(p for p in parts if p)

    def sync_user_name(self) -> None:
        """Mirror full_name onto User first/last for auth display."""
        name = (self.full_name or "").strip()
        if not name:
            return
        parts = name.split(None, 1)
        self.user.first_name = parts[0]
        self.user.last_name = parts[1] if len(parts) > 1 else ""
        self.user.save(update_fields=["first_name", "last_name"])

    @property
    def display_name(self) -> str:
        if (self.full_name or "").strip():
            return self.full_name.strip()
        full = (self.user.get_full_name() or "").strip()
        if full:
            return full
        if self.user.first_name:
            return self.user.first_name
        return "—"

    @property
    def first_name(self) -> str:
        if (self.full_name or "").strip():
            return self.full_name.strip().split()[0]
        if self.user.first_name:
            return self.user.first_name.strip()
        full = (self.user.get_full_name() or "").strip()
        if full:
            return full.split()[0]
        return "there"

    @property
    def vertical_display(self) -> str:
        if self.vertical_industry == self.Vertical.OTHER and self.vertical_other:
            return self.vertical_other
        try:
            return self.Vertical(self.vertical_industry).label
        except ValueError:
            return self.vertical_industry or "—"

    @property
    def niche_display(self) -> str:
        try:
            return self.Niche(self.desired_niche).label
        except ValueError:
            return self.desired_niche or "—"


class CallSlot(models.Model):
    """Admin-curated open time slots merchants can book on Schedule."""

    starts_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    topic = models.CharField(max_length=255, default="BrandBox strategy call")
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["starts_at"]

    def __str__(self) -> str:
        state = "open" if self.is_open else "taken"
        return f"{self.starts_at:%Y-%m-%d %H:%M} · {self.topic} ({state})"


class ScheduledCall(models.Model):
    """A merchant's booked (or past) live call."""

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="scheduled_calls",
    )
    starts_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    topic = models.CharField(max_length=255, default="BrandBox strategy call")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    slot = models.OneToOneField(
        CallSlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booking",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["starts_at"]

    def __str__(self) -> str:
        return f"user {self.user_id} · {self.starts_at:%Y-%m-%d %H:%M} · {self.status}"

    @classmethod
    def next_for_user(cls, user):
        """Upcoming scheduled call, if any."""
        from django.utils import timezone

        return (
            cls.objects.filter(
                user=user,
                status=cls.Status.SCHEDULED,
                starts_at__gte=timezone.now(),
            )
            .order_by("starts_at")
            .first()
        )

    @classmethod
    def has_past_for_user(cls, user) -> bool:
        from django.utils import timezone

        return cls.objects.filter(user=user).filter(
            models.Q(status=cls.Status.COMPLETED)
            | models.Q(starts_at__lt=timezone.now())
        ).exists()


class ActivityEvent(models.Model):
    class EventType(models.TextChoices):
        STORE = "store", "Store"
        PRODUCT = "product", "Product"
        IMPORT = "import", "Import"
        BILLING = "billing", "Billing"
        SYSTEM = "system", "System"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activity_events",
    )
    event_type = models.CharField(
        max_length=32,
        choices=EventType.choices,
        default=EventType.SYSTEM,
    )
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user_id}: {self.message[:40]}"
