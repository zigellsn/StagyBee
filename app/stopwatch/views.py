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

from django.shortcuts import get_object_or_404
from django.views.generic import ListView
from guardian.mixins import PermissionRequiredMixin

from console.models import TimeEntry
from picker.models import Credential


class TimerView(PermissionRequiredMixin, ListView):
    model = TimeEntry
    return_403 = True
    permission_required = "access_stopwatch"
    template_name = "stopwatch/timer.html"

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
        return TimeEntry.objects.by_congregation(congregation=self.credentials)