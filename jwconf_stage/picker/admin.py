from django.contrib import admin
from .forms import CredentialForm

from .models import Credential


class CredentialAdmin(admin.ModelAdmin):
    form = CredentialForm


admin.site.register(Credential, CredentialAdmin)
