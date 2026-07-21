from django.urls import path

from .views import ContactView, HomeView, NewsletterSubscribeView, legal_page

app_name = "home"

urlpatterns = [
    path("", HomeView.as_view(), name="index"),
    path("contact/", ContactView.as_view(), name="contact"),
    path(
        "newsletter/",
        NewsletterSubscribeView.as_view(),
        name="newsletter",
    ),
    path("about/", legal_page, {"key": "about"}, name="about"),
    path("privacy/", legal_page, {"key": "privacy"}, name="privacy"),
    path("terms/", legal_page, {"key": "terms"}, name="terms"),
    path("refund/", legal_page, {"key": "refund"}, name="refund"),
]
