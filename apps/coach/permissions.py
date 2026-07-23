"""Coach desk access — staff + CoachProfile.is_coach."""

from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden, JsonResponse

from .models import CoachProfile


def user_is_coach(user) -> bool:
    return CoachProfile.user_is_coach(user)


def user_can_view_all_sessions(user) -> bool:
    """Superuser or staff can view/export all chat logs (Coach flag not required)."""
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and (getattr(user, "is_superuser", False) or getattr(user, "is_staff", False))
    )


def coach_required(view_func):
    """Require staff + Coach feature. JSON 403 for API-ish paths."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.path.startswith(
                "/dashboard/coach-desk/api/"
            ):
                return JsonResponse({"ok": False, "error": "login_required"}, status=401)
            return redirect_to_login(request.get_full_path())
        if not user_is_coach(user):
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or "/coach-desk/api/" in request.path:
                return JsonResponse(
                    {
                        "ok": False,
                        "error": "not_a_coach",
                        "detail": "Enable Coach on this staff account in Django admin.",
                    },
                    status=403,
                )
            return HttpResponseForbidden(
                "Coach desk requires a staff account with the Coach feature enabled in Django admin."
            )
        return view_func(request, *args, **kwargs)

    return _wrapped
