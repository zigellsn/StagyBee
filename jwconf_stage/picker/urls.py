from django.urls import path

from . import views

app_name = 'picker'
urlpatterns = [
    path('', views.picker, name='picker'),
    path('confirm_shutdown/', views.confirm_shutdown, name='confirm_shutdown'),
    path('shutdown/', views.shutdown, name='shutdown'),
]
