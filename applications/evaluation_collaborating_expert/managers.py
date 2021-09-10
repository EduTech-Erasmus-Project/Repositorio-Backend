
from django.db import models

class EvaluationExpertManager(models.Manager):
    def rating_by_learningObject(self, oa_id):
        return self.filter(learning_object_id=oa_id)