"""Capture My Imports empty-state screenshot (dev only)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

import re

import requests
from django.contrib.auth import get_user_model

from apps.catalog.models import ShopImport
from apps.dashboard.models import ShopConnection

BASE = "http://127.0.0.1:8000"

User = get_user_model()
USERNAME = "__preview_imports__"
PASSWORD = "preview-imports-local"
SHOP = "preview-imports.myshopify.com"
OUT = ROOT / "tmp" / "imports-empty-preview.png"


def ensure_preview_user() -> None:
    user, created = User.objects.get_or_create(
        username=USERNAME,
        defaults={"email": "preview-imports@local.test"},
    )
    if created:
        user.set_password(PASSWORD)
        user.save()

    ShopConnection.objects.update_or_create(
        shop=SHOP,
        defaults={"user": user, "app_installed": True},
    )
    ShopImport.objects.filter(shop=SHOP).delete()


def login_session() -> requests.Session:
    session = requests.Session()
    login_page = session.get(f"{BASE}/login/")
    login_page.raise_for_status()
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_page.text)
    assert match, "csrf token not found"
    resp = session.post(
        f"{BASE}/login/",
        data={
            "csrfmiddlewaretoken": match.group(1),
            "username": USERNAME,
            "password": PASSWORD,
        },
        headers={"Referer": f"{BASE}/login/"},
    )
    resp.raise_for_status()
    return session


def main() -> None:
    ensure_preview_user()
    session = login_session()

    OUT.parent.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    cookies = []
    for cookie in session.cookies:
        cookies.append(
            {
                "name": cookie.name,
                "value": cookie.value,
                "domain": "127.0.0.1",
                "path": cookie.path or "/",
            }
        )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        context.add_cookies(cookies)
        page = context.new_page()
        page.goto(f"{BASE}/dashboard/imports/", wait_until="networkidle")
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT), full_page=False)
        browser.close()

    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
