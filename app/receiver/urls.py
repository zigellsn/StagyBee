from django.urls import path

from .views import ReceiverView

app_name = 'receiver'

urlpatterns = [
    path('<str:pk>/', ReceiverView.as_view(), name='receiver'),
]
