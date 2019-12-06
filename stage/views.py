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

import urllib.parse

from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.clickjacking import xframe_options_exempt

from picker.models import Credential


@xframe_options_exempt
def stage(request, congregation):
    if 'HTTP_REFERER' in request.META and "picker" not in request.META['HTTP_REFERER']:
        return redirect('picker')
    credentials = get_object_or_404(Credential, congregation=congregation)
    congregation_ws = urllib.parse.quote(congregation)
    context = {
        'congregation': credentials.congregation,
        'username': credentials.username,
        'password': credentials.password,
        'autologin': credentials.autologin,
        'touch': credentials.touch,
        'show_only_request_to_speak': credentials.show_only_request_to_speak,
        'congregation_ws': congregation_ws
    }
    if credentials.touch:
        return render(request, 'stage/stage.html', context)
    else:
        return render(request, 'stage/stage_extractor.html', context)


@xframe_options_exempt
def stage_form(request, congregation):
    credentials = get_object_or_404(Credential, congregation=congregation)
    context = {
        'congregation': credentials.congregation,
        'username': credentials.username,
        'password': credentials.password,
        'autologin': credentials.autologin,
    }
    return render(request, 'stage/stage_form.html', context)
