from django.forms import ModelForm, PasswordInput

from .models import Credential


class CredentialForm(ModelForm):
    class Meta:
        model = Credential
        fields = ['congregation', 'autologin', 'username', 'password', 'display_name', 'extractor_url', 'touch']
        widgets = {
            'password': PasswordInput(),
        }
