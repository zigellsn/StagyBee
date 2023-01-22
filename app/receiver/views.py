#  Copyright 2019-2023 Simon Zigelli
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

from channels.layers import get_channel_layer
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View

from stage.consumers import generate_channel_group_name


@method_decorator(csrf_exempt, name="dispatch")
class ReceiverView(View):

    @staticmethod
    async def post(request, *args, **kwargs):
        event = request.META.get("HTTP_X_STAGYBEE_EXTRACTOR_EVENT")
        channel_layer = get_channel_layer()
        congregation_group_name = generate_channel_group_name("stage", kwargs.get("pk"))
        if event == "listeners":
            await channel_layer.group_send(
                congregation_group_name,
                {"type": "extractor.listeners", "listeners": request.body},
            )
            return HttpResponse(content="success", status=202)
        elif event == "status":
            await channel_layer.group_send(
                congregation_group_name,
                {"type": "extractor.status", "status": request.body},
            )
            return HttpResponse(content="success", status=202)
        elif event == "meta":
            return HttpResponse(content="success", status=200)

        return HttpResponse(status=204)
