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
import aiohttp
from asgiref.sync import async_to_sync
from django import forms
from django.conf import settings
from django.forms import ModelChoiceField, ChoiceField, CharField
from django.utils.translation import gettext_lazy as _
from tenacity import retry_if_exception_type, retry, stop_after_delay, wait_random_exponential, RetryError

from console.models import UserPreferences, KnownClient
from picker.models import Credential


class CongregationForm(forms.ModelForm):
    class Meta:
        model = Credential
        fields = ["congregation"]

    congregation = ModelChoiceField(queryset=None, empty_label=None,
                                    to_field_name="congregation")
    congregation.widget.attrs.update({"data-role": "select"})

    def __init__(self, *args, **kwargs):
        super(CongregationForm, self).__init__(*args, **kwargs)
        self.fields["congregation"].queryset = Credential.objects.active()


class LanguageForm(forms.ModelForm):
    class Meta:
        model = UserPreferences
        fields = ["locale"]

    locales = settings.LANGUAGES.copy()
    locale = ChoiceField(choices=locales, label=_("Bevorzugte Sprache"))
    locale.widget.attrs.update({"data-role": "select"})


class KnownClientForm(forms.ModelForm):
    class Meta:
        model = KnownClient
        fields = ["uri", "alias"]

    uri = CharField(label=_("Client URI"))
    alias = CharField(label=_("Alias Name"))

    def is_valid(self):
        if not super().is_valid():
            return False
        try:
            task = async_to_sync(self.__get_request)(self.instance.uri + "/token")
        except aiohttp.ClientError:
            return False
        except RetryError:
            return False
        else:
            self.instance.token = task
            return True

    @retry(retry=retry_if_exception_type(aiohttp.ClientError), wait=wait_random_exponential(multiplier=1, max=15),
           stop=stop_after_delay(15))
    async def __get_request(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=False) as response:
                return await response.read()
