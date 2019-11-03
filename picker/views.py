import socket
from subprocess import call
from sys import platform

from django.http import HttpResponse
from django.shortcuts import render

from .models import Credential


def picker(request):
    credentials = Credential.objects.order_by("congregation")
    host_ip, host_name = __get_address(request.get_port())

    col, size = __get_tiles_configuration(credentials)
    for cred in credentials:
        if not cred.display_name:
            cred.display_name = cred.congregation
    context = {"credentials": credentials, "ip": host_ip, "port": request.get_port(),
               "hostname": host_name, "shutdown_icon": True, "size": size, "col": col}
    return render(request, "picker/tiles.html", context)


def shutdown(request):
    if platform.startswith("freebsd") or platform.startswith("linux") or platform.startswith(
            "aix") or platform.startswith("cygwin"):
        call(["sh shutdown.sh", "-h", "now"], shell=False)
    elif platform.startswith("win32"):
        call(["shutdown.bat", "-h"], shell=False)
    return HttpResponse("Shutdown in progress")


def reboot(request):
    if platform.startswith("freebsd") or platform.startswith("linux") or platform.startswith(
            "aix") or platform.startswith("cygwin"):
        call(["sh shutdown.sh", "-r"], shell=False)
    elif platform.startswith("win32"):
        call(["shutdown.bat", "-r"], shell=False)
    return HttpResponse("Reboot in progress")


# Origin: https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib by Jamieson Becker,
# Public domain.
def __get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except socket.error:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def __get_address(port):
    host_name, host_ip, host_ipv6 = "", "", ""
    try:
        host_name = socket.getfqdn()
        host_ip = __get_ip()
    except socket.error:
        print("Unable to get Hostname and IP")
    return host_ip, host_name


def __get_tiles_configuration(credentials):
    if credentials.count() == 1:
        size = 2
        col = 0
    elif credentials.count() == 2:
        size = 2
        col = 0
    elif credentials.count() == 3:
        size = 3
        col = 2
    else:
        size = 4
        col = 3
    return col, size
