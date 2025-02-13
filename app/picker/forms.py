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

from django.forms import ModelForm, PasswordInput, URLField, ChoiceField
from django.utils.translation import gettext_lazy as _

from StagyBee.utils import DockerURLValidator
from .models import Credential


class DockerURLField(URLField):
    default_validators = [DockerURLValidator()]


class CredentialForm(ModelForm):
    class Meta:
        model = Credential
        fields = ['congregation', 'autologin', 'username', 'password', 'display_name', 'extractor_url', 'touch',
                  'show_only_request_to_speak', 'send_times_to_stage', 'sort_order', 'name_order']
        widgets = {
            'password': PasswordInput(render_value=True),
        }

    extractor_url = DockerURLField(label=_("Extractor URL"), initial="https://extractor:8443/", required=False,
                                   assume_scheme="https")
