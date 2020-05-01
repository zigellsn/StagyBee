#  Copyright 2019 Simon Zigelli
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
# Needed for now when using Python 3.8 on Windows
from environ import environ

if sys.platform == 'win32' and sys.version_info.major == 3 and sys.version_info.minor == 8:
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

VERSION = "1.0.0-beta01"

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

# Application definition

INSTALLED_APPS = [
    'channels',
    'guardian',
    'stage',
    'receiver',
    'console',
    'picker.apps.PickerConfig',
    'audit.apps.AuditConfig',
    'stopwatch.apps.StopwatchConfig',
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
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

ROOT_URLCONF = 'StagyBee.urls'
LOGIN_REDIRECT_URL = '/console/'
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
            "hosts": [env.str('REDIS_URL', default='redis://localhost:6379/0')],
            "symmetric_encryption_keys": [env.str("SECRET_KEY")],
        },
    },
}

REDIS_EXPIRATION = env.int("REDIS_EXPIRATION", default=21600)
EXTRACTOR_TIMEOUT = env.int("EXTRACTOR_TIMEOUT", default=120)
SHOW_SHUTDOWN_ICON = env.bool("SHOW_SHUTDOWN_ICON", default=True)
RUN_IN_CONTAINER = env.bool("RUN_IN_CONTAINER", default=False)
EXTERNAL_IP = env.str("EXTERNAL_IP", default='127.0.0.1:8000')
KEEP_TIMER_DAYS = env.int("KEEP_TIMER_DAYS", default=30)
RECEIVER_HOST = env.str('RECEIVER_HOST', default='')
RECEIVER_PORT = env.int('RECEIVER_PORT', default=0)

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': env.db_url(default='sqlite:///db.sqlite3')
}

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGES = [(x.split(':')[0], _(x.split(':')[1])) for x in
             env.list('LANGUAGES', default=[('de', 'German'), ('en', 'English')])]

LANGUAGE_CODE = 'de'

LOCALE_PATHS = (
    str(PROJECT_PACKAGE.joinpath('locale')),
)

TIME_ZONE = 'CET'

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/assets/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/assets')
STATICFILES_DIRS = [str(PROJECT_PACKAGE.joinpath('static'))]
