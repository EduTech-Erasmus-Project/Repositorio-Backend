"""roabackend URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from applications.user.views import PasswordTokenCkeckAPI, RequestPasswordResetEmail, SetNewPasswordAPIView
from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path, include
from rest_framework_swagger.views import get_swagger_view
from django.conf.urls import url
from django.conf.urls.static import static

schema_view = get_swagger_view(title='ROA API-REST Documentation')

urlpatterns = [
    url(r'api-view', schema_view),
    # Admin url
    path('admin/', admin.site.urls),
    # Reset password
    path('api/v1/request-reset-email/', RequestPasswordResetEmail.as_view(), name='request-reset-email'),
    path('api/v1/password-resed/<uidb64>/<token>/', PasswordTokenCkeckAPI.as_view(), name='password-reset-confirm'),
    path('api/v1/password-reset-complete/', SetNewPasswordAPIView.as_view(), name='password-reset-complete'),
    # Roa App url
    re_path('',include('applications.user.urls')),
    re_path('',include('applications.evaluation_collaborating_expert.urls')),
    re_path('',include('applications.evaluation_student.urls')),
    re_path('',include('applications.evaluation_student.routers')),
    re_path('',include('applications.learning_object_metadata.urls')),
    re_path('',include('applications.recommendation_system.urls')),
    re_path('',include('applications.interaction.urls')),
    re_path('',include('applications.user.routers')),
    re_path('',include('applications.learning_object_file.routers')),
    re_path('',include('applications.education_level.routers')),
    re_path('',include('applications.knowledge_area.routers')),
    re_path('',include('applications.preferences.routers')),
    re_path('',include('applications.preferences.urls')),
    re_path('',include('applications.license.urls')),
    re_path('',include('applications.profession.routers')),
    re_path('',include('applications.evaluation_collaborating_expert.routers')),
    re_path('',include('applications.learning_object_metadata.routers')),
    re_path('',include('applications.license.routers')),
    re_path('',include('applications.interaction.routers')),

]

#urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#print(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
#print(settings.MEDIA_ROOT)
# + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)