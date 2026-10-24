"""
PEFA GraceWorks Community Services - Django settings.

Every secret / environment-specific value is read from the .env file
(see .env.example). Never commit your real .env to Git.
"""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="dev-only-insecure-key-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

# Render gives every web service a public hostname, e.g. pefa-graceworks.onrender.com
RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", default="")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

if DEBUG:
    # Let phones and other laptops on the same Wi-Fi open the development server
    # (python manage.py runserver 0.0.0.0:8001 → http://<this laptop's IP>:8001). Never applies in production.
    import socket

    try:
        ALLOWED_HOSTS += [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")]
    except OSError:
        pass
    ALLOWED_HOSTS += [".local"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sitemaps",
    # third party
    "rest_framework",
    "tinymce",
    # local apps
    "apps.core",
    "apps.programs",
    "apps.news",
    "apps.events",
    "apps.donations",
    "apps.community",
    "apps.dashboard",
    "apps.api",
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
                "apps.core.context_processors.site_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database: PostgreSQL (set DATABASE_URL in .env).
# Falls back to SQLite only so you can try the site before Postgres is ready.
# ---------------------------------------------------------------------------
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
DATABASES["default"]["ATOMIC_REQUESTS"] = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

# Static & media ------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Uploaded photos and videos go to Cloudinary when CLOUDINARY_URL is set (needed on hosts whose disk is
# wiped on each deploy, like Render's free plan); otherwise to MEDIA_ROOT. See apps/core/storage.py.
CLOUDINARY_ENABLED = bool(env("CLOUDINARY_URL", default=""))

STORAGES = {
    "default": {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage" if CLOUDINARY_ENABLED
                else "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if not DEBUG
        else "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Cache (used for rate limiting & cached stats). Set REDIS_URL in production
# if you have Redis; local memory is fine for a single server.
if env("REDIS_URL", default=""):
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": env("REDIS_URL")}}
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Email ---------------------------------------------------------------------
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="PEFA GraceWorks <no-reply@pefagraceworks.org>")
STAFF_NOTIFICATION_EMAILS = env.list("STAFF_NOTIFICATION_EMAILS", default=[])

# M-Pesa Daraja (STK Push / Lipa na M-Pesa Online) ---------------------------
MPESA = {
    "ENV": env("MPESA_ENV", default="sandbox"),  # sandbox | production
    "CONSUMER_KEY": env("MPESA_CONSUMER_KEY", default=""),
    "CONSUMER_SECRET": env("MPESA_CONSUMER_SECRET", default=""),
    "SHORTCODE": env("MPESA_SHORTCODE", default="174379"),
    "PASSKEY": env("MPESA_PASSKEY", default=""),
    "CALLBACK_URL": env("MPESA_CALLBACK_URL", default=""),
    "TRANSACTION_TYPE": env("MPESA_TRANSACTION_TYPE", default="CustomerPayBillOnline"),
}

# PayPal Checkout: PayPal balance plus debit / credit cards (guest checkout, no PayPal account needed).
# Get keys at https://developer.paypal.com → Apps & Credentials. PayPal does not settle in KES, so these
# gifts are taken in USD and converted at PAYPAL_KES_PER_USD for project totals.
PAYPAL = {
    "ENV": env("PAYPAL_ENV", default="sandbox"),  # sandbox | live
    "CLIENT_ID": env("PAYPAL_CLIENT_ID", default=""),
    "CLIENT_SECRET": env("PAYPAL_CLIENT_SECRET", default=""),
    "CURRENCY": env("PAYPAL_CURRENCY", default="USD"),
}
PAYPAL_KES_PER_USD = env.float("PAYPAL_KES_PER_USD", default=129.0)

# Rich text editor used in the admin (like the WordPress editor)
TINYMCE_DEFAULT_CONFIG = {
    "height": 420,
    "menubar": "edit view insert format table",
    "plugins": "link image lists table code autoresize media",
    "toolbar": "undo redo | blocks | bold italic | bullist numlist | link image media table | code",
    "relative_urls": False,
}

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticatedOrReadOnly"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": "120/hour"},
}

ADMIN_URL = env("ADMIN_URL", default="admin/")
LOGIN_URL = "admin:login"

MESSAGE_TAGS = {40: "danger"}

# Security hardening (only when DEBUG is off) --------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "[{asctime}] {levelname} {name}: {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {"django": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", default="INFO"), "propagate": False}},
}
