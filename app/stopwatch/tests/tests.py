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
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from guardian.shortcuts import assign_perm

from picker.tests import create_credential


class StopwatchViewTests(TestCase):

    def setUp(self):
        congregation = create_credential()
        create_credential(congregation='FE')
        test_user = User.objects.create(username="testuser")
        test_user.set_password("12345")
        assign_perm("access_stopwatch", test_user, congregation)
        test_user.save()

    def test_permission_stopwatch(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("console:choose_console"))
        self.assertContains(response, "LE")
        self.assertNotContains(response, "FE")

    def test_not_authorized(self):
        response = self.client.get(reverse("console:stopwatch:timer", kwargs={"pk": "FE"}))
        self.assertEqual(response.status_code, 403)
