#  Copyright 2019-2024 Simon Zigelli
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

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from picker.models import Credential


class AuditQuerySet(QuerySet):
    def invalid(self):
        date = timezone.now() - timedelta(days=settings.KEEP_TIMER_DAYS)
        return self.filter(send_time__lt=date)

    def by_congregation(self, congregation):
        return self.filter(congregation=congregation)


class AuditManager(models.Manager):

    def get_query_set(self):
        return AuditQuerySet(self.model, using=self._db)

    def create_audit(self, congregation, user, message):
        self.delete_invalid()
        return self.create(congregation=congregation, user=user, message=message)

    def delete_invalid(self):
        return self.get_query_set().invalid().delete()

    def by_congregation(self, congregation):
        self.delete_invalid()
        return self.get_query_set().by_congregation(congregation)


class Audit(models.Model):

    congregation = models.ForeignKey(Credential, on_delete=models.CASCADE, related_name="audits")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="audits")
    message = models.TextField(db_default="", blank=True)
    send_time = models.DateTimeField(default=timezone.now)

    objects = AuditManager()

    class Meta:
        ordering = ["-send_time"]
