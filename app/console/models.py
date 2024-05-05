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
from django.contrib.auth import user_logged_in
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _, get_language


@receiver(user_logged_in, sender=User)
def user_logged_in(sender, **kwargs):
    if "user" not in kwargs or "request" not in kwargs:
        return
    try:
        preferences = UserPreferences.objects.get(user=kwargs["user"])
        scheme = preferences.scheme
    except UserPreferences.DoesNotExist:
        UserPreferences.objects.create(user=kwargs["user"], scheme=UserPreferences.Scheme.LIGHT)
        scheme = UserPreferences.Scheme.LIGHT
    kwargs["request"].session["scheme"] = scheme


@receiver(post_save, sender=User)
def update_profile_signal(sender, instance, created, **kwargs):
    current_language = get_language()
    if created and current_language is not None:
        UserPreferences.objects.create(user=instance, scheme=UserPreferences.Scheme.LIGHT, locale=current_language)


class PreferencesManager(models.Manager):

    def create_user_preferences(self, user, scheme, locale):
        return self.create(user=user, scheme=scheme, locale=locale)


class UserPreferences(models.Model):
    class Scheme(models.IntegerChoices):
        DARK = 0, _('Dunkles Design')
        LIGHT = 1, _('Helles Design')
        FOLLOW = 2, _('Wie Betriebssystem')

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )

    scheme = models.IntegerField(choices=Scheme.choices, default=Scheme.LIGHT,
                                 verbose_name=_("Erscheinungsbild"))
    locale = models.CharField(max_length=10, verbose_name=_("Sprache"), default="en")

    objects = PreferencesManager()


class KnownClientManager(models.Manager):

    def create_known_client(self, uri, alias, token, cert_file):
        return self.create(uri=uri, alias=alias, token=token, cert_file=cert_file)


class KnownClient(models.Model):
    uri = models.URLField(verbose_name=_("Client URL"), unique=True)
    alias = models.TextField(verbose_name=_("Alias Name"), default="Client")
    token = models.BinaryField(max_length=64, verbose_name=_("Token"))
    cert_file = models.FileField(upload_to="certs", verbose_name=_("Zertifikatsdatei"))

    objects = KnownClientManager()

    class Meta:
        ordering = ["alias", "uri"]
        verbose_name = _("Bekannter Client")
        verbose_name_plural = _("Bekannte Clients")
        permissions = (
            ("control_client", _("Client steuern")),
        )

    def __str__(self):
        return f"{self.alias} ({self.uri})"
