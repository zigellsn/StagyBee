from django.db import models


class CredentialManager(models.Manager):
    def create_credential(self, congregation, autologin, username, password, display_name, extractor_url, touch):
        credential = self.create(congregation=congregation, autologin=autologin, username=username, password=password,
                                 display_name=display_name, extractor_url=extractor_url, touch=touch)
        return credential


class Credential(models.Model):
    class Meta:
        ordering = ["display_name", "congregation"]

    congregation = models.CharField(max_length=200, primary_key=True)
    autologin = models.CharField(max_length=128, default="", blank=True)
    username = models.CharField(max_length=200, default="", blank=True)
    password = models.CharField(max_length=200, default="", blank=True)
    display_name = models.CharField(max_length=200, default="", blank=True)
    extractor_url = models.CharField(max_length=200, default="http://localhost:5000/", blank=True,
                                     verbose_name="Extractor URL")
    touch = models.BooleanField(default=True)

    objects = CredentialManager()

    def __str__(self):
        if not self.display_name:
            return self.congregation
        else:
            return self.display_name
