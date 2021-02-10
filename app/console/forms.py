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

from django import forms
from django.conf import settings
from django.forms import ModelChoiceField, ChoiceField
from django.utils.translation import gettext_lazy as _

from console.models import UserPreferences
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
