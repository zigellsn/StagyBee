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

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from stage.consumers import generate_channel_group_name

logger = logging.getLogger("django.request")


@require_POST
@csrf_exempt
def receiver(request, congregation):
    event = request.META.get('HTTP_X_STAGYBEE_EXTRACTOR_EVENT')
    if event == 'listeners':
        channel_layer = get_channel_layer()
        congregation_group_name = generate_channel_group_name("stage", congregation)
        async_to_sync(channel_layer.group_send)(
            congregation_group_name,
            {"type": "extractor_listeners", "listeners": request.body},
        )
        return HttpResponse('success')
    elif event == 'status':
        logger.info(str(request.body))
    elif event == 'meta':
        return HttpResponse('success')

    return HttpResponse(status=204)
