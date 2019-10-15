from django.urls import path

from . import views

app_name = 'receiver'
urlpatterns = [
    path('', views.receiver, name='receiver'),
]
