from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated ,AllowAny
from .models import EducationLevel
from .serializers import EducationLevelSerializer
from applications.user.mixins import IsAdministratorUser
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
) 
# Create your views here.
class EducationLevelView(viewsets.ModelViewSet):
    """
    Gestión de los niveles de educación. 
    """
    def get_permissions(self):
        if(self.action=='list' or self.action=='retrieve'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated,IsAdministratorUser]
        return [permission() for permission in permission_classes]
    serializer_class = EducationLevelSerializer
    queryset = EducationLevel.objects.all()