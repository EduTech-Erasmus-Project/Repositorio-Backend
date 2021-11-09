from rest_framework import viewsets
from .models import KnowledgeArea
from .serializers import KnowledgeAreaEnSerializer, KnowledgeAreaEsSerializer, KnowledgeAreaSerializer,KnowledgeAreaUpdateSerializer,KnowledgeAreaListSerializer
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
        if self.request.META.get('HTTP_ACCEPT_LANGUAGE') is None:
            return Response({"message":"Accept Language in header is required"},status=HTTP_200_OK)

        queryset = KnowledgeArea.objects.all()
        serializer_es = KnowledgeAreaEsSerializer(queryset,many=True)
        serializer_en = KnowledgeAreaEnSerializer(queryset,many=True)
        if 'es' in self.request.META.get('HTTP_ACCEPT_LANGUAGE'):
            return Response({
                "key":"knowledge_area",
                "filter_param_value": "id",
                "name":"Área de conocimiento",
                "values":serializer_es.data}, status=HTTP_200_OK)
        elif 'en' in self.request.META.get('HTTP_ACCEPT_LANGUAGE'):
            return Response({
                "key":"knowledge_area",
                "filter_param_value": "id",
                "name":"Knowledge area",
                "values":serializer_en.data}, status=HTTP_200_OK)
        else:
            return Response({"message":"No available language"},status=HTTP_200_OK)

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