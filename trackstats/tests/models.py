from django.db import models
from django.utils import timezone


class Comment(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
