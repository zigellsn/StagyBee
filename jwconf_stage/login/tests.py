from django.test import TestCase
from django.urls import reverse
import importlib

picker = importlib.import_module('picker.models')
picker_tests = importlib.import_module('picker.tests')


class LoginViewTests(TestCase):
    def test_no_congregation(self):
        response = self.client.get(reverse('login:login', args=["FE"]))
        self.assertEqual(response.status_code, 404) 

    def test_one_congregation(self):
        credential = picker_tests.create_credential('LE', 'abc', 'def', 'ghi', 'www.abc.com', False)
        response = self.client.get(reverse('login:login', args=["LE"]))        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, credential.congregation)
        self.assertNotContains(response, credential.username)
        self.assertNotContains(response, credential.password)
        self.assertNotContains(response, credential.extractor_url)
        self.assertNotContains(response, credential.touch)
