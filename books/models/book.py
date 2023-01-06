from django.db import models

from .person import Person


class Book(models.Model):
    title = models.CharField(max_length=256)
    author = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="writings"
    )
    readers = models.ManyToManyField(Person, related_name="readings")
