"""My Imports — Django-owned drafts; Node only for push + live status."""

from __future__ import annotations

from decimal import Decimal

from apps.catalog.models import CatalogProduct, ShopImport
from apps.catalog.services.money import money_or_default, normalize_compare_usd, normalize_price_usd, normalize_usd


def _money_str(value, default: str = "10") -> str:
    return normalize_price_usd(value, default) or default


def create_from_vault(*, shop: str, source_id: str) -> tuple[ShopImport | None, str]:
    product = CatalogProduct.objects.filter(source_id=source_id, archived=False).first()
    if not product:
        return None, "Product not found in Winning Product Vault"

    cost = _money_str(product.price, "10")
    try:
        sell = str((Decimal(cost) * 3).quantize(Decimal("0.01")))
    except Exception:
        sell = cost

    image = (product.feature_image or "").strip()
    if not image and product.product_images:
        image = product.product_images.split(",")[0].strip()

    compare = normalize_compare_usd(
        product.compare_price, cost=cost, sell=sell
    ) if product.compare_price else ""

    obj, created = ShopImport.objects.update_or_create(
        shop=shop,
        source_id=source_id,
        defaults={
            "title": product.title or "Untitled",
            "cost": cost,
            "sell_price": sell,
            "compare_at_price": compare,
            "description": (product.description or "")[:2000],
            "category": product.category or "",
            "country": product.country or "",
            "image_url": image[:1000],
            "product_url": product.product_url or "",
        },
    )
    # Already live → leave in_store; removed/new → imported queue
    if obj.shopify_product_id and obj.status == ShopImport.Status.IN_STORE:
        pass
    else:
        obj.status = ShopImport.Status.IMPORTED
        if not obj.shopify_product_id:
            obj.shopify_product_id = ""
        obj.save(update_fields=["status", "shopify_product_id", "updated_at"])

    return obj, ""


def shop_import_to_item(obj: ShopImport):
    from apps.dashboard.catalog import ImportItem, _hue_from_id

    cost = money_or_default(obj.cost, "10")
    sell = money_or_default(obj.sell_price, str(cost * 3))
    compare_raw = normalize_compare_usd(
        obj.compare_at_price, cost=cost, sell=sell
    ) if obj.compare_at_price else ""
    compare = money_or_default(compare_raw) if compare_raw else None
    # Heal stored cents-style compare quietly
    if compare_raw and compare_raw != (obj.compare_at_price or ""):
        obj.compare_at_price = compare_raw
        obj.save(update_fields=["compare_at_price", "updated_at"])
    return ImportItem(
        id=str(obj.pk),
        title=obj.title,
        niche=obj.category or "—",
        country=obj.country or "—",
        cost=cost,
        sell=sell,
        compare_at=compare,
        status=obj.status,
        image_url=obj.image_url or "",
        image_hue=_hue_from_id(str(obj.pk)),
        shopify_product_id=obj.shopify_product_id or "",
    )


def sync_live_status_from_node(*, shop: str) -> int:
    """
    Best-effort: pull Node PendingProduct status into ShopImport.
    Returns number of rows updated. Silent if tunnel/Node down.
    """
    try:
        from config.brandbox_client import list_imports
    except Exception:
        return 0

    result = list_imports(shop=shop, status="")
    if not result.get("ok"):
        return 0

    updated = 0
    by_source = {
        str(row.get("sourceId") or ""): row
        for row in (result.get("imports") or [])
        if row.get("sourceId")
    }
    for imp in ShopImport.objects.filter(shop=shop):
        row = by_source.get(imp.source_id)
        if not row:
            continue
        st = str(row.get("status") or row.get("productStatus") or "").lower()
        sid = str(row.get("shopifyProductId") or "")
        node_id = str(row.get("id") or "")
        new_status = imp.status
        if st in ("in_store", "published") or sid:
            new_status = ShopImport.Status.IN_STORE
        elif st in ("removed_from_store", "removed"):
            new_status = ShopImport.Status.REMOVED
            sid = ""
        elif st in ("imported", "available"):
            new_status = ShopImport.Status.IMPORTED
            sid = ""
        fields = []
        if new_status != imp.status:
            imp.status = new_status
            fields.append("status")
        if sid != (imp.shopify_product_id or ""):
            imp.shopify_product_id = sid
            fields.append("shopify_product_id")
        if node_id and node_id != (imp.node_import_id or ""):
            imp.node_import_id = node_id
            fields.append("node_import_id")
        if fields:
            fields.append("updated_at")
            imp.save(update_fields=fields)
            updated += 1
    return updated


def push_to_shopify(*, shop: str, import_id: int) -> dict:
    """
    Ensure Node PendingProduct exists (from sheet/sourceId), then publish.
    Updates local ShopImport on success.
    """
    from config.brandbox_client import create_import, publish_import

    imp = ShopImport.objects.filter(pk=import_id, shop=shop).first()
    if not imp:
        return {"ok": False, "error": "not_found", "message": "Import not found"}

    # Upsert on Node so live tracker / delete webhook can follow this sourceId
    created = create_import(
        shop=shop,
        source_id=imp.source_id,
        title=imp.title,
        cost=imp.cost,
        sellPrice=imp.sell_price or None,
        compareAtPrice=imp.compare_at_price or None,
        description=imp.description or None,
        category=imp.category or None,
        source=imp.product_url or None,
        imageUrl=imp.image_url or None,
    )
    if not created.get("ok"):
        return {
            "ok": False,
            "error": created.get("error") or "node_import_failed",
            "message": created.get("message")
            or "Could not reach Node to push. Is the Shopify app tunnel running?",
            "status": created.get("status"),
        }

    node_row = created.get("import") or {}
    node_id = str(node_row.get("id") or imp.node_import_id or "")
    if node_id:
        imp.node_import_id = node_id
        imp.save(update_fields=["node_import_id", "updated_at"])

    if not node_id:
        return {"ok": False, "error": "missing_node_id", "message": "Node did not return import id"}

    published = publish_import(shop=shop, import_id=node_id)
    # Product may already exist in Shopify even if Node returned a soft error
    shopify_id_early = str(
        published.get("shopifyProductId")
        or (published.get("import") or {}).get("shopifyProductId")
        or ""
    )
    if not published.get("ok") and not shopify_id_early:
        return {
            "ok": False,
            "error": published.get("error") or "publish_failed",
            "message": published.get("message") or "Push to Shopify failed",
            "status": published.get("status"),
        }

    row = published.get("import") or node_row
    shopify_id = str(
        published.get("shopifyProductId")
        or row.get("shopifyProductId")
        or shopify_id_early
        or ""
    )
    if not shopify_id:
        # Node said ok but returned no product id — nothing verifiable is live.
        return {
            "ok": False,
            "error": "missing_shopify_id",
            "message": "Push did not return a Shopify product id. Try again.",
        }
    imp.status = ShopImport.Status.IN_STORE
    imp.shopify_product_id = shopify_id
    if node_id:
        imp.node_import_id = node_id
    imp.save(
        update_fields=[
            "status",
            "shopify_product_id",
            "node_import_id",
            "updated_at",
        ]
    )
    return {
        "ok": True,
        "import": {
            "id": str(imp.pk),
            "sourceId": imp.source_id,
            "status": imp.status,
            "shopifyProductId": imp.shopify_product_id,
            "title": imp.title,
            "sellPrice": imp.sell_price,
        },
    }
