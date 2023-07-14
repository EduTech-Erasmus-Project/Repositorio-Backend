from django.urls import path
from . import views

app_name = 'licenses'
urlpatterns = [
    path('api/v1/endpoint-filter', views.EndpontFilter.as_view()),
]