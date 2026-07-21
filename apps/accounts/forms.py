"""Account forms."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class BrandBoxAuthenticationForm(AuthenticationForm):
    """Login with email or username + password."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": _(
            "Please enter a correct email or username and password."
        ),
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        self.fields["username"].label = "Email or username"
        self.fields["username"].widget.attrs.update(
            {
                "placeholder": "Email or username",
                "autocomplete": "username",
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "placeholder": "••••••••",
                "autocomplete": "current-password",
            }
        )

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username is not None and password is not None:
            login_id = username.strip()
            user = (
                User.objects.filter(username__iexact=login_id).first()
                or User.objects.filter(email__iexact=login_id).first()
            )
            if user is not None:
                # ModelBackend authenticates against USERNAME_FIELD
                self.cleaned_data["username"] = user.get_username()

        return super().clean()


class SignupForm(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        label="First name",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Alex",
                "autocomplete": "given-name",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        label="Last name",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Rivera",
                "autocomplete": "family-name",
            }
        ),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "name@company.com",
                "autocomplete": "email",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "••••••••",
                "autocomplete": "new-password",
            }
        ),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def save(self):
        email = self.cleaned_data["email"]
        user = User(
            username=email,
            email=email,
            first_name=self.cleaned_data["first_name"].strip(),
            last_name=self.cleaned_data["last_name"].strip(),
        )
        user.set_password(self.cleaned_data["password"])
        user.save()
        return user


class ProfileForm(forms.Form):
    """Customer profile — Settings → Account (same MerchantProfile fields as onboarding)."""

    name = forms.CharField(
        max_length=255,
        label="Name",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Alex Rivera",
                "autocomplete": "name",
            }
        ),
    )
    username = forms.CharField(
        max_length=150,
        label="Username",
        help_text="Used with your password to sign in.",
        widget=forms.TextInput(
            attrs={
                "placeholder": "alexrivera",
                "autocomplete": "username",
            }
        ),
    )
    company = forms.CharField(
        max_length=255,
        required=False,
        label="Company (Optional)",
        widget=forms.TextInput(
            attrs={
                "placeholder": "BrandBox Co.",
                "autocomplete": "organization",
            }
        ),
    )
    address_country = forms.CharField(
        max_length=128,
        required=False,
        label="Country",
        widget=forms.HiddenInput(attrs={"data-address-country": "1"}),
    )
    address_street = forms.CharField(
        max_length=255,
        required=False,
        label="Street address",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "data-address-street": "1",
                "placeholder": "Start typing an address",
            }
        ),
    )
    address_state = forms.CharField(
        max_length=128,
        required=False,
        label="State / Province",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "data-address-state": "1",
                "placeholder": "Search state or province",
            }
        ),
    )
    address_city = forms.CharField(
        max_length=128,
        required=False,
        label="City",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "address-level2",
                "data-address-city": "1",
                "placeholder": "City",
            }
        ),
    )
    address_zip = forms.CharField(
        max_length=32,
        required=False,
        label="ZIP / Postal code",
        widget=forms.TextInput(
            attrs={"autocomplete": "postal-code", "data-address-zip": "1"}
        ),
    )
    email = forms.EmailField(
        label="Email",
        help_text="Used with your password to sign in.",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "name@company.com",
                "autocomplete": "email",
            }
        ),
    )
    phone = forms.CharField(
        max_length=64,
        required=False,
        label="Phone",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Phone number",
                "autocomplete": "tel",
                "inputmode": "tel",
                "data-address-phone": "1",
            }
        ),
    )
    vertical_industry = forms.ChoiceField(
        required=False,
        label="Vertical / Industry",
        choices=[("", "—")],
    )
    vertical_other = forms.CharField(
        max_length=255,
        required=False,
        label="Other industry",
    )
    desired_niche = forms.ChoiceField(
        required=False,
        label="Desired Niche",
        choices=[("", "—")],
    )
    bio = forms.CharField(
        required=False,
        label="Bio",
        widget=forms.Textarea(
            attrs={
                "placeholder": "Short bio about you or your brand",
                "rows": 4,
            }
        ),
    )

    def __init__(self, *args, user=None, profile=None, geo_country=None, **kwargs):
        from apps.dashboard.models import MerchantProfile

        self.user = user
        self.profile = profile
        self.geo_country = geo_country or {}
        super().__init__(*args, **kwargs)
        self.fields["vertical_industry"].choices = [("", "—")] + list(
            MerchantProfile.Vertical.choices
        )
        self.fields["desired_niche"].choices = [("", "—")] + list(
            MerchantProfile.Niche.choices
        )
        locked_country = (self.geo_country.get("name") or "").strip()
        if not locked_country and profile is not None:
            locked_country = (profile.address_country or "").strip()
        self.fields["address_country"].initial = locked_country
        if user is not None and not self.is_bound:
            full = ""
            if profile is not None and profile.full_name:
                full = profile.full_name
            else:
                full = (user.get_full_name() or "").strip() or user.first_name or ""
            self.fields["name"].initial = full
            self.fields["username"].initial = user.username or ""
            self.fields["email"].initial = user.email or ""
        if profile is not None and not self.is_bound:
            self.fields["company"].initial = profile.company or ""
            self.fields["address_street"].initial = profile.address_street
            self.fields["address_city"].initial = profile.address_city
            self.fields["address_state"].initial = profile.address_state
            self.fields["address_zip"].initial = profile.address_zip
            if profile.address_country:
                self.fields["address_country"].initial = profile.address_country
            from apps.dashboard.geo import country_code_for_name, format_phone_display

            cc = country_code_for_name(
                self.fields["address_country"].initial or ""
            ) or (self.geo_country.get("code") or "")
            self.fields["phone"].initial = format_phone_display(
                profile.phone, country_code=cc
            ) or profile.phone
            self.fields["vertical_industry"].initial = profile.vertical_industry
            self.fields["vertical_other"].initial = profile.vertical_other
            self.fields["desired_niche"].initial = profile.desired_niche
            self.fields["bio"].initial = profile.bio

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if not username:
            raise forms.ValidationError("Enter a username.")
        qs = User.objects.filter(username__iexact=username)
        if self.user is not None:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError("That username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.user is not None:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_phone(self):
        from apps.dashboard.geo import country_code_for_name, normalize_phone

        raw = (self.cleaned_data.get("phone") or "").strip()
        if not raw:
            return ""
        country = (self.cleaned_data.get("address_country") or "").strip()
        if not country:
            country = (self.geo_country.get("name") or "").strip()
        code = country_code_for_name(country) or (self.geo_country.get("code") or "")
        return normalize_phone(raw, country_code=code)

    def clean(self):
        from apps.dashboard.models import MerchantProfile

        cleaned = super().clean()
        if cleaned.get("vertical_industry") == MerchantProfile.Vertical.OTHER:
            if not (cleaned.get("vertical_other") or "").strip():
                self.add_error("vertical_other", "Please specify your industry.")
        return cleaned

    def save(self):
        from apps.dashboard.models import MerchantProfile

        user = self.user
        profile = self.profile or MerchantProfile.for_user(user)

        name = self.cleaned_data["name"].strip()
        parts = name.split(None, 1)
        user.first_name = parts[0] if parts else ""
        user.last_name = parts[1] if len(parts) > 1 else ""
        user.username = self.cleaned_data["username"]
        user.email = self.cleaned_data["email"]
        user.save(update_fields=["first_name", "last_name", "username", "email"])

        profile.full_name = name
        profile.company = self.cleaned_data.get("company", "").strip()
        profile.address_street = self.cleaned_data.get("address_street", "").strip()
        profile.address_city = self.cleaned_data.get("address_city", "").strip()
        profile.address_state = self.cleaned_data.get("address_state", "").strip()
        profile.address_zip = self.cleaned_data.get("address_zip", "").strip()
        profile.address_country = self.cleaned_data.get("address_country", "").strip()
        profile.sync_address_text()
        profile.phone = self.cleaned_data.get("phone", "").strip()
        profile.vertical_industry = self.cleaned_data.get("vertical_industry", "").strip()
        profile.vertical_other = self.cleaned_data.get("vertical_other", "").strip()
        profile.desired_niche = self.cleaned_data.get("desired_niche", "").strip()
        profile.bio = self.cleaned_data.get("bio", "").strip()
        profile.save()
        return profile
