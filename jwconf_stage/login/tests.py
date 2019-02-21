from django.test import TestCase
from django.urls import reverse
from picker.models import Credential
from picker.tests import create_credential


class LoginViewTests(TestCase):
    def test_no_congregation(self):
        response = self.client.get(reverse('login:login', args=["FE"]))
        self.assertEqual(response.status_code, 404) 

    def test_one_congregation(self):
        credential = create_credential('LE', 'abc', 'abc', False)
        response = self.client.get(reverse('login:login', args=["LE"]))        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, credential.congregation)
        self.assertContains(response, credential.username)
        self.assertContains(response, credential.password)
        self.assertNotContains(response, credential.touch)
