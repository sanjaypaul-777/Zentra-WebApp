from django.core.management.base import BaseCommand

from apps.help.models import HelpArticle, HelpCategory
from apps.help.seed_data import CATEGORIES


class Command(BaseCommand):
    help = "Seed Help Center categories and articles (upsert by slug)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush-missing",
            action="store_true",
            help="Unpublish categories/articles not present in seed data.",
        )

    def handle(self, *args, **options):
        cat_slugs = set()
        article_keys = set()
        created_c = updated_c = created_a = updated_a = 0

        for cat_data in CATEGORIES:
            articles = cat_data.get("articles") or []
            defaults = {
                "name": cat_data["name"],
                "description": cat_data.get("description", ""),
                "icon": cat_data.get("icon", "help"),
                "sort_order": cat_data.get("sort_order", 0),
                "is_published": True,
            }
            cat, was_created = HelpCategory.objects.update_or_create(
                slug=cat_data["slug"],
                defaults=defaults,
            )
            cat_slugs.add(cat.slug)
            if was_created:
                created_c += 1
            else:
                updated_c += 1

            for i, art in enumerate(articles, start=1):
                art_defaults = {
                    "title": art["title"],
                    "summary": art.get("summary", ""),
                    "body": art.get("body", "").strip(),
                    "is_published": True,
                    "is_coming_soon": bool(art.get("is_coming_soon")),
                    "sort_order": art.get("sort_order", i),
                }
                obj, was_created = HelpArticle.objects.update_or_create(
                    category=cat,
                    slug=art["slug"],
                    defaults=art_defaults,
                )
                article_keys.add((cat.slug, obj.slug))
                if was_created:
                    created_a += 1
                else:
                    updated_a += 1

        if options["flush_missing"]:
            HelpCategory.objects.exclude(slug__in=cat_slugs).update(is_published=False)
            for article in HelpArticle.objects.select_related("category"):
                if (article.category.slug, article.slug) not in article_keys:
                    article.is_published = False
                    article.save(update_fields=["is_published"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Categories +{created_c}/~{updated_c}; articles +{created_a}/~{updated_a}"
            )
        )
