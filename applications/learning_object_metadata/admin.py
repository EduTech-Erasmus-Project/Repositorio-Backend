from .models import LearningObjectMetadata
from django.contrib import admin

# Register your models here.
class LearningObjectAdmin(admin.ModelAdmin):
    list_display = ('id','general_title','general_description')
admin.site.register(LearningObjectMetadata,LearningObjectAdmin)