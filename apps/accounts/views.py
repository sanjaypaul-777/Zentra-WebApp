"""
Accounts — login, signup, logout (Django auth).
Staff / superuser use /admin/ (Django admin).
"""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from .forms import BrandBoxAuthenticationForm, SignupForm

SOCIAL_PROVIDERS = {
    "google": "Google",
    "apple": "Apple",
    "facebook": "Facebook",
}

# Browser cookie: user has signed in on this device before (survives logout).
RETURNING_USER_COOKIE = "bb_returning_user"
RETURNING_USER_MAX_AGE = 60 * 60 * 24 * 365  # 1 year


def _mark_returning_user(response):
    response.set_cookie(
        RETURNING_USER_COOKIE,
        "1",
        max_age=RETURNING_USER_MAX_AGE,
        samesite="Lax",
        httponly=False,
    )
    return response


class BrandBoxLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True
    authentication_form = BrandBoxAuthenticationForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["show_welcome_back"] = (
            self.request.COOKIES.get(RETURNING_USER_COOKIE) == "1"
        )
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        return _mark_returning_user(response)


class BrandBoxLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if isinstance(response, HttpResponseRedirect):
            return _mark_returning_user(response)
        return response


class SignupView(View):
    template_name = "accounts/signup.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard:home")
        return render(request, self.template_name, {"form": SignupForm()})

    def post(self, request):
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return _mark_returning_user(redirect("dashboard:home"))
        return render(request, self.template_name, {"form": form})


class ForgotView(View):
    """UI placeholder — wire email reset later."""

    template_name = "accounts/forgot.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        return render(request, self.template_name, {"sent": True})


class BrandBoxPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("dashboard:settings")

    def form_valid(self, form):
        messages.success(self.request, "Your password was updated.")
        return super().form_valid(form)


class SocialOAuthStartView(View):
    """
    Entry point for Google / Apple / Facebook.
    UI is live; provider OAuth apps + callbacks wire in next.
    """

    def get(self, request, provider: str):
        label = SOCIAL_PROVIDERS.get(provider)
        next_path = request.GET.get("next", "")
        if not label:
            messages.error(request, "Unknown sign-in provider.")
            return redirect("accounts:login")

        messages.info(
            request,
            f"{label} sign-in is almost ready — connect your {label} app "
            "credentials in settings to enable it.",
        )
        if next_path.startswith("/signup"):
            return redirect("accounts:signup")
        return redirect("accounts:login")
