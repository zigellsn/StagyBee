from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from .forms import CredentialForm
from .models import Credential


class CredentialAdmin(GuardedModelAdmin):
    form = CredentialForm


admin.site.register(Credential, CredentialAdmin)
