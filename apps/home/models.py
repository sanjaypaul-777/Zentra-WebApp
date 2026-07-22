from django.core.exceptions import ValidationError
from django.db import models


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} — {self.email}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email


class LegalPage(models.Model):
    """About / Privacy / Terms / Refund / Disclaimer — editable in Django admin."""

    class PageKey(models.TextChoices):
        ABOUT = "about", "About Us"
        PRIVACY = "privacy", "Privacy Policy"
        TERMS = "terms", "Terms of Service"
        REFUND = "refund", "Refund Policy"
        DISCLAIMER = "disclaimer", "Disclaimer"

    key = models.CharField(
        max_length=32,
        unique=True,
        choices=PageKey.choices,
        help_text="Which policy this is (fixed URL).",
    )
    title = models.CharField(max_length=200)
    body = models.TextField(
        help_text="HTML allowed (headings, paragraphs, lists). Staff-only content.",
    )
    is_published = models.BooleanField(
        default=True,
        help_text="Unpublished pages show a simple unavailable message publicly.",
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["key"]
        verbose_name = "Legal page"
        verbose_name_plural = "Legal pages"

    def __str__(self) -> str:
        return self.title


class SiteSeoSettings(models.Model):
    """Singleton site-wide SEO defaults — edit once in admin."""

    site_name = models.CharField(
        max_length=120,
        default="BrandBox",
        help_text="Shown in social previews (og:site_name).",
    )
    default_title_suffix = models.CharField(
        max_length=80,
        default="BrandBox",
        blank=True,
        help_text="Optional suffix for pages without a custom title (e.g. BrandBox).",
    )
    default_meta_description = models.CharField(
        max_length=320,
        blank=True,
        help_text="Fallback meta description when a page has none. Aim for ~150–160 characters.",
    )
    default_og_image_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Default share image (1200×630 recommended). Absolute URL.",
    )
    twitter_handle = models.CharField(
        max_length=64,
        blank=True,
        help_text="Without @ — e.g. brandbox. Used for twitter:site.",
    )
    organization_name = models.CharField(max_length=120, default="BrandBox", blank=True)
    organization_logo_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Logo URL for Organization JSON-LD. Absolute URL.",
    )
    google_site_verification = models.CharField(
        max_length=120,
        blank=True,
        help_text="Google Search Console verification token only (not the full meta tag).",
    )
    bing_site_verification = models.CharField(
        max_length=120,
        blank=True,
        help_text="Bing Webmaster verification token only.",
    )
    robots_extra = models.TextField(
        blank=True,
        help_text="Extra lines appended to robots.txt (one directive per line).",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site SEO settings"
        verbose_name_plural = "Site SEO settings"

    def __str__(self) -> str:
        return "Site SEO settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls) -> "SiteSeoSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class SeoPage(models.Model):
    """Per-page SEO — admin can fix titles, descriptions, social share, and indexing."""

    class PageKey(models.TextChoices):
        HOME = "home", "Home"
        CONTACT = "contact", "Contact"
        ABOUT = "about", "About Us"
        PRIVACY = "privacy", "Privacy Policy"
        TERMS = "terms", "Terms of Service"
        REFUND = "refund", "Refund Policy"
        DISCLAIMER = "disclaimer", "Disclaimer"
        AFFILIATE = "affiliate", "Affiliate"
        AFFILIATE_APPLY = "affiliate_apply", "Affiliate Register"

    class RobotsChoice(models.TextChoices):
        INDEX_FOLLOW = "index, follow", "Index + follow (default)"
        NOINDEX_FOLLOW = "noindex, follow", "Noindex + follow"
        INDEX_NOFOLLOW = "index, nofollow", "Index + nofollow"
        NOINDEX_NOFOLLOW = "noindex, nofollow", "Noindex + nofollow"

    class ChangeFreq(models.TextChoices):
        ALWAYS = "always", "Always"
        HOURLY = "hourly", "Hourly"
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"
        YEARLY = "yearly", "Yearly"
        NEVER = "never", "Never"

    key = models.CharField(
        max_length=32,
        unique=True,
        choices=PageKey.choices,
        help_text="Which public page these tags apply to.",
    )
    meta_title = models.CharField(
        max_length=70,
        help_text="Browser tab + Google title. Keep under ~60 characters.",
    )
    meta_description = models.CharField(
        max_length=320,
        blank=True,
        help_text="Search snippet. Aim for ~150–160 characters.",
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional comma-separated keywords (low SEO impact; optional).",
    )
    canonical_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Leave blank to auto-build from the page URL. Use only to force a specific canonical.",
    )
    robots = models.CharField(
        max_length=32,
        choices=RobotsChoice.choices,
        default=RobotsChoice.INDEX_FOLLOW,
        help_text="Tell search engines whether to index this page.",
    )
    og_title = models.CharField(
        max_length=70,
        blank=True,
        help_text="Open Graph / social title. Blank = use meta title.",
    )
    og_description = models.CharField(
        max_length=320,
        blank=True,
        help_text="Social share description. Blank = use meta description.",
    )
    og_image_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Social share image for this page. Blank = site default.",
    )
    include_in_sitemap = models.BooleanField(
        default=True,
        help_text="Include this page in sitemap.xml.",
    )
    sitemap_priority = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=0.5,
        help_text="0.1 (low) to 1.0 (highest). Home is usually 1.0.",
    )
    sitemap_changefreq = models.CharField(
        max_length=16,
        choices=ChangeFreq.choices,
        default=ChangeFreq.WEEKLY,
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["key"]
        verbose_name = "Page SEO"
        verbose_name_plural = "Page SEO"

    def __str__(self) -> str:
        return f"{self.get_key_display()} SEO"

    def clean(self):
        if self.sitemap_priority is not None and not (
            0.0 <= float(self.sitemap_priority) <= 1.0
        ):
            raise ValidationError(
                {"sitemap_priority": "Priority must be between 0.0 and 1.0."}
            )

    @property
    def title_length(self) -> int:
        return len(self.meta_title or "")

    @property
    def description_length(self) -> int:
        return len(self.meta_description or "")


class AffiliateApplication(models.Model):
    """Public affiliate program application (not an account signup)."""

    class AudienceSize(models.TextChoices):
        UNDER_1K = "under_1k", "Under 1K"
        FROM_1K = "1k_10k", "1K–10K"
        FROM_10K = "10k_50k", "10K–50K"
        FROM_50K = "50k_plus", "50K+"

    class PrimaryPlatform(models.TextChoices):
        INSTAGRAM = "instagram", "Instagram"
        YOUTUBE = "youtube", "YouTube"
        TIKTOK = "tiktok", "TikTok"
        BLOG = "blog", "Blog/Website"
        EMAIL = "email", "Email newsletter"
        COMMUNITY = "community", "Community/Discord"
        OTHER = "other", "Other"

    class ContentFocus(models.TextChoices):
        ECOMMERCE = "ecommerce", "Ecommerce/dropshipping"
        BUSINESS = "business", "Business/marketing"
        FINANCE = "finance", "Personal finance"
        LIFESTYLE = "lifestyle", "General lifestyle"
        OTHER = "other", "Other"

    class PromotionPlan(models.TextChoices):
        CONTENT = "content", "Content/reviews"
        ADS = "ads", "Paid ads"
        EMAIL = "email", "Email list"
        COMMUNITY = "community", "Community/group"
        OTHER = "other", "Other"

    class CurrentActivity(models.TextChoices):
        STUDENT = "student", "Student"
        FREELANCER = "freelancer", "Freelancer"
        INFLUENCER = "influencer", "Influencer / Creator"
        BLOGGER = "blogger", "Blogger"
        MARKETER = "marketer", "Marketer"
        AGENCY = "agency", "Agency owner"
        ENTREPRENEUR = "entrepreneur", "Entrepreneur / Founder"
        COACH = "coach", "Coach / Educator"
        EMPLOYEE = "employee", "In-house employee"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        REVIEWING = "reviewing", "Reviewing"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    name = models.CharField(max_length=120)
    email = models.EmailField()
    current_activity = models.CharField(
        max_length=32,
        choices=CurrentActivity.choices,
        default=CurrentActivity.FREELANCER,
    )
    activity_other = models.CharField(
        max_length=120,
        blank=True,
        help_text="Required when current activity is Other.",
    )
    primary_platform = models.CharField(
        max_length=32,
        choices=PrimaryPlatform.choices,
        default=PrimaryPlatform.OTHER,
    )
    promo_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Link to profile or site.",
    )
    audience_size = models.CharField(
        max_length=32,
        choices=AudienceSize.choices,
        default=AudienceSize.UNDER_1K,
    )
    content_focus = models.CharField(
        max_length=32,
        choices=ContentFocus.choices,
        default=ContentFocus.ECOMMERCE,
    )
    promotion_plan = models.CharField(
        max_length=32,
        choices=PromotionPlan.choices,
        default=PromotionPlan.CONTENT,
    )
    promotion_other = models.TextField(
        blank=True,
        help_text="Required when promotion plan is Other — describe the strategy.",
    )
    has_affiliate_experience = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Affiliate application"
        verbose_name_plural = "Affiliate applications"

    def __str__(self) -> str:
        return f"{self.name} <{self.email}> — {self.status}"
