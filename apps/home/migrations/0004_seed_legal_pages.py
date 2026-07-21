# Generated manually — seed Privacy / Terms / Refund copy

from django.db import migrations


def seed_legal_pages(apps, schema_editor):
    LegalPage = apps.get_model("home", "LegalPage")
    from apps.home.legal_copy import PRIVACY_BODY, REFUND_BODY, TERMS_BODY

    pages = (
        ("privacy", "Privacy Policy", PRIVACY_BODY),
        ("terms", "Terms of Service", TERMS_BODY),
        ("refund", "Refund Policy", REFUND_BODY),
    )
    for key, title, body in pages:
        LegalPage.objects.update_or_create(
            key=key,
            defaults={
                "title": title,
                "body": body.strip(),
                "is_published": True,
            },
        )


def unseed_legal_pages(apps, schema_editor):
    LegalPage = apps.get_model("home", "LegalPage")
    LegalPage.objects.filter(key__in=("privacy", "terms", "refund")).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0003_legal_pages"),
    ]

    operations = [
        migrations.RunPython(seed_legal_pages, unseed_legal_pages),
    ]
