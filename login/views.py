import urllib.parse

from django.shortcuts import get_object_or_404, render, redirect

from picker.models import Credential


def login(request, congregation):
    if 'HTTP_REFERER' in request.META and "picker" not in request.META['HTTP_REFERER']:
        return redirect('picker')
    credentials = get_object_or_404(Credential, congregation=congregation)
    congregation_ws = urllib.parse.quote(congregation)
    context = {
        'congregation': credentials.congregation,
        'username': credentials.username,
        'password': credentials.password,
        'autologin': credentials.autologin,
        'touch': credentials.touch,
        'congregation_ws': congregation_ws
    }
    if credentials.touch:
        return render(request, 'login/login.html', context)
    else:
        return render(request, 'login/login_extractor.html', context)


def login_form(request, congregation):
    credentials = get_object_or_404(Credential, congregation=congregation)
    context = {
        'congregation': credentials.congregation,
        'username': credentials.username,
        'password': credentials.password,
        'autologin': credentials.autologin,
    }
    return render(request, 'login/login_form.html', context)
