#  Copyright 2019-2021 Simon Zigelli
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
import asyncio
import json
import os
import sys
from pathlib import Path

from django.utils.translation import gettext_lazy as _
from environ import environ

# Needed for now when using Python 3.8 on Windows
if sys.platform == 'win32' and sys.version_info.major == 3 and sys.version_info.minor >= 8:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

PROJECT_PACKAGE = Path(__file__).resolve().parent.parent

BASE_DIR = PROJECT_PACKAGE.parent

env = environ.Env()
env.read_env(env_file=os.path.dirname(PROJECT_PACKAGE) + "/.env")

try:
    with open(f"{PROJECT_PACKAGE}/regex.json", encoding="utf-8") as json_file:
        WB_LANGUAGE_SWITCHER = json.load(json_file)
except FileNotFoundError:
    WB_LANGUAGE_SWITCHER = {}

VERSION = "1.0.0-rc03"

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# Application definition

INSTALLED_APPS = [
    'channels',
    'guardian',
    'stage',
    'receiver',
    'console.apps.ConsoleConfig',
    'picker.apps.PickerConfig',
    'audit.apps.AuditConfig',
    'stopwatch.apps.StopwatchConfig',
    'notification.apps.NotificationConfig',
    'qr_code',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

ROOT_URLCONF = 'StagyBee.urls'
LOGIN_REDIRECT_URL = '/startup'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/login/'

DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="webmaster@localhost")
EMAIL_CONFIG = env.email_url(default='smtp://user:password@localhost:25')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'StagyBee.wsgi.application'

ASGI_APPLICATION = "StagyBee.routing.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env.str('REDIS_URL', default='redis://localhost:6379/0')]
        },
    },
}

REDIS_EXPIRATION = env.int("REDIS_EXPIRATION", default=21600)
EXTRACTOR_TIMEOUT = env.int("EXTRACTOR_TIMEOUT", default=120)
SHOW_SHUTDOWN_ICON = env.bool("SHOW_SHUTDOWN_ICON", default=True)
SHOW_LOGIN = env.bool("SHOW_LOGIN", default=True)
EXTERNAL_IP = env.str("EXTERNAL_IP", default=None)
EXTERNAL_HOST_NAME = env.str("EXTERNAL_HOST_NAME", default=None)
KEEP_TIMER_DAYS = env.int("KEEP_TIMER_DAYS", default=30)
RECEIVER_HOST = env.str('RECEIVER_HOST', default='')
RECEIVER_PORT = env.int('RECEIVER_PORT', default=0)

DATABASES = {
    'default': env.db_url(default='sqlite:///db.sqlite3')
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGES = [(x.split(':')[0], _(x.split(':')[1])) for x in env.list('LANGUAGES', default=['de:German', 'en:English'])]

LANGUAGE_CODE = 'de'

LOCALE_PATHS = (
    str(PROJECT_PACKAGE.joinpath('locale')),
)

TIME_ZONE = env.str("TIME_ZONE", default="Europe/Berlin")

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

REDIS_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/assets/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/assets')
STATICFILES_DIRS = [str(PROJECT_PACKAGE.joinpath('static'))]

MEDIA_URL = '/files/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'files/')
