from django.db import models
from model_utils.models import TimeStampedModel

# Create your models here.
class License(TimeStampedModel):
    description = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return self.description