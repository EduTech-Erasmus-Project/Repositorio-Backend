from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.user.models import User
from django.db import models
from model_utils.models import TimeStampedModel
# Create your models here.

class Interaction(TimeStampedModel):
    liked = models.BooleanField(default=False)
    viewed = models.BooleanField(default=False)
    learning_object = models.ForeignKey(LearningObjectMetadata,on_delete=models.CASCADE, related_name='oa_liked')
    user = models.ForeignKey(
    User, 
    on_delete=models.CASCADE, 
    related_name='user_interacted'
    )
    def __str__(self):
        return str(self.id)
