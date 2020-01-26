
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

from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path

from .views import redirect_root

urlpatterns = []
urlpatterns += i18n_patterns(
    path('', include('django.contrib.auth.urls')),
    path('', redirect_root),
    path('stage/', include('stage.urls')),
    path('picker/', include('picker.urls')),
    path('receiver/', include('receiver.urls')),
    path('console/', include('console.urls')),
    path('admin/', admin.site.urls),
    prefix_default_language=False
)
