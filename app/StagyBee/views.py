#  Copyright 2019-2024 Simon Zigelli
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
from django.views.generic.base import ContextMixin

from console.models import UserPreferences


class SchemeMixin(ContextMixin):

    @staticmethod
    def get_scheme(request):
        preferences = None
        if request.user.is_authenticated:
            if "actual" in request.GET:
                try:
                    preferences = UserPreferences.objects.get(user=request.user)
                    if request.GET["actual"] == "light":
                        preferences.scheme = UserPreferences.Scheme.LIGHT
                    elif request.GET["actual"] == "dark":
                        preferences.scheme = UserPreferences.Scheme.DARK
                    else:
                        preferences.scheme = UserPreferences.Scheme.FOLLOW
                    preferences.save()
                except UserPreferences.DoesNotExist:
                    UserPreferences.objects.create(user=request.user, scheme=UserPreferences.Scheme.LIGHT)
            else:
                try:
                    preferences = UserPreferences.objects.get(user=request.user)
                except UserPreferences.DoesNotExist:
                    UserPreferences.objects.create(user=request.user, scheme=UserPreferences.Scheme.LIGHT)
        if preferences is not None:
            request.session["scheme"] = preferences.scheme
        else:
            request.session["scheme"] = UserPreferences.Scheme.LIGHT
        return request.session["scheme"]

    def get_context_data(self, **kwargs):
        if "scheme" not in kwargs:
            kwargs["scheme"] = self.get_scheme(self.request)
        return super().get_context_data(**kwargs)


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
