from django.shortcuts import get_object_or_404, render

from picker.models import Credential


def login(request, congregation):
    credentials = get_object_or_404(Credential, congregation=congregation)
    context = {
        'congregation': credentials.congregation,
        'username': credentials.username,
        'password': credentials.password,
    }
    # TODO: Turn touch on or off
    return render(request, 'login/login.html', context)
