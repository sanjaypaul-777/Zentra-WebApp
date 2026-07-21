"""
AI Store Builder wizard — 2 steps at /dashboard/builder/.

1) Choose niche
2) Build confirmation (default = full AI niche set from Node/R2)
"""

from __future__ import annotations

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.dashboard.models import ShopConnection
from apps.dashboard.overview import get_or_create_plan

from .models import NichePack
from .niches import ensure_niche_packs

SESSION_NICHE = "builder_niche_slug"
SESSION_SKIP = "builder_skip_products"
# default | none  (manual dummy picks removed)
SESSION_MODE = "builder_product_mode"
SESSION_SHOP = "builder_shop_domain"


def _session_clear_products(request) -> None:
    request.session.pop(SESSION_SKIP, None)
    request.session.pop(SESSION_MODE, None)
    request.session.pop("builder_product_ids", None)


def _get_selected_niche(request) -> NichePack | None:
    slug = request.session.get(SESSION_NICHE)
    if not slug:
        return None
    return NichePack.objects.filter(slug=slug, is_active=True).first()


def _require_connected(request):
    from config.shopify import normalize_shop_domain

    shop_raw = (
        request.GET.get("shop")
        or request.POST.get("shop")
        or request.session.get(SESSION_SHOP)
        or ""
    )
    shop = normalize_shop_domain(shop_raw) if shop_raw else ""
    if shop:
        connection = ShopConnection.objects.filter(
            user=request.user, shop=shop, app_installed=True
        ).first()
        if connection:
            request.session[SESSION_SHOP] = connection.shop
            return connection
        messages.error(request, "That store isn’t connected to your account.")
        return None

    connection = ShopConnection.for_builder(request.user)
    if not connection:
        return None
    return connection


def _seed_default_products(request, niche: NichePack) -> None:
    """Default = Node uploads full niche CSV; none = empty niche (e.g. POD)."""
    if niche.has_products:
        request.session[SESSION_MODE] = "default"
        request.session[SESSION_SKIP] = False
    else:
        request.session[SESSION_MODE] = "none"
        request.session[SESSION_SKIP] = True


def _products_summary(request, niche: NichePack) -> dict:
    mode = request.session.get(SESSION_MODE) or "none"
    count = niche.catalog_product_count if mode == "default" else 0

    if count > 0:
        return {
            "skip": False,
            "count": count,
            "mode": mode,
            "ids": [],
        }

    return {
        "skip": True,
        "count": 0,
        "mode": "none",
        "ids": [],
    }


def _builder_redirect(step: int = 1, shop: str | None = None):
    url = f"{reverse('dashboard:builder')}?step={step}"
    if shop:
        url += f"&shop={shop}"
    return redirect(url)


@require_http_methods(["GET", "POST"])
def wizard(request):
    ensure_niche_packs()
    connection = _require_connected(request)
    if connection is None:
        return redirect("dashboard:connect")

    shop = connection.shop
    plan = get_or_create_plan(request.user)
    raw_step = request.GET.get("step") or request.POST.get("step") or "1"
    try:
        step = int(raw_step)
    except ValueError:
        step = 1
    if step >= 3:
        step = 2
    if step not in (1, 2):
        step = 1

    if request.method == "POST":
        action = (request.POST.get("action") or "").strip()

        if action == "select_niche":
            slug = (request.POST.get("niche") or "").strip().lower()
            niche = NichePack.objects.filter(slug=slug, is_active=True).first()
            if not niche:
                messages.error(request, "Pick a niche to continue.")
                return _builder_redirect(1, shop)

            prev = request.session.get(SESSION_NICHE)
            request.session[SESSION_NICHE] = niche.slug
            if prev != niche.slug:
                _session_clear_products(request)
                _seed_default_products(request, niche)
            elif SESSION_MODE not in request.session:
                _seed_default_products(request, niche)

            return _builder_redirect(2, shop)

        if action == "confirm_build":
            niche = _get_selected_niche(request)
            if not niche:
                return _builder_redirect(1, shop)
            summary = _products_summary(request, niche)
            from .views import create_build_job

            job = create_build_job(
                user=request.user,
                connection=connection,
                niche=niche,
                product_ids=[],
                skip_products=summary["skip"],
            )
            request.session.pop(SESSION_NICHE, None)
            _session_clear_products(request)
            return redirect("builder:building", job_id=job.pk)

    niche = _get_selected_niche(request)
    if not niche and step == 1 and SESSION_NICHE not in request.session:
        from apps.dashboard.models import NotificationPreferences

        prefs = NotificationPreferences.for_user(request.user)
        if prefs.default_niche_slug:
            niche = NichePack.objects.filter(
                slug=prefs.default_niche_slug, is_active=True
            ).first()
            if niche:
                request.session[SESSION_NICHE] = niche.slug
                _seed_default_products(request, niche)

    if step == 2 and not niche:
        return _builder_redirect(1, shop)

    if step == 2 and niche and SESSION_MODE not in request.session:
        _seed_default_products(request, niche)
    elif step == 2 and niche and request.session.get(SESSION_MODE) == "default":
        _seed_default_products(request, niche)

    niches = list(NichePack.objects.filter(is_active=True))
    summary = _products_summary(request, niche) if niche and step == 2 else None

    ctx = {
        "nav_active": "builder",
        "plan_label": plan.label,
        "is_free_plan": not plan.is_pro,
        "wizard_step": step,
        "wizard_total": 2,
        "niches": niches,
        "selected_niche": niche,
        "summary": summary,
        "connection": connection,
    }
    return render(request, "dashboard/builder.html", ctx)
