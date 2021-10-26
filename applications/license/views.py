from django.http.response import Http404
from django.shortcuts import render
import json
from rest_framework import exceptions, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser ,AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from applications.user.mixins import IsAdministratorUser, IsTeacherUser
from .serializers import LicenseSerializer
from .models import License
# Create your views here.
class LicenseView(viewsets.ModelViewSet):
    """
        Servicio para CRUD licencias.
        CREATE & UPDATE son accesibles para usuarios administrador autenticado correctamente.
        LIST & RETRIEVE son servicios accesibles para usuarios anonimos 
    """
    def get_permissions(self):
        if(self.action=='create') or (self.action=='update'):
            permission_classes = [IsAuthenticated,IsAdministratorUser]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    serializer_class = LicenseSerializer
    queryset = License.objects.all()
    def list(self, request, *args, **kwargs):
        """Servicio para listar licencias registrados en la plataforma."""
        queryset = License.objects.all()
        serializer = LicenseSerializer(queryset, many=True)
        return Response(
            {
                "key": "license",
                "filter_param_value": "value",
                "name": "License",
                "values":serializer.data
            },status=HTTP_200_OK
            )

class EndpontFilter(APIView):
    """
        Listado de endpoints por cada filtro.
    """
    permission_classes = [AllowAny]
    def get(self, request, format=None):
        values = [
                    {
                          "name": "license",
                          "endpoint": "https://repositorio.edutech-project.org/api/v1/license",  
                    },
                    {
                          "name": "Nivel educativo",
                          "endpoint": "https://repositorio.edutech-project.org/api/v1/education-level",  
                    },
                    {
                          "name": "Área de conocimiento",
                          "endpoint": "https://repositorio.edutech-project.org/api/v1/knowledge-area",  
                    }
                ]
        
        return Response(values,status=HTTP_200_OK)