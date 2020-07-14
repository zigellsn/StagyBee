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

from django.http import HttpResponseRedirect
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormMixin
from guardian.mixins import LoginRequiredMixin, PermissionRequiredMixin

from picker.models import Credential
from .forms import CongregationForm


class ChooseConsoleView(LoginRequiredMixin, FormMixin, ListView):
    template_name = 'console/choose_console.html'
    form_class = CongregationForm

    def form_valid(self, form):
        congregation = form.cleaned_data["congregation"].congregation
        return HttpResponseRedirect(f"/console/{congregation}")

    def get_queryset(self):
        return Credential.objects.active()

    def get_template_names(self):
        if len(Credential.objects.active()) < 10:
            return "console/choose_console_cards.html"
        else:
            return "console/choose_console.html"


class ConsoleView(PermissionRequiredMixin, DetailView):
    model = Credential
    return_403 = True
    permission_required = "access_console"
    template_name = "console/console.html"
