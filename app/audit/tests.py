#  Copyright 2021-2025 Simon Zigelli
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

from audit.models import Audit
from picker.models import Credential
from picker.tests import create_credential


class AuditViewTests(TestCase):
    def setUp(self):
        congregation = create_credential()
        create_credential(congregation='NO_LE')
        test_user = User.objects.create(username="testuser")
        test_user.set_password("12345")
        permission = Permission.objects.get(codename="view_audit")
        test_user.user_permissions.add(permission)
        assign_perm("access_audit_log", test_user, congregation)
        test_user.save()

    def test_permission_audit(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("console:choose_console"))
        self.assertContains(response, "LE")
        self.assertNotContains(response, "NO_LE")
        self.assertContains(response, "Zum Audit-Log...")

    def test_audit(self):
        congregation = Credential.objects.get(congregation="LE")
        congregation_no_le = Credential.objects.get(congregation="NO_LE")
        test_user = User.objects.get(username="testuser")
        Audit.objects.create_audit(congregation=congregation, message="Bla", user=test_user)
        Audit.objects.create_audit(congregation=congregation, message="Blub", user=test_user)
        Audit.objects.create_audit(congregation=congregation_no_le, message="Foo", user=test_user)
        Audit.objects.create_audit(congregation=congregation_no_le, message="Bar", user=test_user)
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("console:audit:audit", kwargs={"pk": "LE"}))
        self.assertContains(response, "Bla")
        self.assertNotContains(response, "Foo")
        self.assertNotContains(response, "Bar")
        self.assertContains(response, "Blub")

    def test_not_authorized(self):
        response = self.client.get(reverse("console:audit:audit", kwargs={"pk": "NO_LE"}))
        self.assertEqual(response.status_code, 403)
