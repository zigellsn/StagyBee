#  Copyright 2025 Simon Zigelli
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
from django.views.decorators.csrf import csrf_exempt
from ninja import NinjaAPI

from StagyBee.views import SchemeMixin
from stage.consumers import generate_channel_group_name

api = NinjaAPI(csrf=True)


@api.post("/receiver/{pk}")
@csrf_exempt
async def receiver(request, pk):
    event = request.META.get("HTTP_X_STAGYBEE_EXTRACTOR_EVENT")
    channel_layer = get_channel_layer()
    congregation_group_name = generate_channel_group_name("stage", pk)
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


@api.get("/scheme")
def scheme(request):
    active_scheme = SchemeMixin.get_scheme(request)
    return HttpResponse(active_scheme, status=200)
