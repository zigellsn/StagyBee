#  Copyright 2019-2022 Simon Zigelli
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

from stopwatch.views import TimerView, ArchiveView, StopwatchControlView, NewestArchiveView

app_name = 'stopwatch'

urlpatterns = [
    path('<str:pk>/', TimerView.as_view(), name='timer'),
    path('<str:pk>/stopwatch/', StopwatchControlView.as_view(), name='stopwatch'),
    path('<str:pk>/newest/', NewestArchiveView.as_view(), name='newest'),
    path('<str:pk>/<int:year>/<int:week>/', ArchiveView.as_view(), name='archive'),
]

