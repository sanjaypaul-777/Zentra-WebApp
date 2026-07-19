"""
Build runner — drives BuildJob from BrandBox Node internal APIs.

Staff preview shops (admin-preview-*) keep a local timed simulator for UI work.
"""

from __future__ import annotations

import logging

from django.utils import timezone

from config.brandbox_client import (
    get_remote_build_status,
    retry_remote_build,
    start_remote_build,
)

from .models import BuildJob

logger = logging.getLogger(__name__)

# Seconds per progress step in the staff-preview simulator
STEP_SECONDS = 2.0
STEP_PERCENTS = (33, 66, 100)


def _is_preview_shop(shop: str) -> bool:
    return (shop or "").startswith("admin-preview-")


def map_engine_step(current_step: int, progress: int, *, completed: bool) -> int:
    """Map Node currentStep / progress onto the 3-step builder UI."""
    if completed or progress >= 100:
        return 2
    step = int(current_step or 0)
    pct = int(progress or 0)
    if step <= 0 or pct < 15:
        return 0
    if step == 1 or pct < 50:
        return 1
    return 2


def _apply_remote_payload(job: BuildJob, data: dict) -> BuildJob:
    """Copy Node build status fields onto the local BuildJob."""
    completed = bool(data.get("completed") or data.get("status") == "completed")
    failed = bool(data.get("failed") or data.get("status") == "failed")
    progress = int(data.get("progress") or 0)
    current_step = int(data.get("currentStep") or 0)
    label = (data.get("stepLabel") or "").strip()
    product_count = data.get("productCount")
    build_id = data.get("buildId") or data.get("id")

    fields = ["updated_at"]
    if build_id and build_id != job.brandbox_build_id:
        job.brandbox_build_id = str(build_id)
        fields.append("brandbox_build_id")

    job.engine_progress = min(100, max(0, progress))
    fields.append("engine_progress")

    if label:
        job.live_label = label[:255]
        fields.append("live_label")

    step = map_engine_step(current_step, progress, completed=completed)
    if step != job.progress_step:
        job.progress_step = step
        fields.append("progress_step")

    if product_count is not None:
        try:
            pc = int(product_count)
            if pc != job.product_count and not job.skip_products:
                job.product_count = pc
                fields.append("product_count")
        except (TypeError, ValueError):
            pass

    if completed:
        job.status = BuildJob.Status.DONE
        job.engine_progress = 100
        job.progress_step = 2
        job.error_message = ""
        fields.extend(["status", "error_message"])
    elif failed:
        job.status = BuildJob.Status.FAILED
        err = (data.get("error") or data.get("errorMessage") or "Build failed").strip()
        job.error_message = err[:2000]
        fields.extend(["status", "error_message"])
    elif job.status == BuildJob.Status.PENDING:
        job.status = BuildJob.Status.RUNNING
        fields.append("status")

    job.save(update_fields=list(dict.fromkeys(fields)))
    return job


def kickoff_remote_build(job: BuildJob) -> BuildJob:
    """POST /api/build/start and attach brandbox_build_id. No-op for preview shops."""
    if _is_preview_shop(job.shop):
        return job
    if job.brandbox_build_id:
        return job

    niche_id = job.niche.slug if job.niche_id else ""
    if not niche_id:
        job.status = BuildJob.Status.FAILED
        job.error_message = "Pick a niche before building."
        job.save(update_fields=["status", "error_message", "updated_at"])
        return job

    result = start_remote_build(shop=job.shop, niche_id=niche_id)
    if not result.get("ok"):
        job.status = BuildJob.Status.FAILED
        err = result.get("error") or "Could not start the store build"
        if err == "app_not_installed":
            err = "Install the BrandBox app on your Shopify store, then try again."
        job.error_message = str(err)[:2000]
        job.save(update_fields=["status", "error_message", "updated_at"])
        return job

    return _apply_remote_payload(job, result)


def advance_build_job(job: BuildJob) -> BuildJob:
    """Poll Node build status (or advance local preview simulator)."""
    if job.status in (BuildJob.Status.DONE, BuildJob.Status.FAILED):
        return job

    if _is_preview_shop(job.shop):
        return _advance_preview_job(job)

    if not job.brandbox_build_id:
        return kickoff_remote_build(job)

    result = get_remote_build_status(shop=job.shop, build_id=job.brandbox_build_id)
    if not result.get("ok"):
        # Transient network blip — keep running; hard 404/409 fail the job.
        status = result.get("status")
        if status in (404, 409, 400):
            job.status = BuildJob.Status.FAILED
            job.error_message = str(result.get("error") or "Build not found")[:2000]
            job.save(update_fields=["status", "error_message", "updated_at"])
        else:
            logger.warning(
                "build status poll failed for job %s: %s",
                job.pk,
                result.get("error"),
            )
        return job

    return _apply_remote_payload(job, result)


def _advance_preview_job(job: BuildJob) -> BuildJob:
    """Local timed simulator for staff admin-preview shops only."""
    total_steps = len(STEP_PERCENTS)

    if job.status == BuildJob.Status.PENDING:
        job.status = BuildJob.Status.RUNNING
        job.progress_step = 0
        job.save(update_fields=["status", "progress_step", "updated_at"])

    elapsed = (timezone.now() - job.created_at).total_seconds()
    step = min(total_steps - 1, int(elapsed // STEP_SECONDS))

    if step != job.progress_step:
        job.progress_step = step
        job.engine_progress = STEP_PERCENTS[step]
        job.save(update_fields=["progress_step", "engine_progress", "updated_at"])

    if elapsed >= STEP_SECONDS * total_steps:
        if job.skip_products:
            products = 0
        elif job.selected_product_ids:
            products = len(job.selected_product_ids)
        elif job.niche_id:
            products = job.niche.catalog_product_count or job.niche.product_count
        else:
            products = 0
        job.status = BuildJob.Status.DONE
        job.progress_step = total_steps - 1
        job.engine_progress = 100
        job.product_count = products
        job.save(
            update_fields=[
                "status",
                "progress_step",
                "engine_progress",
                "product_count",
                "updated_at",
            ]
        )

    return job


def build_failure_copy(job: BuildJob) -> dict[str, str]:
    """
    User-facing build failure copy — never expose raw exception text.
    Based on which progress step failed.
    """
    step = int(job.progress_step or 0)
    headline = "We hit a snag building your store"

    if step <= 0:
        body = (
            "We couldn't finish installing your theme. "
            "No changes were lost — you can try this step again."
        )
    elif step == 1:
        body = (
            "Your theme was installed successfully, but we couldn't finish "
            "uploading your winning products. No changes were lost."
        )
    else:
        body = (
            "Your theme and products are in place, but we couldn't finish "
            "setting up menus and policies. No changes were lost."
        )

    return {"headline": headline, "body": body}


def retry_failed_step(job: BuildJob) -> BuildJob:
    """Retry via Node /api/build/retry (new buildId) or reset preview simulator."""
    if job.status != BuildJob.Status.FAILED:
        return job

    if _is_preview_shop(job.shop):
        job.status = BuildJob.Status.RUNNING
        job.error_message = ""
        job.live_label = ""
        job.created_at = timezone.now() - timezone.timedelta(
            seconds=STEP_SECONDS * max(0, int(job.progress_step or 0))
        )
        job.save(
            update_fields=[
                "status",
                "error_message",
                "live_label",
                "created_at",
                "updated_at",
            ]
        )
        return job

    previous_id = job.brandbox_build_id
    if not previous_id:
        # Never reached Node — try a fresh start
        job.status = BuildJob.Status.PENDING
        job.error_message = ""
        job.live_label = ""
        job.engine_progress = 0
        job.progress_step = 0
        job.save(
            update_fields=[
                "status",
                "error_message",
                "live_label",
                "engine_progress",
                "progress_step",
                "updated_at",
            ]
        )
        return kickoff_remote_build(job)

    result = retry_remote_build(shop=job.shop, build_id=previous_id)
    if not result.get("ok"):
        job.error_message = str(result.get("error") or "Retry failed")[:2000]
        job.save(update_fields=["error_message", "updated_at"])
        return job

    job.status = BuildJob.Status.RUNNING
    job.error_message = ""
    job.live_label = ""
    job.engine_progress = 0
    job.progress_step = 0
    job.brandbox_build_id = ""
    job.save(
        update_fields=[
            "status",
            "error_message",
            "live_label",
            "engine_progress",
            "progress_step",
            "brandbox_build_id",
            "updated_at",
        ]
    )
    return _apply_remote_payload(job, result)


def build_status_payload(job: BuildJob) -> dict:
    job = advance_build_job(job)
    labels = list(job.progress_labels())
    total = len(labels)

    if job.status == BuildJob.Status.DONE:
        percent = 100
    elif job.brandbox_build_id or not _is_preview_shop(job.shop):
        percent = int(job.engine_progress or 0)
    else:
        elapsed = (timezone.now() - job.created_at).total_seconds()
        raw = min(total - 1, int(elapsed // STEP_SECONDS))
        prev = STEP_PERCENTS[raw - 1] if raw > 0 else 0
        target = STEP_PERCENTS[raw]
        frac = (elapsed % STEP_SECONDS) / STEP_SECONDS
        percent = int(prev + (target - prev) * min(1.0, frac))

    eta = 0
    if job.status not in (BuildJob.Status.DONE, BuildJob.Status.FAILED):
        if _is_preview_shop(job.shop):
            eta = max(
                0,
                int(
                    STEP_SECONDS * total
                    - (timezone.now() - job.created_at).total_seconds()
                ),
            )
        else:
            # Rough ETA from remaining percent
            eta = max(0, int((100 - percent) * 1.5))

    return {
        "id": job.pk,
        "status": job.status,
        "progress_step": job.progress_step,
        "progress_total": total,
        "progress_percent": percent,
        "progress_label": job.progress_label,
        "labels": labels,
        "shop": job.shop,
        "store_name": job.display_name,
        "product_count": job.product_count,
        "skip_products": job.skip_products,
        "niche": job.niche.slug if job.niche_id else None,
        "niche_name": job.niche.display_codename if job.niche_id else None,
        "done": job.status == BuildJob.Status.DONE,
        "failed": job.status == BuildJob.Status.FAILED,
        "error_message": job.error_message,
        "eta_seconds": eta,
        "brandbox_build_id": job.brandbox_build_id or None,
        "live": bool(job.live_label),
    }
