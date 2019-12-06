from django.test import TestCase
from django.urls import reverse


class ReceiverViewTests(TestCase):
    def test_no_event(self):
        response = self.client.post(reverse('receiver:receiver', args=("Test",)))
        self.assertEqual(response.status_code, 204)
