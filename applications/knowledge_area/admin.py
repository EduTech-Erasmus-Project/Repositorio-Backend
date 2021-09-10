from .models import KnowledgeArea
from django.contrib import admin

# Register your models here.
class KnowledgeAreaAdmin(admin.ModelAdmin):
    list_display = ('id','name','description')

admin.site.register(KnowledgeArea,KnowledgeAreaAdmin)