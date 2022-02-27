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
from datetime import timedelta

from channels.db import database_sync_to_async
from django.utils import timezone

from StagyBee.settings import env
from picker.models import Credential
from stopwatch.models import TimeEntry

GLOBAL_TIMERS = {}


class Timer:
    def __init__(self, interval, callback, first_immediately=True, timer_name="timer", context=None):
        self._interval = interval
        self._first_immediately = first_immediately
        self._callback = callback
        self._name = timer_name
        self._context = context
        self._is_first_call = True
        self._running = False
        self._task = None
        if callback is not None:
            self._running = True
            self._task = asyncio.create_task(self._job())

    async def _job(self):
        try:
            while self._running:
                if not self._is_first_call or not self._first_immediately:
                    await asyncio.sleep(self._interval)
                if self._running:
                    await self._callback(self, self._running)
                self._is_first_call = False
            self._running = False
        except Exception as ex:
            print(ex)

    def is_running(self):
        return self._running

    def get_context(self):
        return self._context

    def set_callback(self, callback):
        if self._callback is None:
            self._callback = callback
            self._running = True
            self._task = asyncio.create_task(self._job())
        else:
            self._callback = callback

    def get_timer_name(self):
        return self._name

    def get_elapsed_time(self):
        if "start" in self._context:
            return timezone.localtime(timezone.now()) - self._context["start"]
        else:
            return None

    def get_formatted_elapsed_time(self):
        time_delta = self.get_elapsed_time()
        if time_delta is not None:
            return self._time_delta_to_string(time_delta)
        else:
            return "00:00:00"

    def get_remaining_time(self):
        elapsed_time = self.get_elapsed_time()
        if "duration" in self._context and elapsed_time is not None:
            return self._context["duration"] - elapsed_time
        else:
            return None

    def get_formatted_remaining_time(self):
        remaining_time = self.get_remaining_time()
        if remaining_time is not None:
            if remaining_time > timedelta():
                return self._time_delta_to_string(remaining_time)
            else:
                return f"-{self._time_delta_to_string(abs(remaining_time))}"
        else:
            return "00:00:00"

    def get_elapsed_percentage(self):
        if "duration" in self._context:
            return (self.get_elapsed_time() / self._context["duration"]) * 100
        else:
            return 0.0

    async def cancel(self):
        self._running = False
        await self._persist_time_entry()
        if self._task is not None:
            self._task.cancel()
        if self._callback is not None:
            await self._callback(self, self._running)

    @staticmethod
    def _time_delta_to_string(delta) -> str:
        mm, ss = divmod(delta.seconds, 60)
        hh, mm = divmod(mm, 60)
        s = f"{hh:02d}:{mm:02d}:{ss:02d}"
        if delta.days:
            def plural(n):
                return n, abs(n) != 1 and "s" or ""

            s = f"{plural(delta.days)[0]} day{plural(delta.days)[1]}, {s}"
        return s

    async def _persist_time_entry(self):
        elapsed_time = self.get_elapsed_time()
        if elapsed_time is None or elapsed_time < timedelta(seconds=env.int("DO_NOT_SAVE_TIMER_DELTA", default=15)):
            return
        if "congregation" in self._context and "duration" in self._context and "start" in self._context:
            congregation = await database_sync_to_async(Credential.objects.get)(
                congregation__exact=self._context.get("congregation"))
            await database_sync_to_async(TimeEntry.objects.create_time_entry)(congregation, self._name,
                                                                              self._context.get("start"),
                                                                              timezone.now(),
                                                                              self._context.get(
                                                                                  "duration").total_seconds())
