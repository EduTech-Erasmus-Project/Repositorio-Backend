from django.contrib import admin
from .models import LearningObjectFile
# Register your models here.

# class LearningObjectAdmin(admin.ModelAdmin):
#     list_display = ('id','file','url')
admin.site.register(LearningObjectFile)