"""Routers principales del módulo de metadata de objetos de aprendizaje.

Aqui solo se registran los recursos CRUD expuestos por `DefaultRouter`. Los
endpoints de búsqueda, publicación y listados especiales viven en `urls.py`
porque responden a flujos manuales y no a operaciones REST directas.
"""

from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()

# CRUD de metadata y comentarios asociados al OA.
router.register(
    r"api/v1/learning-object-metadata",
    views.LearningObjectMetadataViewSet,
    basename="learning_object_metadata",
)
router.register(
    r"api/v1/learning-object/create/commentary",
    views.CommentaryModelView,
    basename="create-commentary",
)

urlpatterns = router.urls