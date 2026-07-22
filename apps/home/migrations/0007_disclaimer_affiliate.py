# Disclaimer legal page + affiliate applications + SEO keys

from django.db import migrations, models


def seed_disclaimer_and_seo(apps, schema_editor):
    LegalPage = apps.get_model("home", "LegalPage")
    SeoPage = apps.get_model("home", "SeoPage")
    from apps.home.legal_copy import DISCLAIMER_BODY

    LegalPage.objects.update_or_create(
        key="disclaimer",
        defaults={
            "title": "Disclaimer",
            "body": DISCLAIMER_BODY.strip(),
            "is_published": True,
        },
    )

    seo_defaults = [
        {
            "key": "disclaimer",
            "meta_title": "Disclaimer · BrandBox",
            "meta_description": (
                "BrandBox disclaimer: no earnings guarantees, AI assistive tools, "
                "and your responsibilities when building Shopify stores."
            ),
            "meta_keywords": "BrandBox disclaimer",
            "include_in_sitemap": True,
            "sitemap_changefreq": "yearly",
            "sitemap_priority": 0.3,
        },
        {
            "key": "affiliate",
            "meta_title": "Affiliate Program · BrandBox",
            "meta_description": (
                "Earn with BrandBox. Promote AI Shopify store tools to creators "
                "and founders — apply to join the affiliate program."
            ),
            "meta_keywords": "BrandBox affiliate, Shopify affiliate",
            "include_in_sitemap": True,
            "sitemap_changefreq": "monthly",
            "sitemap_priority": 0.6,
        },
        {
            "key": "affiliate_apply",
            "meta_title": "Apply · BrandBox Affiliate",
            "meta_description": (
                "Apply to the BrandBox affiliate program. Share your audience "
                "and how you’ll promote AI-powered Shopify store tools."
            ),
            "meta_keywords": "BrandBox affiliate apply",
            "include_in_sitemap": True,
            "sitemap_changefreq": "monthly",
            "sitemap_priority": 0.5,
        },
    ]
    for row in seo_defaults:
        key = row.pop("key")
        SeoPage.objects.update_or_create(key=key, defaults=row)


def unseed_disclaimer_and_seo(apps, schema_editor):
    LegalPage = apps.get_model("home", "LegalPage")
    SeoPage = apps.get_model("home", "SeoPage")
    LegalPage.objects.filter(key="disclaimer").delete()
    SeoPage.objects.filter(
        key__in=("disclaimer", "affiliate", "affiliate_apply")
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0006_seo_settings_and_pages"),
    ]

    operations = [
        migrations.AlterField(
            model_name="legalpage",
            name="key",
            field=models.CharField(
                choices=[
                    ("about", "About Us"),
                    ("privacy", "Privacy Policy"),
                    ("terms", "Terms of Service"),
                    ("refund", "Refund Policy"),
                    ("disclaimer", "Disclaimer"),
                ],
                help_text="Which policy this is (fixed URL).",
                max_length=32,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="seopage",
            name="key",
            field=models.CharField(
                choices=[
                    ("home", "Home"),
                    ("contact", "Contact"),
                    ("about", "About Us"),
                    ("privacy", "Privacy Policy"),
                    ("terms", "Terms of Service"),
                    ("refund", "Refund Policy"),
                    ("disclaimer", "Disclaimer"),
                    ("affiliate", "Affiliate"),
                    ("affiliate_apply", "Affiliate Apply"),
                ],
                help_text="Which public page these tags apply to.",
                max_length=32,
                unique=True,
            ),
        ),
        migrations.CreateModel(
            name="AffiliateApplication",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254)),
                (
                    "promo_url",
                    models.URLField(
                        blank=True,
                        help_text="Website, YouTube, or primary profile URL.",
                        max_length=500,
                    ),
                ),
                (
                    "audience_size",
                    models.CharField(
                        choices=[
                            ("under_1k", "Under 1,000"),
                            ("1k_10k", "1,000 – 10,000"),
                            ("10k_50k", "10,000 – 50,000"),
                            ("50k_plus", "50,000+"),
                        ],
                        default="under_1k",
                        max_length=32,
                    ),
                ),
                (
                    "channels",
                    models.CharField(
                        help_text="Where you promote (e.g. YouTube, TikTok, newsletter).",
                        max_length=255,
                    ),
                ),
                (
                    "experience",
                    models.TextField(
                        help_text="Affiliate / creator experience in your own words."
                    ),
                ),
                (
                    "pitch",
                    models.TextField(help_text="How you plan to promote BrandBox."),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("reviewing", "Reviewing"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=32,
                    ),
                ),
                ("admin_notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Affiliate application",
                "verbose_name_plural": "Affiliate applications",
                "ordering": ["-created_at"],
            },
        ),
        migrations.RunPython(seed_disclaimer_and_seo, unseed_disclaimer_and_seo),
    ]
