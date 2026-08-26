from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent


SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="127.0.0.1,localhost",
    cast=Csv(),
)

# Full scheme+host origins allowed to submit unsafe (POST/PUT/etc) requests
# — needed for django-admin logins in production, where Caddy terminates
# TLS and this is the https:// address the browser actually sees.
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="",
    cast=Csv(),
)

# The publicly reachable origin for this backend — used to build the
# webhook callback URL sent to the payment gateway. Deliberately NOT
# derived from the incoming request's Host header: in local dev the
# browser talks to the backend directly on localhost, bypassing whatever
# tunnel (ngrok, etc.) actually exposes it to the internet, so
# request.build_absolute_uri() would hand the gateway an unreachable
# localhost URL. Leave blank in a normal single-domain deployment where
# the request's own host is already correct.
PUBLIC_BASE_URL = config("PUBLIC_BASE_URL", default="").rstrip("/")

# The public site's URL — used for links inside outgoing emails (e.g. the
# "track your registration" button).
PUBLIC_SITE_URL = config("PUBLIC_SITE_URL", default="").rstrip("/")

# Shown in the footer of outgoing emails.
EVENT_CONTACT_PHONE = config("EVENT_CONTACT_PHONE", default="")
EVENT_CONTACT_EMAIL = config("EVENT_CONTACT_EMAIL", default="")

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    # This project
    "apps.common",
    "apps.accounts",
    "apps.registrations",
    "apps.vendors",
    "apps.payments",
    "apps.notifications",
]

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lusaka"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # Safer default: endpoints must opt IN to being public (AllowAny)
    # rather than opt out of requiring auth. The public registration/
    # payment/lookup endpoints set permission_classes = [AllowAny]
    # explicitly.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173,http://localhost:5174",
    cast=Csv(),
)


# ---------------------------------------------------------------------------
# Email (registration + payment notifications)
# ---------------------------------------------------------------------------
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)


# ---------------------------------------------------------------------------
# SMS (pluggable — no provider wired up yet, see apps/notifications/sms.py)
# ---------------------------------------------------------------------------
SMS_BACKEND = config(
    "SMS_BACKEND",
    # "console" just logs the message instead of sending it, so the rest
    # of the notification pipeline (and the admin's notification log)
    # works end-to-end before a real SMS provider is wired up.
    default="console",
)
SMS_SENDER_ID = config("SMS_SENDER_ID", default="SiavongaRun")

# Africa's Talking is the most common SMS provider for Zambia, so the
# client is stubbed for it — fill these in and set
# SMS_BACKEND=africastalking once an account exists.
AFRICASTALKING_USERNAME = config("AFRICASTALKING_USERNAME", default="")
AFRICASTALKING_API_KEY = config("AFRICASTALKING_API_KEY", default="")


# ---------------------------------------------------------------------------
# Payment gateway
# ---------------------------------------------------------------------------
# "console" (default) simulates mobile money / card collections locally —
# no credentials needed, a payment auto-settles a few seconds after being
# initiated so the whole registration -> pay -> confirmed flow can be
# exercised end-to-end before Lipila credentials exist. Switch to "lipila"
# once real sandbox/production keys are available below. See
# apps/payments/gateways/.
PAYMENT_GATEWAY = config("PAYMENT_GATEWAY", default="console")

# NOTE: Lipila's public docs describe two API surfaces (a legacy
# "collections" API under /api/v1/collections/... using an x-api-key
# header, and a newer "transactions" API using a Bearer secret key). The
# client in apps/payments/gateways/lipila/ is built against the
# x-api-key / /api/v1/... style. If your Lipila dashboard issued a
# "secret key" instead, or your account is on the newer surface, update
# apps/payments/gateways/lipila/client.py to match your dashboard.
LIPILA_ENVIRONMENT = config("LIPILA_ENVIRONMENT", default="sandbox")
LIPILA_SANDBOX_BASE_URL = config("LIPILA_SANDBOX_BASE_URL", default="https://api.lipila.dev")
LIPILA_PRODUCTION_BASE_URL = config("LIPILA_PRODUCTION_BASE_URL", default="https://blz.lipila.io")
LIPILA_SANDBOX_API_KEY = config("LIPILA_SANDBOX_API_KEY", default="")
LIPILA_PRODUCTION_API_KEY = config("LIPILA_PRODUCTION_API_KEY", default="")
LIPILA_WEBHOOK_SECRET = config("LIPILA_WEBHOOK_SECRET", default="")


# ---------------------------------------------------------------------------
# Bank account (for the "Bank Transfer" payment method)
# ---------------------------------------------------------------------------
# Shown to runners who pay by bank transfer instead of mobile money/card —
# kept server-side (rather than hardcoded in the frontend) so it can be
# corrected/rotated without a frontend deploy.
BANK_ACCOUNT_DETAILS = {
    "bank_name": config("BANK_NAME", default=""),
    "account_name": config("BANK_ACCOUNT_NAME", default=""),
    "account_number": config("BANK_ACCOUNT_NUMBER", default=""),
    "branch": config("BANK_BRANCH", default=""),
    "sort_code": config("BANK_SORT_CODE", default=""),
    "swift_code": config("BANK_SWIFT_CODE", default=""),
}


# ---------------------------------------------------------------------------
# This event
# ---------------------------------------------------------------------------
EVENT_NAME = config("EVENT_NAME", default="Siavonga Independence Run 2026")
EVENT_DATE = config("EVENT_DATE", default="2026-10-24")
EVENT_LOCATION = config("EVENT_LOCATION", default="Lakeshore, Siavonga, Lake Kariba")
