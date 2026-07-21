"""
Django settings for BrandBox-Web (marketing + dashboard).
Shopify OAuth / store engine stays in ../BrandBoxApp (Node).
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
)
# .env first, then .env.local wins (overwrite) for local secrets
environ.Env.read_env(BASE_DIR / ".env")
environ.Env.read_env(BASE_DIR / ".env.local", overwrite=True)
SECRET_KEY = env("SECRET_KEY", default="django-insecure-dev-only-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Feature apps
    "apps.home",
    "apps.accounts",
    "apps.dashboard",
    "apps.checkout",
    "apps.builder",
    "apps.catalog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "config.middleware.MaintenanceModeMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.dashboard.middleware.OnboardingRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.ErrorReferenceMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "config.context_processors.brandbox_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Local default: SQLite. Production: set DATABASE_URL to shared Postgres with BrandBox.
if env("DATABASE_URL", default=""):
    DATABASES = {"default": env.db("DATABASE_URL")}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "home:index"

# Email (console in local; set SMTP + CONTACT_NOTIFY_EMAIL in production)
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="help@brandbox.co")
CONTACT_NOTIFY_EMAIL = env("CONTACT_NOTIFY_EMAIL", default="help@brandbox.co")

# BrandBox product URLs
MARKETING_URL = env("MARKETING_URL", default="http://127.0.0.1:8000")
DASHBOARD_URL = env("DASHBOARD_URL", default="http://127.0.0.1:8000/dashboard/")
SHOPIFY_APP_URL = env("SHOPIFY_APP_URL", default="")
SHOPIFY_PARTNER_SIGNUP_URL = env(
    "SHOPIFY_PARTNER_SIGNUP_URL",
    default="https://www.shopify.com/free-trial",
)
# Shared secret for Django ↔ BrandBox Node install-status API
BRANDBOX_INTERNAL_API_SECRET = env("BRANDBOX_INTERNAL_API_SECRET", default="")
# DEBUG-only: allow niche step without live API (local UI work)
ALLOW_INSTALL_BYPASS = env.bool("ALLOW_INSTALL_BYPASS", default=False)
# Localhost / failed IP lookup fallback (ISO2)
GEO_FALLBACK_COUNTRY = env("GEO_FALLBACK_COUNTRY", default="US")
# Google Places Autocomplete (browser key; restrict by HTTP referrer in Cloud Console)
GOOGLE_PLACES_API_KEY = env("GOOGLE_PLACES_API_KEY", default="")

# Site-wide maintenance (DB-independent middleware)
MAINTENANCE_MODE = env.bool("MAINTENANCE_MODE", default=False)
MAINTENANCE_ETA = env("MAINTENANCE_ETA", default="")
STATUS_PAGE_URL = env("STATUS_PAGE_URL", default="")

# Celery (wire broker later — store builds run async via apps.builder)
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=CELERY_BROKER_URL)

# Product catalog scraper (dual-write: Google Sheet for Node + Django DB mirror)
CATALOG_SPREADSHEET_ID = env(
    "CATALOG_SPREADSHEET_ID",
    default="1RiqcsWpY0mDPMjh5gZ7RcDvQkVGwbAr9nHo54ENUTac",
)
CATALOG_SHEET_TAB = env("CATALOG_SHEET_TAB", default="Meta Ads Products")
CATALOG_SERVICE_ACCOUNT_FILE = env(
    "CATALOG_SERVICE_ACCOUNT_FILE",
    default=str(BASE_DIR / "secrets" / "google-sheets-sa.json"),
)
