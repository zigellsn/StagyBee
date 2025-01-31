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

import aiohttp
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from django.views.generic.base import View
from tenacity import RetryError

from StagyBee.utils import post_request, get_client_ip
from StagyBee.views import set_host, SchemeMixin
from console.models import KnownClient
from .models import Credential


class PickerView(SchemeMixin, ListView):
    model = Credential
    template_name = "picker/tiles.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        credentials = Credential.objects.all()
        col, size = __get_tiles_configuration__(credentials, settings.SHOW_LOGIN)
        set_host(self.request, context)
        context["size"] = size
        context["col"] = col
        context["show_login"] = settings.SHOW_LOGIN
        context["version"] = settings.VERSION
        ip = get_client_ip(self.request)
        client = KnownClient.objects.filter(uri__contains=ip)
        if client.count() == 1:
            context["shutdown_icon"] = settings.SHOW_SHUTDOWN_ICON
        return context


class ShutdownView(View):

    @staticmethod
    def get(request):
        ip = get_client_ip(request)
        client = KnownClient.objects.filter(uri__contains=ip)
        if client.count() == 1:
            try:
                post_request(client[0].uri + "/shutdown", payload=client[0].token, certificate=client[0].cert_file)
            except aiohttp.ClientError:
                return HttpResponseRedirect("/picker")
            except RetryError:
                return HttpResponseRedirect("/picker")
            else:
                return HttpResponse(content=_("Herunterfahren-Anfrage erfolgreich gesendet"), status=202)
        else:
            return HttpResponseRedirect("/picker")


class RebootView(View):

    @staticmethod
    def get(request):
        ip = get_client_ip(request)
        client = KnownClient.objects.filter(uri__contains=ip)
        if client.count() == 1:
            try:
                post_request(client[0].uri + "/reboot", payload=client[0].token, certificate=client[0].cert_file)
            except aiohttp.ClientError:
                return HttpResponseRedirect("/picker")
            except RetryError:
                return HttpResponseRedirect("/picker")
            else:
                return HttpResponse(content=_("Neustart-Anfrage erfolgreich gesendet"), status=202)
        else:
            return HttpResponseRedirect("/picker")


def __get_tiles_configuration__(credentials, show_login):
    if show_login:
        if credentials.count() == 0 or credentials.count() == 1:
            size = 2
            col = 1
        elif credentials.count() == 2:
            size = 2
            col = 0
        elif credentials.count() == 3:
            size = 3
            col = 2
        else:
            size = 4
            col = 3
    else:
        if credentials.count() == 0:
            size = 0
        elif credentials.count() == 1:
            size = 1
        elif credentials.count() == 2:
            size = 2
        elif credentials.count() == 3:
            size = 3
        else:
            size = 4
        col = 0
    return col, size
