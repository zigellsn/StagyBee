#  Copyright 2019 Simon Zigelli
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
from datetime import datetime, timedelta

from decouple import config
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView, FormView
from django.views.generic.edit import FormMixin
from guardian.mixins import LoginRequiredMixin, PermissionRequiredMixin

from console.models import Audit, TimeEntry
from picker.models import Credential
from .forms import CongregationForm


class ChooseConsoleView(LoginRequiredMixin, FormMixin, ListView):
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


class ConsoleView(PermissionRequiredMixin, DetailView):
    model = Credential
    return_403 = True
    permission_required = "access_console"
    template_name = "console/console.html"


def __get_duration_string__(timespan):
    hours, minutes, seconds = timespan // 3600, timespan // 60 % 60, timespan % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"


class TimerView(PermissionRequiredMixin, ListView):
    model = TimeEntry
    return_403 = True
    permission_required = "access_stopwatch"
    template_name = "console/timer.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.credentials = None
        date = datetime.now() - timedelta(days=config("KEEP_TIMER_DAYS", default=30))
        TimeEntry.objects.filter(start__lt=date).delete()

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["congregation"] = self.credentials
        return context

    def get_permission_object(self):
        return get_object_or_404(Credential, congregation=self.kwargs.get("pk"))

    def get_queryset(self):
        self.credentials = get_object_or_404(Credential, congregation=self.kwargs.get("pk"))
        time_entries = TimeEntry.objects.filter(congregation=self.credentials, start__day=datetime.now().day,
                                                start__month=datetime.now().month, start__year=datetime.now().year)
        for time_entry in time_entries:
            td1 = time_entry.stop - time_entry.start
            time_entry.duration = __get_duration_string__(td1.seconds)
            td2 = timedelta(seconds=time_entry.max_duration)
            time_entry.display_max_duration = __get_duration_string__(time_entry.max_duration)

            if td2 > td1:
                difference = td2 - td1
                time_entry.difference = __get_duration_string__(difference.seconds)
            else:
                difference = td1 - td2
                time_entry.difference = "-" + __get_duration_string__(difference.seconds)
        return time_entries


class AuditView(PermissionRequiredMixin, ListView):
    model = Audit
    return_403 = True
    permission_required = "access_audit_log"
    template_name = "console/audit.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        date = datetime.now() - timedelta(days=180)
        Audit.objects.filter(send_time__lt=date).delete()

    def get_queryset(self):
        credentials = get_object_or_404(Credential, congregation=self.kwargs.get("pk"))
        return Audit.objects.filter(congregation__exact=credentials)

    def get_permission_object(self):
        return get_object_or_404(Credential, congregation=self.kwargs.get("pk"))


class SettingsView(LoginRequiredMixin, FormView):
    model = User
    template_name = 'console/settings.html'
    form_class = PasswordChangeForm
    success_url = '/settings/'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, _("Das Passwort wurde geändert."))
        return super().form_valid(form)
