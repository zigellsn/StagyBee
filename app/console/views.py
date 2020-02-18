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

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from guardian.shortcuts import get_perms

from console.models import Audit
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
        return render(request, "console/console.html", {"congregation_ws": mark_safe(congregation)})
    else:
        return HttpResponse(_("Nicht berechtigt"))


@login_required
def timer(request, congregation):
    credentials = get_object_or_404(Credential, congregation=congregation)
    if 'access_stopwatch' in get_perms(request.user, credentials):
        return render(request, "console/timer.html", {"congregation_ws": mark_safe(congregation)})
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
