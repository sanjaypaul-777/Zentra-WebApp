"""Google Sheets client — schema Node Product Finder reads (with stable id)."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import gspread
from django.conf import settings
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Node datasheetStorage accepts: id | product_id | source_id | brandbox_id | sku
SHEET_HEADERS = [
    "id",
    "Ad ID",
    "Page Name",
    "Landing URL",
    "Product URL",
    "Title",
    "Price",
    "Compare Price",
    "Ratings",
    "Review Count",
    "Product Images",
    "Feature Image",
    "Category",
    "Country",
    "Description",
]

# 1-based column index for Product URL when headers == SHEET_HEADERS
COL_PRODUCT_URL = 5  # E


def spreadsheet_id() -> str:
    return getattr(settings, "CATALOG_SPREADSHEET_ID", "") or ""


def sheet_tab_default() -> str:
    return getattr(settings, "CATALOG_SHEET_TAB", "Meta Ads Products") or "Meta Ads Products"


def service_account_path() -> Path:
    raw = getattr(settings, "CATALOG_SERVICE_ACCOUNT_FILE", "") or ""
    if raw:
        return Path(raw)
    return Path(settings.BASE_DIR) / "secrets" / "google-sheets-sa.json"


def get_sheets_client():
    creds_path = service_account_path()
    if not creds_path.exists():
        raise FileNotFoundError(
            f"Credentials file not found: {creds_path}. "
            "Set CATALOG_SERVICE_ACCOUNT_FILE or place secrets/google-sheets-sa.json"
        )
    creds = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
    return gspread.authorize(creds)


def ensure_sheet_ready(client, sheet_name: str | None = None):
    sid = spreadsheet_id()
    if not sid:
        raise RuntimeError("CATALOG_SPREADSHEET_ID is not configured")
    sheet_name = sheet_name or sheet_tab_default()
    spreadsheet = client.open_by_key(sid)
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)

    existing = worksheet.row_values(1)
    if existing != SHEET_HEADERS:
        if not existing or not any(existing):
            worksheet.update("A1", [SHEET_HEADERS], value_input_option="USER_ENTERED")
    return worksheet


def normalize_product_key(url: str) -> str:
    if not url or not url.strip():
        return ""
    try:
        parsed = urlparse((url or "").strip().split("?")[0].rstrip("/"))
        domain = (parsed.netloc or "").lower()
        if domain.startswith("www."):
            domain = domain[4:]
        path = (parsed.path or "").strip("/")
        if "/products/" in path.lower():
            handle = path.split("/")[-1] if "/" in path else path
        else:
            handle = path.split("/")[-1] if path else ""
        return f"{domain}::{handle}" if domain and handle else url
    except Exception:
        return (url or "").strip()


def source_id_from_key(product_key: str) -> str:
    """Stable catalog id for Sheet + Django + Node sourceId."""
    import hashlib

    digest = hashlib.sha1(product_key.encode("utf-8")).hexdigest()[:16]
    return f"zp_{digest}"


def product_url_column_index(headers: list[str]) -> int:
    """0-based index of Product URL column."""
    for i, h in enumerate(headers):
        if h.strip().lower().replace(" ", "_") in ("product_url", "source", "url"):
            return i
    # Legacy sheet without id column
    if headers and headers[0].strip().lower() != "id":
        return 3  # D
    return COL_PRODUCT_URL - 1


def get_existing_product_keys(worksheet) -> set[str]:
    try:
        headers = worksheet.row_values(1)
        if not headers:
            return set()
        col = product_url_column_index(headers) + 1  # 1-based for col_values
        col_vals = worksheet.col_values(col)
        if len(col_vals) <= 1:
            return set()
        keys = set()
        for url in col_vals[1:]:
            key = normalize_product_key(url)
            if key:
                keys.add(key)
        return keys
    except Exception:
        return set()


def append_rows(worksheet, rows: list[list]):
    if not rows:
        return
    next_row = len(worksheet.get_all_values()) + 1
    worksheet.update(
        values=rows,
        range_name=f"A{next_row}",
        value_input_option="USER_ENTERED",
    )


def row_dict_from_values(headers: list[str], values: list[str]) -> dict:
    mapped = {}
    for i, h in enumerate(headers):
        key = h.strip().lower().replace(" ", "_")
        mapped[key] = values[i] if i < len(values) else ""
    return mapped


def ensure_stable_ids_on_sheet(worksheet, log=None) -> dict:
    """
    Ensure column A is `id` with zp_* (or keep existing non-empty ids).
    Rewrites the tab safely. Returns stats.
    """
    def _log(msg: str) -> None:
        if log:
            log(msg)

    all_rows = worksheet.get_all_values()
    if not all_rows:
        worksheet.update("A1", [SHEET_HEADERS], value_input_option="USER_ENTERED")
        return {"rows": 0, "filled": 0, "kept": 0}

    headers = [h.strip() for h in all_rows[0]]
    data = all_rows[1:]
    has_id = bool(headers) and headers[0].lower() == "id"
    url_idx = product_url_column_index(headers)

    filled = 0
    kept = 0
    out_rows: list[list[str]] = []

    for row in data:
        while len(row) < len(headers):
            row.append("")
        if has_id:
            body = row[1:]
            existing_id = (row[0] or "").strip()
            # body[0] is Ad ID when has_id; product url at url_idx-1 in full row terms
            purl = row[url_idx] if url_idx < len(row) else ""
        else:
            body = list(row)
            existing_id = ""
            purl = row[url_idx] if url_idx < len(row) else ""

        key = normalize_product_key(purl)
        expected = source_id_from_key(key) if key else ""
        # Always prefer URL-derived zp_* ; keep non-zp ids (e.g. care1001 niche packs).
        if existing_id and not existing_id.startswith("zp_"):
            sid = existing_id
            kept += 1
        elif expected:
            sid = expected
            if existing_id == expected:
                kept += 1
            else:
                filled += 1
        elif existing_id:
            sid = existing_id
            kept += 1
        else:
            sid = ""
            filled += 1

        # Normalize body to SHEET_HEADERS[1:] length
        expected_body = len(SHEET_HEADERS) - 1
        if len(body) > expected_body:
            body = body[:expected_body]
        while len(body) < expected_body:
            body.append("")
        out_rows.append([sid] + body)

    # Clear and rewrite (header + data)
    end_col = chr(ord("A") + len(SHEET_HEADERS) - 1)  # O for 15 cols
    clear_end = max(len(all_rows) + 5, len(out_rows) + 5)
    worksheet.batch_clear([f"A1:{end_col}{clear_end}"])
    payload = [SHEET_HEADERS] + out_rows
    worksheet.update(values=payload, range_name="A1", value_input_option="USER_ENTERED")
    _log(f"[DONE] Sheet ids: filled={filled} kept={kept} rows={len(out_rows)}")
    return {"rows": len(out_rows), "filled": filled, "kept": kept}
