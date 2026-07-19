"""Persist scraped rows to Django DB + Google Sheet (Node still reads Sheet)."""

from __future__ import annotations

from django.utils import timezone

from apps.catalog.models import CatalogProduct
from apps.catalog.scraper.sheets_client import (
    normalize_product_key,
    source_id_from_key,
)
from apps.catalog.services.money import normalize_compare_usd, normalize_price_usd


def product_from_sheet_row(headers: list[str], values: list[str], sheet_row: int | None = None) -> dict:
    from apps.catalog.scraper.sheets_client import row_dict_from_values

    row = row_dict_from_values(headers, values)
    product_url = (row.get("product_url") or "").strip()
    key = normalize_product_key(product_url)
    if not key:
        return {}
    sheet_id = (
        row.get("id")
        or row.get("product_id")
        or row.get("source_id")
        or row.get("brandbox_id")
        or row.get("zentra_id")  # legacy Sheet column name
        or ""
    ).strip()
    source_id = sheet_id or source_id_from_key(key)
    images = row.get("product_images") or row.get("feature_image") or ""
    feature = row.get("feature_image") or ""
    if not feature and images:
        feature = images.split(",")[0].strip()
    return {
        "source_id": source_id,
        "product_key": key,
        "ad_id": row.get("ad_id") or "",
        "page_name": (row.get("page_name") or "")[:255],
        "landing_url": row.get("landing_url") or "",
        "product_url": product_url,
        "title": (row.get("title") or "Untitled")[:500],
        "price": normalize_price_usd(
            row.get("price") or "",
            "",
            country=row.get("country") or None,
        ),
        "compare_price": normalize_compare_usd(
            row.get("compare_price") or "",
            cost=row.get("price") or "",
            country=row.get("country") or None,
        ),
        "ratings": row.get("ratings") or "",
        "review_count": row.get("review_count") or "",
        "product_images": images,
        "feature_image": feature[:1000],
        "category": (row.get("category") or "")[:128],
        "country": (row.get("country") or "")[:64],
        "description": row.get("description") or "",
        "sheet_row": sheet_row,
        "last_synced_at": timezone.now(),
    }


def upsert_catalog_product(**fields) -> tuple[CatalogProduct, bool]:
    source_id = fields.pop("source_id")
    product_key = fields.get("product_key") or ""
    fields.setdefault("last_synced_at", timezone.now())
    if "price" in fields:
        fields["price"] = normalize_price_usd(
            fields.get("price") or "",
            "",
            country=fields.get("country") or None,
        )
    if "compare_price" in fields:
        fields["compare_price"] = normalize_compare_usd(
            fields.get("compare_price") or "",
            cost=fields.get("price") or "",
            country=fields.get("country") or None,
        )

    # Prefer match by product_key (stable URL identity), then source_id.
    obj = None
    if product_key:
        obj = CatalogProduct.objects.filter(product_key=product_key).first()
    if obj is None:
        obj = CatalogProduct.objects.filter(source_id=source_id).first()

    if obj is None:
        obj = CatalogProduct(source_id=source_id, **fields)
        obj.save()
        return obj, True

    # Re-key if sheet id / hash changed
    if obj.source_id != source_id:
        # Clear any other row that already owns this source_id
        CatalogProduct.objects.filter(source_id=source_id).exclude(pk=obj.pk).delete()
        obj.source_id = source_id
    for k, v in fields.items():
        setattr(obj, k, v)
    obj.save()
    return obj, False


def sheet_values_from_product_dict(data: dict) -> list[str]:
    sid = str(data.get("source_id") or "")
    if not sid and data.get("product_key"):
        sid = source_id_from_key(str(data["product_key"]))
    return [
        sid,
        str(data.get("ad_id") or ""),
        str(data.get("page_name") or ""),
        str(data.get("landing_url") or ""),
        str(data.get("product_url") or ""),
        str(data.get("title") or ""),
        normalize_price_usd(
            data.get("price") or "",
            "",
            country=data.get("country") or None,
        ),
        normalize_compare_usd(
            data.get("compare_price") or "",
            cost=data.get("price") or "",
            country=data.get("country") or None,
        ),
        str(data.get("ratings") or ""),
        str(data.get("review_count") or ""),
        str(data.get("product_images") or ""),
        str(data.get("feature_image") or ""),
        str(data.get("category") or ""),
        str(data.get("country") or ""),
        str(data.get("description") or "")[:500],
    ]
