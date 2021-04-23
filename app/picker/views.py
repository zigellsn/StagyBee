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
from asgiref.sync import async_to_sync
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import ListView
from django.views.generic.base import View
from tenacity import retry, retry_if_exception_type, wait_random_exponential, stop_after_delay, RetryError

from StagyBee.views import set_host, get_scheme
from console.models import KnownClient
from .models import Credential


class PickerView(ListView):
    model = Credential
    template_name = "picker/tiles.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        credentials = Credential.objects.all()
        col, size = __get_tiles_configuration__(credentials, settings.SHOW_LOGIN)
        set_host(self.request, context)
        context["size"] = size
        context["col"] = col
        context["shutdown_icon"] = settings.SHOW_SHUTDOWN_ICON
        context["show_login"] = settings.SHOW_LOGIN
        context["version"] = settings.VERSION
        context["dark"] = get_scheme(self.request)
        return context


class ShutdownView(View):

    @staticmethod
    def get(request):
        ip = __get_client_ip__(request)
        client = KnownClient.objects.filter(uri__contains=ip)
        if len(client) == 1:
            try:
                __post_request__(client[0].uri + "/shutdown", client[0].token)
            except aiohttp.ClientError:
                return HttpResponseRedirect("/picker")
            except RetryError:
                return HttpResponseRedirect("/picker")
            else:
                return HttpResponse(content="Shutdown in progress", status=202)
        else:
            return HttpResponseRedirect("/picker")


class RebootView(View):

    @staticmethod
    def get(request):
        ip = __get_client_ip__(request)
        client = KnownClient.objects.filter(uri__contains=ip)
        if len(client) == 1:
            try:
                __post_request__(client[0].uri + "/reboot", client[0].token)
            except aiohttp.ClientError:
                return HttpResponseRedirect("/picker")
            except RetryError:
                return HttpResponseRedirect("/picker")
            else:
                return HttpResponse(content="Reboot in progress", status=202)
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


@retry(retry=retry_if_exception_type(aiohttp.ClientError), wait=wait_random_exponential(multiplier=1, max=15),
       stop=stop_after_delay(15))
@async_to_sync
async def __post_request__(url, payload):
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, data=payload, ssl=False) as response:
            return await response.read()


def __get_client_ip__(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
