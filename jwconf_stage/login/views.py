from django.shortcuts import get_object_or_404, render
import importlib

picker = importlib.import_module('picker.models')


def login(request, congregation):
    credentials = get_object_or_404(picker.Credential, congregation=congregation)
    context = {
        'congregation': credentials.congregation,
        'username': credentials.username,
        'password': credentials.password,
    }
    # TODO: Turn touch on or off
    return render(request, 'login/login.html', context)
