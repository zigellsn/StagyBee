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

import asyncio


GLOBAL_TIMERS = {}


class Timer:
    def __init__(self, interval, callback, first_immediately=True, timer_name="timer", context=None):
        self._interval = interval
        self._first_immediately = first_immediately
        self._callback = callback
        self._name = timer_name
        self._context = context
        self._is_first_call = True
        self._running = True
        self._task = asyncio.create_task(self._job())

    async def _job(self):
        try:
            while self._running:
                if not self._is_first_call or not self._first_immediately:
                    await asyncio.sleep(self._interval)
                await self._callback(self._name, self._context, self)
                self._is_first_call = False
            self._running = False
        except Exception as ex:
            print(ex)

    def get_context(self):
        return self._context

    def get_timer_name(self):
        return self._name

    def cancel(self):
        self._running = False
        self._task.cancel()
