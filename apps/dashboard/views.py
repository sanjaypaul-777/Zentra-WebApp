"""
Dashboard — shell pages + store connect / OAuth handoff.
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from apps.builder.models import BuildJob
from config.shopify import build_shopify_install_url, normalize_shop_domain
from config.brandbox_client import check_app_installed, sync_connection_install_flag

from .models import ShopConnection
from .overview import PRO_FEATURES, build_overview_context, get_or_create_plan


def _primary_connection(user, shop: str | None = None) -> ShopConnection | None:
    """Prefer an active (installed) connection; fall back to pending."""
    if shop:
        return ShopConnection.objects.filter(user=user, shop=shop).first()
    active = ShopConnection.active_for_user(user)
    if active:
        return active
    return ShopConnection.pending_for_user(user)


def _page(request, template: str, nav_active: str, **extra):
    plan = get_or_create_plan(request.user)
    ctx = {
        "nav_active": nav_active,
        "plan_label": plan.label,
        "is_free_plan": not plan.is_pro,
        **extra,
    }
    return render(request, template, ctx)


@login_required
@require_GET
def address_suggest(request):
    """
    Address autocomplete biased to the selected country.
    Prefers Google Places when GOOGLE_PLACES_API_KEY is set; falls back to
    Photon then Nominatim.
    """
    from .geo import (
        country_name_for_code,
        detect_country,
        google_place_autocomplete,
        nominatim_address_suggest,
        photon_address_suggest,
    )

    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    geo = detect_country(request)
    country_code = (request.GET.get("country") or geo["code"] or "").strip().upper()
    country_name = country_name_for_code(country_code) or geo["name"]

    results = google_place_autocomplete(q, country_code=country_code)
    source = "google" if results else ""
    if not results:
        results = photon_address_suggest(q, country_code=country_code)
        source = "photon" if results else ""
    if not results:
        results = nominatim_address_suggest(
            q, country_code=country_code, country_name=country_name
        )
        source = "nominatim" if results else ""

    return JsonResponse(
        {
            "results": results,
            "source": source,
            "country": {"code": country_code, "name": country_name},
        }
    )


@login_required
@require_GET
def address_details(request):
    """Resolve a Google place_id into fillable address fields."""
    from .geo import google_place_details

    place_id = (request.GET.get("place_id") or "").strip()
    if not place_id:
        return JsonResponse({"ok": False, "error": "missing place_id"}, status=400)
    details = google_place_details(place_id)
    if not details:
        return JsonResponse({"ok": False, "error": "not_found"}, status=404)
    return JsonResponse({"ok": True, "result": details})


@login_required
@require_GET
def geo_phone_meta(request):
    """Dial code + example format for the selected country."""
    from .geo import (
        country_code_for_name,
        detect_country,
        phone_meta_for_country,
    )

    geo = detect_country(request)
    code = (request.GET.get("country_code") or "").strip().upper()
    if not code:
        name = (request.GET.get("country") or "").strip()
        code = country_code_for_name(name) if name else geo.get("code") or "US"
    return JsonResponse({"ok": True, "phone": phone_meta_for_country(code)})


@login_required
@require_GET
def geo_resolve_timezone(request):
    """Map browser IANA timezone → country (soft hint)."""
    from .geo import country_from_timezone

    tz = (request.GET.get("tz") or "").strip()
    hit = country_from_timezone(tz)
    if not hit:
        return JsonResponse({"ok": False, "results": None})
    return JsonResponse({"ok": True, "country": hit})


@login_required
@require_GET
def geo_countries(request):
    """Worldwide country list for searchable Country dropdown."""
    from .geo import filter_countries

    q = (request.GET.get("q") or "").strip()
    rows = filter_countries(q, limit=300)
    return JsonResponse(
        {
            "results": [r["name"] for r in rows],
            "items": rows,
        }
    )


@login_required
@require_GET
def geo_states(request):
    """States/provinces for the selected country — searchable dropdown list."""
    from .geo import (
        country_code_for_name,
        country_name_for_code,
        detect_country,
        filter_names,
        states_for_country,
        states_for_country_code,
    )

    geo = detect_country(request)
    country_code = (request.GET.get("country_code") or "").strip().upper()
    country = (request.GET.get("country") or "").strip()
    if not country_code and country:
        country_code = country_code_for_name(country)
    if not country_code:
        country_code = geo["code"]
    if not country:
        country = country_name_for_code(country_code) or geo["name"]
    q = (request.GET.get("q") or "").strip()
    names = (
        states_for_country_code(country_code)
        if country_code
        else states_for_country(country)
    )
    return JsonResponse(
        {
            "country": {"code": country_code, "name": country},
            "results": filter_names(names, q, limit=80),
        }
    )


@login_required
@require_GET
def geo_cities(request):
    """Cities for country + state — optional typeahead (Settings)."""
    from .geo import cities_for_state, detect_country, filter_names

    geo = detect_country(request)
    country = (request.GET.get("country") or geo["name"] or "").strip()
    state = (request.GET.get("state") or "").strip()
    q = (request.GET.get("q") or "").strip()
    if not state:
        return JsonResponse(
            {"country": geo, "state": "", "results": []},
        )
    names = cities_for_state(country, state)
    return JsonResponse(
        {
            "country": {"code": geo["code"], "name": country or geo["name"]},
            "state": state,
            "results": filter_names(names, q),
        }
    )


SESSION_SETUP_FUNNEL = "store_setup_funnel"  # "create" | "connect"


def _set_setup_funnel(request, funnel: str) -> None:
    request.session[SESSION_SETUP_FUNNEL] = funnel


def _setup_funnel(request) -> str:
    """Active connect funnel: create (4 steps) or connect (3 steps)."""
    raw = (request.GET.get("from") or "").strip().lower()
    if raw == "create":
        _set_setup_funnel(request, "create")
        return "create"
    if raw == "connect":
        _set_setup_funnel(request, "connect")
        return "connect"
    return request.session.get(SESSION_SETUP_FUNNEL) or "connect"


def _funnel_progress(funnel: str, step: int) -> dict:
    """
    create: 1 Create Shopify → 2 Connect domain → 3 Install → 4 Build
    connect: 1 Connect domain → 2 Install → 3 Build
    """
    if funnel == "create":
        total = 4
        etas = {
            1: "About 5 minutes",
            2: "About 2 minutes",
            3: "About 1 minute",
            4: "About 2 minutes",
        }
    else:
        total = 3
        etas = {1: "About 2 minutes", 2: "About 1 minute", 3: "About 2 minutes"}
    step = max(1, min(int(step), total))
    return {
        "funnel": funnel,
        "flow_step": step,
        "flow_total": total,
        "flow_eta": etas.get(step, ""),
        "flow_segments": list(range(1, total + 1)),
    }


def _shop_owned_by_other(shop: str, user) -> ShopConnection | None:
    return ShopConnection.objects.filter(shop=shop).exclude(user=user).first()


def _save_pending_shop(user, shop: str) -> tuple[ShopConnection | None, str | None]:
    """
    Create/update a pending ShopConnection for this user.
    Does not mark connected (app_installed stays False until OAuth confirms).
    Returns (connection, error_message).
    """
    other = _shop_owned_by_other(shop, user)
    if other:
        return None, (
            "This Shopify store is already linked to another BrandBox account. "
            "Sign in with that account, or use a different store."
        )

    existing = ShopConnection.objects.filter(shop=shop, user=user).first()
    if existing:
        # Keep active status if already connected; otherwise ensure pending.
        return existing, None

    # Drop older pending rows for this user so prefill stays a single domain.
    ShopConnection.objects.filter(user=user, app_installed=False).exclude(
        shop=shop
    ).delete()

    try:
        with transaction.atomic():
            connection = ShopConnection.objects.create(
                user=user,
                shop=shop,
                app_installed=False,
            )
    except IntegrityError:
        return None, (
            "This Shopify store is already linked to another BrandBox account. "
            "Sign in with that account, or use a different store."
        )
    return connection, None


def _oauth_failure_redirect(shop: str | None = None):
    url = reverse("dashboard:connect_error")
    if shop:
        url = f"{url}?shop={shop}"
    return redirect(url)


@login_required
def dashboard_home(request):
    """
    Overview landing + OAuth return handler.

    After Shopify OAuth (same-tab), BrandBox Node redirects here with ?shop=...
    (and optionally installed=1). We confirm install via the Node API, mark the
    pending ShopConnection active, then show View B. Failures go to the
    connect error page — no polling, no session flag.
    """
    shop_raw = request.GET.get("shop", "").strip() or None
    shop = normalize_shop_domain(shop_raw) if shop_raw else None
    oauth_error = (request.GET.get("error") or "").strip()

    if oauth_error and shop:
        return _oauth_failure_redirect(shop)
    if oauth_error:
        return _oauth_failure_redirect()

    if shop:
        # Already connected to this shop — land on View B, ignore stale params.
        existing_active = ShopConnection.active_for_user(request.user)
        if existing_active and existing_active.shop == shop:
            return redirect("dashboard:home")

        other = _shop_owned_by_other(shop, request.user)
        if other:
            messages.error(
                request,
                "This Shopify store is already linked to another BrandBox account.",
            )
            return _oauth_failure_redirect(shop)

        connection = ShopConnection.objects.filter(
            user=request.user, shop=shop
        ).first()
        if not connection:
            connection, err = _save_pending_shop(request.user, shop)
            if err or not connection:
                messages.error(request, err or "Could not save this store.")
                return _oauth_failure_redirect(shop)

        # DEBUG-only local bypass (no live Node session).
        if (
            settings.DEBUG
            and settings.ALLOW_INSTALL_BYPASS
            and request.GET.get("bypass") == "1"
        ):
            from django.utils import timezone

            connection.app_installed = True
            connection.app_installed_at = timezone.now()
            connection.save(update_fields=["app_installed", "app_installed_at"])
            request.session.pop(SESSION_SETUP_FUNNEL, None)
            return redirect(f"{reverse('dashboard:builder')}?shop={connection.shop}")

        # OAuth return: confirm real install / valid token via BrandBox Node.
        result = check_app_installed(connection.shop)
        if sync_connection_install_flag(connection, result):
            request.session.pop(SESSION_SETUP_FUNNEL, None)
            # Step 4 (create) / Step 3 (connect) — AI Store Builder
            return redirect(f"{reverse('dashboard:builder')}?shop={connection.shop}")

        # User cancelled or install not confirmed — error page (no polling).
        return _oauth_failure_redirect(shop)

    ctx = build_overview_context(request.user)
    ctx["nav_active"] = "overview"
    just_done = bool(request.session.pop("just_completed_onboarding", False))
    # Design preview: /dashboard/?welcome=1 (survives refresh)
    preview = (request.GET.get("welcome") or "").strip().lower() in ("1", "true", "yes")
    if just_done or preview:
        from .models import MerchantProfile

        profile = MerchantProfile.for_user(request.user)
        ctx["show_onboarding_welcome"] = True
        ctx["welcome_full_name"] = profile.first_name or profile.display_name or request.user.get_username()
    else:
        ctx["show_onboarding_welcome"] = False
        ctx["welcome_full_name"] = ""
    return render(request, "dashboard/overview.html", ctx)


@login_required
def builder_page(request):
    from apps.builder.wizard import wizard

    return wizard(request)


@login_required
@require_http_methods(["GET", "POST"])
def winning_products_page(request):
    """Legacy URL — dummy WinningProduct catalog removed; use Product Hunter."""
    return redirect("dashboard:product_hunter")


@login_required
def product_finder_page(request):
    """Product Hunter — Winning Product Vault (Django SQL). Import needs a real shop."""
    from .catalog import connected_shop_for_user, search_vault
    from .models import ShopConnection

    connection = connected_shop_for_user(request.user)
    # Browse vault without Shopify; staff preview is fine for viewing only.
    if not connection:
        connection = ShopConnection.for_builder(request.user)
    can_import = bool(connection and connection.is_connected)

    q = (request.GET.get("q") or "").strip()
    country = (request.GET.get("country") or "").strip()
    niche = (request.GET.get("niche") or "").strip()
    is_ai_picks = (request.GET.get("picks") or "").strip() in ("1", "true", "yes")
    try:
        page = max(1, int(request.GET.get("page") or "1"))
    except ValueError:
        page = 1
    page_size = 16

    # Import / in-store badges from local My Imports (no Node required)
    imported_ids: set[str] = set()
    published_ids: set[str] = set()
    shop_domain = connection.shop if can_import else ""
    if can_import:
        try:
            from apps.catalog.models import ShopImport

            for row in ShopImport.objects.filter(shop=connection.shop).only(
                "source_id", "status"
            ):
                if row.status == ShopImport.Status.IN_STORE:
                    published_ids.add(row.source_id)
                elif row.status in (
                    ShopImport.Status.IMPORTED,
                    ShopImport.Status.REMOVED,
                ):
                    imported_ids.add(row.source_id)
        except Exception:
            pass

    result = search_vault(
        q=q,
        country=country,
        niche=niche,
        page=page,
        page_size=page_size,
        imported_ids=imported_ids,
        published_ids=published_ids,
    )

    products = result.get("products") or []
    countries = result.get("countries") or []
    niches = result.get("niches") or []
    total = int(result.get("total") or 0)
    total_pages = max(1, int(result.get("total_pages") or 1))
    page = int(result.get("page") or page)
    has_next = bool(result.get("has_next"))
    has_prev = bool(result.get("has_prev"))
    api_error = ""
    show_empty = not products

    return _page(
        request,
        "dashboard/product_finder.html",
        "ai_picks" if is_ai_picks else "product_hunter",
        products=products,
        countries=countries,
        niches=niches,
        q=q,
        country=country,
        niche=niche,
        show_empty=show_empty,
        api_error=api_error,
        shop=shop_domain,
        can_import=can_import,
        needs_shop_connect=not can_import,
        page=page,
        total_pages=total_pages,
        total=total,
        has_next=has_next,
        has_prev=has_prev,
        import_api_url=reverse("dashboard:api_imports_create"),
        is_ai_picks=is_ai_picks,
    )


@login_required
def imports_page(request):
    """My Imports — Django ShopImport queue. Node only for push/status sync."""
    import json

    from apps.catalog.models import ShopImport
    from apps.catalog.services.imports import (
        shop_import_to_item,
        sync_live_status_from_node,
    )

    from .access import is_dev_admin
    from .catalog import TOAST_VARIANTS, connected_shop_for_user
    from .models import ShopConnection

    connection = connected_shop_for_user(request.user)
    if not connection and is_dev_admin(request.user):
        connection = ShopConnection.for_builder(request.user)

    toast_map = {t["key"]: t for t in TOAST_VARIANTS}
    needs_shop_connect = not connection or (
        connection.is_preview and not is_dev_admin(request.user)
    )
    if needs_shop_connect:
        return _page(
            request,
            "dashboard/imports.html",
            "imports",
            imports=[],
            show_empty=True,
            api_error="",
            shop="",
            needs_shop_connect=True,
            toast_variants=TOAST_VARIANTS,
            toast_variants_json=json.dumps(toast_map),
            unpublished_count=0,
            import_api_base=reverse("dashboard:api_imports_create"),
        )

    # Best-effort live status (deleted / in_store) when Node tunnel is up
    try:
        sync_live_status_from_node(shop=connection.shop)
    except Exception:
        pass

    status_filter = (request.GET.get("status") or "imported").strip().lower()
    if status_filter not in ("imported", "in_store", "removed_from_store", "all"):
        status_filter = "imported"

    qs = ShopImport.objects.filter(shop=connection.shop)
    if status_filter == "imported":
        # Queue: drafts + removed (can re-push)
        qs = qs.filter(
            status__in=[
                ShopImport.Status.IMPORTED,
                ShopImport.Status.REMOVED,
            ]
        )
    elif status_filter != "all":
        qs = qs.filter(status=status_filter)

    imports = [shop_import_to_item(row) for row in qs]
    unpublished = [i for i in imports if i.status != "in_store"]

    return _page(
        request,
        "dashboard/imports.html",
        "imports",
        imports=imports,
        show_empty=not imports,
        api_error="",
        shop=connection.shop,
        needs_shop_connect=False,
        toast_variants=TOAST_VARIANTS,
        toast_variants_json=json.dumps(toast_map),
        unpublished_count=len(unpublished),
        import_api_base=reverse("dashboard:api_imports_create"),
    )


def _shop_for_api(request) -> tuple[ShopConnection | None, JsonResponse | None]:
    from .catalog import connected_shop_for_user

    connection = connected_shop_for_user(request.user)
    if not connection or connection.is_preview:
        return None, JsonResponse(
            {"ok": False, "error": "Connect your Shopify store first."},
            status=403,
        )
    return connection, None


@login_required
@require_http_methods(["POST"])
def api_imports_create(request):
    """POST JSON { sourceId } → Django ShopImport (no Node)."""
    import json

    from apps.catalog.services.imports import create_from_vault, shop_import_to_item

    connection, err = _shop_for_api(request)
    if err:
        return err

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        body = {}

    source_id = (body.get("sourceId") or body.get("source_id") or "").strip()
    if not source_id:
        return JsonResponse({"ok": False, "error": "sourceId required"}, status=400)

    obj, error = create_from_vault(shop=connection.shop, source_id=source_id)
    if error or not obj:
        return JsonResponse({"ok": False, "error": error or "Import failed"}, status=404)

    item = shop_import_to_item(obj)
    return JsonResponse(
        {
            "ok": True,
            "created": True,
            "import": {
                "id": item.id,
                "sourceId": obj.source_id,
                "title": item.title,
                "status": item.status,
                "cost": str(item.cost),
                "sellPrice": str(item.sell),
            },
        },
        status=201,
    )


@login_required
@require_http_methods(["PATCH", "POST", "DELETE"])
def api_import_detail(request, import_id: str):
    """
    Django-owned edit/delete. Push → Node publish + live tracker.
    """
    import json

    from apps.catalog.models import ShopImport
    from apps.catalog.services.imports import push_to_shopify, shop_import_to_item

    connection, err = _shop_for_api(request)
    if err:
        return err

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        body = {}

    action = (body.get("action") or request.GET.get("action") or "").strip().lower()
    method = request.method.upper()

    try:
        pk = int(import_id)
    except ValueError:
        return JsonResponse({"ok": False, "error": "invalid_id"}, status=400)

    imp = ShopImport.objects.filter(pk=pk, shop=connection.shop).first()
    if not imp:
        return JsonResponse({"ok": False, "error": "not_found"}, status=404)

    if method == "DELETE" or action == "delete":
        # Only this shop's import draft — never CatalogProduct / vault.
        ShopImport.objects.filter(pk=imp.pk, shop=connection.shop).delete()
        return JsonResponse({"ok": True, "deleted": True, "vault_kept": True})

    if action == "publish" or (method == "POST" and body.get("publish")):
        result = push_to_shopify(shop=connection.shop, import_id=pk)
        if not result.get("ok"):
            status = result.get("status") or 502
            return JsonResponse(
                {
                    "ok": False,
                    "error": result.get("error") or "Push failed",
                    "message": result.get("message"),
                },
                status=int(status) if str(status).isdigit() else 502,
            )
        return JsonResponse(result)

    # PATCH fields locally
    from apps.catalog.services.money import normalize_compare_usd, normalize_usd

    if "title" in body:
        imp.title = str(body["title"] or "")[:500]
    if "cost" in body:
        imp.cost = normalize_usd(body["cost"], "0.00")
    if "sellPrice" in body or "sell" in body:
        imp.sell_price = normalize_usd(body.get("sellPrice", body.get("sell")) or "", "0.00")
    if "compareAt" in body or "compareAtPrice" in body:
        imp.compare_at_price = normalize_compare_usd(
            body.get("compareAtPrice", body.get("compareAt")) or "",
            cost=imp.cost,
            sell=imp.sell_price,
        )
    if "description" in body:
        imp.description = str(body["description"] or "")
    imp.save()
    item = shop_import_to_item(imp)
    return JsonResponse(
        {
            "ok": True,
            "import": {
                "id": item.id,
                "title": item.title,
                "sellPrice": str(item.sell),
                "cost": str(item.cost),
                "compareAtPrice": str(item.compare_at) if item.compare_at else None,
                "status": item.status,
            },
        }
    )


@login_required
def stores_page(request):
    """
    My Stores — one row per connected Shopify shop (not per AI build).
    Status is derived from the latest BuildJob for that shop.
    """
    from .stores import build_store_rows

    rows = build_store_rows(request.user)
    return _page(
        request,
        "dashboard/stores.html",
        "stores",
        store_rows=rows,
        has_stores=bool(rows),
        connect_url=reverse("dashboard:connect"),
    )


@login_required
def store_detail_page(request, pk: int):
    """Detail for one connected Shopify shop."""
    from .stores import derive_store_row
    from apps.builder.models import BuildJob

    connection = get_object_or_404(
        ShopConnection, pk=pk, user=request.user, app_installed=True
    )
    latest = (
        BuildJob.objects.filter(user=request.user, shop=connection.shop)
        .select_related("niche")
        .order_by("-created_at")
        .first()
    )
    row = derive_store_row(connection, latest)
    return _page(
        request,
        "dashboard/store_detail.html",
        "stores",
        connection=connection,
        store_row=row,
    )


@login_required
@require_http_methods(["POST"])
def store_disconnect(request, pk: int):
    """
    Disconnect a connected Shopify store (destructive).
    Removes the ShopConnection for this user — requires confirmation in UI.
    """
    connection = get_object_or_404(
        ShopConnection, pk=pk, user=request.user, app_installed=True
    )
    domain = connection.shop
    connection.delete()
    messages.success(request, f"Disconnected {domain}.")
    return redirect("dashboard:stores")


@login_required
def onboarding_page(request):
    """Required multi-step store setup — gates dashboard until complete."""
    from .models import MerchantProfile
    from .onboarding_forms import (
        OnboardingStep1Form,
        OnboardingStep2Form,
        OnboardingStep3Form,
        OnboardingStep4Form,
    )

    profile = MerchantProfile.for_user(request.user)
    from .access import is_dev_admin

    is_admin = is_dev_admin(request.user)
    if profile.onboarding_completed and not is_admin:
        return redirect("dashboard:home")

    # Seed full_name from account if empty
    if not profile.full_name:
        profile.full_name = (request.user.get_full_name() or "").strip() or (
            request.user.first_name or ""
        )
        if profile.full_name:
            profile.save(update_fields=["full_name", "updated_at"])

    step = int(request.GET.get("step") or profile.onboarding_step or 1)
    step = max(1, min(4, step))
    # Merchants cannot skip ahead of saved progress; staff/superuser can preview any step
    if not is_admin:
        step = min(step, max(1, profile.onboarding_step or 1))

    forms_by_step = {
        1: OnboardingStep1Form,
        2: OnboardingStep2Form,
        3: OnboardingStep3Form,
        4: OnboardingStep4Form,
    }
    form_cls = forms_by_step[step]
    form_kwargs = {"profile": profile}
    if step == 1:
        from .geo import detect_country, resolve_initial_country

        geo = resolve_initial_country(
            profile_country=profile.address_country,
            geo=detect_country(request),
        )
        form_kwargs["user"] = request.user
        form_kwargs["geo_country"] = geo
    else:
        geo = None

    if request.method == "POST":
        posted_step = int(request.POST.get("step") or step)
        posted_step = max(1, min(4, posted_step))
        form_cls = forms_by_step[posted_step]
        form_kwargs = {"profile": profile, "data": request.POST}
        if posted_step == 1:
            from .geo import detect_country, resolve_initial_country

            geo = resolve_initial_country(
                profile_country=profile.address_country,
                geo=detect_country(request),
            )
            form_kwargs["user"] = request.user
            form_kwargs["geo_country"] = geo
        form = form_cls(**form_kwargs)
        if form.is_valid():
            if posted_step == 4:
                form.save(complete=True)
                request.session["just_completed_onboarding"] = True
                return redirect("dashboard:home")
            form.save()
            return redirect(f"{reverse('onboarding')}?step={posted_step + 1}")
        step = posted_step
    else:
        form = form_cls(**form_kwargs)
        if step == 1 and geo is None:
            from .geo import detect_country, resolve_initial_country

            geo = resolve_initial_country(
                profile_country=profile.address_country,
                geo=detect_country(request),
            )

    titles = {
        1: "First, a bit about you",
        2: "Now, tell us about your business",
        3: "What are you hoping to achieve?",
        4: "Almost done — just your resources and goals",
    }

    from django.conf import settings as dj_settings

    return render(
        request,
        "onboarding/index.html",
        {
            "step": step,
            "step_total": 4,
            "step_title": titles[step],
            "form": form,
            "profile": profile,
            "geo_country": geo,
            "google_places_api_key": getattr(dj_settings, "GOOGLE_PLACES_API_KEY", "")
            or "",
            "vertical_choices": MerchantProfile.Vertical.choices,
            "niche_choices": MerchantProfile.Niche.choices,
            "revenue_choices": MerchantProfile.Revenue.choices,
            "goal_choices": MerchantProfile.EcommerceGoal.choices,
            "experience_choices": MerchantProfile.PreviousExperience.choices,
            "success_choices": MerchantProfile.SuccessDefinition.choices,
            "time_choices": MerchantProfile.WeeklyTime.choices,
            "budget_choices": MerchantProfile.AdBudget.choices,
            "challenge_choices": MerchantProfile.CHALLENGE_CHOICES,
        },
    )


@login_required
def schedule_page(request):
    """Schedule — live greeting + next call / calendar booking."""
    from datetime import timedelta

    from django.utils import timezone

    from .models import CallSlot, MerchantProfile, ScheduledCall

    now = timezone.localtime()
    profile = MerchantProfile.for_user(request.user)
    first_name = profile.first_name

    hour = now.hour
    if hour < 12:
        day_part = "morning"
    elif hour < 17:
        day_part = "afternoon"
    else:
        day_part = "evening"

    live_clock = now.strftime("%I:%M %p").lstrip("0") + " — " + now.strftime("%A, %B ") + str(
        now.day
    )

    next_call = ScheduledCall.next_for_user(request.user)
    is_first_call = not ScheduledCall.has_past_for_user(request.user)

    open_slots_payload = []
    if next_call is None:
        _ensure_open_call_slots()
        slots = list(
            CallSlot.objects.filter(
                is_open=True,
                starts_at__gte=timezone.now(),
                starts_at__lte=timezone.now() + timedelta(days=45),
            ).order_by("starts_at")[:80]
        )
        for slot in slots:
            open_slots_payload.append(
                {
                    "id": slot.pk,
                    "iso": slot.starts_at.isoformat(),
                    "duration": slot.duration_minutes,
                    "topic": slot.topic,
                }
            )

    return _page(
        request,
        "dashboard/schedule.html",
        "schedule",
        live_date=live_clock,
        greeting=f"Good {day_part}, {first_name}",
        first_name=first_name,
        next_call=next_call,
        is_first_call=is_first_call,
        open_slots=open_slots_payload,
        has_open_slots=bool(open_slots_payload),
        book_url=reverse("dashboard:schedule_book"),
    )


@login_required
@require_GET
def coach_page(request):
    """BrandBox Coach — chat (left) + Help Center shortcuts (right)."""
    from apps.coach import services as coach_services
    from apps.coach.permissions import user_is_coach
    from apps.help.models import HelpArticle, HelpCategory

    plan = get_or_create_plan(request.user)
    can_transfer = plan.is_pro
    transfer_gate = "pro" if can_transfer else "free"
    transfer_requested = (request.GET.get("transfer") or "") in {"1", "true", "yes"}

    session = coach_services.get_or_create_open_session(request.user)
    if transfer_requested and can_transfer and session.status == session.STATUS_BOT:
        coach_services.request_human_coach(session=session)
        session.refresh_from_db()

    knowledge_groups = []
    for cat in HelpCategory.objects.filter(is_published=True).order_by("sort_order")[:8]:
        articles = list(
            HelpArticle.objects.filter(
                category=cat,
                is_published=True,
                is_coming_soon=False,
            ).order_by("sort_order")[:4]
        )
        if not articles:
            continue
        knowledge_groups.append(
            {
                "name": cat.name,
                "icon": cat.icon or "help",
                "articles": [
                    {"title": a.title, "url": a.get_absolute_url()} for a in articles
                ],
            }
        )

    messages = [
        coach_services.serialize_message(m) for m in session.messages.all()[:200]
    ]

    return _page(
        request,
        "dashboard/coach.html",
        "coach",
        can_transfer=can_transfer,
        transfer_gate=transfer_gate,
        transfer_requested=transfer_requested,
        knowledge_groups=knowledge_groups,
        coach_session=coach_services.serialize_session(session),
        coach_messages=messages,
        is_coach_user=user_is_coach(request.user),
    )


def _ensure_open_call_slots() -> None:
    """Keep a few weekday slots ahead so calendar booking stays usable pre-integration."""
    from datetime import datetime, time, timedelta

    from django.utils import timezone

    from .models import CallSlot

    now = timezone.now()
    horizon = now + timedelta(days=28)
    existing = CallSlot.objects.filter(
        is_open=True, starts_at__gte=now, starts_at__lte=horizon
    ).count()
    if existing >= 10:
        return

    tz = timezone.get_current_timezone()
    hours = (10, 14, 16)
    topics = (
        "BrandBox strategy call",
        "Store launch review",
        "Product hunt strategy",
    )
    day = timezone.localtime(now).date() + timedelta(days=1)
    end = timezone.localtime(horizon).date()
    created = 0
    topic_i = 0
    while day <= end and created < 24:
        if day.weekday() < 5:  # Mon–Fri
            for hour in hours:
                starts = timezone.make_aware(datetime.combine(day, time(hour, 0)), tz)
                if starts <= now:
                    continue
                _, was_created = CallSlot.objects.get_or_create(
                    starts_at=starts,
                    defaults={
                        "duration_minutes": 30,
                        "topic": topics[topic_i % len(topics)],
                        "is_open": True,
                    },
                )
                if was_created:
                    created += 1
                    topic_i += 1
                    if created >= 24:
                        break
        day += timedelta(days=1)


@login_required
@require_http_methods(["POST"])
def schedule_book(request):
    """Book an open CallSlot → ScheduledCall for the current user."""
    from django.utils import timezone

    from .models import CallSlot, ScheduledCall

    if ScheduledCall.next_for_user(request.user):
        messages.info(request, "You already have an upcoming call booked.")
        return redirect("dashboard:schedule")

    slot_id = request.POST.get("slot_id")
    slot = get_object_or_404(CallSlot, pk=slot_id, is_open=True)

    if slot.starts_at < timezone.now():
        messages.error(request, "That time slot is no longer available.")
        return redirect("dashboard:schedule")

    try:
        with transaction.atomic():
            slot = CallSlot.objects.select_for_update().get(pk=slot.pk, is_open=True)
            ScheduledCall.objects.create(
                user=request.user,
                starts_at=slot.starts_at,
                duration_minutes=slot.duration_minutes,
                topic=slot.topic,
                status=ScheduledCall.Status.SCHEDULED,
                slot=slot,
            )
            slot.is_open = False
            slot.save(update_fields=["is_open"])
    except CallSlot.DoesNotExist:
        messages.error(request, "That time slot was just taken. Pick another.")
        return redirect("dashboard:schedule")
    except IntegrityError:
        messages.error(request, "Could not book that slot. Please try again.")
        return redirect("dashboard:schedule")

    messages.success(request, "Your call is booked.")
    return redirect("dashboard:schedule")


@login_required
def training_page(request):
    """Training — on-demand merchant lessons."""
    return _page(request, "dashboard/training.html", "training")


@login_required
def settings_page(request):
    from .models import MerchantProfile, NotificationPreferences
    from .stores import connected_shops_for_user

    prefs = NotificationPreferences.for_user(request.user)
    profile = MerchantProfile.for_user(request.user)
    stores_count = connected_shops_for_user(request.user).count()
    email = request.user.email or request.user.username or "—"

    return _page(
        request,
        "dashboard/settings.html",
        "settings",
        prefs=prefs,
        profile=profile,
        stores_count=stores_count,
        account_email=email,
        account_name=profile.display_name,
        account_username=request.user.username or "—",
        password_change_url=reverse("accounts:password_change"),
        profile_edit_url=reverse("dashboard:settings_profile"),
        stores_url=reverse("dashboard:stores"),
    )


@login_required
@require_http_methods(["GET", "POST"])
def settings_profile_page(request):
    """Edit customer profile — Account section grows here over time."""
    from django.conf import settings as dj_settings

    from apps.accounts.forms import ProfileForm

    from .geo import detect_country, resolve_initial_country
    from .models import MerchantProfile

    profile = MerchantProfile.for_user(request.user)
    geo = resolve_initial_country(
        profile_country=profile.address_country,
        geo=detect_country(request),
    )
    form = ProfileForm(
        request.POST or None,
        user=request.user,
        profile=profile,
        geo_country=geo,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile was updated.")
        return redirect("dashboard:settings")

    return _page(
        request,
        "dashboard/settings_profile.html",
        "settings",
        form=form,
        profile=profile,
        geo_country=geo,
        google_places_api_key=getattr(dj_settings, "GOOGLE_PLACES_API_KEY", "") or "",
    )


@login_required
@require_http_methods(["POST"])
def settings_notification_toggle(request):
    """Save a single notification toggle immediately (JSON)."""
    import json

    from .models import NotificationPreferences

    prefs = NotificationPreferences.for_user(request.user)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = request.POST

    field = (payload.get("field") or "").strip()
    if field not in NotificationPreferences.NOTIFICATION_FIELDS:
        return JsonResponse({"ok": False, "error": "Unknown preference."}, status=400)

    raw = payload.get("value")
    if isinstance(raw, bool):
        value = raw
    else:
        value = str(raw).lower() in ("1", "true", "on", "yes")

    setattr(prefs, field, value)
    prefs.save(update_fields=[field, "updated_at"])
    return JsonResponse({"ok": True, "field": field, "value": value})


@login_required
@require_http_methods(["POST"])
def settings_default_niche(request):
    """Save preferred niche for AI Store Builder pre-select."""
    import json

    from apps.builder.models import NichePack
    from .models import NotificationPreferences

    prefs = NotificationPreferences.for_user(request.user)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = request.POST

    slug = (payload.get("niche") or "").strip().lower()
    if slug and not NichePack.objects.filter(slug=slug, is_active=True).exists():
        return JsonResponse({"ok": False, "error": "Unknown niche."}, status=400)

    prefs.default_niche_slug = slug
    prefs.save(update_fields=["default_niche_slug", "updated_at"])
    return JsonResponse({"ok": True, "niche": slug})


@login_required
@require_http_methods(["POST"])
def settings_delete_account(request):
    """
    Permanently delete the BrandBox user account after email confirmation.
    Does not uninstall or modify live Shopify stores — only removes BrandBox data.
    """
    from django.contrib.auth import logout

    typed = (request.POST.get("confirm_email") or "").strip().lower()
    expected = (request.user.email or request.user.username or "").strip().lower()
    if not expected or typed != expected:
        messages.error(
            request,
            "Type your account email exactly to confirm deletion.",
        )
        return redirect("dashboard:settings")

    user = request.user
    logout(request)
    user.delete()
    messages.success(request, "Your BrandBox account has been deleted.")
    return redirect("home:index")


@login_required
def upgrade_page(request):
    plan = get_or_create_plan(request.user)
    return _page(
        request,
        "dashboard/upgrade.html",
        "upgrade",
        plan=plan,
        is_free_plan=not plan.is_pro,
        pro_features=PRO_FEATURES,
    )


@login_required
@require_http_methods(["GET", "POST"])
def connect_page(request):
    """
    Connect existing store — Section A (domain) → Section B (install guide).
    Pending shop is saved on Continue; Install uses the existing OAuth route.

    Progress:
      from=create → Step 2/4 (domain) then 3/4 (install)
      default     → Step 1/3 (domain) then 2/3 (install)
    """
    funnel = _setup_funnel(request)
    pending = ShopConnection.pending_for_user(request.user)
    active = ShopConnection.active_for_user(request.user)
    if active:
        return redirect("dashboard:home")

    shop_prefill = ""
    if pending:
        shop_prefill = pending.shop
    elif request.GET.get("shop"):
        shop_prefill = normalize_shop_domain(request.GET.get("shop", "")) or ""

    field_error = ""
    show_install = False

    if request.method == "POST":
        raw = request.POST.get("shop", "")
        shop = normalize_shop_domain(raw)
        if not shop:
            field_error = "Enter a valid store domain like yourstorename.myshopify.com"
            shop_prefill = (raw or "").strip()
        else:
            connection, err = _save_pending_shop(request.user, shop)
            if err:
                field_error = err
                shop_prefill = shop
            else:
                return redirect(
                    f"{reverse('dashboard:connect')}?step=install&from={funnel}"
                )

    pending = ShopConnection.pending_for_user(request.user)
    if pending:
        shop_prefill = pending.shop
        show_install = request.GET.get("step") == "install"

    install_url = None
    if show_install and pending:
        try:
            install_url = build_shopify_install_url(pending.shop)
        except ValueError:
            install_url = None

    # create funnel: domain=2, install=3; connect funnel: domain=1, install=2
    if funnel == "create":
        step = 3 if show_install else 2
    else:
        step = 2 if show_install else 1
    progress = _funnel_progress(funnel, step)

    return _page(
        request,
        "dashboard/connect.html",
        "overview",
        shop_prefill=shop_prefill,
        field_error=field_error,
        show_install=show_install,
        pending_shop=pending,
        install_url=install_url,
        **progress,
    )


@login_required
def connect_error_page(request):
    """OAuth failure / cancel — simple retry into connect with prefilled shop."""
    shop_raw = request.GET.get("shop", "")
    shop = normalize_shop_domain(shop_raw) if shop_raw else None
    if not shop:
        pending = ShopConnection.pending_for_user(request.user)
        shop = pending.shop if pending else ""
    return _page(
        request,
        "dashboard/connect_error.html",
        "overview",
        shop_prefill=shop or "",
    )


@login_required
@require_http_methods(["GET", "POST"])
def create_store_page(request):
    """
    Create Shopify (new tab) + paste store URL on the same card.
    POST: normalize admin URL → save pending → install OAuth (or builder if already in).
    """
    if ShopConnection.active_for_user(request.user):
        return redirect("dashboard:home")

    _set_setup_funnel(request, "create")
    field_error = ""
    shop_prefill = ""

    if request.method == "POST":
        raw = request.POST.get("shop", "")
        shop = normalize_shop_domain(raw)
        if not shop:
            field_error = (
                "Paste a valid admin URL like "
                "https://admin.shopify.com/store/your-store "
                "or yourstore.myshopify.com"
            )
            shop_prefill = (raw or "").strip()
        else:
            other = _shop_owned_by_other(shop, request.user)
            if other:
                field_error = (
                    "This Shopify store is already linked to another BrandBox account."
                )
                shop_prefill = shop
            else:
                connection, err = _save_pending_shop(request.user, shop)
                if err or not connection:
                    field_error = err or "Could not save this store."
                    shop_prefill = shop
                else:
                    # Already installed → jump straight to builder
                    result = check_app_installed(shop)
                    if sync_connection_install_flag(connection, result):
                        request.session.pop(SESSION_SETUP_FUNNEL, None)
                        return redirect(
                            f"{reverse('dashboard:builder')}?shop={shop}"
                        )
                    # Not installed yet → same-tab OAuth, then builder on return
                    try:
                        return redirect(build_shopify_install_url(shop))
                    except ValueError:
                        messages.error(
                            request,
                            "Set SHOPIFY_APP_URL in .env.local to your BrandBox tunnel.",
                        )
                        return redirect(
                            f"{reverse('dashboard:connect')}?step=install&from=create"
                        )

    progress = _funnel_progress("create", 1)
    return _page(
        request,
        "dashboard/create_store.html",
        "overview",
        signup_url=settings.SHOPIFY_PARTNER_SIGNUP_URL,
        brandbox_email=getattr(request.user, "email", "") or "",
        field_error=field_error,
        shop_prefill=shop_prefill,
        **progress,
    )


@login_required
@require_http_methods(["POST"])
def install_app(request):
    """
    Same-tab OAuth redirect to BrandBox Node /auth?shop=...
    Reused by Connect Section B — do not open in a new tab.
    """
    raw = request.POST.get("shop", "")
    shop = normalize_shop_domain(raw)
    if not shop:
        pending = ShopConnection.pending_for_user(request.user)
        shop = pending.shop if pending else None
    if not shop:
        messages.error(request, "Enter your store domain first.")
        return redirect("dashboard:connect")

    other = _shop_owned_by_other(shop, request.user)
    if other:
        messages.error(
            request,
            "This Shopify store is already linked to another BrandBox account.",
        )
        return redirect("dashboard:connect")

    connection, err = _save_pending_shop(request.user, shop)
    if err or not connection:
        messages.error(request, err or "Could not save this store.")
        return redirect("dashboard:connect")

    try:
        url = build_shopify_install_url(shop)
    except ValueError:
        messages.error(
            request,
            "Set SHOPIFY_APP_URL in .env.local to your BrandBox tunnel, then try Install again.",
        )
        return redirect(f"{reverse('dashboard:connect')}?step=install")

    return redirect(url)


@login_required
@require_GET
def install_status(request):
    """JSON: verify app install via BrandBox Node API, update ShopConnection."""
    shop = normalize_shop_domain(request.GET.get("shop", ""))
    if not shop:
        return JsonResponse(
            {"ok": False, "installed": False, "error": "shop required"},
            status=400,
        )

    other = _shop_owned_by_other(shop, request.user)
    if other:
        return JsonResponse(
            {
                "ok": False,
                "installed": False,
                "error": "This store is linked to another BrandBox account.",
            },
            status=409,
        )

    connection = ShopConnection.objects.filter(user=request.user, shop=shop).first()
    if not connection:
        return JsonResponse(
            {"ok": False, "installed": False, "error": "No pending store for this domain."},
            status=404,
        )

    result = check_app_installed(shop)
    installed = sync_connection_install_flag(connection, result)

    if (
        not installed
        and settings.DEBUG
        and settings.ALLOW_INSTALL_BYPASS
        and request.GET.get("bypass") == "1"
    ):
        connection.app_installed = True
        from django.utils import timezone

        connection.app_installed_at = timezone.now()
        connection.save(update_fields=["app_installed", "app_installed_at"])
        installed = True
        result["bypassed"] = True

    payload = {
        "ok": True,
        "shop": shop,
        "installed": installed,
        "connected": bool(result.get("connected", installed)),
        "checkable": result.get("checkable", False),
        "productsCount": result.get("productsCount"),
        "productsCountAvailable": bool(result.get("productsCountAvailable")),
        "statusKey": result.get("statusKey"),
        "statusCopy": result.get("statusCopy"),
        "error": result.get("error"),
        "checkedAt": result.get("checkedAt"),
        "next": reverse("dashboard:home") if installed else None,
        "install_url": None,
    }
    try:
        payload["install_url"] = build_shopify_install_url(shop)
    except ValueError:
        pass

    return JsonResponse(payload)
