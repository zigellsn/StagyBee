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
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class NotificationQuerySet(QuerySet):

    def by_state(self, active=True, show_in_locale=None):
        if show_in_locale is None:
            show_in_locale = ["en"]
        if " " not in show_in_locale:
            show_in_locale.append(" ")
        return self.filter(active=active, show_in_locale__in=show_in_locale, max_duration__gt=timezone.now())


class NotificationManager(models.Manager):

    def get_query_set(self):
        return NotificationQuerySet(self.model, using=self._db)

    def create_notification(self, user, message, importance=1, max_duration=timezone.now() + timedelta(days=30)):
        return self.create(user=user, message=message, importance=importance, max_duration=max_duration)

    def by_state(self, active=True, show_in_locale=None):
        return self.get_query_set().by_state(active, show_in_locale)


class Notification(models.Model):
    class Meta:
        ordering = ["-create_date", "-importance"]

    class Importance(models.IntegerChoices):
        INFORMATION = 0, _('Information')
        IMPORTANT = 1, _('Wichtig')
        URGENT = 2, _('Dringend')
        ERROR = 3, _('Warnung')

    subject = models.CharField(default="", max_length=255, verbose_name=_("Betreff"))
    message = models.TextField(default="", blank=True, verbose_name=_("Nachricht"))
    locale = models.CharField(default=" ", max_length=10, verbose_name=_("Sprache der Nachricht"))
    show_in_locale = models.CharField(default=" ", max_length=10, verbose_name=_("Anzeigen für Sprache"))
    importance = models.IntegerField(choices=Importance.choices, default=Importance.INFORMATION,
                                     verbose_name=_("Wichtigkeit"))
    max_duration = models.DateField(verbose_name=_("Gültig bis"), null=True, blank=True)
    active = models.BooleanField(verbose_name=_("Aktiv"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    create_date = models.DateField(default=timezone.now)

    objects = NotificationManager()
