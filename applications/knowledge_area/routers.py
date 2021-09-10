from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'api/v1/knowledge-area', views.KnowledgeAreaView, basename='areas_de_conocimiento')
urlpatterns = router.urls