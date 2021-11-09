from django.db import models
from model_utils.models import TimeStampedModel

# Create your models here.

class EducationLevel(TimeStampedModel):
    name_es = models.CharField(max_length=100, unique=True)
    name_en = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return str(self.id) + ' ' + self.name_es