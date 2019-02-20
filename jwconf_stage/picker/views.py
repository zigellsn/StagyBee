from django.shortcuts import render

from .models import Credential


def picker(request):
    credentials = Credential.objects.order_by('-congregation')
    context = {'credentials': credentials}
    return render(request, "picker/tiles.html", context)
