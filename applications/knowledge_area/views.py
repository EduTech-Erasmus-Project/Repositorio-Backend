from rest_framework import viewsets
from .models import KnowledgeArea
from .serializers import KnowledgeAreaSerializer,KnowledgeAreaUpdateSerializer,KnowledgeAreaListSerializer
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated ,AllowAny
from applications.user.mixins import IsAdministratorUser
from django.shortcuts import get_object_or_404
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
) 
# Create your views here.
class KnowledgeAreaView(viewsets.ViewSet):
    # authentication_classes = (TokenAuthentication,)
    def get_permissions(self):
        if(self.action=='list' or self.action=='retrieve'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsAdministratorUser]
        return [permission() for permission in permission_classes]
    def create(self, request, *args, **kwargs):
        """
        Servicio para crear un nuevo area de conocimiento. API accesible para usuario administrador.
        """
        serializer = KnowledgeAreaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_instance = KnowledgeArea.objects.create(
            name= serializer.validated_data['name'],
            description= serializer.validated_data['description']
            )
        new_instance.save()
        serializer =  KnowledgeAreaSerializer(new_instance)
        return Response(serializer.data,status=HTTP_200_OK)
    
    def list(self, request):
        """
        Servicio para listar areas de conocimiento.
        """
        queryset = KnowledgeArea.objects.all()
        serializer = KnowledgeAreaListSerializer(queryset,many=True)
        return Response({
            "key":"knowledge_area",
            "filter_param_value": "name",
            "name":"Área de conocimiento",
            "values":serializer.data
        },status=HTTP_200_OK)
    def retrieve(self, request, pk=None):
        """
        Servicio para listar areas de conocimiento por id.
        """
        queryset = KnowledgeArea.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = KnowledgeAreaSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)
    def update(self, request, pk=None, project_pk=None):
        """
        Servicio para actualizar area de conocimiento.
        """
        queryset = KnowledgeArea.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = KnowledgeAreaUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.name= serializer.validated_data['name']
        instance.description = serializer.validated_data['description']
        instance.save()
        serializer =  KnowledgeAreaSerializer(instance)
        return Response(serializer.data,status=HTTP_200_OK)
    def destroy(self, request, pk=None):
        """
        Servicio para eliminar areas de conocimiento.
        """
        queryset = KnowledgeArea.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.delete()
        return Response({"message": "success"},status=HTTP_200_OK)