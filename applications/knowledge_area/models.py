from django.db import models
from model_utils.models import TimeStampedModel

# Create your models here.
class KnowledgeArea(TimeStampedModel):
    name_es = models.CharField(max_length=250, unique=True)
    description_es = models.TextField(blank=True, null=True)
    name_en = models.CharField(max_length=250, unique=True)
    description_en = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.name_es
