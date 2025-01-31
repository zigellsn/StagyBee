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
from datetime import datetime

import aiohttp
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.base import View
from django.views.generic.edit import FormMixin, UpdateView
from guardian.mixins import LoginRequiredMixin, PermissionRequiredMixin
from qr_code.qrcode.utils import QRCodeOptions
from tenacity import RetryError

from StagyBee.utils import post_request
from StagyBee.views import set_host, SchemeMixin
from audit.models import Audit
from picker.models import Credential, is_active, get_running_since
from stage.consumers import generate_channel_group_name
from stopwatch.forms import StopwatchForm
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

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.headers["Cache-Control"] = "no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


class ConsoleView(PermissionRequiredMixin, SchemeMixin, FormMixin, DetailView):
    model = Credential
    return_403 = True
    permission_required = "access_console"
    form_class = StopwatchForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        set_host(self.request, context)
        path = reverse("console:stopwatch:timer", args=[context["object"].congregation])
        context["timer_url"] = f"{self.request.scheme}://{context['ip']}{path}"
        context["qr_options_dark"] = QRCodeOptions(size="s", border=6, error_correction="L",
                                                   dark_color="white", light_color=None)
        context["qr_options_light"] = QRCodeOptions(size="s", border=6, error_correction="L",
                                                    dark_color="black", light_color=None)
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

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.headers["Cache-Control"] = "no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


class ConsoleActionView(PermissionRequiredMixin, View):
    return_403 = True
    permission_required = "access_console"

    @staticmethod
    def post(request, *args, **kwargs):
        channel_layer = get_channel_layer()
        congregation_group_name = generate_channel_group_name("console", kwargs.get("pk"))
        stage_group_name = generate_channel_group_name("message", kwargs.get("pk"))
        if request.POST.get("action") == "message-send":
            if request.POST.get("message") == "":
                return HttpResponse("", status=202)
            async_to_sync(channel_layer.group_send)(
                stage_group_name,
                {"type": "message.alert", "alert": {"value": request.POST.get("message")}}
            )
            async_to_sync(channel_layer.group_send)(
                congregation_group_name,
                {"type": "console.wait_for_ack"}
            )
            congregation = Credential.objects.get(congregation=kwargs.get("pk"))
            if congregation is not None:
                Audit.objects.create_audit(congregation=congregation, message=request.POST.get("message"),
                                           user=request.user)
        elif request.POST.get("action") == "message-ack":
            async_to_sync(channel_layer.group_send)(
                congregation_group_name,
                {"type": "console.message", "message": {"message": "ACK"}}
            )
        elif request.POST.get("action") == "message-cancel":
            async_to_sync(channel_layer.group_send)(
                stage_group_name,
                {"type": "message.cancel"}
            )
            async_to_sync(channel_layer.group_send)(
                congregation_group_name,
                {"type": "console.cancel_message"}
            )
        elif request.POST.get("action") == "scrim-toggle":
            async_to_sync(channel_layer.group_send)(
                congregation_group_name,
                {"type": "console.scrim"}
            )
        elif request.POST.get("action") == "scrim-refresh":
            async_to_sync(channel_layer.group_send)(
                congregation_group_name,
                {"type": "console.scrim_refresh"}
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
        language = kwargs["language"]
        # if not workbook_extractor.language_exists(language):
        #     return HttpResponse(f"Regular Expressions for {language} are not available.", status=400)
        if "date_from" in kwargs and kwargs["date_from"] != "today":
            date_from = kwargs["date_from"]
        else:
            date_from = datetime.today()
        if "date_to" in kwargs and kwargs["date_from"] != "today":
            date_to = kwargs["date_to"]
        elif "date_to" in kwargs and kwargs["date_from"] == "today":
            date_to = datetime.today()
        else:
            date_to = date_from
        urls = workbook_extractor.create_urls(date_from, date_to)
        times = await workbook_extractor.get_workbooks(urls, language)
        workbooks = []
        if times != {}:
            filter_list = request.GET.getlist("filter")
            filters_times = ()
            filters_directions = ()
            filters_part = ()
            for f in filter_list:
                match f:
                    case "times":
                        filters_times = filters_times + (lambda item: item[1] > 0,)
                    case "no_times":
                        filters_times = filters_times + (lambda item: item[1] == 0,)
                    case "directions":
                        filters_directions = filters_directions + (lambda item: item[3] != "",)
                    case "no_directions":
                        filters_directions = filters_directions + (lambda item: item[3] == "",)
                    case "0":
                        filters_part = filters_part + (lambda item: item[0] == 0,)
                    case "1":
                        filters_part = filters_part + (lambda item: item[0] == 1,)
                    case "2":
                        filters_part = filters_part + (lambda item: item[0] == 2,)
                    case "3":
                        filters_part = filters_part + (lambda item: item[0] == 3,)
                    case _:
                        return HttpResponse(
                            "Only 'times', 'no_times', 'directions', "
                            "'no_directions', '0', '1', '2' and '3' are valid filters.",
                            status=400)

            if filters_part == ():
                filters_part = (lambda item: item[0] == 0 or item[0] == 1 or item[0] == 2 or item[0] == 3,)

            def filter_list(item):
                return all((any(fu(item) for fu in filters_part), all(fu(item) for fu in filters_directions),
                            all(fu(item) for fu in filters_times)))

            for time in times:
                times_list = [item for item in times[time] if filter_list(item)]
                workbooks += [{"date": time, "times": times_list}]

        return render(request, "console/fragments/workbook.html",
                      {"workbooks": workbooks, "language": request.LANGUAGE_CODE})


class SettingsView(LoginRequiredMixin, SchemeMixin, UpdateView):
    template_name = "console/settings.html"
    form_class = LanguageForm
    success_url = reverse_lazy("settings")
    model = UserPreferences

    def get_object(self, queryset=None):
        return UserPreferences.objects.get(user=self.request.user)

    def form_valid(self, form):
        locale = form.cleaned_data["locale"]
        scheme = form.cleaned_data["scheme"]
        try:
            preferences = UserPreferences.objects.get(user=self.request.user)
            preferences.locale = locale
            preferences.scheme = scheme
            preferences.save()
            cur_language = translation.get_language()
            if cur_language != locale:
                translation.activate(locale)
        except UserPreferences.DoesNotExist:
            UserPreferences.objects.create_user_preferences(user=self.request.user,
                                                            design=UserPreferences.Scheme.LIGHT, locale=locale)
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
