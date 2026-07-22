# Affiliate application fields for partner form copy

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0007_disclaimer_affiliate"),
    ]

    operations = [
        migrations.AddField(
            model_name="affiliateapplication",
            name="primary_platform",
            field=models.CharField(
                choices=[
                    ("instagram", "Instagram"),
                    ("youtube", "YouTube"),
                    ("tiktok", "TikTok"),
                    ("blog", "Blog/Website"),
                    ("email", "Email newsletter"),
                    ("community", "Community/Discord"),
                    ("other", "Other"),
                ],
                default="other",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="affiliateapplication",
            name="content_focus",
            field=models.CharField(
                choices=[
                    ("ecommerce", "Ecommerce/dropshipping"),
                    ("business", "Business/marketing"),
                    ("finance", "Personal finance"),
                    ("lifestyle", "General lifestyle"),
                    ("other", "Other"),
                ],
                default="ecommerce",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="affiliateapplication",
            name="promotion_plan",
            field=models.CharField(
                choices=[
                    ("content", "Content/reviews"),
                    ("ads", "Paid ads"),
                    ("email", "Email list"),
                    ("community", "Community/group"),
                    ("other", "Other"),
                ],
                default="content",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="affiliateapplication",
            name="has_affiliate_experience",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="affiliateapplication",
            name="notes",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="affiliateapplication",
            name="audience_size",
            field=models.CharField(
                choices=[
                    ("under_1k", "Under 1K"),
                    ("1k_10k", "1K–10K"),
                    ("10k_50k", "10K–50K"),
                    ("50k_plus", "50K+"),
                ],
                default="under_1k",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="affiliateapplication",
            name="promo_url",
            field=models.URLField(
                blank=True,
                help_text="Link to profile or site.",
                max_length=500,
            ),
        ),
        migrations.RemoveField(
            model_name="affiliateapplication",
            name="channels",
        ),
        migrations.RemoveField(
            model_name="affiliateapplication",
            name="experience",
        ),
        migrations.RemoveField(
            model_name="affiliateapplication",
            name="pitch",
        ),
    ]
