from django.urls import path

from . import views

app_name = 'picker'
urlpatterns = [
    path('', views.picker, name='picker'),
]
