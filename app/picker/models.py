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
import asyncio
import datetime
import logging

import aioredis
from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

REDIS_KEY = "stagybee::console:congregation.console."
logger = logging.getLogger(__name__)


async def __get_redis_congregations():
    host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]
    redis = await aioredis.create_redis(host)
    congregations = await redis.keys(REDIS_KEY + "*")
    redis.close()
    await redis.wait_closed()
    return congregations


async def __get_active_congregations__():
    congregation_filter = []
    try:
        congregation_filter = await __get_redis_congregations()
    except():
        logger.error("Redis Server not available")
    finally:
        congregation_filter[:] = [c.decode()[len(REDIS_KEY):len(c)] for c in congregation_filter]
        return congregation_filter


async def __get_running_since__(congregation):
    host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]
    redis = await aioredis.create_redis(host)
    members = await redis.smembers(f"stagybee::console:congregation.console.{congregation}")
    with_since = [x for x in members if x.decode("utf-8").startswith("since:")]
    if with_since:
        redis.close()
        await redis.wait_closed()
        return datetime.datetime.strptime(with_since[0].decode("utf-8")[6:31], settings.DATETIME_FORMAT)


class CredentialQuerySet(QuerySet):

    def active(self):
        return self.all()


class CredentialManager(models.Manager):

    def get_query_set(self):
        return CredentialQuerySet(self.model, using=self._db)

    def active(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        congregation_filter = loop.run_until_complete(__get_active_congregations__())
        congregation_set = self.get_query_set().all()
        for congregation in congregation_set:
            if congregation.congregation in congregation_filter:
                congregation.active = True
                congregation.since = loop.run_until_complete(__get_running_since__(congregation.congregation))
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


class Credential(models.Model):
    class Meta:
        ordering = ["display_name", "congregation"]
        permissions = (
            ("access_console", _("Zugriff auf Management Console")),
            ("access_stopwatch", _("Zugriff auf Stoppuhr")),
            ("access_audit_log", _("Zugriff auf Audit-Log")),
        )

    congregation = models.CharField(max_length=200, primary_key=True)
    autologin = models.CharField(max_length=128, default="", blank=True)
    username = models.CharField(max_length=200, default="", blank=True)
    password = models.CharField(max_length=200, default="", blank=True)
    display_name = models.CharField(max_length=200, default="", blank=True)
    extractor_url = models.CharField(max_length=200, default="http://extractor:8080/", blank=True,
                                     verbose_name="Extractor URL")
    touch = models.BooleanField(default=True)
    show_only_request_to_speak = models.BooleanField(default=False, verbose_name=_("Zeige nur Meldungen"))
    send_times_to_stage = models.BooleanField(default=False, verbose_name=_("Sende Zeiten an Bühne"))

    objects = CredentialManager()

    def __str__(self):
        if not self.display_name:
            return self.congregation
        else:
            return self.display_name
