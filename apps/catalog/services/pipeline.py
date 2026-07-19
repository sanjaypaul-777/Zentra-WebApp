"""Scrape pipeline: Meta Ads → Shopify products → Sheet + Django DB."""

from __future__ import annotations

import time
import traceback
from collections.abc import Callable
from urllib.parse import urlparse

import httpx
from django.db import close_old_connections
from django.utils import timezone

from apps.catalog.models import ScrapeRun
from apps.catalog.scraper.ads_collector import collect_landing_pages
from apps.catalog.scraper.config import (
    COUNTRIES,
    DELAY_BETWEEN_REQUESTS,
    NICHES,
    PRODUCTS_PER_STORE,
    TARGET_ROWS,
)
from apps.catalog.scraper.sheets_client import (
    append_rows,
    ensure_sheet_ready,
    get_existing_product_keys,
    get_sheets_client,
    normalize_product_key,
    sheet_tab_default,
    source_id_from_key,
)
from apps.catalog.scraper.shopify_scraper import (
    fetch_page,
    get_top_products_from_store,
    is_shopify_store,
)
from apps.catalog.services.dual_write import (
    sheet_values_from_product_dict,
    upsert_catalog_product,
)
from apps.catalog.services.money import normalize_compare_usd, normalize_price_usd
from apps.catalog.services.validate import product_is_storable, purge_dead_vault_products

LogFn = Callable[[str], None]


def _get_store_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        domain = (parsed.netloc or "").lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return url


def _log(log: LogFn | None, msg: str) -> None:
    if log:
        log(msg)


def scrape_single(
    *,
    search_terms: str,
    country: str = "US",
    target_rows: int = TARGET_ROWS,
    products_per_store: int = PRODUCTS_PER_STORE,
    sheet_name: str | None = None,
    log: LogFn | None = None,
    existing_keys: set[str] | None = None,
) -> int:
    sheet_name = sheet_name or sheet_tab_default()
    _log(log, f"[*] Searching Meta Ads: '{search_terms}' in {country}")
    _log(log, "[*] 404 guard + FX: skip dead sources; convert prices to USD before save")
    ads = collect_landing_pages(
        search_terms=search_terms,
        country=country,
        max_ads=max(target_rows * 2, 50),
    )
    _log(log, f"   Found {len(ads)} landing pages")
    if not ads:
        return 0

    client = get_sheets_client()
    worksheet = ensure_sheet_ready(client, sheet_name)
    seen = existing_keys if existing_keys is not None else get_existing_product_keys(worksheet)
    # Also seed from Django DB
    from apps.catalog.models import CatalogProduct

    for key in CatalogProduct.objects.values_list("product_key", flat=True):
        if key:
            seen.add(key)

    rows_written = 0
    seen_stores: set[str] = set()
    country_label = COUNTRIES.get(country.upper(), country)

    for i, ad in enumerate(ads):
        if rows_written >= target_rows:
            break
        landing_url = ad["landing_url"]
        store_domain = _get_store_domain(landing_url)
        if store_domain in seen_stores:
            continue
        seen_stores.add(store_domain)
        _log(log, f"\n[{i + 1}] {landing_url[:65]}...")

        try:
            html, _ = fetch_page(landing_url)
        except Exception as e:
            _log(log, f"   [!] Fetch failed: {e}")
            time.sleep(DELAY_BETWEEN_REQUESTS)
            continue

        if not is_shopify_store(html, landing_url):
            _log(log, "   [>] Not Shopify, skip")
            time.sleep(DELAY_BETWEEN_REQUESTS)
            continue

        products = get_top_products_from_store(
            landing_url,
            max_products=products_per_store,
            country=country or country_label,
        )
        if not products:
            _log(log, "   [!] No products")
            time.sleep(DELAY_BETWEEN_REQUESTS)
            continue

        batch_sheet: list[list] = []
        with httpx.Client(
            timeout=8.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; BrandBoxProductHunter/1.0)",
                "Accept": "*/*",
            },
        ) as http:
            for prod in products:
                if rows_written >= target_rows:
                    break
                purl = prod.get("product_url") or ""
                pkey = normalize_product_key(purl)
                if not pkey or pkey in seen:
                    continue
                ok, live_img, reason = product_is_storable(
                    product_url=purl,
                    feature_image=prod.get("feature_image") or "",
                    product_images=prod.get("product_images") or "",
                    client=http,
                )
                if not ok:
                    _log(log, f"   [>] skip (dead/{reason}): {(prod.get('title') or '')[:36]}")
                    continue
                seen.add(pkey)
                price = normalize_price_usd(
                    prod.get("price") or "",
                    "",
                    currency=prod.get("currency") or None,
                    country=country or country_label,
                )
                compare = normalize_compare_usd(
                    prod.get("compare_price") or "",
                    cost=price or prod.get("price") or "",
                    currency=prod.get("currency") or None,
                    country=country or country_label,
                )
                data = {
                    "source_id": source_id_from_key(pkey),
                    "product_key": pkey,
                    "ad_id": ad.get("ad_id", ""),
                    "page_name": ad.get("page_name", ""),
                    "landing_url": landing_url,
                    "product_url": purl,
                    "title": prod.get("title", "") or "Untitled",
                    "price": price,
                    "compare_price": compare,
                    "ratings": prod.get("ratings", ""),
                    "review_count": prod.get("review_count", ""),
                    "product_images": prod.get("product_images", ""),
                    "feature_image": live_img or prod.get("feature_image", ""),
                    "category": prod.get("category", "") or search_terms,
                    "country": country_label,
                    "description": (prod.get("description", "") or "")[:500],
                }
                # Prices cleaned (Shopify cents → USD) before vault + Sheet write
                upsert_catalog_product(**data)
                batch_sheet.append(sheet_values_from_product_dict(data))
                rows_written += 1
                _log(log, f"   [+] {rows_written}/{target_rows}: {data['title'][:40]}")
                time.sleep(DELAY_BETWEEN_REQUESTS)

        if batch_sheet:
            append_rows(worksheet, batch_sheet)

    _log(log, f"\n[DONE] Wrote {rows_written} products (Sheet + Django DB).")
    return rows_written


def scrape_all_niches(
    *,
    target: int = 500,
    sheet_name: str | None = None,
    log: LogFn | None = None,
) -> int:
    sheet_name = sheet_name or sheet_tab_default()
    client = get_sheets_client()
    worksheet = ensure_sheet_ready(client, sheet_name)
    current = max(0, len(worksheet.get_all_values()) - 1)
    _log(log, f"[*] Sheet rows now: {current}. Target: {target}")
    if current >= target:
        _log(log, "[DONE] Already at target.")
        return 0
    needed = target - current
    written_total = 0
    seen = get_existing_product_keys(worksheet)
    for niche in NICHES:
        if written_total >= needed:
            break
        for code, label in COUNTRIES.items():
            if written_total >= needed:
                break
            batch = min(needed - written_total, 50)
            _log(log, f"\n=== {niche} / {label} → {batch} ===")
            n = scrape_single(
                search_terms=niche,
                country=code,
                target_rows=batch,
                sheet_name=sheet_name,
                log=log,
                existing_keys=seen,
            )
            written_total += n
    return written_total


def sync_sheet_into_db(*, sheet_name: str | None = None, log: LogFn | None = None) -> int:
    sheet_name = sheet_name or sheet_tab_default()
    from apps.catalog.models import CatalogProduct, ShopImport
    from apps.catalog.services.dual_write import product_from_sheet_row

    client = get_sheets_client()
    worksheet = ensure_sheet_ready(client, sheet_name)
    all_rows = worksheet.get_all_values()
    if len(all_rows) <= 1:
        _log(log, "[*] Sheet empty")
        return 0
    headers = all_rows[0]
    count = 0
    skipped = 0
    with httpx.Client(
        timeout=8.0,
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; BrandBoxProductHunter/1.0)",
            "Accept": "*/*",
        },
    ) as http:
        for i, values in enumerate(all_rows[1:], start=2):
            data = product_from_sheet_row(headers, values, sheet_row=i)
            if not data:
                continue
            ok, live_img, reason = product_is_storable(
                product_url=data.get("product_url") or "",
                feature_image=data.get("feature_image") or "",
                product_images=data.get("product_images") or "",
                client=http,
            )
            if not ok:
                skipped += 1
                sid = data.get("source_id") or ""
                if sid:
                    ShopImport.objects.filter(source_id=sid).delete()
                    CatalogProduct.objects.filter(source_id=sid).delete()
                if skipped <= 20 or skipped % 25 == 0:
                    _log(log, f"   [>] skip dead/{reason}: {(data.get('title') or '')[:40]}")
                continue
            if live_img:
                data["feature_image"] = live_img
            upsert_catalog_product(**data)
            count += 1
            if count % 50 == 0:
                _log(log, f"   synced {count}…")
    _log(log, f"[DONE] Synced {count} live products (skipped {skipped} dead) Sheet → Django DB")
    return count


def clean_sheet_duplicates(*, sheet_name: str | None = None, log: LogFn | None = None) -> int:
    from apps.catalog.scraper.sheets_client import SHEET_HEADERS, product_url_column_index

    sheet_name = sheet_name or sheet_tab_default()
    client = get_sheets_client()
    worksheet = ensure_sheet_ready(client, sheet_name)
    all_rows = worksheet.get_all_values()
    if len(all_rows) <= 1:
        return 0
    headers = all_rows[0]
    col_idx = product_url_column_index(headers)
    seen: set[str] = set()
    unique = []
    dupes = 0
    for row in all_rows[1:]:
        if len(row) <= col_idx:
            continue
        key = normalize_product_key(row[col_idx] or "")
        if key and key in seen:
            dupes += 1
            continue
        if key:
            seen.add(key)
        unique.append(row)
    if dupes == 0:
        _log(log, "[*] No duplicates")
        return 0
    expected = len(SHEET_HEADERS)
    fixed = []
    for row in unique:
        # If old schema without id, ids will be filled by ensure_stable_ids later
        while len(row) < expected:
            row.append("")
        fixed.append(row[:expected] if len(row) >= expected else row)
    end_col = chr(ord("A") + expected - 1)
    worksheet.batch_clear([f"A2:{end_col}{len(all_rows)}"])
    if fixed:
        worksheet.update(values=fixed, range_name="A2", value_input_option="USER_ENTERED")
    _log(log, f"[DONE] Removed {dupes} duplicates")
    return dupes


def clean_sheet_prices(*, sheet_name: str | None = None, log: LogFn | None = None) -> int:
    """
    Rewrite Price / Compare Price columns on the Google Sheet to USD dollars
    (e.g. 12000 → 120.00). Also heals Django vault from the cleaned values.
    """
    from apps.catalog.models import CatalogProduct
    from apps.catalog.scraper.sheets_client import SHEET_HEADERS

    sheet_name = sheet_name or sheet_tab_default()
    client = get_sheets_client()
    worksheet = ensure_sheet_ready(client, sheet_name)
    all_rows = worksheet.get_all_values()
    if len(all_rows) <= 1:
        _log(log, "[*] Sheet empty")
        return 0

    headers = all_rows[0]
    # Resolve price columns (case-insensitive)
    lower = {str(h).strip().lower(): i for i, h in enumerate(headers)}
    price_i = lower.get("price")
    compare_i = lower.get("compare price") or lower.get("compare_price")
    country_i = lower.get("country")
    if price_i is None and compare_i is None:
        _log(log, "[!] No Price / Compare Price columns found")
        return 0

    expected = len(SHEET_HEADERS)
    fixed_rows: list[list] = []
    changed = 0
    for values in all_rows[1:]:
        row = list(values)
        while len(row) < max(expected, (compare_i or 0) + 1, (price_i or 0) + 1):
            row.append("")
        country = row[country_i] if country_i is not None and country_i < len(row) else ""
        old_price = row[price_i] if price_i is not None else ""
        old_compare = row[compare_i] if compare_i is not None else ""
        new_price = (
            normalize_price_usd(old_price, "", country=country or None)
            if price_i is not None
            else ""
        )
        new_compare = (
            normalize_compare_usd(
                old_compare,
                cost=new_price or old_price,
                country=country or None,
            )
            if compare_i is not None
            else ""
        )
        if price_i is not None:
            if new_price != str(old_price or ""):
                changed += 1
            row[price_i] = new_price
        if compare_i is not None:
            if new_compare != str(old_compare or ""):
                changed += 1
            row[compare_i] = new_compare
        # Pad / trim to schema
        while len(row) < expected:
            row.append("")
        fixed_rows.append(row[:expected])

    end_col = chr(ord("A") + expected - 1)
    worksheet.batch_clear([f"A2:{end_col}{len(all_rows)}"])
    if fixed_rows:
        worksheet.update(
            values=fixed_rows, range_name="A2", value_input_option="USER_ENTERED"
        )
    _log(log, f"[DONE] Cleaned sheet prices — {changed} cell(s) updated across {len(fixed_rows)} rows")

    # Keep Django vault in sync with cleaned sheet prices
    from apps.catalog.services.dual_write import product_from_sheet_row

    synced = 0
    for values in fixed_rows:
        data = product_from_sheet_row(SHEET_HEADERS, values)
        if not data or not data.get("source_id"):
            continue
        CatalogProduct.objects.filter(source_id=data["source_id"]).update(
            price=data.get("price") or "",
            compare_price=data.get("compare_price") or "",
        )
        synced += 1
    _log(log, f"[*] Vault price sync touched {synced} row(s)")
    return changed


def fill_sheet_ids(*, sheet_name: str | None = None, log: LogFn | None = None) -> int:
    from apps.catalog.scraper.sheets_client import ensure_stable_ids_on_sheet

    sheet_name = sheet_name or sheet_tab_default()
    client = get_sheets_client()
    worksheet = ensure_sheet_ready(client, sheet_name)
    stats = ensure_stable_ids_on_sheet(worksheet, log=log)
    # Keep Django in sync with sheet ids
    sync_sheet_into_db(sheet_name=sheet_name, log=log)
    return int(stats.get("filled") or 0) + int(stats.get("kept") or 0)


def execute_scrape_run(run_id: int) -> None:
    """Background-safe entry: load ScrapeRun, execute, update status."""
    close_old_connections()
    try:
        run = ScrapeRun.objects.get(pk=run_id)
    except ScrapeRun.DoesNotExist:
        return

    def log(msg: str) -> None:
        close_old_connections()
        try:
            r = ScrapeRun.objects.get(pk=run_id)
            r.append_log(msg)
        except Exception:
            pass

    run.status = ScrapeRun.Status.RUNNING
    run.started_at = timezone.now()
    run.error = ""
    run.save(update_fields=["status", "started_at", "error"])

    sheet = run.sheet_tab or sheet_tab_default()
    try:
        if run.mode == ScrapeRun.Mode.SYNC_SHEET:
            n = sync_sheet_into_db(sheet_name=sheet, log=log)
        elif run.mode == ScrapeRun.Mode.CLEAN_DUPES:
            n = clean_sheet_duplicates(sheet_name=sheet, log=log)
        elif run.mode == ScrapeRun.Mode.FILL_IDS:
            n = fill_sheet_ids(sheet_name=sheet, log=log)
        elif run.mode == ScrapeRun.Mode.PURGE_DEAD:
            n = purge_dead_vault_products(log=log)
        elif run.mode == ScrapeRun.Mode.CLEAN_PRICES:
            n = clean_sheet_prices(sheet_name=sheet, log=log)
        elif run.mode == ScrapeRun.Mode.ALL_NICHES:
            n = scrape_all_niches(target=run.target_rows, sheet_name=sheet, log=log)
        else:
            n = scrape_single(
                search_terms=run.query or "fashion",
                country=run.country or "US",
                target_rows=run.target_rows or 50,
                products_per_store=run.products_per_store or 10,
                sheet_name=sheet,
                log=log,
            )
        close_old_connections()
        run = ScrapeRun.objects.get(pk=run_id)
        run.rows_written = n
        run.status = ScrapeRun.Status.SUCCESS
        run.finished_at = timezone.now()
        run.save(update_fields=["rows_written", "status", "finished_at"])
    except Exception as e:
        close_old_connections()
        run = ScrapeRun.objects.get(pk=run_id)
        run.status = ScrapeRun.Status.FAILED
        run.error = f"{e}\n{traceback.format_exc()}"
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "error", "finished_at"])
        log(f"[ERROR] {e}")
