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
import asyncio

from django.utils import timezone

GLOBAL_TIMEOUT = {}


class Timeout:
    def __init__(self, callback=None):
        self._task = None
        self.count = 1
        self.start_time = timezone.localtime(timezone.now())
        if callback is not None:
            self._task = asyncio.create_task(callback)

    def cancel(self):
        if self._task is not None:
            self._task.cancel()

    def set_timeout(self, callback):
        self.cancel()
        self._task = asyncio.create_task(callback)
