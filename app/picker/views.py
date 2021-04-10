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

from subprocess import call
from sys import platform

from django.conf import settings
from django.http import HttpResponse
from django.views.generic import ListView
from django.views.generic.base import View

from StagyBee.views import set_host, get_scheme
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
