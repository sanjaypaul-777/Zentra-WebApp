from django.urls import path

from .views import (
    ForgotView,
    SignupView,
    SocialOAuthStartView,
    BrandBoxLoginView,
    BrandBoxLogoutView,
    BrandBoxPasswordChangeView,
)

app_name = "accounts"

urlpatterns = [
    path("login/", BrandBoxLoginView.as_view(), name="login"),
    path("signup/", SignupView.as_view(), name="signup"),
    path("logout/", BrandBoxLogoutView.as_view(), name="logout"),
    path("forgot/", ForgotView.as_view(), name="forgot"),
    path("password/change/", BrandBoxPasswordChangeView.as_view(), name="password_change"),
    path("oauth/<str:provider>/", SocialOAuthStartView.as_view(), name="oauth"),
]
