from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
import importlib
import urllib.parse

picker = importlib.import_module('picker.models')


def login(request, congregation):
    if 'HTTP_REFERER' in request.META and "picker" not in request.META['HTTP_REFERER']:
        return redirect('picker')
    credentials = get_object_or_404(picker.Credential, congregation=congregation)
    context = {
        'congregation': credentials.congregation,
        'username': credentials.username,
        'password': credentials.password,
        'autologin': credentials.autologin,
        'touch': credentials.touch,
    }
    return render(request, 'login/login.html', context)


def login_form(request, congregation):
    credentials = get_object_or_404(picker.Credential, congregation=congregation)
    context = {
        'congregation': credentials.congregation,
        'username': credentials.username,
        'password': credentials.password,
        'autologin': credentials.autologin,
    }
    return render(request, 'login/login_form.html', context)


class LoginExtractorView(View):

    def get(self, request, congregation):
        congregation_ws = urllib.parse.quote(congregation)
        credentials = get_object_or_404(picker.Credential, congregation=congregation)
        context = {
            'congregation': credentials.congregation,
            'username': credentials.username,
            'password': credentials.password,
            'autologin': credentials.autologin,
            'congregation_ws': urllib.parse.quote(credentials.congregation)
        }
        return render(request, 'login/login_extractor.html', context)
