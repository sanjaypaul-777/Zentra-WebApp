"""Session lifecycle — exclusive assign, reassign, leave, agent replies."""

from __future__ import annotations

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from config.product import COACH_WELCOME

from apps.help.coach_reply import synthesize_agent_reply, wants_human_coach

from .models import CoachAssignment, CoachMessage, CoachProfile, CoachSession


WELCOME_BODY = COACH_WELCOME



def get_or_create_open_session(merchant) -> CoachSession:
    session = (
        CoachSession.objects.filter(merchant=merchant)
        .exclude(status=CoachSession.STATUS_CLOSED)
        .order_by("-updated_at")
        .first()
    )
    if session:
        return session
    session = CoachSession.objects.create(
        merchant=merchant,
        status=CoachSession.STATUS_BOT,
    )
    CoachMessage.objects.create(
        session=session,
        role=CoachMessage.ROLE_AGENT,
        body=WELCOME_BODY,
    )
    return session


def serialize_message(msg: CoachMessage) -> dict:
    author_name = ""
    if msg.role == CoachMessage.ROLE_AGENT:
        author_name = "Coach Agent"
    elif msg.role == CoachMessage.ROLE_COACH and msg.author_id:
        try:
            author_name = msg.author.coach_profile.public_name
        except CoachProfile.DoesNotExist:
            full = f"{msg.author.first_name} {msg.author.last_name}".strip()
            author_name = full or msg.author.get_username()
    elif msg.role == CoachMessage.ROLE_MERCHANT:
        author_name = "You"
    elif msg.role == CoachMessage.ROLE_SYSTEM:
        author_name = "System"

    return {
        "id": msg.id,
        "role": msg.role,
        "body": msg.body,
        "author_name": author_name,
        "guide_title": msg.guide_title or "",
        "guide_url": msg.guide_url or "",
        "created_at": msg.created_at.isoformat(),
    }


def serialize_session(session: CoachSession) -> dict:
    coach_name = ""
    if session.assigned_coach_id:
        try:
            coach_name = session.assigned_coach.coach_profile.public_name
        except CoachProfile.DoesNotExist:
            u = session.assigned_coach
            coach_name = f"{u.first_name} {u.last_name}".strip() or u.get_username()
    needs_attention = False
    if session.status == CoachSession.STATUS_WAITING:
        needs_attention = True
    elif session.status == CoachSession.STATUS_LIVE and session.last_merchant_message_at:
        if (
            not session.last_coach_message_at
            or session.last_merchant_message_at > session.last_coach_message_at
        ):
            needs_attention = True
    return {
        "id": session.id,
        "status": session.status,
        "status_label": session.status_label,
        "assigned_coach_id": session.assigned_coach_id,
        "assigned_coach_name": coach_name,
        "agent_active": session.agent_active,
        "updated_at": session.updated_at.isoformat(),
        "merchant_id": session.merchant_id,
        "merchant_username": session.merchant.get_username(),
        "merchant_email": getattr(session.merchant, "email", "") or "",
        "needs_attention": needs_attention,
        "last_merchant_message_at": (
            session.last_merchant_message_at.isoformat()
            if session.last_merchant_message_at
            else None
        ),
    }


def _live_count_for_coach(coach) -> int:
    return CoachSession.objects.filter(
        assigned_coach=coach,
        status=CoachSession.STATUS_LIVE,
    ).count()


def claim_session(*, session: CoachSession, coach, by_user=None) -> tuple[bool, str]:
    """Exclusive claim — fails if already assigned."""
    by_user = by_user or coach
    if not CoachProfile.user_is_coach(coach):
        return False, "not_a_coach"
    if session.status == CoachSession.STATUS_CLOSED:
        return False, "session_closed"
    if session.assigned_coach_id and session.assigned_coach_id != coach.id:
        return False, "already_assigned"
    if session.assigned_coach_id == coach.id and session.status == CoachSession.STATUS_LIVE:
        return True, "already_yours"

    profile = coach.coach_profile
    if _live_count_for_coach(coach) >= profile.max_concurrent:
        return False, "at_capacity"
    if not profile.is_available and session.assigned_coach_id != coach.id:
        return False, "unavailable"

    with transaction.atomic():
        locked = CoachSession.objects.select_for_update().get(pk=session.pk)
        if locked.assigned_coach_id and locked.assigned_coach_id != coach.id:
            return False, "already_assigned"
        from_coach = locked.assigned_coach
        locked.assigned_coach = coach
        locked.status = CoachSession.STATUS_LIVE
        locked.save(update_fields=["assigned_coach", "status", "updated_at"])
        CoachAssignment.objects.create(
            session=locked,
            from_coach=from_coach,
            to_coach=coach,
            by_user=by_user,
            reason=CoachAssignment.REASON_CLAIM,
        )
        CoachMessage.objects.create(
            session=locked,
            role=CoachMessage.ROLE_SYSTEM,
            body=f"{coach.coach_profile.public_name} joined the chat.",
        )
    return True, "claimed"


def reassign_session(*, session: CoachSession, new_coach, by_user) -> tuple[bool, str]:
    """Hand off to another coach — previous assignee auto-leaves."""
    if not CoachProfile.user_is_coach(new_coach):
        return False, "target_not_a_coach"
    if not CoachProfile.user_is_coach(by_user) and not (
        getattr(by_user, "is_staff", False) or getattr(by_user, "is_superuser", False)
    ):
        return False, "forbidden"
    if session.status == CoachSession.STATUS_CLOSED:
        return False, "session_closed"
    if not session.assigned_coach_id:
        return claim_session(session=session, coach=new_coach, by_user=by_user)

    # Only current assignee or staff can reassign
    is_assignee = session.assigned_coach_id == by_user.id
    is_staff = getattr(by_user, "is_staff", False) or getattr(by_user, "is_superuser", False)
    if not is_assignee and not is_staff:
        return False, "forbidden"
    if new_coach.id == session.assigned_coach_id:
        return True, "already_assigned_to_target"

    profile = new_coach.coach_profile
    if _live_count_for_coach(new_coach) >= profile.max_concurrent:
        return False, "at_capacity"

    with transaction.atomic():
        locked = CoachSession.objects.select_for_update().get(pk=session.pk)
        old = locked.assigned_coach
        if locked.assigned_coach_id != (old.id if old else None):
            pass
        locked.assigned_coach = new_coach
        locked.status = CoachSession.STATUS_LIVE
        locked.save(update_fields=["assigned_coach", "status", "updated_at"])
        CoachAssignment.objects.create(
            session=locked,
            from_coach=old,
            to_coach=new_coach,
            by_user=by_user,
            reason=CoachAssignment.REASON_REASSIGN,
        )
        old_name = ""
        if old:
            try:
                old_name = old.coach_profile.public_name
            except CoachProfile.DoesNotExist:
                old_name = old.get_username()
        new_name = new_coach.coach_profile.public_name
        CoachMessage.objects.create(
            session=locked,
            role=CoachMessage.ROLE_SYSTEM,
            body=(
                f"Chat reassigned to {new_name}."
                + (f" {old_name} left the chat." if old_name else "")
            ),
        )
    return True, "reassigned"


def leave_session(*, session: CoachSession, coach, return_to_waiting: bool = False) -> tuple[bool, str]:
    if session.assigned_coach_id != coach.id:
        return False, "not_assignee"
    with transaction.atomic():
        locked = CoachSession.objects.select_for_update().get(pk=session.pk)
        if locked.assigned_coach_id != coach.id:
            return False, "not_assignee"
        locked.assigned_coach = None
        locked.status = (
            CoachSession.STATUS_WAITING if return_to_waiting else CoachSession.STATUS_BOT
        )
        locked.save(update_fields=["assigned_coach", "status", "updated_at"])
        CoachAssignment.objects.create(
            session=locked,
            from_coach=coach,
            to_coach=None,
            by_user=coach,
            reason=CoachAssignment.REASON_LEAVE,
        )
        name = coach.coach_profile.public_name
        if return_to_waiting:
            body = f"{name} left. Waiting for another coach…"
        else:
            body = f"{name} left. Coach Agent is back to help."
        CoachMessage.objects.create(
            session=locked,
            role=CoachMessage.ROLE_SYSTEM,
            body=body,
        )
    return True, "left"


def close_session(*, session: CoachSession, by_user, as_coach: bool = False) -> tuple[bool, str]:
    """End the chat. Merchant or assigned coach (or staff) can close."""
    if session.status == CoachSession.STATUS_CLOSED:
        return True, "already_closed"
    is_merchant = session.merchant_id == by_user.id
    is_assignee = session.assigned_coach_id == by_user.id
    is_staff = getattr(by_user, "is_staff", False) or getattr(by_user, "is_superuser", False)
    if as_coach and not (is_assignee or is_staff):
        return False, "forbidden"
    if not as_coach and not is_merchant:
        return False, "forbidden"

    with transaction.atomic():
        locked = CoachSession.objects.select_for_update().get(pk=session.pk)
        if locked.status == CoachSession.STATUS_CLOSED:
            return True, "already_closed"
        locked.status = CoachSession.STATUS_CLOSED
        locked.assigned_coach = None
        locked.closed_at = timezone.now()
        locked.save(update_fields=["status", "assigned_coach", "closed_at", "updated_at"])
        who = "Coach" if as_coach else "You"
        if as_coach:
            try:
                who = by_user.coach_profile.public_name
            except CoachProfile.DoesNotExist:
                who = by_user.get_username()
        CoachMessage.objects.create(
            session=locked,
            role=CoachMessage.ROLE_SYSTEM,
            body=f"{who} ended this chat. Send a new message anytime to start again.",
            author=by_user,
        )
    return True, "closed"


def request_human_coach(*, session: CoachSession) -> CoachMessage:
    """Merchant requests live coach — enter waiting queue."""
    if session.status == CoachSession.STATUS_LIVE:
        return CoachMessage.objects.create(
            session=session,
            role=CoachMessage.ROLE_SYSTEM,
            body="A coach is already with you in this chat.",
        )
    session.status = CoachSession.STATUS_WAITING
    session.assigned_coach = None
    session.save(update_fields=["status", "assigned_coach", "updated_at"])
    return CoachMessage.objects.create(
        session=session,
        role=CoachMessage.ROLE_AGENT,
        body=(
            "Got it — I've put you in the queue for a live coach. "
            "Stay on this chat; a coach will join when available. "
            "You can keep asking me questions meanwhile."
        ),
    )


def handle_merchant_message(*, session: CoachSession, text: str, request=None) -> list[CoachMessage]:
    """Persist merchant message; Agent replies only when not live."""
    # Closed sessions should not receive more messages — open a new one first
    if session.status == CoachSession.STATUS_CLOSED:
        session = get_or_create_open_session(session.merchant)

    now = timezone.now()
    merchant_msg = CoachMessage.objects.create(
        session=session,
        role=CoachMessage.ROLE_MERCHANT,
        author=session.merchant,
        body=text.strip(),
    )
    session.last_merchant_message_at = now
    session.save(update_fields=["last_merchant_message_at", "updated_at"])

    created = [merchant_msg]

    if session.status == CoachSession.STATUS_LIVE:
        return created

    if wants_human_coach(text):
        # Gate is enforced in the API layer via config.product
        created.append(request_human_coach(session=session))
        return created

    reply = synthesize_agent_reply(text, request=request)
    agent_msg = CoachMessage.objects.create(
        session=session,
        role=CoachMessage.ROLE_AGENT,
        body=reply["body"],
        guide_title=reply.get("guide_title") or "",
        guide_url=reply.get("guide_url") or "",
    )
    created.append(agent_msg)
    return created


def handle_coach_message(*, session: CoachSession, coach, text: str) -> tuple[bool, str, CoachMessage | None]:
    if session.status != CoachSession.STATUS_LIVE:
        return False, "not_live", None
    if session.assigned_coach_id != coach.id:
        return False, "not_assignee", None
    msg = CoachMessage.objects.create(
        session=session,
        role=CoachMessage.ROLE_COACH,
        author=coach,
        body=text.strip(),
    )
    session.last_coach_message_at = timezone.now()
    session.save(update_fields=["last_coach_message_at", "updated_at"])
    return True, "ok", msg


def list_waiting_sessions():
    return (
        CoachSession.objects.filter(status=CoachSession.STATUS_WAITING)
        .select_related("merchant")
        .order_by("updated_at")
    )


def list_coach_sessions(coach):
    return (
        CoachSession.objects.filter(
            assigned_coach=coach,
            status=CoachSession.STATUS_LIVE,
        )
        .select_related("merchant")
        .order_by("-updated_at")
    )


def list_available_coaches(exclude_user=None):
    qs = (
        CoachProfile.objects.filter(is_coach=True, user__is_staff=True, user__is_active=True)
        .select_related("user")
        .annotate(
            live_count=Count(
                "user__assigned_coach_sessions",
                filter=Q(user__assigned_coach_sessions__status=CoachSession.STATUS_LIVE),
            )
        )
    )
    if exclude_user is not None:
        qs = qs.exclude(user=exclude_user)
    return qs
