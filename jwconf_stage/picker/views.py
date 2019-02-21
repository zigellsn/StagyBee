from django.shortcuts import render, redirect

from .models import Credential


def picker(request):
    credentials = Credential.objects.order_by('congregation')
    if credentials.count() == 1:
        return redirect('login:login', congregation=credentials[0].congregation)
    context = {'credentials': credentials}
    return render(request, "picker/tiles.html", context)
