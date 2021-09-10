from django.shortcuts import render
from rest_framework import exceptions, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser ,AllowAny
from rest_framework.response import Response
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
    # authentication_classes = (TokenAuthentication,)
    def get_permissions(self):
        if(self.action=='create') or (self.action=='update'):
            permission_classes = [IsAuthenticated,IsAdministratorUser]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    serializer_class = LicenseSerializer
    queryset = License.objects.all()