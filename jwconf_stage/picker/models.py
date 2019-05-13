from django.db import models


class CredentialManager(models.Manager):
    def create_credential(self, congregation, autologin, username, password, touch):
        credential = self.create(congregation=congregation, autologin=autologin, username=username, password=password,
                                 touch=touch)
        return credential


class Credential(models.Model):    
    congregation = models.CharField(max_length=200, primary_key=True)
    autologin = models.CharField(max_length=128, default="", blank=True)
    username = models.CharField(max_length=200, default="", blank=True)
    password = models.CharField(max_length=200, default="", blank=True)
    touch = models.BooleanField(default=False)

    objects = CredentialManager()

    def __str__(self):
        return self.congregation
