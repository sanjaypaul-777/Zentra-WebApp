from django.urls import path

from . import views

app_name = "help"

urlpatterns = [
    path("", views.help_home, name="home"),
    path("api/suggest/", views.help_api_suggest, name="api_suggest"),
    path(
        "<slug:category_slug>/",
        views.help_category,
        name="category",
    ),
    path(
        "<slug:category_slug>/<slug:article_slug>/",
        views.help_article,
        name="article",
    ),
    path(
        "<slug:category_slug>/<slug:article_slug>/feedback/",
        views.help_feedback,
        name="feedback",
    ),
]
