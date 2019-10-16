from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
import importlib
# import requests

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
        credentials = get_object_or_404(picker.Credential, congregation=congregation)
        context = {
            'congregation': credentials.congregation,
            'username': credentials.username,
            'password': credentials.password,
            'autologin': credentials.autologin,
        }
        if not request.session.session_key:
            request.session.create()
        print(request.session.session_key)
        url = "http://127.0.0.1:8000/receiver/%s" % request.session.session_key
        if credentials.autologin is not None:
            payload = {"id": credentials.autologin, "url": url}
        else:
            payload = {"congregation": credentials.congregation,
                       "username": credentials.username,
                       "password": credentials.password,
                       "url": url}
        # response = requests.post("http://localhost:5000/api/subscribe",
        #                          json=payload)
        # result = response.json()
        return render(request, 'login/login_extractor.html', context)
