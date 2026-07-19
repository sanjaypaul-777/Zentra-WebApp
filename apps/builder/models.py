"""
Builder models — niche packs and build jobs.
Winning products for builds come from Node/R2, not Django.
"""

from django.conf import settings
from django.db import models


class NichePack(models.Model):
    slug = models.SlugField(unique=True)
    # Codename shown large on cards (e.g. "Paws")
    codename = models.CharField(max_length=64, blank=True)
    # Category subtitle (e.g. "Pet")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    theme_name = models.CharField(max_length=120, blank=True)
    # Placeholder accent for card thumbnail (hex)
    accent = models.CharField(max_length=16, default="#4edea3")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    # Engine product count (synced from Node GET /api/niches)
    product_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "codename", "name"]

    def __str__(self) -> str:
        return self.codename or self.name

    @property
    def display_codename(self) -> str:
        return self.codename or self.name

    @property
    def display_theme(self) -> str:
        if self.theme_name:
            return self.theme_name
        return f"BrandBox {self.display_codename}"

    @property
    def catalog_product_count(self) -> int:
        return int(self.product_count or 0)

    @property
    def has_products(self) -> bool:
        return self.catalog_product_count > 0


class BuildJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    # 3-step builder checklist (theme name filled in progress_labels)
    PROGRESS_LABELS = (
        "Installing theme",
        "Uploading AI generated winning products",
        "Setting up menu and policy",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="build_jobs",
    )
    shop = models.CharField(max_length=255)
    store_name = models.CharField(max_length=255, blank=True)
    niche = models.ForeignKey(
        NichePack,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="builds",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    # Node Build.id from POST /api/build/start (or retry)
    brandbox_build_id = models.CharField(max_length=64, blank=True, db_index=True)
    progress_step = models.PositiveSmallIntegerField(default=0)
    # Live percent / label from Node GET /api/build/status
    engine_progress = models.PositiveSmallIntegerField(default=0)
    live_label = models.CharField(max_length=255, blank=True)
    product_count = models.PositiveIntegerField(default=0)
    skip_products = models.BooleanField(default=False)
    selected_product_ids = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.shop} ({self.status})"

    def progress_labels(self) -> tuple[str, ...]:
        theme = "theme"
        if self.niche_id:
            theme = self.niche.display_theme or self.niche.display_codename or "theme"
        labels = [
            f"Installing {theme}",
            "Uploading AI generated winning products",
            "Setting up menu and policy",
        ]
        if self.product_count == 0 or self.skip_products:
            labels[1] = "Setting up your product catalog"
        return tuple(labels)

    @property
    def progress_label(self) -> str:
        # Prefer live Node stepLabel (e.g. "Uploading winning products 3/20…")
        if self.live_label:
            return self.live_label
        labels = self.progress_labels()
        idx = min(self.progress_step, len(labels) - 1)
        return labels[idx]

    @property
    def display_name(self) -> str:
        if self.store_name:
            return self.store_name
        return self.shop.replace(".myshopify.com", "")

    @property
    def progress_percent(self) -> int:
        """Prefer live Node progress; else map step index → ~33 / 66 / 100."""
        if self.status == self.Status.DONE:
            return 100
        if self.brandbox_build_id or self.engine_progress:
            return min(100, int(self.engine_progress or 0))
        thresholds = (33, 66, 100)
        idx = min(self.progress_step, len(thresholds) - 1)
        return thresholds[idx]
