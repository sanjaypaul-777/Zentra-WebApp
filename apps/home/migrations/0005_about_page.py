# Generated manually — add About Us legal page

from django.db import migrations, models


def seed_about_page(apps, schema_editor):
    LegalPage = apps.get_model("home", "LegalPage")
    from apps.home.legal_copy import ABOUT_BODY

    LegalPage.objects.update_or_create(
        key="about",
        defaults={
            "title": "About Us",
            "body": ABOUT_BODY.strip(),
            "is_published": True,
        },
    )


def unseed_about_page(apps, schema_editor):
    LegalPage = apps.get_model("home", "LegalPage")
    LegalPage.objects.filter(key="about").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0004_seed_legal_pages"),
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
                ],
                help_text="Which policy this is (fixed URL).",
                max_length=32,
                unique=True,
            ),
        ),
        migrations.RunPython(seed_about_page, unseed_about_page),
    ]
