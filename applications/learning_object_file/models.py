from model_utils.models import TimeStampedModel
from django.db import models


class LearningObjectFile(TimeStampedModel):
    file = models.FileField(upload_to='oazip', blank=False)
    url = models.URLField(editable=False,max_length=300)
    file_name = models.CharField(editable=False,max_length=100)
    file_size = models.IntegerField(editable=False, blank=True, null=True)
    path_origin = models.TextField(blank=True, null=True)

    REQUIRED_FIELDS = ['file','file_name','file_size']
    
    def __str__(self):
        return str(self.id)