from model_utils.models import TimeStampedModel
from django.db import models


class LearningObjectFile(TimeStampedModel):
    file = models.FileField(upload_to='oazip', blank=False)
    url = models.URLField(editable=False,max_length=300)
    

    REQUIRED_FIELDS = ['file']
    
    def __str__(self):
        return str(self.id)