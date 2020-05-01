#  Copyright 2019-2020 Simon Zigelli
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

from .common import *  # noqa

SECRET_KEY = env.str("SECRET_KEY")

DEBUG = False

if "symmetric_encryption_keys" not in CHANNEL_LAYERS["default"]["CONFIG"]:
    CHANNEL_LAYERS["default"]["CONFIG"]["symmetric_encryption_keys"] = [SECRET_KEY]

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
