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
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import get_perms

from console.models import Audit, TimeEntry
from picker.models import Credential
from .forms import CongregationForm


@login_required
def choose_console(request):
    if request.method == 'POST':
        form = CongregationForm(request.POST)
        if form.is_valid():
            congregation = form.cleaned_data["congregation"].congregation
            return HttpResponseRedirect(f"/console/{congregation}")
    else:
        form = CongregationForm()
        if len(form.congregation_set) < 10:
            return render(request, "console/choose_console_cards.html", {"congregations": form.congregation_set})
        else:
            return render(request, "console/choose_console.html", {"form": form})
    return render(request, "console/choose_console.html", {"form": form})


@login_required
def console(request, congregation):
    credentials = get_object_or_404(Credential, congregation=congregation)
    if 'access_console' in get_perms(request.user, credentials):
        return render(request, "console/console.html",
                      {"congregation_ws": mark_safe(congregation), "credentials": credentials})
    else:
        return HttpResponse(_("Nicht berechtigt"))


@login_required
def timer(request, congregation):
    credentials = get_object_or_404(Credential, congregation=congregation)
    date = datetime.now() - timedelta(days=config("KEEP_TIMER_DAYS", default=30))
    TimeEntry.objects.filter(start__lt=date).delete()
    time_entries = TimeEntry.objects.filter(congregation=credentials, start__day=datetime.now().day,
                                            start__month=datetime.now().month, start__year=datetime.now().year)
    for time_entry in time_entries:
        td1 = time_entry.stop - time_entry.start
        time_entry.duration = __get_duration_string(td1.seconds)
        td2 = timedelta(seconds=time_entry.max_duration)
        time_entry.display_max_duration = __get_duration_string(time_entry.max_duration)

        if td2 > td1:
            difference = td2 - td1
            time_entry.difference = __get_duration_string(difference.seconds)
        else:
            difference = td1 - td2
            time_entry.difference = "-" + __get_duration_string(difference.seconds)

    if 'access_stopwatch' in get_perms(request.user, credentials):
        return render(request, "console/timer.html",
                      {"congregation_ws": mark_safe(congregation), "time_entries": time_entries})
    else:
        return HttpResponse(_("Nicht berechtigt"))


@login_required
def audit(request, congregation):
    credentials = get_object_or_404(Credential, congregation=congregation)
    if 'access_audit_log' in get_perms(request.user, credentials):
        date = datetime.now() - timedelta(days=180)
        Audit.objects.filter(send_time__lt=date).delete()
        log = Audit.objects.filter(congregation__exact=congregation)
        return render(request, "console/audit.html", {"log": log})
    else:
        return HttpResponse(_("Nicht berechtigt"))


@login_required
def settings(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, _("Das Passwort wurde geändert."))
            return redirect('console:settings')
        else:
            messages.error(request, _("Bitte den unten stehenden Fehler korrigieren."))
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, "console/settings.html", {"no_settings": True, "form": form})


def __get_duration_string(timespan):
    hours, minutes, seconds = timespan // 3600, timespan // 60 % 60, timespan % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"
