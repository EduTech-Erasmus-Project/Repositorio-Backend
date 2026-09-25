"""Rutas manuales del módulo de archivos de objetos de aprendizaje.

Aqui viven endpoints que no salen del router principal: integración con OER
Adapt y variantes legacy de borrado con y sin slash final.
"""

from django.urls import path
from . import views

app_name = 'learning_object_file'

# Adaptadores de ViewSet usados por rutas legacy de borrado.
teacher_delete_legacy = views.DeleteLearningObjectViewSet.as_view({"delete": "destroy"})
admin_delete_legacy = views.DeleteLearningObjectViewSetAdmin.as_view({"delete": "destroy"})

urlpatterns = [
    # Integracion con OER Adapt.
    path('api/v1/learning-object-oer/', views.getDataNewLearningObject.as_view(), name='learningobject-oeradap'),
    path('api/v1/learning-object-oer/create', views.saveDataIntegrationWithOer.as_view(), name='learningobject-oeradap-create'),

    # Borrado legacy expuesto como rutas manuales.
    path('api/v1/learning-object-file-delete/<int:pk>', teacher_delete_legacy, name='learningobject-delete-legacy'),
    path('api/v1/learning-object-file-delete-admin/<int:pk>', admin_delete_legacy, name='learningobject-delete-admin-legacy'),
]
