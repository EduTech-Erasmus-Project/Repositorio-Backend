
from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404
class LearningObjectManager(models.Manager):
    def learning_object_metadata_by_user(self, user):
        return self.filter(
            user_created=user
        ).exclude(public=False).order_by('-pk')
    def learning_object_metadata_by_user_destroy(self, user, pk):
        return self.filter(
            Q(user_created=user) and Q(pk=pk)
        ).delete()

    def learning_object_metadata_retrieve_by_user(self, user,pk):
        return get_object_or_404(self.filter(
            user_created=user
        ).order_by('-pk'),pk=pk)

    def learningobjectBySlug(self, slug):
        return self.filter(
            slug=slug
        )
    def learning_object_by_knowledge_area(self, knowledge_area):
        return self.filter(knowledge_area__name__contains=knowledge_area).exclude(public=False).order_by('-created')

    def get_all_learning_objects(self):
        return self.filter(public=True).count()

    # Recommendation System
    def get_learning_objects(self):
        return self.filter(public=True).order_by('pk')
        