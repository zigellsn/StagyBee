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
from datetime import timedelta

from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import TestCase
from django.utils import timezone

from notification.models import Notification


def create_message(message, importance, max_duration, active, create_date, user, subject, locale):
    return Notification.objects.create(message=message, importance=importance, max_duration=max_duration,
                                       active=active, create_date=create_date, user=user, subject=subject,
                                       locale=locale)


class NotificationTemplateTagTest(TestCase):

    def test_empty_rendered(self):
        context = Context({"Notification": "notification"})
        template_to_render = Template(
            "{% load notification %}"
            "{% notifications %}"
        )
        rendered_template = template_to_render.render(context)
        self.assertEquals("\n", rendered_template)

    def test_message_rendered(self):
        testuser = User.objects.create(username="testuser")
        create_message("Test bla bla bla", 1, timezone.now() + timedelta(days=7), True, timezone.now(), testuser,
                       "Message!", "en")
        create_message("Something bad", 4, timezone.now() + timedelta(days=7), True, timezone.now(), testuser,
                       "Oh no! Everything kaputt!", " ")
        create_message("Something very bad", 4, timezone.now() + timedelta(days=7), True, timezone.now(), testuser,
                       "Oh no! Desaster!", "de")
        context = Context({"Notification": "notification"})
        template_to_render = Template(
            "{% load notification %}"
            "{% notifications %}"
        )
        rendered_template = template_to_render.render(context)
        self.assertInHTML("Something bad", rendered_template)
        self.assertInHTML("Something very bad", rendered_template)
