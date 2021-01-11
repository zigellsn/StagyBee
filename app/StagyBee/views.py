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

import socket

from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse


def redirect_root(request):
    return HttpResponseRedirect('/login/')


def toggle_scheme(request):
    if "dark" not in request.session:
        request.session["dark"] = True
    else:
        request.session["dark"] = not request.session["dark"]
    return HttpResponse(status=200)


def set_host(request, context):
    if settings.RUN_IN_CONTAINER:
        context["ip"] = settings.EXTERNAL_IP
        context["hostname"] = settings.EXTERNAL_HOST_NAME
    else:
        host_ip, host_name = __get_address__(request.get_port())
        context["hostname"] = host_name
        port = request.get_port()
        if port == 80 or port == 443:
            context["ip"] = host_ip
        else:
            context["ip"] = f"{host_ip}:{port}"


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


def __get_address__(port):
    host_name, host_ip, host_ipv6 = "", "", ""
    try:
        host_name = socket.getfqdn()
        host_ip = __get_ip()
    except socket.error:
        print("Unable to get Hostname and IP")
    return host_ip, host_name
