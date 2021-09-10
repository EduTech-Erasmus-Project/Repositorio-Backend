from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from .models import Preferences, PreferencesArea, PreferencesFilter, PreferencesFilterArea
from rest_framework.permissions import IsAuthenticated ,AllowAny
from .serializers import PreferencesAreaFilterSerializer, PreferencesAreaListSerializer, PreferencesByAreaSerializer, PreferencesSerializer
from applications.user.mixins import IsAdministratorUser

# Create your views here.
class UserPrefrencesView(viewsets.ModelViewSet):
    """
        CRUD preferencias de usuarios
    """
    def get_permissions(self):
        if(self.action=='list' or self.action=='retrieve'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated,IsAdministratorUser]
        return [permission() for permission in permission_classes]
    serializer_class = PreferencesSerializer
    queryset = Preferences.objects.all()

class PrefrencesAreaView(viewsets.ModelViewSet):
    """
        CRUD preferencias por area
    """
    def get_permissions(self):
        if(self.action=='list' or self.action=='retrieve'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated,IsAdministratorUser]
        return [permission() for permission in permission_classes]
    serializer_class = PreferencesAreaListSerializer
    queryset = PreferencesArea.objects.all()
    action_serializers = {
        'list': PreferencesByAreaSerializer,
    }
    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            return self.action_serializers.get(self.action, self.serializer_class)
        return super(PrefrencesAreaView, self).get_serializer_class()

class AreaFilters(ListAPIView):
    permission_classes = [AllowAny]
    pagination_class=None
    serializer_class = PreferencesAreaFilterSerializer
    queryset = PreferencesFilterArea.objects.all()