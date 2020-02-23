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

from . import views

app_name = 'console'

js_info = {
   'domain': 'django',
   'packages': None,
}

urlpatterns = [
    path('', views.choose_console, name='chose_console'),
    path('<str:congregation>', views.console, name='console'),
    path('timer/<str:congregation>', views.timer, name='timer'),
    path('audit/<str:congregation>', views.audit, name='audit'),
    path('settings/', views.settings, name='settings'),
    path('jsi18n/', JavaScriptCatalog.as_view(), js_info, name='javascript-catalog'),
]
