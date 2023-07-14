from model_utils.models import TimeStampedModel
from django.db import models

from roabackend.storage_backends import PublicMediaStorage


class LearningObjectFile(TimeStampedModel):
    file = models.FileField(upload_to='oazip', blank=False)
    url = models.URLField(editable=False,max_length=300)
    file_name = models.CharField(editable=False,max_length=100)
    file_size = models.IntegerField(editable=False, blank=True, null=True)
    path_origin = models.TextField(blank=True, null=True)
    #Atributos para la integracion con el OerAdap
    oa_integration_id = models.IntegerField(blank=True, null=True)
    oa_created_at = models.DateTimeField(blank=True, null=True)
    oa_expires_at = models.DateTimeField(blank=True, null=True)
    oa_preview_origin = models.URLField(max_length=300, blank=True, null=True)
    oa_preview_adapted = models.URLField(max_length=300, blank=True, null=True)
    oa_oer_adap_url= models.URLField(max_length=300, blank=True, null=True)

    REQUIRED_FIELDS = ['file','file_name','file_size']
    
    def __str__(self):
        return str(self.id)