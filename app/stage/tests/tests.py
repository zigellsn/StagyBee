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

from django.test import TestCase
from django.urls import reverse

from picker.tests import create_credential


class StageViewTests(TestCase):
    def test_no_congregation(self):
        response = self.client.get(reverse("stage:stage", args=("FE",)))
        self.assertEqual(response.status_code, 404)

    def test_no_touch(self):
        create_credential("LE", "abc", "def", "ghi", "The LE", "www.abc.com", False)
        response = self.client.get(reverse("stage:stage", args=("LE",)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "sum-listeners")

    def test_touch(self):
        create_credential("LE", "abc", "def", "ghi", "The LE", "www.abc.com", True)
        response = self.client.get(reverse("stage:stage", args=("LE",)))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Zuhörer gesamt:")
