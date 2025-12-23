#  Copyright 2019-2025 Simon Zigelli
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import json
import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from environ import environ

from StagyBee.utils import linear_gradient

env = environ.Env(
    DEBUG=(bool, False)
)

PROJECT_PACKAGE = Path(__file__).resolve().parent
BASE_DIR = Path(PROJECT_PACKAGE).resolve().parent
env.read_env(env_file=os.path.join(BASE_DIR, ".env"))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")
SHOW_DEBUG_TOOLBAR = DEBUG

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

try:
    with open(os.path.join(PROJECT_PACKAGE, "regex.json"), encoding="utf-8") as json_file:
        WB_LANGUAGE_SWITCHER = json.load(json_file)
except FileNotFoundError:
    WB_LANGUAGE_SWITCHER = {}

COLOR_GRADIENT = linear_gradient("#3B82F6", "#EF4444", n=100)

VERSION = "2.0.0-alpha01"

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["https://127.0.0.1", "https://localhost"])

if DEBUG:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
            },
        },
        "loggers": {
            "console.workbook.workbook": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "StagyBee.consumers": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "stage.consumers": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "picker.apps": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

# Application definition

INSTALLED_APPS = [
    "daphne",
    "guardian",
    "stage",
    "console.apps.ConsoleConfig",
    "picker.apps.PickerConfig",
    "audit.apps.AuditConfig",
    "stopwatch.apps.StopwatchConfig",
    "notification.apps.NotificationConfig",
    "qr_code",
    "widget_tweaks",
    "django.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware"
]

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
)

ROOT_URLCONF = "StagyBee.urls"
LOGIN_REDIRECT_URL = "/startup"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "/login/"

DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="webmaster@localhost")
EMAIL_CONFIG = env.email_url(default="smtp://user:password@localhost:25")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'
GUARDIAN_RENDER_403 = True

WSGI_APPLICATION = "StagyBee.wsgi.application"

ASGI_APPLICATION = "StagyBee.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env.str("REDIS_URL", default="redis://localhost:6379/0")]
        },
    },
}

EXTRACTOR_TIMEOUT = env.int("EXTRACTOR_TIMEOUT", default=120)
SHOW_SHUTDOWN_ICON = env.bool("SHOW_SHUTDOWN_ICON", default=True)
SHOW_LOGIN = env.bool("SHOW_LOGIN", default=True)
EXTERNAL_IP = env.str("EXTERNAL_IP", default=None)
EXTERNAL_HOST_NAME = env.str("EXTERNAL_HOST_NAME", default=None)
KEEP_TIMER_DAYS = env.int("KEEP_TIMER_DAYS", default=30)
RECEIVER_PROTOCOL = env.str("RECEIVER_PROTOCOL", default="http")
RECEIVER_HOST = env.str("RECEIVER_HOST", default="")
RECEIVER_PORT = env.int("RECEIVER_PORT", default=0)

DATABASES = {
    "default": env.db_url(default="sqlite:///db.sqlite3")
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

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

LANGUAGES = [(x.split(":")[0], _(x.split(":")[1])) for x in env.list("LANGUAGES", default=["de:German", "en:English"])]

if not [item for item in LANGUAGES if item[0] == env.str("DEFAULT_LANGUAGE", default="de")]:
    raise ImproperlyConfigured("Language list does not contain the default language.")

LANGUAGE_CODE = env.str("DEFAULT_LANGUAGE", default="de")

LOCALE_PATHS = (
    str(PROJECT_PACKAGE.joinpath("locale")),
)

TIME_ZONE = env.str("TIME_ZONE", default="Europe/Berlin")

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

USE_I18N = True

USE_TZ = True

STATIC_URL = "/static/assets/"
STATIC_ROOT = os.path.join(BASE_DIR, "static/assets")
STATICFILES_DIRS = [("stagybee", str(PROJECT_PACKAGE.joinpath("static")))]

MEDIA_URL = "/files/"
MEDIA_ROOT = os.path.join(BASE_DIR, "files/")

TESTING = "test" in sys.argv or "PYTEST_VERSION" in os.environ

if DEBUG:
    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = env.str("SECRET_KEY", "django-insecure-qhmmb46a$-j_#%yt0@1enx=mxpercrdbu!sc4^x=a1n_+a!^y5")
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

    import mimetypes

    mimetypes.add_type("application/javascript", ".js", True)
    if not TESTING:
        try:
            import debug_toolbar
        except ImportError:
            pass
        else:
            INSTALLED_APPS.append("debug_toolbar")
            INTERNAL_IPS = ["127.0.0.1"]
            MIDDLEWARE.insert(
                MIDDLEWARE.index("django.middleware.common.CommonMiddleware") + 1,
                "debug_toolbar.middleware.DebugToolbarMiddleware"
            )
            DEBUG_TOOLBAR_CONFIG = { "ROOT_TAG_EXTRA_ATTRS": "hx-preserve" }
else:
    SECRET_KEY = env.str("SECRET_KEY")

    if "symmetric_encryption_keys" not in CHANNEL_LAYERS["default"]["CONFIG"]:
        CHANNEL_LAYERS["default"]["CONFIG"]["symmetric_encryption_keys"] = [SECRET_KEY]

    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    SESSION_COOKIE_AGE = 43200
