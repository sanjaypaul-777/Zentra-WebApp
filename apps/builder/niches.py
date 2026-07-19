"""Canonical niche packs for the AI store builder (metadata only — no dummy products).

Real niche products live on Node/R2 (care1001…). Django only stores NichePack rows
and product_count synced from Node GET /api/niches.
"""

from __future__ import annotations

# Ten niches — Pod has zero products on the engine.
NICHES = (
    {
        "slug": "living",
        "codename": "Living",
        "name": "Home Decor",
        "theme_name": "BrandBox Living",
        "description": "Warm, editorial spaces built to feel premium.",
        "accent": "#4edea3",
        "sort_order": 1,
        "default_product_count": 20,
    },
    {
        "slug": "peak",
        "codename": "Peak",
        "name": "Fitness",
        "theme_name": "BrandBox Peak",
        "description": "Gear and essentials built for movers.",
        "accent": "#10b981",
        "sort_order": 2,
        "default_product_count": 20,
    },
    {
        "slug": "care",
        "codename": "Care",
        "name": "Beauty",
        "theme_name": "BrandBox Care",
        "description": "Clean beauty, skincare, and self-care.",
        "accent": "#6ffbbe",
        "sort_order": 3,
        "default_product_count": 20,
    },
    {
        "slug": "junior",
        "codename": "Junior",
        "name": "Kids & Baby",
        "theme_name": "BrandBox Junior",
        "description": "Soft essentials for little ones.",
        "accent": "#059669",
        "sort_order": 4,
        "default_product_count": 20,
    },
    {
        "slug": "paws",
        "codename": "Paws",
        "name": "Pet",
        "theme_name": "BrandBox Paws",
        "description": "Products pets (and their people) love.",
        "accent": "#34d399",
        "sort_order": 5,
        "default_product_count": 20,
    },
    {
        "slug": "lux",
        "codename": "Luxe",
        "name": "Jewelry",
        "theme_name": "BrandBox Luxe",
        "description": "Fine pieces with a modern edge.",
        "accent": "#a7f3d0",
        "sort_order": 6,
        "default_product_count": 20,
    },
    {
        "slug": "tech",
        "codename": "Tech",
        "name": "Electronics",
        "theme_name": "BrandBox Tech",
        "description": "Gadgets and everyday tech.",
        "accent": "#ff00e5",
        "sort_order": 7,
        "default_product_count": 20,
    },
    {
        "slug": "vogue",
        "codename": "Vogue",
        "name": "Fashion",
        "theme_name": "BrandBox Vogue",
        "description": "Apparel and accessories that move.",
        "accent": "#ad7bff",
        "sort_order": 8,
        "default_product_count": 20,
    },
    {
        "slug": "mart",
        "codename": "Mart",
        "name": "General",
        "theme_name": "BrandBox Mart",
        "description": "A broad mix of winning bestsellers.",
        "accent": "#c3c0ff",
        "sort_order": 9,
        "default_product_count": 100,
    },
    {
        "slug": "pod",
        "codename": "POD",
        "name": "Print on Demand",
        "theme_name": "BrandBox POD",
        "description": "Print-on-demand ready storefront.",
        "accent": "#6861f2",
        "sort_order": 10,
        "default_product_count": 0,
    },
)


def ensure_niche_packs():
    """Upsert niche metadata; sync product counts from Node when reachable."""
    from config.brandbox_client import sync_niche_product_counts

    from .models import NichePack

    keep_slugs = set()
    for item in NICHES:
        keep_slugs.add(item["slug"])
        meta = {
            "codename": item["codename"],
            "name": item["name"],
            "theme_name": item["theme_name"],
            "description": item["description"],
            "accent": item["accent"],
            "sort_order": item["sort_order"],
            "is_active": True,
        }
        # product_count is seeded once on create; after that only the Node
        # sync below updates it, so a dead tunnel can't reset live counts.
        NichePack.objects.update_or_create(
            slug=item["slug"],
            defaults=meta,
            create_defaults={
                **meta,
                "product_count": item["default_product_count"],
            },
        )

    NichePack.objects.exclude(slug__in=keep_slugs).update(is_active=False)

    try:
        sync_niche_product_counts()
    except Exception:
        pass

    return list(NichePack.objects.filter(is_active=True))
