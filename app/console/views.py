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
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.base import View
from django.views.generic.edit import FormMixin, UpdateView, CreateView, DeleteView
from guardian.mixins import LoginRequiredMixin, PermissionRequiredMixin
from tenacity import RetryError

from StagyBee.utils import post_request
from StagyBee.views import set_host, get_scheme
from picker.models import Credential, is_active, get_running_since
from .forms import CongregationForm, LanguageForm, KnownClientForm
from .models import UserPreferences, KnownClient


class StartupView(LoginRequiredMixin, View):

    def dispatch(self, request, *args, **kwargs):
        preferences = UserPreferences.objects.get(user=request.user)
        cur_language = translation.get_language()
        if cur_language != preferences.locale:
            translation.activate(preferences.locale)
        return HttpResponseRedirect(f"/{preferences.locale}/console/")


class ChooseConsoleView(LoginRequiredMixin, FormMixin, ListView):
    template_name = 'console/choose_console.html'
    form_class = CongregationForm

    def form_valid(self, form):
        congregation = form.cleaned_data["congregation"].congregation
        return HttpResponseRedirect(f"/console/{congregation}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dark"] = get_scheme(self.request)

        return context

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dark"] = get_scheme(self.request)
        set_host(self.request, context)
        path = reverse("console:stopwatch:timer", args=[context["object"].congregation])
        context["timer_url"] = f"{self.request.scheme}://{context['ip']}{path}"
        return context

    def get_template_names(self):
        if is_active(self.get_object()):
            return "console/console.html"
        else:
            return "console/console_not_ready.html"

    def get_object(self, queryset=None):
        congregation = super().get_object(queryset)
        congregation.since = get_running_since(congregation)
        return congregation


class SettingsView(LoginRequiredMixin, UpdateView):
    template_name = "console/settings.html"
    form_class = LanguageForm
    success_url = reverse_lazy("settings")
    model = UserPreferences

    def get_object(self, queryset=None):
        return UserPreferences.objects.get(user=self.request.user)

    def form_valid(self, form):
        locale = form.cleaned_data["locale"]
        try:
            preferences = UserPreferences.objects.get(user=self.request.user)
            preferences.locale = locale
            preferences.save()
            cur_language = translation.get_language()
            if cur_language != locale:
                translation.activate(locale)
        except UserPreferences.DoesNotExist:
            UserPreferences.objects.create_user_preferences(user=self.request.user, dark_mode=True, locale=locale)
        return super().form_valid(form)


class KnownClientShutdown(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = KnownClient

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            post_request(context["object"].uri + "/shutdown", payload=context["object"].token,
                         certificate=context["object"].cert_file)
        except aiohttp.ClientError as err:
            context["message"] = str(err.args)
        except RetryError as err:
            context["message"] = str(err.args)
        else:
            context["message"] = _("Herunterfahren-Anfrage erfolgreich gesendet")
        return context

    def test_func(self):
        return self.request.user.is_superuser


class KnownClientReboot(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = KnownClient

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            post_request(context["object"].uri + "/reboot", payload=context["object"].token,
                         certificate=context["object"].cert_file)
        except aiohttp.ClientError as err:
            context["message"] = str(err.args)
        except RetryError as err:
            context["message"] = str(err.args)
        else:
            context["message"] = _("Neustart-Anfrage erfolgreich gesendet")
        return context

    def test_func(self):
        return self.request.user.is_superuser
