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

from datetime import timedelta, datetime

from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from picker.models import Credential


class TimeEntryQuerySet(QuerySet):

    def invalid(self):
        date = timezone.now() - timedelta(days=settings.KEEP_TIMER_DAYS)
        return self.filter(start__lt=date)

    def all_by_congregation(self, congregation):
        return self.filter(congregation=congregation)


class TimeEntryManager(models.Manager):

    def get_query_set(self):
        return TimeEntryQuerySet(self.model, using=self._db)

    def create_time_entry(self, congregation, talk, start, stop, max_duration):
        return self.create(congregation=congregation, talk=talk, start=start, stop=stop, max_duration=max_duration)

    def delete_invalid(self):
        return self.get_query_set().invalid().delete()

    def all_by_congregation(self, congregation):
        time_entries = self.get_query_set().all_by_congregation(congregation)
        return self.calculate_additional_values(time_entries)

    def by_congregation(self, congregation):
        now = datetime.now()
        time_entries = self.all_by_congregation(congregation).filter(congregation=congregation, start__day=now.day,
                                                                     start__month=now.month, start__year=now.year)
        return self.calculate_additional_values(time_entries)

    @staticmethod
    def calculate_additional_values(time_entries):
        for time_entry in time_entries:
            td1 = time_entry.stop - time_entry.start
            time_entry.duration = __get_duration_string__(td1.seconds)
            td2 = timedelta(seconds=time_entry.max_duration)
            time_entry.display_max_duration = __get_duration_string__(time_entry.max_duration)

            if td2 > td1:
                difference = td2 - td1
                time_entry.difference = __get_duration_string__(difference.seconds)
            else:
                difference = td1 - td2
                time_entry.difference = "-" + __get_duration_string__(difference.seconds)
        return time_entries


class TimeEntry(models.Model):
    class Meta:
        ordering = ["start"]

    congregation = models.ForeignKey(Credential, on_delete=models.CASCADE)
    talk = models.CharField(max_length=255)
    start = models.DateTimeField()
    stop = models.DateTimeField()
    max_duration = models.IntegerField()

    objects = TimeEntryManager()


def __get_duration_string__(timespan):
    hours, minutes, seconds = timespan // 3600, timespan // 60 % 60, timespan % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"
