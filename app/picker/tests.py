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

from picker.models import Credential


def create_credential(congregation='LE', autologin='abc', username='abc', password='abc', display_name='The LE',
                      extractor_url='www.abc.com', touch=False):
    return Credential.objects.create(congregation=congregation, autologin=autologin,
                                     username=username, password=password, display_name=display_name,
                                     extractor_url=extractor_url, touch=touch)


class PickerViewTests(TestCase):
    def test_no_congregation(self):
        response = self.client.get(reverse('picker:picker'))
        self.assertEqual(response.status_code, 200)

    def test_one_congregation(self):
        create_credential()
        response = self.client.get(reverse('picker:picker'))
        self.assertEqual(response.status_code, 200)

    def test_many_congregations(self):
        credential_le = create_credential()
        credential_fe = create_credential(congregation='FE', display_name='The FE')
        response = self.client.get(reverse('picker:picker'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, credential_le)
        self.assertContains(response, credential_fe)
