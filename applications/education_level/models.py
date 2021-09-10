from django.db import models
from model_utils.models import TimeStampedModel

# Create your models here.
class EducationLevel(TimeStampedModel):
    description = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return str(self.id) + ' ' + self.description