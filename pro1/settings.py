import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-farmer-support-project"
)

# Use DEBUG=True locally (default). Vercel sets DJANGO_DEBUG=False for production.
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".vercel.app",
]

# ---------------------------------------------------------------------------
# CSRF & Security – Required for Vercel HTTPS proxy
# ---------------------------------------------------------------------------
CSRF_TRUSTED_ORIGINS = [
    "https://farmer-support-agriculture-portal.vercel.app",
    "https://*.vercel.app",
]

# Tell Django the real protocol is HTTPS (Vercel terminates TLS and forwards
# X-Forwarded-Proto: https to the backend)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Trust the Host header forwarded by Vercel's reverse proxy so that
# Django's CSRF referer-check uses the correct origin.
USE_X_FORWARDED_HOST = True

# Cookies must be sent only over HTTPS (production only – disable locally so HTTP works)
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

# SameSite=Lax: cookie is included in top-level form POSTs from same origin.
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

# Keep CSRF cookie readable by JS (needed if any fetch() POST is ever added)
CSRF_COOKIE_HTTPONLY = False

# Explicit cookie name (default, but stated for clarity/debuggability)
CSRF_COOKIE_NAME = "csrftoken"

# ---------------------------------------------------------------------------
# Authentication redirects
# ---------------------------------------------------------------------------
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

DATA_GOV_API_KEY = os.environ.get(
    "DATA_GOV_API_KEY",
    ""
)

DATA_GOV_MANDI_RESOURCE_ID = os.environ.get(
    "DATA_GOV_MANDI_RESOURCE_ID",
    "9ef84268-d588-465a-a308-a864a43d0070"
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "app1",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pro1.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "app1" / "template1"
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "app1.context_processors.notifications_processor",
            ],
        },
    },
]

WSGI_APPLICATION = "pro1.wsgi.application"

import shutil

# ---------------------------------------------------------------------------
# DATABASE – Vercel read-only filesystem workaround
# ---------------------------------------------------------------------------
# Vercel deploys files to /var/task/ (read-only). SQLite writes (e.g., auth
# last_login, session data, new registrations) would crash with:
#   OperationalError: attempt to write a readonly database
#
# Fix: on Vercel we point Django at /tmp/db.sqlite3 (always writable).
#       wsgi.py copies the committed snapshot there before the app starts.
# ---------------------------------------------------------------------------

_COMMITTED_DB = BASE_DIR / "db.sqlite3"          # read-only on Vercel
_VERCEL_DB    = "/tmp/db.sqlite3"                 # writable on Vercel

# Detect Vercel: its runtime sets the VERCEL env var.
_ON_VERCEL = bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"))

if _ON_VERCEL:
    # Copy the committed snapshot to /tmp/ if not already there.
    # (We copy every time so a fresh deployment always starts with the
    #  latest data that was committed to git.)
    try:
        shutil.copy2(str(_COMMITTED_DB), _VERCEL_DB)
    except Exception:
        pass  # If copy fails, Django will create a fresh DB at that path
    _DB_PATH = _VERCEL_DB
else:
    _DB_PATH = str(_COMMITTED_DB)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": _DB_PATH,
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "app1" / "static"
]

STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Sessions – Use signed cookies so no DB/filesystem writes are needed on Vercel
# (Vercel's filesystem is ephemeral/read-only between invocations)
# ---------------------------------------------------------------------------
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"