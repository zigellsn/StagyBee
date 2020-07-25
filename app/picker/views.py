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

import socket
from subprocess import call
from sys import platform

from django.conf import settings
from django.http import HttpResponse
from django.views.generic import ListView
from django.views.generic.base import View

from .models import Credential


class PickerView(ListView):
    model = Credential
    template_name = "picker/tiles.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        credentials = Credential.objects.all()
        col, size = __get_tiles_configuration__(credentials, settings.SHOW_LOGIN)
        if settings.RUN_IN_CONTAINER:
            context["ip"] = settings.EXTERNAL_IP
            context["hostname"] = settings.EXTERNAL_HOST_NAME
        else:
            host_ip, host_name = __get_address__(self.request.get_port())
            context["hostname"] = host_name
            port = self.request.get_port()
            if port == 80 or port == 443:
                context["ip"] = host_ip
            else:
                context["ip"] = f"{host_ip}:{port}"
        context["size"] = size
        context["col"] = col
        context["shutdown_icon"] = settings.SHOW_SHUTDOWN_ICON
        context["show_login"] = settings.SHOW_LOGIN
        context["version"] = settings.VERSION
        return context


class ShutdownView(View):

    @staticmethod
    def get(request):
        if platform.startswith("freebsd") or platform.startswith("linux") or platform.startswith(
                "aix") or platform.startswith("cygwin"):
            if settings.RUN_IN_CONTAINER:
                __write_signal_file__("shutdown_signal", "shutdown")
            else:
                call(["sh scripts/shutdown.sh", "-h", "now"], shell=False)
        elif platform.startswith("win32"):
            call(["scripts/shutdown.bat", "-h"], shell=False)
        return HttpResponse("Shutdown in progress")


class RebootView(View):

    @staticmethod
    def get(request):
        if platform.startswith("freebsd") or platform.startswith("linux") or platform.startswith(
                "aix") or platform.startswith("cygwin"):
            if settings.RUN_IN_CONTAINER:
                __write_signal_file__("shutdown_signal", "reboot")
            else:
                call(["sh scripts/shutdown.sh", "-r"], shell=False)
        elif platform.startswith("win32"):
            call(["scripts/shutdown.bat", "-r"], shell=False)
        return HttpResponse("Reboot in progress")


def __write_signal_file__(filename, mode):
    f = open(filename, "w")
    f.write(mode)
    f.close()


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
