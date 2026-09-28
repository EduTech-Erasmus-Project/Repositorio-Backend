"""Mapa principal de rutas del proyecto `roabackend`.

Este archivo centraliza la composición del API REST del proyecto y mezcla dos
fuentes de rutas heredadas:

- `urls.py` manuales para endpoints explícitos o legacy
- `routers.py` para recursos expuestos con DRF Router

La organización actual se conserva por compatibilidad con el frontend y con la
superficie histórica del API. Por eso este archivo funciona como punto de
entrada global para ubicar rápidamente en que módulo vive cada endpoint.
"""

from applications.user.views import PasswordTokenCkeckAPI, RequestPasswordResetEmail, SetNewPasswordAPIView
from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.conf.urls.static import static


urlpatterns = [
    # Documentacion OpenAPI/Swagger actualizada. Se conserva `/api-view` para
    # compatibilidad con el acceso historico usado por el equipo.
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api-view', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # URL de admin deshabilitada en la configuración actual.
    # path('admin/', admin.site.urls),

    # Flujo público de recuperación de contraseña.
    path('api/v1/request-reset-email/', RequestPasswordResetEmail.as_view(), name='request-reset-email'),
    path('api/v1/password-resed/<uidb64>/<token>/', PasswordTokenCkeckAPI.as_view(), name='password-reset-confirm'),
    path('api/v1/password-reset-complete/', SetNewPasswordAPIView.as_view(), name='password-reset-complete'),

    # Módulos con endpoints manuales o contracts legacy.
    re_path('', include('applications.user.urls')),
    re_path('', include('applications.evaluation_collaborating_expert.urls')),
    re_path('', include('applications.learning_object_metadata.urls')),
    re_path('', include('applications.interaction.urls')),
    re_path('', include('applications.preferences.urls')),
    re_path('', include('applications.license.urls')),
    re_path('', include('applications.learning_object_file.urls')),
    re_path('', include('applications.address.urls')),
    re_path('', include('applications.settings.urls')),

    # Recursos expuestos con DRF Router.
    re_path('', include('applications.evaluation_student.routers')),
    re_path('', include('applications.recommendation_system.urls')),
    re_path('', include('applications.user.routers')),
    re_path('', include('applications.learning_object_file.routers')),
    re_path('', include('applications.education_level.routers')),
    re_path('', include('applications.knowledge_area.routers')),
    re_path('', include('applications.preferences.routers')),
    re_path('', include('applications.profession.routers')),
    re_path('', include('applications.evaluation_collaborating_expert.routers')),
    re_path('', include('applications.learning_object_metadata.routers')),
    re_path('', include('applications.license.routers')),
    re_path('', include('applications.interaction.routers')),
    re_path('', include('applications.evaluation_student.urls')),
]

if settings.DEBUG:
    # En desarrollo se sirven archivos media directamente desde Django para
    # facilitar pruebas locales del frontend y de cargas de archivos.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
