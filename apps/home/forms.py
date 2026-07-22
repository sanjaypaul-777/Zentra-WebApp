"""Public contact, newsletter, and affiliate application forms."""

from django import forms

from .models import AffiliateApplication, ContactMessage, NewsletterSubscriber

HONEYPOT_ATTRS = {
    "autocomplete": "off",
    "tabindex": "-1",
    "aria-hidden": "true",
    "class": "brandbox-honeypot__field",
}


class HoneypotMixin:
    """Hidden `website` field — bots fill it; humans leave it empty."""

    def is_honeypot_triggered(self) -> bool:
        return bool((self.cleaned_data.get("website") or "").strip())


class ContactForm(HoneypotMixin, forms.ModelForm):
    website = forms.CharField(
        required=False,
        label="Website",
        widget=forms.TextInput(attrs=HONEYPOT_ATTRS),
    )

    class Meta:
        model = ContactMessage
        fields = ("name", "email", "subject", "message")
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Your name",
                    "autocomplete": "name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "name@company.com",
                    "autocomplete": "email",
                }
            ),
            "subject": forms.TextInput(
                attrs={
                    "placeholder": "How can we help?",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "placeholder": "Tell us a bit more…",
                    "rows": 5,
                }
            ),
        }

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_subject(self):
        return self.cleaned_data["subject"].strip()

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Please write at least a short message.")
        return message


class NewsletterForm(HoneypotMixin, forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Email address",
                "autocomplete": "email",
                "class": "brandbox-footer__email",
            }
        ),
    )
    website = forms.CharField(
        required=False,
        label="Website",
        widget=forms.TextInput(attrs=HONEYPOT_ATTRS),
    )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def save(self):
        """Create subscriber if new; ignore duplicates."""
        email = self.cleaned_data["email"]
        subscriber, _created = NewsletterSubscriber.objects.get_or_create(
            email=email,
            defaults={"is_active": True},
        )
        if not subscriber.is_active:
            subscriber.is_active = True
            subscriber.save(update_fields=["is_active"])
        return subscriber


class AffiliateApplicationForm(HoneypotMixin, forms.ModelForm):
    website = forms.CharField(
        required=False,
        label="Website",
        widget=forms.TextInput(attrs=HONEYPOT_ATTRS),
    )
    has_affiliate_experience = forms.TypedChoiceField(
        label="Have you done affiliate marketing before?",
        choices=((True, "Yes"), (False, "No")),
        coerce=lambda v: v in (True, "True", "true", "1", 1),
        widget=forms.RadioSelect,
        initial=False,
    )
    agree_terms = forms.BooleanField(
        required=True,
        label="I agree to the Terms of Service and Privacy Policy",
        error_messages={
            "required": (
                "Please agree to the Terms of Service and Privacy Policy "
                "to submit your application."
            ),
        },
    )

    class Meta:
        model = AffiliateApplication
        fields = (
            "name",
            "email",
            "current_activity",
            "activity_other",
            "primary_platform",
            "promo_url",
            "audience_size",
            "content_focus",
            "promotion_plan",
            "promotion_other",
            "has_affiliate_experience",
            "notes",
        )
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Your full name", "autocomplete": "name"}
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "name@company.com",
                    "autocomplete": "email",
                }
            ),
            "current_activity": forms.Select(
                attrs={"data-aff-other-trigger": "activity"}
            ),
            "activity_other": forms.TextInput(
                attrs={
                    "placeholder": "e.g. Podcast host, YouTube editor…",
                    "autocomplete": "organization-title",
                }
            ),
            "primary_platform": forms.Select(),
            "promo_url": forms.URLInput(
                attrs={
                    "placeholder": "https://…",
                    "autocomplete": "url",
                }
            ),
            "audience_size": forms.Select(),
            "content_focus": forms.Select(),
            "promotion_plan": forms.Select(
                attrs={"data-aff-other-trigger": "promotion"}
            ),
            "promotion_other": forms.Textarea(
                attrs={
                    "placeholder": (
                        "Describe how you’ll promote BrandBox "
                        "(channels, content type, cadence)…"
                    ),
                    "rows": 4,
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "placeholder": (
                        "Share why you’re a strong fit, who your audience is, "
                        "and how you’ll promote BrandBox…"
                    ),
                    "rows": 5,
                    "required": True,
                }
            ),
        }
        labels = {
            "name": "Full name",
            "email": "Email",
            "current_activity": "What is your current activity?",
            "activity_other": "Please specify your activity",
            "primary_platform": "Where's your main audience?",
            "promo_url": "Link to your profile or site",
            "audience_size": "About how large is your audience?",
            "content_focus": "What's your content mainly about?",
            "promotion_plan": "How do you plan to promote BrandBox?",
            "promotion_other": "Describe your promotion strategy",
            "notes": (
                "Why are you a fit for this program? "
                "Tell us your strategy and why you’re confident you’ll succeed"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["notes"].required = True
        self.fields["notes"].error_messages["required"] = (
            "Please explain why you’re a fit and how you plan to promote BrandBox."
        )
        self.fields["promotion_other"].required = False
        self.fields["activity_other"].required = False

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_activity_other(self):
        return (self.cleaned_data.get("activity_other") or "").strip()

    def clean_promotion_other(self):
        return (self.cleaned_data.get("promotion_other") or "").strip()

    def clean_notes(self):
        notes = (self.cleaned_data.get("notes") or "").strip()
        if len(notes) < 40:
            raise forms.ValidationError(
                "Please write a bit more — include your audience, strategy, "
                "and why you’re confident you’ll succeed (at least a few sentences)."
            )
        return notes

    def clean(self):
        cleaned = super().clean()

        activity = cleaned.get("current_activity")
        activity_other = (cleaned.get("activity_other") or "").strip()
        if activity == AffiliateApplication.CurrentActivity.OTHER:
            if len(activity_other) < 2:
                self.add_error(
                    "activity_other",
                    "Please tell us what your current activity is.",
                )
        else:
            cleaned["activity_other"] = ""

        plan = cleaned.get("promotion_plan")
        other = (cleaned.get("promotion_other") or "").strip()
        if plan == AffiliateApplication.PromotionPlan.OTHER:
            if len(other) < 20:
                self.add_error(
                    "promotion_other",
                    "Please describe your promotion strategy "
                    "(at least a couple of sentences).",
                )
        else:
            cleaned["promotion_other"] = ""
        return cleaned
