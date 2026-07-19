"""Public contact + newsletter forms (honeypot spam protection)."""

from django import forms

from .models import ContactMessage, NewsletterSubscriber

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
                "class": (
                    "bg-white/5 border border-outline-variant rounded-lg "
                    "px-4 py-2 w-full text-sm focus:border-primary outline-none"
                ),
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
