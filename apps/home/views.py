"""
Home — marketing landing, contact, newsletter, legal, affiliate (public).
"""

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from .forms import AffiliateApplicationForm, ContactForm, NewsletterForm
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


class AffiliateLandingView(TemplateView):
    template_name = "home/affiliate.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["newsletter_form"] = NewsletterForm()
        return ctx


class AffiliateRegisterView(FormView):
    """Public registration — not account signup; approved partners use /login/ later."""

    template_name = "home/affiliate_apply.html"
    form_class = AffiliateApplicationForm
    success_url = reverse_lazy("home:affiliate_register")

    def form_valid(self, form):
        if form.is_honeypot_triggered():
            messages.success(
                self.request,
                "Registration received. We’ll email you after review.",
            )
            return HttpResponseRedirect(self.get_success_url())

        application = form.save()
        self._send_notification(application)
        messages.success(
            self.request,
            "Registration received. We’ll email you after review.",
        )
        return super().form_valid(form)

    def _send_notification(self, application):
        inbox = getattr(
            settings,
            "CONTACT_NOTIFY_EMAIL",
            "help@brandbox.co",
        )
        body = (
            f"New affiliate registration\n\n"
            f"Name: {application.name}\n"
            f"Email: {application.email}\n"
            f"Activity: {application.get_current_activity_display()}"
            f"{(' — ' + application.activity_other) if application.activity_other else ''}\n"
            f"Platform: {application.get_primary_platform_display()}\n"
            f"Profile/site: {application.promo_url or '—'}\n"
            f"Audience: {application.get_audience_size_display()}\n"
            f"Content focus: {application.get_content_focus_display()}\n"
            f"Promotion plan: {application.get_promotion_plan_display()}\n"
            f"Other strategy: {application.promotion_other or '—'}\n"
            f"Prior affiliate experience: "
            f"{'Yes' if application.has_affiliate_experience else 'No'}\n\n"
            f"Notes:\n{application.notes or '—'}\n"
        )
        email = EmailMessage(
            subject=f"[BrandBox Affiliate] {application.name}",
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[inbox],
            reply_to=[application.email],
        )
        email.send(fail_silently=True)


def legal_page(request, key: str):
    """Public About / Privacy / Terms / Refund / Disclaimer (content from admin)."""
    page = get_object_or_404(LegalPage, key=key)
    return render(
        request,
        "home/legal.html",
        {
            "page": page,
            "page_available": page.is_published and bool((page.body or "").strip()),
        },
    )
