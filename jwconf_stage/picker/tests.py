from django.test import TestCase
from django.urls import reverse
from picker.models import Credential


def create_credential(congregation, username, password, touch):
    return Credential.objects.create(congregation=congregation, 
            username=username, password=password, touch=touch)


class PickerViewTests(TestCase):
    def test_no_congregation(self):
        response = self.client.get(reverse('picker:picker'))
        self.assertEquals(response.status_code, 200)
    
    def test_one_congregation(self):
        credential = create_credential('LE', 'abc', 'abc', False)
        response = self.client.get(reverse('picker:picker'))
        self.assertEquals(response.status_code, 302)
    
    def test_many_congregations(self):
        credential_le = create_credential('LE', 'abc', 'abc', False)
        credential_fe = create_credential('FE', 'abc', 'abc', False)
        response = self.client.get(reverse('picker:picker'))
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, credential_le)
        self.assertContains(response, credential_fe)
