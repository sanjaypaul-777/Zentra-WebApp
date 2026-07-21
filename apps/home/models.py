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
    """About / Privacy / Terms / Refund — editable in Django admin."""

    class PageKey(models.TextChoices):
        ABOUT = "about", "About Us"
        PRIVACY = "privacy", "Privacy Policy"
        TERMS = "terms", "Terms of Service"
        REFUND = "refund", "Refund Policy"

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
