from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
#calificar evaluacion
router.register(r'api/v1/learning-objects/student-evaluation', views.StudentEvaluationView, basename='evaluation_student')
#listar preguntas
router.register(r'api/v1/object-learning-concept-evaluation-student-questions', views.EvaluationPrincipleGuidelienViewSet, basename='student_list')
#crear nuevas preguntas
router.register(r'api/v1/learning-objective-assessment-student', views.EvaluationQuestionsStudentViewSet, basename='create_question')
#crear principios
router.register(r'api/v1/learning-objects/student-register-principles', views.EvaluationPrincipleRegisterViewSet, basename='register-principles')
#crear guidelines/learning-objective-assessment-student/
router.register(r'api/v1/learning-objects/student-register-guideline', views. EvaluationGuidelineRegisterViewSet, basename='register-principles')

urlpatterns = router.urls