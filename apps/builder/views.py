"""
Builder — start AI store build, progress UI, success.
Progress is driven by BrandBox Node /api/build/* (see services.py).
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from apps.dashboard.models import ShopConnection
from config.shopify import normalize_shop_domain

from .models import BuildJob, NichePack
from .niches import ensure_niche_packs
from .services import (
    advance_build_job,
    build_failure_copy,
    build_status_payload,
    retry_failed_step,
)


def _job_for_request(request, job_id: int) -> BuildJob:
    """Merchants: own jobs only. Staff/superuser: any job (dev QA)."""
    from apps.dashboard.access import is_dev_admin

    if is_dev_admin(request.user):
        return get_object_or_404(BuildJob, pk=job_id)
    return get_object_or_404(BuildJob, pk=job_id, user=request.user)


def _require_ready_shop(user, shop_raw: str | None) -> tuple[ShopConnection | None, str | None]:
    from config.brandbox_client import check_app_installed, sync_connection_install_flag

    # Staff preview bypasses live Shopify install checks
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        connection = ShopConnection.for_builder(user)
        if connection:
            return connection, None

    shop = normalize_shop_domain(shop_raw or "")
    if shop:
        connection = ShopConnection.objects.filter(user=user, shop=shop).first()
    else:
        connection = ShopConnection.active_for_user(user)
    if not connection or not connection.app_installed:
        if connection and not connection.app_installed:
            return None, "Install the BrandBox app on your store before building."
        return None, "Connect your Shopify store first."

    result = check_app_installed(connection.shop)
    installed = sync_connection_install_flag(connection, result)

    if not installed and not (settings.DEBUG and settings.ALLOW_INSTALL_BYPASS):
        return None, "Install the BrandBox app on your store before building."
    return connection, None


def create_build_job(*, user, connection, niche, product_ids=None, skip_products=False):
    """Create a BuildJob and kick off the Node build (or preview simulator)."""
    from .services import kickoff_remote_build

    product_ids = list(product_ids or [])
    store_name = connection.shop.replace(".myshopify.com", "").replace("-", " ").title()
    if niche and niche.codename:
        store_name = f"{niche.codename} Store"

    count = 0
    if not skip_products and niche:
        count = niche.catalog_product_count or niche.product_count or 0

    job = BuildJob.objects.create(
        user=user,
        shop=connection.shop,
        store_name=store_name,
        niche=niche,
        status=BuildJob.Status.PENDING,
        progress_step=0,
        product_count=count,
        skip_products=bool(skip_products) or count == 0,
        selected_product_ids=[],
    )
    return kickoff_remote_build(job)


@login_required
@require_http_methods(["POST"])
def start_build(request):
    """Legacy POST entry — prefer wizard confirm_build."""
    ensure_niche_packs()
    niche_slug = (request.POST.get("niche") or "").strip().lower()
    connection, err = _require_ready_shop(request.user, request.POST.get("shop"))
    if err:
        messages.error(request, err)
        return redirect("dashboard:home")

    niche = NichePack.objects.filter(slug=niche_slug, is_active=True).first()
    if not niche:
        messages.error(request, "Pick a niche to continue.")
        return redirect("dashboard:builder")

    skip = request.POST.get("skip_products") == "1"
    job = create_build_job(
        user=request.user,
        connection=connection,
        niche=niche,
        product_ids=[],
        skip_products=skip or not niche.has_products,
    )
    return redirect("dashboard:builder:building", job_id=job.pk)


@login_required
def building(request, job_id: int):
    job = _job_for_request(request, job_id)
    advance_build_job(job)
    if job.status == BuildJob.Status.DONE:
        return redirect("dashboard:builder:success", job_id=job.pk)

    if job.status == BuildJob.Status.FAILED:
        copy = build_failure_copy(job)
        plan = None
        try:
            from apps.dashboard.overview import get_or_create_plan

            plan = get_or_create_plan(request.user)
        except Exception:
            plan = None
        return render(
            request,
            "builder/build_failed.html",
            {
                "nav_active": "builder",
                "plan_label": plan.label if plan else "",
                "is_free_plan": (not plan.is_pro) if plan else True,
                "job": job,
                "build_error_headline": copy["headline"],
                "build_error_body": copy["body"],
                "retry_url": reverse("dashboard:builder:retry", kwargs={"job_id": job.pk}),
                "support_email": getattr(settings, "CONTACT_NOTIFY_EMAIL", "help@brandbox.co"),
            },
        )

    return render(
        request,
        "builder/building.html",
        {
            "job": job,
            "labels": job.progress_labels(),
            "status_url": reverse("dashboard:builder:job_status", kwargs={"job_id": job.pk}),
        },
    )


@login_required
@require_http_methods(["POST"])
def retry_build(request, job_id: int):
    """Retry a failed build via Node /api/build/retry (new buildId). POST-only."""
    job = _job_for_request(request, job_id)
    if job.status == BuildJob.Status.FAILED:
        retry_failed_step(job)
    return redirect("dashboard:builder:building", job_id=job.pk)


@login_required
@require_GET
def job_status(request, job_id: int):
    job = _job_for_request(request, job_id)
    payload = build_status_payload(job)
    if payload["done"]:
        payload["redirect"] = reverse("dashboard:builder:success", kwargs={"job_id": job.pk})
    if payload["failed"]:
        payload["redirect"] = reverse("dashboard:builder:building", kwargs={"job_id": job.pk})
    return JsonResponse(payload)


@login_required
def success(request, job_id: int):
    job = _job_for_request(request, job_id)
    advance_build_job(job)
    if job.status != BuildJob.Status.DONE:
        return redirect("dashboard:builder:building", job_id=job.pk)

    # Prefer the job's shop; fall back to viewer's active shop
    store_url = f"https://{job.shop}" if job.shop else ""
    if not store_url:
        connection = ShopConnection.active_for_user(request.user)
        store_url = connection.storefront_url if connection else ""

    if job.product_count > 0:
        lede = (
            f"{job.display_name} is stocked with {job.product_count} winning products — "
            "go live and keep stacking winners."
        )
    else:
        lede = (
            f"{job.display_name} is live — open your storefront or stack it with "
            "products that convert."
        )

    return render(
        request,
        "builder/success.html",
        {
            "job": job,
            "store_url": store_url,
            "success_lede": lede,
        },
    )


@login_required
def builder_status(request):
    """Legacy entry — send users to AI Store Builder."""
    return redirect("dashboard:builder")
