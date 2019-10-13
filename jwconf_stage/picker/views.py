from subprocess import call

from django.http import HttpResponse
from django.shortcuts import render, redirect
import socket

from .models import Credential


def picker(request):
    credentials = Credential.objects.order_by('congregation')
    if credentials.count() == 1:
        return redirect('login:login', congregation=credentials[0].congregation)
    host_name, host_ip = '', ''
    try:
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
    except socket.error:
        print("Unable to get Hostname and IP")
    context = {'credentials': credentials, 'ip': host_ip, 'port': request.get_port(), 'hostname': host_name}
    return render(request, "picker/tiles.html", context)


def confirm_shutdown(request):
    return render(request, "picker/shutdown.html")


def shutdown(request):
    call(['shutdown', '-h', 'now'], shell=False)
    return HttpResponse("Shutdown in progress")
