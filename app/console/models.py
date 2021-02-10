#  Copyright 2019-2021 Simon Zigelli
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
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _, get_language


@receiver(post_save, sender=User)
def update_profile_signal(sender, instance, created, **kwargs):
    current_language = get_language()
    if created:
        UserPreferences.objects.create(user=instance, dark_mode=True, locale=current_language)


class PreferencesManager(models.Manager):

    def create_user_preferences(self, user, dark_mode, locale):
        return self.create(user=user, dark_mode=dark_mode, locale=locale)


class UserPreferences(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    dark_mode = models.BooleanField(verbose_name=_("Dunkles Design"))
    locale = models.CharField(max_length=10, verbose_name=_("Sprache"), default="en")

    objects = PreferencesManager()
