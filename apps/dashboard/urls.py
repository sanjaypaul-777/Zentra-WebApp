from django.urls import include, path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_home, name="home"),
    # Wizard at /dashboard/builder/; job flow at /dashboard/builder/start|building|success/
    path("builder/", views.builder_page, name="builder"),
    path("builder/", include("apps.builder.urls")),
    path("product-hunter/", views.product_finder_page, name="product_hunter"),
    # Legacy URLs — redirect to Product Hunter
    path("product-finder/", views.winning_products_page, name="product_finder"),
    path("winning-products/", views.winning_products_page, name="winning_products"),
    path("imports/", views.imports_page, name="imports"),
    path("my-imports/", views.imports_page, name="my_imports"),
    path("api/imports/", views.api_imports_create, name="api_imports_create"),
    path(
        "api/imports/<str:import_id>/",
        views.api_import_detail,
        name="api_import_detail",
    ),
    path("stores/", views.stores_page, name="stores"),
    path("stores/<int:pk>/", views.store_detail_page, name="store_detail"),
    path("stores/<int:pk>/disconnect/", views.store_disconnect, name="store_disconnect"),
    path("schedule/", views.schedule_page, name="schedule"),
    path("schedule/book/", views.schedule_book, name="schedule_book"),
    path("coach/", views.coach_page, name="coach"),
    path("training/", views.training_page, name="training"),
    path("settings/", views.settings_page, name="settings"),
    path("settings/profile/", views.settings_profile_page, name="settings_profile"),
    path(
        "settings/notifications/",
        views.settings_notification_toggle,
        name="settings_notifications",
    ),
    path(
        "settings/default-niche/",
        views.settings_default_niche,
        name="settings_default_niche",
    ),
    path(
        "settings/delete-account/",
        views.settings_delete_account,
        name="settings_delete_account",
    ),
    path("upgrade/", views.upgrade_page, name="upgrade"),
    # Not-connected flow
    path("connect/", views.connect_page, name="connect"),
    path("connect/error/", views.connect_error_page, name="connect_error"),
    path("create-store/", views.create_store_page, name="create_store"),
    # Same-tab OAuth handoff (existing route — reused by Connect Section B)
    path("install/", views.install_app, name="install"),
    path("api/install-status/", views.install_status, name="install_status"),
]
