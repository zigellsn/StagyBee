#  Copyright 2019 Simon Zigelli
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from django.urls import path
from django.views.i18n import JavaScriptCatalog

from .views import ConsoleView, ChooseConsoleView, AuditView, TimerView, SettingsView

app_name = 'console'

urlpatterns = [
    path('', ChooseConsoleView.as_view(), name='choose_console'),
    path('<str:pk>', ConsoleView.as_view(), name='console'),
    path('timer/<str:pk>', TimerView.as_view(), name='timer'),
    path('audit/<str:pk>', AuditView.as_view(), name='audit'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
]
