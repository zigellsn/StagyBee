from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from stage.consumers import generate_channel_group_name


@require_POST
@csrf_exempt
def receiver(request, congregation):
    event = request.META.get('HTTP_X_JWCONFEXTRACTOR_EVENT')
    if event == 'listeners':
        channel_layer = get_channel_layer()
        congregation_group_name = generate_channel_group_name("stage", congregation)
        async_to_sync(channel_layer.group_send)(
            congregation_group_name,
            {"type": "extractor_listeners", "listeners": request.body},
        )
        return HttpResponse('success')
    elif event == 'meta':
        return HttpResponse('success')

    return HttpResponse(status=204)
