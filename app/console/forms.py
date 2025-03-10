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

from ssl import SSLError

import aiohttp
from django import forms
from django.conf import settings
from django.forms import ModelChoiceField, ChoiceField, CharField, URLField
from django.utils.translation import gettext_lazy as _
from tenacity import RetryError

from StagyBee.utils import get_request
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
        super().__init__(*args, **kwargs)
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
        fields = ["uri", "alias", "cert_file"]

    uri = URLField(label=_("Client URL"), empty_value="https://", assume_scheme="https")
    alias = CharField(label=_("Alias Name"))

    def is_valid(self):
        status = 0
        if not super().is_valid():
            return False
        try:
            (task, status) = get_request(self.instance.uri + "/token", self.instance.cert_file.file)
        except aiohttp.ClientError as err:
            self.add_error("uri", [_("Client hat nicht geantwortet."), f"{_('HTTP Status')} {str(status)}", str(err)])
            return False
        except RetryError as err:
            self.add_error("uri", [_("Client hat nicht geantwortet."), f"{_('HTTP Status')} {str(status)}", str(err)])
            return False
        except SSLError as err:
            self.add_error("cert_file", [_("Zertifikat ist ungültig."), str(err)])
            return False
        except UnicodeDecodeError as err:
            self.add_error("cert_file", [_("Zertifikat ist ungültig."), str(err)])
            return False
        else:
            if status != 200:
                self.add_error("uri", [_("Kein Token vom Client empfangen."), f"{_('HTTP Status')} {str(status)}"])
                return False
            else:
                self.instance.token = task
                return True
