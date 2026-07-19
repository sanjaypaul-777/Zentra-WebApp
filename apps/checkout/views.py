"""
Checkout — public purchase UI (billing wiring later).
Creates a BrandBox account when the buyer is not logged in / has no account.
"""

from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views import View

from .forms import CheckoutForm


class CheckoutView(View):
    template_name = "checkout/index.html"

    def get(self, request):
        form = CheckoutForm(user=request.user)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = CheckoutForm(request.POST, user=request.user)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        user, created = form.resolve_user()
        if not request.user.is_authenticated:
            login(request, user)

        # Payment provider wiring comes later — UI success for now.
        return render(
            request,
            self.template_name,
            {
                "done": True,
                "account_created": created,
                "user": user,
            },
        )
