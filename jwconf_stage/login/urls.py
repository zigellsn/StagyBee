from django.urls import path

from . import views

app_name = 'login'
urlpatterns = [
    path('<str:congregation>', views.login, name='login'),
    ]
