from subprocess import call

from django.http import HttpResponse
from django.shortcuts import render, redirect
import socket

from .models import Credential


def picker(request):
    credentials = Credential.objects.order_by('congregation')
    if credentials.count() == 1:
        return redirect('login:login', congregation=credentials[0].congregation)
    host_ip, host_name = get_address()
    if credentials.count() <= 2:
        size = 3
        col = 1
    else:
        size = 4
        col = 3
    context = {'credentials': credentials, 'ip': host_ip, 'port': request.get_port(), 'hostname': host_name,
               'shutdown_icon': True, 'size': size, 'col': col}
    return render(request, "picker/tiles.html", context)


def shutdown(request):
    call(['shutdown', '-h', 'now'], shell=False)
    return HttpResponse("Shutdown in progress")


def reboot(request):
    call(['shutdown', '-r', 'now'], shell=False)
    return HttpResponse("Reboot in progress")


def get_address():
    host_name, host_ip = '', ''
    try:
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
    except socket.error:
        print("Unable to get Hostname and IP")
    return host_ip, host_name
