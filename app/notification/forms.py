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
from datetime import timedelta

from django import forms
from django.conf import settings
from django.forms import ChoiceField, CharField, BooleanField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Notification


class DateInput(forms.DateInput):
    input_type = "date"


class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ["subject", "message", "importance", "locale", "max_duration", "active"]

    message = CharField(widget=forms.Textarea)
    message.widget.attrs.update({"data-role": "textarea",
                                 "data-clear-button-icon": "<span class='mif-cancel'></span>"})
    importance = ChoiceField(choices=Notification.Importance.choices, label=_("Wichtigkeit"))
    importance.widget.attrs.update({"data-role": "select"})
    locales = settings.LANGUAGES.copy()
    locales.append((" ", _("Alle")))
    locale = ChoiceField(choices=locales, label=_("Sprache"))
    locale.widget.attrs.update({"data-role": "select"})
    max_duration = CharField(label=_("Gültig bis"), initial=timezone.now() + timedelta(days=7))
    max_duration.widget.attrs.update(
        {"data-role": "calendarpicker", "data-size": "280",
         "data-min-date": timezone.now().strftime("%Y/%m/%d")})
    active = BooleanField(label=_("Aktiv"), initial=True, required=False)
    active.widget.attrs.update({"data-role": "switch", "data-material": "true"})
