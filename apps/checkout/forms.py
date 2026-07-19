"""Checkout form — payment UI + account + policy agreement."""

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class CheckoutForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "name@company.com",
                "autocomplete": "email",
            }
        ),
    )
    cardholder = forms.CharField(
        max_length=200,
        label="Name on Card",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Alex Rivera",
                "autocomplete": "cc-name",
            }
        ),
    )
    card_number = forms.CharField(
        max_length=24,
        label="Card number",
        widget=forms.TextInput(
            attrs={
                "placeholder": "ACCT-000003",
                "autocomplete": "cc-number",
                "inputmode": "numeric",
            }
        ),
    )
    expiry = forms.CharField(
        max_length=7,
        label="Expiration date",
        widget=forms.TextInput(
            attrs={
                "placeholder": "MM / YY",
                "autocomplete": "cc-exp",
            }
        ),
    )
    cvc = forms.CharField(
        max_length=4,
        label="Security code",
        widget=forms.TextInput(
            attrs={
                "placeholder": "CVC",
                "autocomplete": "cc-csc",
                "inputmode": "numeric",
            }
        ),
    )
    country = forms.ChoiceField(
        label="Country",
        choices=[
            ("IN", "India"),
            ("US", "United States"),
            ("GB", "United Kingdom"),
            ("CA", "Canada"),
            ("AU", "Australia"),
            ("AE", "United Arab Emirates"),
            ("SG", "Singapore"),
            ("OTHER", "Other"),
        ],
    )
    password = forms.CharField(
        label="Password",
        required=False,
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Create a password for your BrandBox account",
                "autocomplete": "new-password",
            }
        ),
        help_text="Required to create your account if you don’t have one yet.",
    )
    agree_terms = forms.BooleanField(
        label="I agree to the Terms of Service and Privacy Policy",
        required=True,
        error_messages={
            "required": "You must agree to the Terms of Service and Privacy Policy to continue.",
        },
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user is not None and user.is_authenticated:
            self.fields["email"].initial = user.email or user.username
            self.fields["password"].required = False
            self.fields["password"].widget = forms.HiddenInput()
        else:
            self.fields["password"].required = True

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_password(self):
        password = self.cleaned_data.get("password") or ""
        if self.user is not None and self.user.is_authenticated:
            return password
        if not password:
            raise forms.ValidationError("Enter a password to create or access your account.")
        # Only validate strength when creating a new account (checked in clean()).
        return password

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        if not email:
            return cleaned

        if self.user is not None and self.user.is_authenticated:
            return cleaned

        existing = (
            User.objects.filter(email__iexact=email).first()
            or User.objects.filter(username__iexact=email).first()
        )
        if existing:
            auth_user = authenticate(username=existing.username, password=password)
            if auth_user is None:
                self.add_error(
                    "password",
                    "An account with this email already exists. Enter the correct password, or sign in first.",
                )
            else:
                cleaned["existing_user"] = auth_user
        else:
            from django.core.exceptions import ValidationError as DjangoValidationError

            try:
                validate_password(password)
            except DjangoValidationError as exc:
                self.add_error("password", exc)
            cleaned["existing_user"] = None

        return cleaned

    def split_name(self):
        parts = self.cleaned_data["cardholder"].strip().split(None, 1)
        first = parts[0] if parts else ""
        last = parts[1] if len(parts) > 1 else ""
        return first[:150], last[:150]

    def resolve_user(self):
        """Return authenticated user, existing user, or newly created user."""
        if self.user is not None and self.user.is_authenticated:
            return self.user, False

        existing = self.cleaned_data.get("existing_user")
        if existing is not None:
            return existing, False

        email = self.cleaned_data["email"]
        first, last = self.split_name()
        user = User(
            username=email,
            email=email,
            first_name=first,
            last_name=last,
        )
        user.set_password(self.cleaned_data["password"])
        user.save()
        return user, True
