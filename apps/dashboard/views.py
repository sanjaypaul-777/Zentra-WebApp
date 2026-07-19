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
    return render(request, "dashboard/overview.html", ctx)


@login_required
def builder_page(request):
    from apps.builder.wizard import wizard

    return wizard(request)


@login_required
@require_http_methods(["GET", "POST"])
def winning_products_page(request):
    """Legacy URL — dummy WinningProduct catalog removed; use Product Finder."""
    return redirect("dashboard:product_finder")


@login_required
def product_finder_page(request):
    """Product Finder — Winning Product Vault (Django SQL). Import needs a real shop."""
    from .catalog import connected_shop_for_user, search_vault
    from .models import ShopConnection

    connection = connected_shop_for_user(request.user)
    can_import = bool(connection and connection.is_connected)
    # Browse vault without Shopify; staff preview is fine for viewing only
    if not connection:
        connection = ShopConnection.for_builder(request.user)
    if not connection:
        messages.info(
            request,
            "Connect your Shopify store to import products. You can still browse after connecting.",
        )
        return redirect("dashboard:connect")

    q = (request.GET.get("q") or "").strip()
    country = (request.GET.get("country") or "").strip()
    niche = (request.GET.get("niche") or "").strip()
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
        "product_finder",
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

    from .catalog import TOAST_VARIANTS, connected_shop_for_user

    connection = connected_shop_for_user(request.user)
    if not connection or connection.is_preview:
        messages.info(request, "Connect your Shopify store to manage imports.")
        return redirect("dashboard:connect")

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
    toast_map = {t["key"]: t for t in TOAST_VARIANTS}
    unpublished = [i for i in imports if i.status != "in_store"]

    return _page(
        request,
        "dashboard/imports.html",
        "imports",
        imports=imports,
        show_empty=not imports,
        api_error="",
        shop=connection.shop,
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
def settings_page(request):
    from apps.builder.models import NichePack
    from apps.builder.niches import ensure_niche_packs
    from .models import NotificationPreferences
    from .stores import connected_shops_for_user

    ensure_niche_packs()
    plan = get_or_create_plan(request.user)
    prefs = NotificationPreferences.for_user(request.user)
    stores_count = connected_shops_for_user(request.user).count()
    niches = list(NichePack.objects.filter(is_active=True))

    billing_url = ""
    primary = ShopConnection.active_for_user(request.user)
    if primary and not primary.is_preview:
        handle = primary.shop.replace(".myshopify.com", "")
        billing_url = f"https://admin.shopify.com/store/{handle}/settings/billing"

    display_name = (
        request.user.get_full_name()
        or request.user.first_name
        or request.user.username
        or "—"
    )
    email = request.user.email or request.user.username or "—"

    return _page(
        request,
        "dashboard/settings.html",
        "settings",
        plan=plan,
        prefs=prefs,
        stores_count=stores_count,
        niches=niches,
        billing_url=billing_url,
        account_email=email,
        account_name=display_name,
        password_change_url=reverse("accounts:password_change"),
        stores_url=reverse("dashboard:stores"),
        upgrade_url=reverse("dashboard:upgrade"),
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
