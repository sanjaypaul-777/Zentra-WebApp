# Generated manually — existing merchants skip the new onboarding gate.

from django.db import migrations


def mark_existing_complete(apps, schema_editor):
    MerchantProfile = apps.get_model("dashboard", "MerchantProfile")
    User = apps.get_model("auth", "User")

    MerchantProfile.objects.all().update(onboarding_completed=True, onboarding_step=4)

    for profile in MerchantProfile.objects.select_related("user").all():
        user = profile.user
        if not profile.full_name:
            full = f"{user.first_name} {user.last_name}".strip() or user.first_name or ""
            if full:
                profile.full_name = full
                profile.save(update_fields=["full_name"])

    # Any user without a profile yet gets one marked complete (already using the app).
    for user in User.objects.all():
        MerchantProfile.objects.get_or_create(
            user=user,
            defaults={
                "onboarding_completed": True,
                "onboarding_step": 4,
                "full_name": f"{user.first_name} {user.last_name}".strip(),
                "biggest_challenges": [],
            },
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0009_onboarding_profile"),
    ]

    operations = [
        migrations.RunPython(mark_existing_complete, noop_reverse),
    ]
