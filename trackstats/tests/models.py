from django.db import models
from django.utils import timezone


class Comment(models.Model):
    user = models.ForeignKey('auth.User')
    timestamp = models.DateTimeField(default=timezone.now)
