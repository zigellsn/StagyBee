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
from django.contrib.auth.models import User, Permission
from django.test import TestCase
from django.urls import reverse
from guardian.shortcuts import assign_perm

from picker.tests import create_credential


class ConsoleViewTests(TestCase):
    def test_not_logged_in(self):
        create_credential().active = False
        response = self.client.get(reverse("console:chose_console"))
        self.assertEqual(response.status_code, 302)

    def test_logged_in(self):
        self.user()
        logged_in = self.login()
        response = self.client.get(reverse("console:chose_console"))
        self.assertEqual(logged_in, True)
        self.assertEqual(response.status_code, 200)

    def test_audit(self):
        congregation = create_credential()
        create_credential(congregation='FE')
        congregation.active = False
        user = self.user()
        assign_perm("access_audit_log", user, congregation)
        permission = Permission.objects.get(name="Can view audit")
        user.user_permissions.add(permission)
        self.login()
        response = self.client.get(reverse("console:chose_console"))
        self.assertContains(response, "LE")
        self.assertNotContains(response, "FE")
        self.assertContains(response, "Zum Audit-Log...")

    @staticmethod
    def user():
        user = User.objects.create(username="testuser")
        user.set_password("12345")
        user.save()
        return user

    def login(self):
        logged_in = self.client.login(username="testuser", password="12345")
        return logged_in
