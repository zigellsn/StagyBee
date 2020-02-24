from django.urls import path

from .views import PickerView, ShutdownView, RebootView

app_name = 'picker'

urlpatterns = [
    path('', PickerView.as_view(), name='picker'),
    path('shutdown/', ShutdownView.as_view(), name='shutdown'),
    path('reboot/', RebootView.as_view(), name='reboot'),
]
