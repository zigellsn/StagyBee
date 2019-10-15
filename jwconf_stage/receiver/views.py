from django.http import HttpResponse, HttpResponseForbidden
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


@require_POST
@csrf_exempt
def receiver(request):
    event = request.META.get('HTTP_X_JWCONFEXTRACTOR_ACTION', 'listeners')

    if event == 'listeners':
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "extractor",
            {"type": "extractor.listeners", "message": request.body.decode("utf-8")},
        )
        return HttpResponse('success')
    elif event == 'meta':
        return HttpResponse('success')

    return HttpResponse(status=204)
