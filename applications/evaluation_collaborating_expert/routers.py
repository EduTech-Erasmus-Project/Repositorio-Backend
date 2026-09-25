"""Recursos expuestos por router en evaluación colaborativa experta.

Aqui viven los CRUD principales del módulo. Las consultas manuales y los
endpoints auxiliares de resultados quedan en `urls.py`.
"""

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

# Catálogos y captura principal de evaluación  experta.
router.register(r'api/v1/object-learning-concept-evaluation', views.EvaluationConceptViewSet, basename='evaluation_concept')
router.register(r'api/v1/learning-objective-assessment-questions', views.EvaluationQuestionsViewSet, basename='evaluation_question')
router.register(r'api/v1/learning-objects/register-evaluation-expert', views.EvaluationCollaboratingExpertView, basename='evaluation')
# router.register(r'api/v1/learning-object-qualification-expert-collaborator', views.EvaluationQuestionsQualificationVieeSet, basename='qualification')

# Schemas y auto-preguntas para evaluación  automática/administrativa.
router.register(r'api/v1/object-learning-concept-evaluation-schema', views.EvaluationConceptSCHEMAViewSet, basename='evaluation_concept_schema')
router.register(r'api/v1/object-learning-question-evaluation-schema', views.EvaluationSelfQuestionSCHEMAViewSet, basename='evaluation_question_schema')

# Reglas de metadata usadas por el motor de evaluación  automática.
router.register(r'api/v1/learning-objective-assessment-schema', views.EvaluationSchemaDataViewSet, basename='evaluation_schema')

urlpatterns = router.urls