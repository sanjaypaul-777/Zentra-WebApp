# Update affiliate register SEO title/description for /affiliate/register/

from django.db import migrations


def update_affiliate_register_seo(apps, schema_editor):
    SeoPage = apps.get_model("home", "SeoPage")
    SeoPage.objects.filter(key="affiliate_apply").update(
        meta_title="Register · BrandBox Affiliate",
        meta_description=(
            "Register for the BrandBox affiliate program. Share your audience "
            "and how you’ll promote AI-powered Shopify store tools."
        ),
        meta_keywords="BrandBox affiliate register, Shopify affiliate",
    )


def revert_affiliate_register_seo(apps, schema_editor):
    SeoPage = apps.get_model("home", "SeoPage")
    SeoPage.objects.filter(key="affiliate_apply").update(
        meta_title="Apply · BrandBox Affiliate",
        meta_description=(
            "Apply to the BrandBox affiliate program. Share your audience "
            "and how you’ll promote AI-powered Shopify store tools."
        ),
        meta_keywords="BrandBox affiliate, Shopify affiliate",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0009_refresh_privacy_terms_disclaimer"),
    ]

    operations = [
        migrations.RunPython(
            update_affiliate_register_seo,
            revert_affiliate_register_seo,
        ),
    ]
