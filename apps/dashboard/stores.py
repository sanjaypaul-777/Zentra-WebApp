"""
My Stores — one row per connected Shopify shop (ShopConnection).

Status is derived from the latest BuildJob for that shop domain, not a
separate stored status field.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.urls import reverse

from apps.builder.models import BuildJob
from apps.builder.services import advance_build_job

from .models import ShopConnection


@dataclass
class StoreRow:
    connection: ShopConnection
    status: str  # not_built | building | live | failed
    status_label: str
    latest_job: BuildJob | None
    niche_badge: str
    theme_name: str
    connected_at: datetime | None
    progress_line: str
    primary_url: str
    primary_label: str
    primary_external: bool
    detail_url: str

    @property
    def shop(self) -> str:
        return self.connection.shop

    @property
    def pk(self) -> int:
        return self.connection.pk


def _connected_at(connection: ShopConnection) -> datetime | None:
    return connection.app_installed_at or connection.installed_at


def _niche_badge(job: BuildJob | None) -> str:
    if not job or not job.niche_id:
        return ""
    niche = job.niche
    code = niche.display_codename
    name = (niche.name or "").strip()
    if name and name.lower() != code.lower():
        return f"{code} — {name}"
    return code


def _theme_name(job: BuildJob | None) -> str:
    if not job or not job.niche_id:
        return ""
    return job.niche.display_theme


def _progress_line(job: BuildJob) -> str:
    label = job.progress_label or "Building your store"
    return f"{label}… usually under a minute"


def derive_store_row(connection: ShopConnection, latest_job: BuildJob | None) -> StoreRow:
    """Map a connected shop + optional latest build into a My Stores row."""
    if latest_job and latest_job.status in (
        BuildJob.Status.RUNNING,
        BuildJob.Status.PENDING,
    ):
        advance_build_job(latest_job)
        latest_job.refresh_from_db()

    detail_url = reverse("dashboard:store_detail", kwargs={"pk": connection.pk})
    niche_badge = _niche_badge(latest_job)
    theme = _theme_name(latest_job)
    connected = _connected_at(connection)

    if latest_job is None:
        return StoreRow(
            connection=connection,
            status="not_built",
            status_label="Not built yet",
            latest_job=None,
            niche_badge="",
            theme_name="",
            connected_at=connected,
            progress_line="",
            primary_url=f"{reverse('dashboard:builder')}?shop={connection.shop}",
            primary_label="Build AI store",
            primary_external=False,
            detail_url=detail_url,
        )

    if latest_job.status in (BuildJob.Status.RUNNING, BuildJob.Status.PENDING):
        return StoreRow(
            connection=connection,
            status="building",
            status_label="Building",
            latest_job=latest_job,
            niche_badge=niche_badge,
            theme_name=theme,
            connected_at=connected,
            progress_line=_progress_line(latest_job),
            primary_url="",
            primary_label="",
            primary_external=False,
            detail_url=detail_url,
        )

    if latest_job.status == BuildJob.Status.DONE:
        return StoreRow(
            connection=connection,
            status="live",
            status_label="Live",
            latest_job=latest_job,
            niche_badge=niche_badge,
            theme_name=theme,
            connected_at=connected,
            progress_line="",
            primary_url=connection.storefront_url,
            primary_label="Open store",
            primary_external=True,
            detail_url=detail_url,
        )

    # Failed (or any other terminal non-done state)
    return StoreRow(
        connection=connection,
        status="failed",
        status_label="Failed",
        latest_job=latest_job,
        niche_badge=niche_badge,
        theme_name=theme,
        connected_at=connected,
        progress_line="",
        primary_url=reverse(
                "dashboard:builder:retry", kwargs={"job_id": latest_job.pk}
            ),
        primary_label="Retry build",
        primary_external=False,
        detail_url=detail_url,
    )


def connected_shops_for_user(user):
    """Installed shops for this user, newest connection first."""
    return (
        ShopConnection.objects.filter(user=user, app_installed=True)
        .order_by("-app_installed_at", "-installed_at", "-id")
    )


def build_store_rows(user) -> list[StoreRow]:
    shops = list(connected_shops_for_user(user))
    if not shops:
        return []

    domains = [s.shop for s in shops]
    jobs = (
        BuildJob.objects.filter(user=user, shop__in=domains)
        .select_related("niche")
        .order_by("-created_at")
    )
    latest_by_shop: dict[str, BuildJob] = {}
    for job in jobs:
        if job.shop not in latest_by_shop:
            latest_by_shop[job.shop] = job

    return [derive_store_row(shop, latest_by_shop.get(shop.shop)) for shop in shops]
