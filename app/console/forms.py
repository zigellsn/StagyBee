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
import logging

import aioredis
from django import forms
from django.conf import settings
from django.forms import ModelChoiceField

from picker.models import Credential

REDIS_KEY = "stagybee::console:congregation.console."
logger = logging.getLogger(__name__)


async def get_redis_congregations():
    host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]
    redis = await aioredis.create_redis(host)
    congregations = await redis.keys(REDIS_KEY + "*")
    redis.close()
    await redis.wait_closed()
    return congregations


async def get_active_congregations():
    congregation_filter = []
    try:
        congregation_filter = await get_redis_congregations()
    except():
        logger.error("Redis Server not available")
    finally:
        congregation_filter[:] = [c.decode()[len(REDIS_KEY):len(c)] for c in congregation_filter]
        return congregation_filter


class CongregationForm(forms.ModelForm):
    class Meta:
        model = Credential
        fields = ["congregation"]

    congregation = ModelChoiceField(queryset=None, empty_label=None,
                                    to_field_name="congregation")
    congregation.widget.attrs.update({"data-role": "select"})

    def __init__(self, *args, **kwargs):
        super(CongregationForm, self).__init__(*args, **kwargs)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        congregation_filter = loop.run_until_complete(get_active_congregations())
        self.congregation_set = Credential.objects.all()
        for congregation in self.congregation_set:
            if congregation.congregation in congregation_filter:
                congregation.active = True
            else:
                congregation.active = False
        self.fields["congregation"].queryset = self.congregation_set
