#  Copyright 2019-2020 Simon Zigelli
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

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from django.views.i18n import JavaScriptCatalog

from console.views import SettingsView, StartupView
from .views import redirect_root, toggle_scheme, scheme

urlpatterns = []
urlpatterns += i18n_patterns(
    path('', redirect_root),
    path('', include('django.contrib.auth.urls')),
    path('toggle_scheme/', toggle_scheme),
    path('scheme/', scheme),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path('stage/', include('stage.urls')),
    path('picker/', include('picker.urls')),
    path('receiver/', include('receiver.urls')),
    path('console/', include('console.urls')),
    path('startup/', StartupView.as_view(), name='startup'),
    path('notification/', include('notification.urls')),
    path('admin/', admin.site.urls),
    path('settings/', SettingsView.as_view(), name='settings'),
    prefix_default_language=True
)

if settings.DEBUG:
    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        urlpatterns = [
                          path('__debug__/', include(debug_toolbar.urls)),
                      ] + urlpatterns
