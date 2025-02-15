#  Copyright 2019-2025 Simon Zigelli
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
from django.db.models import QuerySet, URLField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from StagyBee.utils import DockerURLValidator
from stage.timeout import GLOBAL_TIMEOUT


def __get_running_since__(congregation):
    if congregation in GLOBAL_TIMEOUT:
        return GLOBAL_TIMEOUT.get(congregation).start_time
    return timezone.localtime(timezone.now())


def is_active(congregation):
    if congregation.congregation in GLOBAL_TIMEOUT:
        return True
    else:
        return False


def get_running_since(congregation):
    return __get_running_since__(congregation.congregation)


class CredentialQuerySet(QuerySet):

    def active(self):
        return self.all()


class CredentialManager(models.Manager):

    def get_query_set(self):
        return CredentialQuerySet(self.model, using=self._db)

    def active(self):
        congregation_set = self.get_query_set().all()
        for congregation in congregation_set:
            if is_active(congregation):
                congregation.active = True
                congregation.since = __get_running_since__(congregation.congregation)
            else:
                congregation.active = False
                congregation.since = None
        return congregation_set

    def create_credential(self, congregation, autologin, username, password, display_name, extractor_url, touch,
                          show_only_request_to_speak, send_times_to_stage):
        return self.create(congregation=congregation, autologin=autologin, username=username, password=password,
                           display_name=display_name, extractor_url=extractor_url, touch=touch,
                           show_only_request_to_speak=show_only_request_to_speak,
                           send_times_to_stage=send_times_to_stage)


class DockerURLField(URLField):
    default_validators = [DockerURLValidator()]


class Credential(models.Model):
    class SortOrder(models.IntegerChoices):
        FAMILY_NAME = 0, _("Familienname")
        GIVEN_NAME = 1, _("Vorname")

    class NameOrder(models.IntegerChoices):
        FAMILY_NAME = 0, _("Familienname zuerst")
        GIVEN_NAME = 1, _("Vorname zuerst")

    congregation = models.CharField(max_length=200, primary_key=True, verbose_name=_("Versammlung"))
    autologin = models.CharField(max_length=128, db_default="", blank=True, verbose_name=_("Auto-Login ID"))
    username = models.CharField(max_length=200, db_default="", blank=True, verbose_name=_("Username"))
    password = models.CharField(max_length=200, db_default="", blank=True, verbose_name=_("Passwort"))
    display_name = models.CharField(max_length=200, db_default="", blank=True, verbose_name=_("Anzeigename"))
    extractor_url = DockerURLField(db_default="https://extractor:8443/", blank=True, verbose_name=_("Extractor URL"))
    touch = models.BooleanField(db_default=True, verbose_name=_("Touch erlaubt"))
    show_only_request_to_speak = models.BooleanField(db_default=False, verbose_name=_("Zeige nur Meldungen"))
    send_times_to_stage = models.BooleanField(db_default=False, verbose_name=_("Sende Zeiten an Bühne"))
    sort_order = models.PositiveSmallIntegerField(choices=SortOrder.choices, db_default=NameOrder.FAMILY_NAME,
                                                  verbose_name=_("Namensliste sortieren nach"))
    name_order = models.PositiveSmallIntegerField(choices=NameOrder.choices, db_default=NameOrder.FAMILY_NAME,
                                                  verbose_name=_("Namensreihenfolge"))

    objects = CredentialManager()

    class Meta:
        verbose_name = _("JWConf Verbindung")
        verbose_name_plural = _("JWConf Verbindungen")
        ordering = ["display_name", "congregation"]
        permissions = (
            ("access_console", _("Zugriff auf Management Console")),
            ("access_stopwatch", _("Zugriff auf Stoppuhr")),
            ("access_audit_log", _("Zugriff auf Audit-Log")),
        )

    def __str__(self):
        if not self.display_name:
            return self.congregation
        else:
            return self.display_name
