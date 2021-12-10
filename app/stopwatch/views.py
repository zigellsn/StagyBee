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
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, WeekArchiveView
from django.views.generic.base import TemplateView
from guardian.mixins import PermissionRequiredMixin

from StagyBee.views import SchemeMixin
from picker.models import Credential
from stage.consumers import generate_channel_group_name
from .models import TimeEntry
from .timer import GLOBAL_TIMERS, Timer


class TimerView(PermissionRequiredMixin, SchemeMixin, ListView):
    model = TimeEntry
    return_403 = True
    permission_required = "access_stopwatch"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.credentials = None
        TimeEntry.objects.delete_invalid()

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["congregation"] = self.credentials
        context["archive"] = True
        return context

    def get_permission_object(self):
        return get_object_or_404(Credential, congregation=self.kwargs.get("pk"))

    def get_queryset(self):
        self.credentials = get_object_or_404(Credential, congregation=self.kwargs.get("pk"))
        return TimeEntry.objects.by_congregation(congregation=self.credentials)


class ArchiveView(PermissionRequiredMixin, SchemeMixin, WeekArchiveView):
    model = TimeEntry
    date_field = "start"
    week_format = "%W"
    allow_empty = True
    allow_future = True
    return_403 = True
    permission_required = "access_stopwatch"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.credentials = None
        TimeEntry.objects.delete_invalid()

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["congregation"] = self.credentials
        return context

    def get_permission_object(self):
        return get_object_or_404(Credential, congregation=self.kwargs.get("pk"))

    def get_queryset(self):
        self.credentials = get_object_or_404(Credential, congregation=self.kwargs.get("pk"))
        return TimeEntry.objects.all_by_congregation(congregation=self.credentials)

    def get_week(self):
        week = super().get_week()
        return week - 1

    def get_dated_items(self):
        dates = super().get_dated_items()
        TimeEntry.objects.calculate_additional_values(dates[1])
        return dates


class StopwatchControlView(PermissionRequiredMixin, View):
    return_403 = True
    permission_required = "access_console"

    async def __call__(self, **kwargs):
        pass

    @staticmethod
    @async_to_sync
    async def post(request, *args, **kwargs):
        congregation = kwargs.get("pk")
        channel_layer = get_channel_layer()
        congregation_group_name = generate_channel_group_name("timer", congregation)
        if request.POST.get("action") == "timer-start":
            if congregation in GLOBAL_TIMERS:
                actual_timer = GLOBAL_TIMERS.get(congregation)
                if actual_timer is not None:
                    await actual_timer.cancel()
                    GLOBAL_TIMERS.pop(congregation)
            context = {
                "duration": timedelta(hours=float(request.POST.get("h")), minutes=float(request.POST.get("m")),
                                      seconds=float(request.POST.get("s"))),
                "start": timezone.now(),
                "index": request.POST.get("talk_index"),
                "congregation": congregation,
                "running": True}
            timer = Timer(1, None, context=context, timer_name=request.POST.get("talk_name"))
            GLOBAL_TIMERS[congregation] = timer
            await channel_layer.group_send(congregation_group_name, {"type": "timer.action"})
        elif request.POST.get("action") == "timer-stop":
            if congregation in GLOBAL_TIMERS and GLOBAL_TIMERS[congregation] is not None:
                await GLOBAL_TIMERS[congregation].cancel()
                GLOBAL_TIMERS.pop(congregation)
        else:
            return HttpResponse(status=404)
        return HttpResponse(status=202)


class NewestArchiveView(PermissionRequiredMixin, SchemeMixin, TemplateView):
    return_403 = True
    permission_required = "access_console"
    template_name = "stopwatch/fragments/timeentry_list_item.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.credentials = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.credentials = get_object_or_404(Credential, congregation=self.kwargs.get("pk"))
        context["time_entry"] = TimeEntry.objects.newest(kwargs.get("pk"))
        return context

    def get_permission_object(self):
        return get_object_or_404(Credential, congregation=self.kwargs.get("pk"))
