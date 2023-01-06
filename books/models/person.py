from django.db import models


class Person(models.Model):
    email = models.TextField(unique=True)
    name = models.TextField()
    bio = models.TextField()
