from django.forms import ModelForm, PasswordInput

from .models import Credential


class CredentialForm(ModelForm):
    class Meta:
        model = Credential
        fields = ['congregation', 'autologin', 'username', 'password', 'display_name', 'extractor_url', 'touch',
                  'show_only_request_to_speak', 'send_times_to_stage']
        widgets = {
            'password': PasswordInput(render_value=True),
        }
