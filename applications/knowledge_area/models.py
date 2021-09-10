from django.db import models
from model_utils.models import TimeStampedModel

# Create your models here.
class KnowledgeArea(TimeStampedModel):
    name = models.CharField(max_length=900, unique=True)
    description = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.name
