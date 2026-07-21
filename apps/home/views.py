"""
Home — marketing landing, contact, newsletter, legal pages (public).
"""

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from .forms import ContactForm, NewsletterForm
from .models import LegalPage


class HomeView(TemplateView):
    template_name = "home/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["newsletter_form"] = NewsletterForm()
        ctx["show_newsletter_thanks"] = (
            self.request.GET.get("newsletter") == "thanks"
        )
        return ctx


class NewsletterSubscribeView(View):
    """Footer newsletter — save email, skip duplicates, thank-you redirect."""

    def post(self, request):
        form = NewsletterForm(request.POST)
        thanks = reverse("home:index") + "?newsletter=thanks"
        if not form.is_valid():
            messages.error(request, "Enter a valid email address.")
            return redirect("home:index")

        # Honeypot filled → silent fake success (no DB write)
        if form.is_honeypot_triggered():
            return HttpResponseRedirect(thanks)

        form.save()
        return HttpResponseRedirect(thanks)

    def get(self, request):
        return redirect("home:index")


class ContactView(FormView):
    template_name = "home/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("home:contact")

    def form_valid(self, form):
        # Honeypot filled → silent fake success (no DB / no email)
        if form.is_honeypot_triggered():
            messages.success(
                self.request,
                "Message sent. We’ll get back to you soon.",
            )
            return HttpResponseRedirect(self.get_success_url())

        message = form.save()
        self._send_notification(message)
        messages.success(
            self.request,
            "Message sent. We’ll get back to you soon.",
        )
        return super().form_valid(form)

    def _send_notification(self, message):
        inbox = getattr(
            settings,
            "CONTACT_NOTIFY_EMAIL",
            "help@brandbox.co",
        )
        body = (
            f"New contact form message\n\n"
            f"Name: {message.name}\n"
            f"Email: {message.email}\n"
            f"Subject: {message.subject}\n\n"
            f"{message.message}\n"
        )
        email = EmailMessage(
            subject=f"[BrandBox Contact] {message.subject}",
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[inbox],
            reply_to=[message.email],
        )
        email.send(fail_silently=True)


def legal_page(request, key: str):
    """Public About / Privacy / Terms / Refund page (content from admin)."""
    page = get_object_or_404(LegalPage, key=key)
    return render(
        request,
        "home/legal.html",
        {
            "page": page,
            "page_available": page.is_published and bool((page.body or "").strip()),
        },
    )
