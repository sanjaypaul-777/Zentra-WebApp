# Refresh Privacy, Terms, and Disclaimer copy (cookies, sessions, promos, affiliates)

from django.db import migrations


def refresh_legal_copy(apps, schema_editor):
    LegalPage = apps.get_model("home", "LegalPage")
    from apps.home.legal_copy import DISCLAIMER_BODY, PRIVACY_BODY, TERMS_BODY

    pages = (
        ("privacy", "Privacy Policy", PRIVACY_BODY),
        ("terms", "Terms of Service", TERMS_BODY),
        ("disclaimer", "Disclaimer", DISCLAIMER_BODY),
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


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0008_affiliate_application_fields"),
    ]

    operations = [
        migrations.RunPython(refresh_legal_copy, noop_reverse),
    ]
