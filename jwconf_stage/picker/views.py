from django.shortcuts import render, redirect
from django.http import HttpResponse
from subprocess import call

from .models import Credential


def picker(request):
    credentials = Credential.objects.order_by('congregation')
    if credentials.count() == 1:
        if credentials[0].autologin:
            return redirect("https://jwconf.org/?key=%s" % credentials[0].autologin)
        else:
            return redirect('login:login', congregation=credentials[0].congregation)
    context = {'credentials': credentials}
    return render(request, "picker/tiles.html", context)


def confirm_shutdown(request):
    return render(request, "picker/shutdown.html")


def shutdown(request):
    call(['shutdown', '-h', 'now'], shell=False)
    return HttpResponse("Shutdown in progress")

