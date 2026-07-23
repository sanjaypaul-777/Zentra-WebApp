"""
Overview page context — real queries with sample fallbacks for empty states.

Overview cases:
  not_connected (Case B entry): No shop with a confirmed install / valid token
      (pending ShopConnection rows do NOT count). Overview shows only the two
      path cards — connect existing vs create new.
  connected (Case A / View B): app_installed=True on ShopConnection.
      Hero modes: "create" (no AI store built yet) or "ready" (≥1 built).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone

from apps.builder.models import BuildJob

from .models import ActivityEvent, ShopConnection, UserPlan

# Shared Pro feature bullets (Upgrade page + Overview — 2×2 on Overview)
PRO_FEATURES = (
    "Unlimited AI store builds",
    "Full winning-products catalog access",
    "Priority theme & product sync",
    "Push imports to Shopify in one click",
)

SPOTLIGHT_COLORS = (
    "#4edea3",
    "#ff00e5",
    "#10b981",
    "#ad7bff",
    "#6861f2",
    "#6ffbbe",
)

# Spotlight niches: (label, category allowlist, title word-boundary fallbacks, title exclude substrings).
# Category match is preferred. Never use broad terms like "home" (pulls wall art).
TOP_SPOTLIGHT_NICHES = (
    (
        "Kids & Baby",
        ("baby onesie", "onesie"),
        ("onesie",),
        (),
    ),
    (
        "Electronics",
        ("phone case", "watch winder", "electronics", "electronic", "gadget"),
        ("electronics", "gadget", "earbuds", "headphones"),
        (),
    ),
    (
        "Home & Kitchen",
        ("mug", "cookware", "brass hardware", "kitchenware"),
        ("cookware", "kitchenware", "kitchen drawer"),
        (
            "power strip",
            "usb",
            "charger",
            "outlet",
            "electronic",
            "gadget",
            "hdmi",
            "led ",
            "wifi",
            "bluetooth",
        ),
    ),
    (
        "Beauty",
        ("wax melt", "wax warmer", "scent", "skincare", "beauty", "cosmetic"),
        ("skincare", "beauty", "serum", "moisturizer"),
        (),
    ),
    (
        "Fitness",
        ("fitness",),
        ("fitness", "workout", "dumbbell"),
        (),
    ),
    (
        "Pet",
        ("pet supplies", "shop dogs", "pet bed"),
        ("pet", "dog", "cat", "puppy", "kitten"),
        (),
    ),
)


def _spotlight_product_image(product) -> str:
    image = (product.feature_image or "").strip()
    if not image and product.product_images:
        image = product.product_images.split(",")[0].strip()
    return image


def _wb(field: str, keyword: str):
    """Word-boundary match so 'pet' does not hit 'Petty' / 'petty knife'."""
    from django.db.models import Q

    pattern = rf"(^|[^A-Za-z0-9]){keyword}([^A-Za-z0-9]|$)"
    return Q(**{f"{field}__iregex": pattern})


def spotlight_niches() -> list[dict]:
    """Top niche product picks — category-first, image required, no false niche hits."""
    from django.db.models import Case, IntegerField, Q, Value, When

    from apps.catalog.models import CatalogProduct

    items: list[dict] = []
    used_ids: set[str] = set()
    has_image = Q(feature_image__gt="") | Q(product_images__gt="")

    for i, (label, cat_terms, title_terms, title_exclude) in enumerate(TOP_SPOTLIGHT_NICHES):
        cat_query = Q()
        for term in cat_terms:
            cat_query |= Q(category__icontains=term.strip())

        title_query = Q()
        for term in title_terms:
            title_query |= _wb("title", term)
            if " " not in term:
                cat_query |= _wb("category", term)

        exclude_q = Q()
        for term in title_exclude:
            exclude_q |= Q(title__icontains=term)

        qs = (
            CatalogProduct.objects.filter(archived=False)
            .filter(has_image)
            .filter(cat_query | title_query)
            .exclude(source_id__in=used_ids)
            .exclude(category__iexact="Petty")
        )
        if title_exclude:
            qs = qs.exclude(exclude_q)
        qs = qs.annotate(
            _cat_hit=Case(
                When(cat_query, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
        ).order_by("_cat_hit", "-updated_at")
        product = qs.first()

        color = SPOTLIGHT_COLORS[i % len(SPOTLIGHT_COLORS)]
        items.append(
            {
                "name": label,
                "image": _spotlight_product_image(product) if product else "",
                "color": color,
            }
        )
        if product:
            used_ids.add(str(product.source_id))

    return items


@dataclass
class ReadinessItem:
    label: str
    done: bool


def get_or_create_plan(user) -> UserPlan:
    profile, _ = UserPlan.objects.get_or_create(user=user)
    return profile


def status_pill(job: BuildJob | None) -> str:
    if not job:
        return "Failed"
    if job.status == BuildJob.Status.DONE:
        return "Live"
    if job.status in (BuildJob.Status.RUNNING, BuildJob.Status.PENDING):
        return "Building"
    return "Failed"


def readiness_summary(readiness: list[ReadinessItem], pct: int) -> str:
    total = len(readiness)
    done = sum(1 for i in readiness if i.done)
    if done == total and total:
        return (
            "✓ All 3 setup steps complete — theme installed, winning products "
            "uploaded, menu & policy set."
        )
    if done == 0:
        return (
            "○ 0 of 3 setup steps complete — install theme, upload winning "
            "products, set menu & policy."
        )
    return f"✓ {done} of {total} setup steps complete — keep going to finish launch."


def build_overview_context(user) -> dict:
    # Customers: only a confirmed install counts.
    # Staff/superuser: use preview shop only when it is marked installed
    # (uncheck App installed in admin to preview the connect UI).
    connection = ShopConnection.active_for_user(user)
    if not connection and (
        getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)
    ):
        preview = ShopConnection.staff_preview_for_user(user)
        if preview is None:
            connection = ShopConnection.ensure_staff_preview(user)
        elif preview.app_installed:
            connection = preview
    is_connected = connection is not None and bool(connection.app_installed)
    plan = get_or_create_plan(user)

    if not is_connected:
        return {
            "is_connected": False,
            "overview_case": "not_connected",
            "hero_mode": "connect",
            "connection": None,
            "plan": plan,
            "plan_label": plan.label,
            "is_free_plan": not plan.is_pro,
        }

    builds = BuildJob.objects.filter(user=user).select_related("niche")
    shop_builds = builds.filter(shop=connection.shop)
    done_builds = shop_builds.filter(status=BuildJob.Status.DONE)
    stores_built = done_builds.count()

    # Live product count from Node — never invent 0 when unknown / not connected.
    products_used = None  # None = unknown (do not display as 0)
    products_count_available = False
    products_status_key = "connected_count_unavailable"
    products_status_copy = "Product count unavailable"
    products_shop_connected = bool(connection.app_installed and not connection.is_preview)
    products_trend = "Unavailable"

    if connection.is_preview:
        products_status_key = "connected_count_unavailable"
        products_status_copy = (
            "Preview builds — connect a real Shopify store for live product count"
        )
        products_trend = "Preview mode"
    else:
        from config.brandbox_client import check_app_installed, sync_connection_install_flag

        cache_age = None
        if connection.store_product_count_at:
            cache_age = (
                timezone.now() - connection.store_product_count_at
            ).total_seconds()

        status = None
        use_fresh_cache = (
            cache_age is not None
            and cache_age < 90
            and connection.store_product_count is not None
        )

        if not use_fresh_cache:
            try:
                status = check_app_installed(connection.shop, timeout=3)
                sync_connection_install_flag(connection, status)
                connection.refresh_from_db()
            except Exception:  # noqa: BLE001
                status = None

        if status:
            products_shop_connected = bool(
                status.get("connected") or status.get("installed")
            )
            products_status_key = status.get("statusKey") or products_status_key
            products_status_copy = status.get("statusCopy") or products_status_copy
            if status.get("productsCountAvailable") and status.get(
                "productsCount"
            ) is not None:
                products_used = int(status["productsCount"])
                products_count_available = True
            elif not products_shop_connected:
                products_used = None
                products_count_available = False
                products_status_key = "not_connected"
                products_status_copy = (
                    status.get("statusCopy")
                    or "Store not connected — connect to see live products"
                )
        elif connection.store_product_count is not None and products_shop_connected:
            products_used = int(connection.store_product_count)
            products_count_available = True
            if products_used == 0:
                products_status_key = "connected_empty"
                products_status_copy = "0 products — ready for winning products"
            else:
                products_status_key = "connected_with_products"
                products_status_copy = (
                    "1 product live"
                    if products_used == 1
                    else f"{products_used} products live"
                )
        elif not products_shop_connected:
            products_status_key = "not_connected"
            products_status_copy = (
                "Store not connected — connect to see live products"
            )

    if connection.is_preview:
        pass  # products_trend already set
    elif products_count_available and products_used == 0:
        products_trend = "Ready to stock"
    elif products_count_available:
        products_trend = "Live from Shopify"
    elif products_status_key == "not_connected":
        products_trend = "Connect store"
    else:
        products_trend = "Unavailable"

    latest = shop_builds.first()
    has_built_store = stores_built > 0

    # View B (Case A): connected via app
    hero_mode = "create" if not has_built_store else "ready"

    activities = list(ActivityEvent.objects.filter(user=user)[:3])
    if not activities:
        now = timezone.now()
        activities = [
            ActivityEvent(
                user=user,
                event_type=ActivityEvent.EventType.SYSTEM,
                message="Welcome to BrandBox — your store is connected.",
                created_at=now - timedelta(minutes=12),
            ),
            ActivityEvent(
                user=user,
                event_type=ActivityEvent.EventType.PRODUCT,
                message="Browse Winning Product Hunt for niche ideas.",
                created_at=now - timedelta(hours=2),
            ),
            ActivityEvent(
                user=user,
                event_type=ActivityEvent.EventType.SYSTEM,
                message="Your Shopify store is ready for the next niche build.",
                created_at=now - timedelta(days=1),
            ),
        ]

    if latest and latest.status == BuildJob.Status.DONE:
        readiness = [
            ReadinessItem("Install theme", True),
            ReadinessItem("Upload winning products", True),
            ReadinessItem("Set menu & policy", True),
        ]
    elif latest:
        readiness = [
            ReadinessItem("Install theme", latest.progress_step >= 0),
            ReadinessItem("Upload winning products", latest.progress_step >= 1),
            ReadinessItem("Set menu & policy", latest.progress_step >= 2),
        ]
    else:
        readiness = [
            ReadinessItem("Install theme", False),
            ReadinessItem("Upload winning products", False),
            ReadinessItem("Set menu & policy", False),
        ]

    done_n = sum(1 for i in readiness if i.done)
    readiness_pct = int(round((done_n / len(readiness)) * 100)) if readiness else 0

    theme_name = "—"
    if latest and latest.niche_id:
        theme_name = latest.niche.display_theme
    elif latest:
        theme_name = "BrandBox"

    snapshot = None
    if latest:
        snapshot = {
            "id": latest.pk,
            "name": latest.display_name,
            "theme": theme_name,
            "status": status_pill(latest),
            "shop": latest.shop,
        }

    return {
        "is_connected": True,
        "overview_case": "connected",
        "hero_mode": hero_mode,
        "connection": connection,
        "plan": plan,
        "plan_label": plan.label,
        "is_free_plan": not plan.is_pro,
        "stats": {
            "stores_built": stores_built,
            "products_used": products_used,
            "products_count_available": products_count_available,
            "products_status_key": products_status_key,
            "products_status_copy": products_status_copy,
            "products_shop_connected": products_shop_connected,
            "plan_label": plan.label,
            "stores_trend": "+1 this week" if stores_built else "New",
            "products_trend": products_trend,
        },
        "products_status_copy": products_status_copy,
        "products_status_key": products_status_key,
        "storefront_url": connection.storefront_url,
        "snapshot": snapshot,
        "activities": activities,
        "readiness_pct": readiness_pct,
        "readiness_summary": readiness_summary(readiness, readiness_pct),
        "readiness": readiness,
        "spotlight": spotlight_niches(),
        "pro_features": PRO_FEATURES,
    }
