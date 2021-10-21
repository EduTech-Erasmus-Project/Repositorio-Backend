from django.db import models
from model_utils.models import TimeStampedModel

# Create your models here.
class License(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    value = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name