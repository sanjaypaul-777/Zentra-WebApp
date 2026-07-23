from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class HelpCategory(models.Model):
    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=64,
        blank=True,
        default="help",
        help_text="Material Symbols icon name, e.g. rocket_launch",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Help category"
        verbose_name_plural = "Help categories"

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("help:category", kwargs={"category_slug": self.slug})

    @property
    def published_article_count(self) -> int:
        return self.articles.filter(is_published=True).count()


class HelpArticle(models.Model):
    category = models.ForeignKey(
        HelpCategory,
        on_delete=models.CASCADE,
        related_name="articles",
    )
    slug = models.SlugField(max_length=120)
    title = models.CharField(max_length=200)
    summary = models.CharField(
        max_length=320,
        blank=True,
        help_text="Short blurb for cards and search snippets.",
    )
    body = models.TextField(
        help_text="HTML allowed (headings, paragraphs, lists, embeds).",
    )
    is_published = models.BooleanField(default=True)
    is_coming_soon = models.BooleanField(
        default=False,
        help_text="Show a Coming soon note when the underlying feature is incomplete.",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)
    hero_image = models.ImageField(
        upload_to="help/heroes/",
        blank=True,
        null=True,
        help_text="Optional screenshot or illustration at top of article.",
    )
    video_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Optional YouTube/Vimeo or direct video URL.",
    )
    video_file = models.FileField(
        upload_to="help/videos/",
        blank=True,
        null=True,
        help_text="Optional uploaded video file.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "title"]
        unique_together = [("category", "slug")]
        verbose_name = "Help article"
        verbose_name_plural = "Help articles"

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:120]
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse(
            "help:article",
            kwargs={
                "category_slug": self.category.slug,
                "article_slug": self.slug,
            },
        )

    @property
    def search_blob(self) -> str:
        return f"{self.title} {self.summary} {self.body}"


class HelpArticleAttachment(models.Model):
    article = models.ForeignKey(
        HelpArticle,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    image = models.ImageField(upload_to="help/attachments/")
    caption = models.CharField(max_length=240, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Article image / screenshot"
        verbose_name_plural = "Article images / screenshots"

    def __str__(self) -> str:
        return self.caption or f"Attachment {self.pk}"


class HelpArticleFeedback(models.Model):
    article = models.ForeignKey(
        HelpArticle,
        on_delete=models.CASCADE,
        related_name="feedback",
    )
    was_helpful = models.BooleanField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="help_feedback",
    )
    session_key = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Article feedback"
        verbose_name_plural = "Article feedback"

    def __str__(self) -> str:
        label = "Yes" if self.was_helpful else "No"
        return f"{self.article_id}: {label}"
