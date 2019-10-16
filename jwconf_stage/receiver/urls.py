from django.urls import path

from . import views

app_name = 'receiver'
urlpatterns = [
    path('<str:session_id>', views.receiver, name='receiver'),
]
