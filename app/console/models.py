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

from django.db import models
from django.utils.translation import gettext_lazy as _

from picker.models import Credential


class AuditManager(models.Manager):
    def create_audit(self, congregation, username, message):
        audit = self.create(congregation=congregation, username=username, message=message)
        return audit


class Audit(models.Model):
    class Meta:
        ordering = ["send_time"]

    congregation = models.ForeignKey(Credential, on_delete=models.CASCADE)
    username = models.CharField(_('username'), max_length=150)
    message = models.TextField(default="", blank=True)
    send_time = models.DateTimeField(auto_now=True)

    objects = AuditManager()


class TimeEntryManager(models.Manager):
    def create_time_entry(self, congregation, talk, start, stop, max_duration):
        audit = self.create(congregation=congregation, talk=talk, start=start, stop=stop, max_duration=max_duration)
        return audit


class TimeEntry(models.Model):
    class Meta:
        ordering = ["talk", "start"]

    congregation = models.ForeignKey(Credential, on_delete=models.CASCADE)
    talk = models.IntegerField()
    start = models.DateTimeField()
    stop = models.DateTimeField()
    max_duration = models.IntegerField()

    objects = TimeEntryManager()
