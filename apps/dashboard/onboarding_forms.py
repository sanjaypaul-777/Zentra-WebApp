"""Onboarding step forms — saves onto MerchantProfile (+ User email/name)."""

from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model

from .models import MerchantProfile

User = get_user_model()

_INPUT = {"class": "ob-input"}
_TEXTAREA = {"class": "ob-input", "rows": 4}


class OnboardingStep1Form(forms.Form):
    full_name = forms.CharField(max_length=255, label="Full Name", widget=forms.TextInput(attrs={**_INPUT, "autocomplete": "name"}))
    company = forms.CharField(
        max_length=255,
        required=False,
        label="Company (if applicable)",
        widget=forms.TextInput(attrs={**_INPUT, "autocomplete": "organization"}),
    )
    address_country = forms.CharField(
        max_length=128,
        label="Country",
        widget=forms.HiddenInput(attrs={"data-address-country": "1"}),
    )
    address_street = forms.CharField(
        max_length=255,
        label="Street address",
        widget=forms.TextInput(
            attrs={
                **_INPUT,
                "autocomplete": "off",
                "placeholder": "Start typing an address",
                "data-address-street": "1",
            }
        ),
    )
    address_state = forms.CharField(
        max_length=128,
        label="State / Province",
        widget=forms.TextInput(
            attrs={
                **_INPUT,
                "autocomplete": "off",
                "placeholder": "Search state or province",
                "data-address-state": "1",
            }
        ),
    )
    address_city = forms.CharField(
        max_length=128,
        label="City",
        widget=forms.TextInput(
            attrs={
                **_INPUT,
                "autocomplete": "address-level2",
                "placeholder": "City",
                "data-address-city": "1",
            }
        ),
    )
    address_zip = forms.CharField(
        max_length=32,
        label="ZIP / Postal code",
        widget=forms.TextInput(
            attrs={
                **_INPUT,
                "autocomplete": "postal-code",
                "data-address-zip": "1",
            }
        ),
    )
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={**_INPUT, "autocomplete": "email"}))
    phone = forms.CharField(
        max_length=64,
        label="Phone",
        widget=forms.TextInput(
            attrs={
                **_INPUT,
                "autocomplete": "tel",
                "inputmode": "tel",
                "data-address-phone": "1",
                "placeholder": "Phone number",
            }
        ),
    )

    def __init__(self, *args, user=None, profile=None, geo_country=None, **kwargs):
        self.user = user
        self.profile = profile
        self.geo_country = geo_country or {}
        super().__init__(*args, **kwargs)
        suggested = (self.geo_country.get("name") or "").strip()
        if not suggested and profile is not None:
            suggested = (profile.address_country or "").strip()
        self.fields["address_country"].initial = suggested
        if user is not None and profile is not None and not self.is_bound:
            self.fields["full_name"].initial = (
                profile.full_name
                or (user.get_full_name() or "").strip()
                or user.first_name
                or ""
            )
            self.fields["company"].initial = profile.company or ""
            self.fields["address_street"].initial = profile.address_street
            self.fields["address_city"].initial = profile.address_city
            self.fields["address_state"].initial = profile.address_state
            self.fields["address_zip"].initial = profile.address_zip
            self.fields["email"].initial = user.email or ""
            from .geo import country_code_for_name, format_phone_display

            cc = country_code_for_name(suggested) or (self.geo_country.get("code") or "")
            self.fields["phone"].initial = format_phone_display(
                profile.phone, country_code=cc
            ) or profile.phone
            if suggested:
                self.fields["address_country"].initial = suggested

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        qs = User.objects.filter(email__iexact=email)
        if self.user:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError("That email is already in use.")
        return email

    def clean_phone(self):
        from .geo import country_code_for_name, normalize_phone

        raw = (self.cleaned_data.get("phone") or "").strip()
        if not raw:
            raise forms.ValidationError("Enter a phone number.")
        country = (self.cleaned_data.get("address_country") or "").strip()
        if not country:
            country = (self.geo_country.get("name") or "").strip()
        code = country_code_for_name(country) or (self.geo_country.get("code") or "")
        return normalize_phone(raw, country_code=code)

    def save(self):
        p = self.profile
        p.full_name = self.cleaned_data["full_name"].strip()
        p.company = self.cleaned_data.get("company") or ""
        p.address_street = self.cleaned_data["address_street"].strip()
        p.address_city = self.cleaned_data["address_city"].strip()
        p.address_state = self.cleaned_data["address_state"].strip()
        p.address_zip = self.cleaned_data["address_zip"].strip()
        p.address_country = self.cleaned_data["address_country"].strip()
        p.phone = self.cleaned_data["phone"].strip()
        p.sync_address_text()
        p.onboarding_step = max(p.onboarding_step, 2)
        p.save()
        p.sync_user_name()
        self.user.email = self.cleaned_data["email"]
        self.user.save(update_fields=["email"])
        return p


class OnboardingStep2Form(forms.Form):
    vertical_industry = forms.ChoiceField(choices=MerchantProfile.Vertical.choices)
    vertical_other = forms.CharField(max_length=255, required=False)
    desired_niche = forms.ChoiceField(choices=MerchantProfile.Niche.choices)
    has_existing_shopify_store = forms.TypedChoiceField(
        choices=(("true", "Yes"), ("false", "No")),
        coerce=lambda v: v == "true",
    )
    current_revenue = forms.ChoiceField(choices=MerchantProfile.Revenue.choices)

    def __init__(self, *args, profile=None, **kwargs):
        self.profile = profile
        super().__init__(*args, **kwargs)
        if profile is not None and not self.is_bound:
            self.fields["vertical_industry"].initial = profile.vertical_industry
            self.fields["vertical_other"].initial = profile.vertical_other
            self.fields["desired_niche"].initial = profile.desired_niche
            if profile.has_existing_shopify_store is not None:
                self.fields["has_existing_shopify_store"].initial = (
                    "true" if profile.has_existing_shopify_store else "false"
                )
            self.fields["current_revenue"].initial = profile.current_revenue

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("vertical_industry") == MerchantProfile.Vertical.OTHER:
            other = (cleaned.get("vertical_other") or "").strip()
            if not other:
                self.add_error("vertical_other", "Please specify your industry.")
            cleaned["vertical_other"] = other
        else:
            cleaned["vertical_other"] = ""
        return cleaned

    def save(self):
        p = self.profile
        p.vertical_industry = self.cleaned_data["vertical_industry"]
        p.vertical_other = self.cleaned_data.get("vertical_other") or ""
        p.desired_niche = self.cleaned_data["desired_niche"]
        p.has_existing_shopify_store = self.cleaned_data["has_existing_shopify_store"]
        p.current_revenue = self.cleaned_data["current_revenue"]
        p.onboarding_step = max(p.onboarding_step, 3)
        p.save()
        return p


class OnboardingStep3Form(forms.Form):
    ecommerce_goal = forms.ChoiceField(choices=MerchantProfile.EcommerceGoal.choices)
    previous_experience = forms.ChoiceField(choices=MerchantProfile.PreviousExperience.choices)
    success_definition = forms.ChoiceField(choices=MerchantProfile.SuccessDefinition.choices)

    def __init__(self, *args, profile=None, **kwargs):
        self.profile = profile
        super().__init__(*args, **kwargs)
        if profile is not None and not self.is_bound:
            self.fields["ecommerce_goal"].initial = profile.ecommerce_goal
            self.fields["previous_experience"].initial = profile.previous_experience
            self.fields["success_definition"].initial = profile.success_definition

    def save(self):
        p = self.profile
        p.ecommerce_goal = self.cleaned_data["ecommerce_goal"]
        p.previous_experience = self.cleaned_data["previous_experience"]
        p.success_definition = self.cleaned_data["success_definition"]
        p.onboarding_step = max(p.onboarding_step, 4)
        p.save()
        return p


class OnboardingStep4Form(forms.Form):
    weekly_time_investment = forms.ChoiceField(choices=MerchantProfile.WeeklyTime.choices)
    ad_budget = forms.ChoiceField(choices=MerchantProfile.AdBudget.choices)
    biggest_challenges = forms.MultipleChoiceField(
        choices=MerchantProfile.CHALLENGE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    biggest_challenges_other = forms.CharField(
        max_length=255,
        required=False,
        label="Please specify",
        widget=forms.TextInput(
            attrs={
                **_INPUT,
                "placeholder": "Describe your other challenge",
            }
        ),
    )
    additional_comments = forms.CharField(
        required=False,
        label="Any additional comments or special requests (optional)",
        widget=forms.Textarea(attrs={**_TEXTAREA, "placeholder": "Optional notes for your coach"}),
    )

    def __init__(self, *args, profile=None, **kwargs):
        self.profile = profile
        super().__init__(*args, **kwargs)
        if profile is not None and not self.is_bound:
            self.fields["weekly_time_investment"].initial = profile.weekly_time_investment
            self.fields["ad_budget"].initial = profile.ad_budget
            self.fields["biggest_challenges"].initial = profile.biggest_challenges or []
            self.fields["biggest_challenges_other"].initial = profile.biggest_challenges_other or ""
            self.fields["additional_comments"].initial = profile.additional_comments or ""

    def clean(self):
        cleaned = super().clean()
        challenges = cleaned.get("biggest_challenges") or []
        other = (cleaned.get("biggest_challenges_other") or "").strip()
        if "other" in challenges and not other:
            self.add_error("biggest_challenges_other", "Please specify your other challenge.")
        if "other" not in challenges:
            cleaned["biggest_challenges_other"] = ""
        else:
            cleaned["biggest_challenges_other"] = other
        return cleaned

    def save(self, *, complete: bool = False):
        p = self.profile
        p.weekly_time_investment = self.cleaned_data["weekly_time_investment"]
        p.ad_budget = self.cleaned_data["ad_budget"]
        p.biggest_challenges = list(self.cleaned_data["biggest_challenges"])
        p.biggest_challenges_other = self.cleaned_data.get("biggest_challenges_other") or ""
        p.additional_comments = self.cleaned_data.get("additional_comments") or ""
        if complete:
            p.onboarding_completed = True
            p.onboarding_step = 4
        p.save()
        return p
