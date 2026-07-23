"""Merchant chat APIs + coach desk UI/APIs."""

from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from apps.dashboard.overview import get_or_create_plan

from .models import CoachMessage, CoachProfile, CoachSession
from .permissions import coach_required, user_can_view_all_sessions, user_is_coach
from . import services


def _json_body(request) -> dict:
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body.decode("utf-8") or "{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
    return {}


def _page_ctx(request, **extra):
    return {
        "nav_active": extra.pop("nav_active", "coach_desk"),
        "user": request.user,
        **extra,
    }


# ── Merchant APIs ─────────────────────────────────────────────────────────────


@login_required
@require_GET
def api_session(request):
    session = services.get_or_create_open_session(request.user)
    after_id = int(request.GET.get("after_id") or 0)
    qs = session.messages.all()
    if after_id:
        qs = qs.filter(id__gt=after_id)
    messages = [services.serialize_message(m) for m in qs[:200]]
    plan = get_or_create_plan(request.user)
    return JsonResponse(
        {
            "ok": True,
            "session": services.serialize_session(session),
            "messages": messages,
            "can_transfer": plan.is_pro,
        }
    )


@login_required
@require_POST
def api_send(request):
    data = _json_body(request)
    text = (data.get("message") or request.POST.get("message") or "").strip()
    if len(text) < 1:
        return JsonResponse({"ok": False, "error": "empty"}, status=400)
    if len(text) > 2000:
        return JsonResponse({"ok": False, "error": "too_long"}, status=400)

    session = services.get_or_create_open_session(request.user)

    from apps.help.coach_reply import wants_human_coach

    if wants_human_coach(text) and session.status != CoachSession.STATUS_LIVE:
        plan = get_or_create_plan(request.user)
        merchant_msg = CoachMessage.objects.create(
            session=session,
            role=CoachMessage.ROLE_MERCHANT,
            author=request.user,
            body=text,
        )
        if not plan.is_pro:
            agent = CoachMessage.objects.create(
                session=session,
                role=CoachMessage.ROLE_AGENT,
                body=(
                    "A live coach needs an active plan. "
                    "You can keep chatting with Coach Agent for now — "
                    "upgrade options will be finalized soon."
                ),
            )
            return JsonResponse(
                {
                    "ok": True,
                    "session": services.serialize_session(session),
                    "messages": [
                        services.serialize_message(merchant_msg),
                        services.serialize_message(agent),
                    ],
                    "needs_upgrade": True,
                }
            )
        created = [merchant_msg, services.request_human_coach(session=session)]
        session.refresh_from_db()
        return JsonResponse(
            {
                "ok": True,
                "session": services.serialize_session(session),
                "messages": [services.serialize_message(m) for m in created],
            }
        )

    created = services.handle_merchant_message(session=session, text=text, request=request)
    session.refresh_from_db()
    return JsonResponse(
        {
            "ok": True,
            "session": services.serialize_session(session),
            "messages": [services.serialize_message(m) for m in created],
        }
    )


@login_required
@require_POST
def api_request_coach(request):
    plan = get_or_create_plan(request.user)
    if not plan.is_pro:
        return JsonResponse({"ok": False, "error": "plan_required"}, status=403)
    session = services.get_or_create_open_session(request.user)
    if session.status == CoachSession.STATUS_LIVE:
        return JsonResponse(
            {
                "ok": True,
                "session": services.serialize_session(session),
                "messages": [],
            }
        )
    msg = services.request_human_coach(session=session)
    session.refresh_from_db()
    return JsonResponse(
        {
            "ok": True,
            "session": services.serialize_session(session),
            "messages": [services.serialize_message(msg)],
        }
    )


@login_required
@require_POST
def api_close(request):
    open_session = (
        CoachSession.objects.filter(merchant=request.user)
        .exclude(status=CoachSession.STATUS_CLOSED)
        .order_by("-updated_at")
        .first()
    )
    if not open_session:
        return JsonResponse({"ok": True, "reason": "already_closed"})
    ok, reason = services.close_session(session=open_session, by_user=request.user, as_coach=False)
    open_session.refresh_from_db()
    last = open_session.messages.order_by("-id").first()
    return JsonResponse(
        {
            "ok": ok,
            "reason": reason,
            "session": services.serialize_session(open_session),
            "messages": [services.serialize_message(last)] if last else [],
        }
    )


# ── Coach desk page + APIs ────────────────────────────────────────────────────


@login_required
@coach_required
@require_GET
def coach_desk_page(request):
    profile = request.user.coach_profile
    waiting = list(services.list_waiting_sessions()[:50])
    mine = list(services.list_coach_sessions(request.user)[:50])
    coaches = list(services.list_available_coaches(exclude_user=request.user))
    return render(
        request,
        "dashboard/coach_desk.html",
        _page_ctx(
            request,
            nav_active="coach_desk",
            profile=profile,
            waiting_sessions=waiting,
            my_sessions=mine,
            other_coaches=coaches,
            is_coach=True,
        ),
    )


@login_required
@coach_required
@require_GET
def api_desk_state(request):
    waiting = [services.serialize_session(s) for s in services.list_waiting_sessions()[:50]]
    mine = [services.serialize_session(s) for s in services.list_coach_sessions(request.user)[:50]]
    coaches = [
        {
            "id": p.user_id,
            "name": p.public_name,
            "available": p.is_available,
            "live_count": p.live_count,
            "max_concurrent": p.max_concurrent,
        }
        for p in services.list_available_coaches()
    ]
    profile = request.user.coach_profile
    return JsonResponse(
        {
            "ok": True,
            "waiting": waiting,
            "mine": mine,
            "coaches": coaches,
            "is_available": profile.is_available,
        }
    )


@login_required
@coach_required
@require_GET
def api_desk_session_messages(request, session_id: int):
    session = get_object_or_404(CoachSession, pk=session_id)
    # Coaches can read waiting + their live; staff can read all
    allowed = (
        session.status == CoachSession.STATUS_WAITING
        or session.assigned_coach_id == request.user.id
        or user_can_view_all_sessions(request.user)
    )
    if not allowed:
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
    after_id = int(request.GET.get("after_id") or 0)
    qs = session.messages.all()
    if after_id:
        qs = qs.filter(id__gt=after_id)
    return JsonResponse(
        {
            "ok": True,
            "session": services.serialize_session(session),
            "messages": [services.serialize_message(m) for m in qs[:300]],
        }
    )


@login_required
@coach_required
@require_POST
def api_desk_claim(request, session_id: int):
    session = get_object_or_404(CoachSession, pk=session_id)
    ok, reason = services.claim_session(session=session, coach=request.user)
    session.refresh_from_db()
    status = 200 if ok else 409
    return JsonResponse(
        {
            "ok": ok,
            "reason": reason,
            "session": services.serialize_session(session),
        },
        status=status,
    )


@login_required
@coach_required
@require_POST
def api_desk_reassign(request, session_id: int):
    session = get_object_or_404(CoachSession, pk=session_id)
    data = _json_body(request)
    target_id = data.get("coach_id") or request.POST.get("coach_id")
    try:
        target_id = int(target_id)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "invalid_coach"}, status=400)
    try:
        target_profile = CoachProfile.objects.select_related("user").get(
            user_id=target_id, is_coach=True
        )
    except CoachProfile.DoesNotExist:
        return JsonResponse({"ok": False, "error": "target_not_a_coach"}, status=400)
    ok, reason = services.reassign_session(
        session=session,
        new_coach=target_profile.user,
        by_user=request.user,
    )
    session.refresh_from_db()
    status = 200 if ok else 409
    return JsonResponse(
        {"ok": ok, "reason": reason, "session": services.serialize_session(session)},
        status=status,
    )


@login_required
@coach_required
@require_POST
def api_desk_leave(request, session_id: int):
    session = get_object_or_404(CoachSession, pk=session_id)
    data = _json_body(request)
    waiting = bool(data.get("return_to_waiting") or request.POST.get("return_to_waiting"))
    ok, reason = services.leave_session(
        session=session,
        coach=request.user,
        return_to_waiting=waiting,
    )
    session.refresh_from_db()
    status = 200 if ok else 409
    return JsonResponse(
        {"ok": ok, "reason": reason, "session": services.serialize_session(session)},
        status=status,
    )


@login_required
@coach_required
@require_POST
def api_desk_close(request, session_id: int):
    session = get_object_or_404(CoachSession, pk=session_id)
    ok, reason = services.close_session(session=session, by_user=request.user, as_coach=True)
    session.refresh_from_db()
    status = 200 if ok else 409
    return JsonResponse(
        {"ok": ok, "reason": reason, "session": services.serialize_session(session)},
        status=status,
    )


@login_required
@coach_required
@require_POST
def api_desk_send(request, session_id: int):
    session = get_object_or_404(CoachSession, pk=session_id)
    data = _json_body(request)
    text = (data.get("message") or request.POST.get("message") or "").strip()
    if not text:
        return JsonResponse({"ok": False, "error": "empty"}, status=400)
    ok, reason, msg = services.handle_coach_message(
        session=session, coach=request.user, text=text
    )
    if not ok:
        return JsonResponse({"ok": False, "error": reason}, status=409)
    session.refresh_from_db()
    return JsonResponse(
        {
            "ok": True,
            "session": services.serialize_session(session),
            "messages": [services.serialize_message(msg)],
        }
    )


@login_required
@coach_required
@require_POST
def api_desk_presence(request):
    data = _json_body(request)
    available = data.get("available")
    if available is None:
        available = request.POST.get("available")
    profile = request.user.coach_profile
    profile.is_available = str(available).lower() in {"1", "true", "yes", "on"}
    profile.save(update_fields=["is_available", "updated_at"])
    return JsonResponse({"ok": True, "is_available": profile.is_available})


@login_required
@require_GET
def api_coach_check(request):
    """Lightweight flag for nav / UI."""
    return JsonResponse(
        {
            "ok": True,
            "is_coach": user_is_coach(request.user),
            "can_view_logs": user_can_view_all_sessions(request.user),
        }
    )
