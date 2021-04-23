#  Copyright 2019-2021 Simon Zigelli
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

from django.urls import path, include

from .views import ConsoleView, ChooseConsoleView, KnownClientCreate, KnownClientDelete, KnownClientUpdate, \
    KnownClientReboot, KnownClientShutdown

app_name = "console"

urlpatterns = [
    path("", ChooseConsoleView.as_view(), name="choose_console"),
    path("<str:pk>/", ConsoleView.as_view(), name="console"),
    path("audit/", include("audit.urls")),
    path("timer/", include("stopwatch.urls")),
    path("knownclient/create/", KnownClientCreate.as_view(), name="knownclient_create"),
    path("knownclient/update/<int:pk>/", KnownClientUpdate.as_view(), name="knownclient_update"),
    path("knownclient/delete/<int:pk>/", KnownClientDelete.as_view(), name="knownclient_delete"),
    path("knownclient/shutdown/<int:pk>/", KnownClientShutdown.as_view(), name="knownclient_shutdown"),
    path("knownclient/reboot/<int:pk>/", KnownClientReboot.as_view(), name="knownclient_reboot"),
]
