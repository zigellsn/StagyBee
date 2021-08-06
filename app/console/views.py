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

from datetime import datetime

import aiohttp
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse, reverse_lazy
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.base import View
from django.views.generic.edit import FormMixin, UpdateView
from guardian.mixins import LoginRequiredMixin, PermissionRequiredMixin
from tenacity import RetryError

from StagyBee.utils import post_request
from StagyBee.views import set_host, SchemeMixin
from picker.models import Credential, is_active, get_running_since
from stage.consumers import generate_channel_group_name
from .forms import CongregationForm, LanguageForm
from .models import UserPreferences, KnownClient
from .workbook.workbook import WorkbookExtractor


class StartupView(LoginRequiredMixin, SchemeMixin, View):

    def dispatch(self, request, *args, **kwargs):
        preferences = UserPreferences.objects.get(user=request.user)
        cur_language = translation.get_language()
        if cur_language != preferences.locale:
            translation.activate(preferences.locale)
        return HttpResponseRedirect(f"/{preferences.locale}/console/")


class ChooseConsoleView(LoginRequiredMixin, FormMixin, SchemeMixin, ListView):
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


class ConsoleView(PermissionRequiredMixin, SchemeMixin, DetailView):
    model = Credential
    return_403 = True
    permission_required = "access_console"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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


class ConsoleActionView(PermissionRequiredMixin, View):
    return_403 = True
    permission_required = "access_console"

    def post(self, request, *args, **kwargs):
        channel_layer = get_channel_layer()
        congregation_group_name = generate_channel_group_name("console", kwargs.get("pk"))
        if request.path.endswith("/action/message/send/"):
            async_to_sync(channel_layer.group_send)(
                congregation_group_name,
                {"type": "alert", "alert": {"value": request.body[8:]}},
            )
        elif request.path.endswith("/action/message/ack/"):
            async_to_sync(channel_layer.group_send)(
                congregation_group_name,
                {"type": "message", "message": {"message": "ACK"}},
            )
        elif request.path.endswith("/action/scrim/toggle/"):
            async_to_sync(channel_layer.group_send)(
                congregation_group_name,
                {"type": "scrim", "scrim": {"value": True}},
            )
        else:
            return HttpResponse("", status=404)
        return HttpResponse("", status=202)

    def get_object(self, queryset=None):
        return Credential.objects.get(congregation=self.kwargs["pk"])


class WorkbookView(LoginRequiredMixin, View):

    async def __call__(self, **kwargs):
        pass

    @async_to_sync
    async def get(self, request, *args, **kwargs):
        workbook_extractor = WorkbookExtractor()
        today = datetime.today()
        urls = workbook_extractor.create_urls(today, today)
        times = await workbook_extractor.get_workbooks(urls, request.LANGUAGE_CODE)
        talk_list = "<label for=\"talk-list\" class=\"pt-4\">Aufgabe</label><ul data-role=\"listview\" " \
                    "data-view=\"list\" data-select-node=\"true\" data-on-node-click=\"doClick\" id=\"talk-list\"><li " \
                    f"data-caption=\"{_('Leben-und-Dienst-Zusammenkunft')}\">"
        if times is not None:
            talk_list = f"{talk_list}<ul>"
            selected = " current current-select"
            for talk in list(times.values())[0]:
                talk_list = f"{talk_list}<li class=\"bg-darkBlue-hover{selected}\" data-caption=\"{talk[1]}\" " \
                            f"data-content=\"{talk[0]}\"></li>"
                selected = ""
            talk_list = f"{talk_list}</ul>"
        talk_list = f"{talk_list}</li>"
        talk_list = f"{talk_list}<li data-caption=\"{_('Zusammenkunft für die Öffentlichkeit')}\"><ul><li " \
                    f"class=\"bg-darkBlue-hover\" data-caption=\"{_('Öffentlicher Vortrag (30 Min.)')}\" " \
                    f"data-content=\"30\"></li><li class=\"bg-darkBlue-hover\" data-caption=\"" \
                    f"{_('Wachtturm-Studium (60 Min.)')}\" data-content=\"60\"></li></ul></li><li data-caption=\"" \
                    f"{_('Benutzerdefiniert')}\"><ul><li class=\"bg-darkBlue-hover\" data-caption=\"" \
                    f"{_('Benutzerdefiniert')}\" data-content=\"10\"></li></ul></li></ul> "
        return HttpResponse(talk_list)


class SettingsView(LoginRequiredMixin, SchemeMixin, UpdateView):
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


class KnownClientShutdown(PermissionRequiredMixin, SchemeMixin, DetailView):
    model = KnownClient
    return_403 = True
    permission_required = "control_client"

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


class KnownClientReboot(PermissionRequiredMixin, SchemeMixin, DetailView):
    model = KnownClient
    return_403 = True
    permission_required = "control_client"

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
