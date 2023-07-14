from rest_framework import viewsets
from .models import Profession
from .serializers import ProfessionSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated ,AllowAny
from django.shortcuts import get_object_or_404
from rest_framework.status import (
    HTTP_200_OK
) 
from applications.user.mixins import IsAdministratorUser
# Create your views here.
class ProfessionView(viewsets.ViewSet):
    def get_permissions(self):
        if(self.action=='list' or self.action=='retrieve'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated,IsAdministratorUser,]
        return [permission() for permission in permission_classes]
    def create(self, request, *args, **kwargs):
        """
            Agregar una neva profesión. 
            Api accesible para un usuraio utenticado como administrador
        """
        serializer = ProfessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_instance = Profession.objects.create(
            description= serializer.validated_data['description']
            )
        new_instance.save()
        serializer = ProfessionSerializer(new_instance)
        return Response(serializer.data,status=HTTP_200_OK)
    def list(self, request):
        """
            Listado de todas las prefesiones.
            Api accesible para todos los usuarios.
        """
        queryset = Profession.objects.all()
        serializer = ProfessionSerializer(queryset,many=True)
        return Response(serializer.data,status=HTTP_200_OK)
    def retrieve(self, request, pk=None):
        """
            Listado de prefesión por id.
            Api accesible para todos los usuarios
        """
        queryset = Profession.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = ProfessionSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)
    def update(self, request, pk=None, project_pk=None):
        """
            Actualizar una profesión por id. 
            Api accesible para un usuario utenticado como administrador
        """
        queryset = Profession.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = ProfessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.description = serializer.validated_data['description']
        instance.save()
        serializer = ProfessionSerializer(instance)
        return Response(serializer.data,status=HTTP_200_OK)
    def destroy(self, request, pk=None):
        """
            Eliminar una profesión por id 
            Api accesible para un usuario utenticado como administrador
        """
        queryset = Profession.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.delete()
        return Response({"message": "success"},status=HTTP_200_OK)