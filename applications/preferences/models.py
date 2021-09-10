from django.db import models
from model_utils.models import TimeStampedModel
# Create your models here.

class PreferencesArea(TimeStampedModel):
    preferences_are= models.CharField(max_length=100, unique=True) 
    def __str__(self):
        return self.preferences_are

class Preferences(TimeStampedModel):
    description = models.CharField(max_length=100)
    priority = models.IntegerField(default=1)
    preferences_area = models.ForeignKey(PreferencesArea, on_delete=models.CASCADE,related_name="preferences")
    def __str__(self):
        return str(self.id) + " " +self.description

class PreferencesFilterArea(TimeStampedModel):
    filters_area = models.CharField(max_length=50, blank=True, null=True)
    def __str__(self):
        return self.filters_area

class PreferencesFilter(TimeStampedModel):
    search_value = models.CharField(max_length=50, null=True, blank=True)
    preferences = models.CharField(max_length=100, null=True, blank=True)
    preferences_filter_area = models.ForeignKey(PreferencesFilterArea, on_delete=models.CASCADE,related_name="preferences_filter")
    def __str__(self):
        return str(self.id) + " " +self.search_value