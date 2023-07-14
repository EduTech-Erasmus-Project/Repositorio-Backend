from .models import KnowledgeArea
from django.contrib import admin

# Register your models here.
class KnowledgeAreaAdmin(admin.ModelAdmin):
    list_display = ('id','name_es','description_es')

admin.site.register(KnowledgeArea,KnowledgeAreaAdmin)