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
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import DetailView

from StagyBee.views import SchemeMixin
from picker.models import Credential
from stage.consumers import generate_channel_group_name


class StageView(SchemeMixin, DetailView):
    model = Credential

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if 'HTTP_REFERER' in request.META and "picker" not in request.META['HTTP_REFERER']:
            return redirect('picker')

    @method_decorator(xframe_options_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_template_names(self):
        if self.get_object().touch:
            return "stage/stage.html"
        else:
            return "stage/stage_extractor.html"


class ExtractorConnectView(View):

    def post(self, request, *args, **kwargs):
        congregation = kwargs.get("pk")
        channel_layer = get_channel_layer()
        stage_congregation_group_name = generate_channel_group_name("stage", congregation)
        if request.POST.get("action") == "connect":
            async_to_sync(channel_layer.group_send)(
                stage_congregation_group_name,
                {"type": "extractor.connect"}
            )
        else:
            return HttpResponse(status=404)
        return HttpResponse(status=202)
