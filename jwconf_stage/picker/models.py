from django.db import models


class Credential(models.Model):    
    congregation = models.CharField(max_length=200, primary_key=True)
    autologin = models.CharField(max_length=128, default="", blank=True)
    username = models.CharField(max_length=200, default="", blank=True)
    password = models.CharField(max_length=200, default="", blank=True)
    touch = models.BooleanField(default=False)

    def __str__(self):
        return self.congregation
