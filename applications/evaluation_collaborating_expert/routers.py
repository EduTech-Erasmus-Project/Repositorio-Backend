from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'api/v1/object-learning-concept-evaluation', views.EvaluationConceptViewSet, basename='evaluation_concept')
router.register(r'api/v1/learning-objective-assessment-questions', views.EvaluationQuestionsViewSet, basename='evaluation_question')
router.register(r'api/v1/learning-objects/register-evaluation-expert', views.EvaluationCollaboratingExpertView, basename='evaluation')
# router.register(r'api/v1/learning-object-qualification-expert-collaborator', views.EvaluationQuestionsQualificationVieeSet, basename='qualification')

###path nuevos
#listar preguntas
router.register(r'api/v1/object-learning-concept-evaluation-schema', views.EvaluationConceptSCHEMAViewSet, basename='evaluation_concept_schema')
#crear preguntas/learning-objective-assessment-schema/
router.register(r'api/v1/learning-objective-assessment-schema', views.EvaluationSchemaDataViewSet, basename='evaluation_schema')

urlpatterns = router.urls