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
import aioredis
from django import forms
from django.conf import settings
from django.forms import ModelChoiceField

from picker.models import Credential


async def get_redis_congregations():
    host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]
    redis = await aioredis.create_redis(host)
    congregations = await redis.keys('stagybee:console:*')
    redis.close()
    await redis.wait_closed()
    return congregations


async def get_active_congregations():
    congregation_filter = await get_redis_congregations()
    in_filter = []
    for congregation in congregation_filter:
        in_filter += [congregation.decode()[30:len(congregation)]]
    return Credential.objects.filter(congregation__in=in_filter)


class CongregationForm(forms.ModelForm):
    class Meta:
        model = Credential
        fields = ["congregation"]

    congregation_set = None
    congregation = ModelChoiceField(queryset=congregation_set, empty_label=None,
                                    to_field_name="congregation")
    congregation.widget.attrs.update({"data-role": "select"})

    def __init__(self, *args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.congregation_set = loop.run_until_complete(get_active_congregations())
        super(CongregationForm, self).__init__(*args, **kwargs)
        self.fields["congregation"].queryset = self.congregation_set
