"""
Onboarding gate — send incomplete merchants to /onboarding/ before dashboard.
"""

from __future__ import annotations

from django.shortcuts import redirect
from django.urls import reverse

from apps.dashboard.access import is_dev_admin


class OnboardingRequiredMiddleware:
    """
    Authenticated users with onboarding_completed=False cannot use
    /dashboard/ (including builder) until they finish /onboarding/.

    Staff/superuser skip this gate so they can open any URL/step for development.
    """

    EXEMPT_PREFIXES = (
        "/onboarding",
        "/admin",
        "/static",
        "/media",
        "/accounts",
        "/checkout",
        "/__debug__",
        "/api/address-suggest",
        "/api/geo",
    )

    GATED_PREFIXES = (
        "/dashboard",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or "/"
        user = getattr(request, "user", None)

        if (
            user is not None
            and user.is_authenticated
            and not is_dev_admin(user)
            and self._is_gated(path)
            and not self._is_exempt(path)
        ):
            from apps.dashboard.models import MerchantProfile

            profile = MerchantProfile.for_user(user)
            if not profile.onboarding_completed:
                return redirect(reverse("onboarding"))

        if (
            user is not None
            and user.is_authenticated
            and path.startswith("/onboarding")
            and not is_dev_admin(user)
        ):
            from apps.dashboard.models import MerchantProfile

            profile = MerchantProfile.for_user(user)
            if profile.onboarding_completed and request.method == "GET":
                return redirect(reverse("dashboard:home"))

        return self.get_response(request)

    def _is_gated(self, path: str) -> bool:
        return any(path == p or path.startswith(p + "/") for p in self.GATED_PREFIXES)

    def _is_exempt(self, path: str) -> bool:
        return any(path == p or path.startswith(p + "/") for p in self.EXEMPT_PREFIXES)
