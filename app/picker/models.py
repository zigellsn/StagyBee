#  Copyright 2019 Simon Zigelli
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


class CredentialManager(models.Manager):
    def create_credential(self, congregation, autologin, username, password, display_name, extractor_url, touch,
                          show_only_request_to_speak):
        credential = self.create(congregation=congregation, autologin=autologin, username=username, password=password,
                                 display_name=display_name, extractor_url=extractor_url, touch=touch,
                                 show_only_request_to_speak=show_only_request_to_speak)
        return credential


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
    extractor_url = models.CharField(max_length=200, default="http://localhost:5000/", blank=True,
                                     verbose_name="Extractor URL")
    touch = models.BooleanField(default=True)
    show_only_request_to_speak = models.BooleanField(default=False, verbose_name=_("Zeige nur Meldungen"))

    objects = CredentialManager()

    def __str__(self):
        if not self.display_name:
            return self.congregation
        else:
            return self.display_name