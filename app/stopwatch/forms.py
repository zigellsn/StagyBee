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

from django import forms
from django.utils.translation import gettext_lazy as _


class StopwatchForm(forms.Form):
    template_name = "stopwatch/form.html"

    default_class = "dark:bg-gray-800 bg-white appearance-none outline-none ltr:mr-2 rtl:ml-2"

    talk_name = forms.CharField(label=_("Aufgabe"), required=False, initial="",
                                widget=forms.TextInput(attrs={"class": default_class}))
    talk_index = forms.IntegerField(required=False, initial=0, widget=forms.HiddenInput())
    talk_user = forms.BooleanField(required=False, widget=forms.HiddenInput())
    hours = []
    for i in range(5):
        hours.append((i, i))
    minutes = []
    for i in range(60):
        minutes.append((i, i))
    h = forms.ChoiceField(label=_("H"), choices=hours, widget=forms.Select(attrs={"class": default_class}))
    m = forms.ChoiceField(label=_("M"), choices=minutes, widget=forms.Select(attrs={"class": default_class}))
    s = forms.ChoiceField(label=_("S"), choices=minutes, widget=forms.Select(attrs={"class": default_class}))
