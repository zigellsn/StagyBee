from django.db import models


class Credential(models.Model):    
    congregation = models.CharField(max_length=200, primary_key=True)
    username = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    touch = models.BooleanField(default=False)

    def __str__(self):
        return self.congregation
