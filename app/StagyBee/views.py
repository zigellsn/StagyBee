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

import socket

from django.conf import settings
from django.http import HttpResponse
from django.views.generic.base import ContextMixin, View

from console.models import UserPreferences


class SchemeMixin(ContextMixin):

    @staticmethod
    def get_scheme(request):
        if request.user.is_authenticated:
            try:
                preferences = UserPreferences.objects.get(user=request.user)
                dark = preferences.dark_mode
            except UserPreferences.DoesNotExist:
                UserPreferences.objects.create(user=request.user, dark_mode=True)
                dark = True
        else:
            if "dark" in request.session:
                dark = request.session["dark"]
            else:
                request.session["dark"] = True
                dark = True
        return dark

    def get_context_data(self, **kwargs):
        if "dark" not in kwargs:
            kwargs["dark"] = self.get_scheme(self.request)
        return super().get_context_data(**kwargs)


class SchemeView(View):

    def dispatch(self, request, *args, **kwargs):
        dark = SchemeMixin.get_scheme(request)
        if dark:
            response = "dark"
        else:
            response = ""
        return HttpResponse(response, status=200)


class ToggleSchemeView(View):

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                preferences = UserPreferences.objects.get(user=request.user)
                preferences.dark_mode = not preferences.dark_mode
                preferences.save()
                request.session["dark"] = preferences.dark_mode
            except UserPreferences.DoesNotExist:
                UserPreferences.objects.create(user=request.user, dark_mode=True)
                request.session["dark"] = True
        else:
            if "dark" not in request.session:
                request.session["dark"] = True
            else:
                request.session["dark"] = not request.session["dark"]
        if request.session["dark"]:
            response = "<svg xmlns=\"http://www.w3.org/2000/svg\" class=\"h-5 w-5\" viewBox=\"0 0 20 20\" " \
                       "fill=\"currentColor\"><path fill-rule=\"evenodd\" d=\"M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 " \
                       "0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 " \
                       "1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 " \
                       "0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 " \
                       "011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 " \
                       "8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 " \
                       "000 2h1z\" clip-rule=\"evenodd\"></path></svg> "
        else:
            response = "<svg xmlns=\"http://www.w3.org/2000/svg\" class=\"h-5 w-5\" viewBox=\"0 0 20 20\" " \
                       "fill=\"currentColor\"><path d=\"M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 " \
                       "10.586z\"></path></svg>"

        return HttpResponse(content=response, status=200)


def set_host(request, context):
    if settings.EXTERNAL_IP is not None and settings.EXTERNAL_HOST_NAME is not None:
        context["ip"] = settings.EXTERNAL_IP
        context["hostname"] = settings.EXTERNAL_HOST_NAME
    else:
        host_ip, host_name = __get_address__(request.get_port())
        context["hostname"] = host_name
        port = request.get_port()
        if port == 80 or port == 443:
            context["ip"] = host_ip
        else:
            context["ip"] = f"{host_ip}:{port}"


# Origin: https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib by Jamieson Becker,
# Public domain.
def __get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except socket.error:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def __get_address__(port):
    host_name, host_ip, host_ipv6 = "", "", ""
    try:
        host_name = socket.getfqdn()
        host_ip = __get_ip()
    except socket.error:
        print("Unable to get Hostname and IP")
    return host_ip, host_name
