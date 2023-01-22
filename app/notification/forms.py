#  Copyright 2019-2023 Simon Zigelli
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
    template_name = "notification/form.html"

    class Meta:
        model = Notification
        fields = ["subject", "message", "importance", "locale", "show_in_locale", "max_duration", "active"]

    default_class = "dark:bg-gray-800 bg-white appearance-none outline-none"

    subject = CharField(label=_("Betreff"), widget=forms.TextInput(attrs={"class": default_class}))
    message = CharField(label=_("Nachricht"), widget=forms.Textarea(attrs={"class": default_class}))
    importance = ChoiceField(choices=Notification.Importance.choices, label=_("Wichtigkeit"),
                             widget=forms.Select(attrs={"class": default_class}))
    locales = settings.LANGUAGES.copy()
    locale = ChoiceField(choices=locales, label=_("Sprache der Nachricht"),
                         widget=forms.Select(attrs={"class": default_class}))
    locales.append((" ", _("Alle")))
    show_in_locale = ChoiceField(choices=locales, label=_("Anzeigen für Sprache"),
                                 widget=forms.Select(attrs={"class": default_class}))
    max_duration = forms.DateField(label=_("Gültig bis"),
                                   initial=(timezone.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                                   widget=forms.DateInput(format="%Y-%m-%d",
                                                          attrs={"class": default_class + " dark:date_input", "type": "date",
                                                                 "min": timezone.now().strftime("%Y-%m-%d")}))
    active = BooleanField(label=_("Aktiv"), initial=True, required=False,
                          widget=forms.CheckboxInput(attrs={"class": default_class}))
