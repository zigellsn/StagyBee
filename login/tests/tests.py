from django.test import TestCase
from django.urls import reverse

from picker.tests import create_credential


class LoginViewTests(TestCase):
    def test_no_congregation(self):
        response = self.client.get(reverse("login:login", args=("FE",)))
        self.assertEqual(response.status_code, 404)

    def test_no_touch(self):
        create_credential("LE", "abc", "def", "ghi", "The LE", "www.abc.com", False)
        response = self.client.get(reverse("login:login", args=("LE",)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Zuhörer gesamt:")

    def test_touch(self):
        create_credential("LE", "abc", "def", "ghi", "The LE", "www.abc.com", True)
        response = self.client.get(reverse("login:login", args=("LE",)))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Zuhörer gesamt:")
