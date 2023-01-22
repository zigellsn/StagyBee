#  Copyright 2019-2023 Simon Zigelli
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
from django.utils import timezone, translation

from notification.models import Notification


def create_message(message, subject, locale, importance, user, active=True,
                   create_date=timezone.now(), max_duration=timezone.now() + timedelta(days=7)):
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
        self.assertEqual("\n", rendered_template)

    def test_language_rendered(self):
        test_user = User.objects.create(username="test_user")
        create_message("Test bla bla bla", "Message!", "en", 1, test_user)
        context = Context({"Notification": "notification"})
        template_to_render = Template(
            "{% load notification %}"
            "{% notifications %}"
        )
        with translation.override("de"):
            rendered_template = template_to_render.render(context)
        print(rendered_template)
        # self.assertEqual("\n", rendered_template)
        with translation.override("en"):
            rendered_template = template_to_render.render(context)
        self.assertInHTML("Test bla bla bla", rendered_template)

    def test_message_rendered(self):
        test_user = User.objects.create(username="test_user")
        create_message("Test bla bla bla", "Message!", "en", 1, test_user)
        create_message("Something bad", "Oh no! Everything kaput!", " ", 2, test_user)
        create_message("Something very bad", "Oh no! Disaster!", "de", 4, test_user)
        context = Context({"Notification": "notification"})
        template_to_render = Template(
            "{% load notification %}"
            "{% notifications %}"
        )
        with translation.override("de"):
            rendered_template = template_to_render.render(context)
        self.assertInHTML("Something bad", rendered_template)
        self.assertInHTML("Something very bad", rendered_template)
