from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from subprocess import call

from .models import Credential


def picker(request):
    credentials = Credential.objects.order_by('congregation')
    if credentials.count() == 1:
        return redirect('login:login', congregation=credentials[0].congregation)
    context = {'credentials': credentials}
    return render(request, "picker/tiles.html", context)


def confirm_shutdown(request):
    return render(request, "picker/shutdown.html")


def shutdown(request):
    call(['shutdown', '-h', 'now'], shell=False)
    return HttpResponse("Shutdown in progress")

