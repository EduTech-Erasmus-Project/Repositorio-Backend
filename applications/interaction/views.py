from django.http.response import Http404
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.interaction.models import Interaction
from applications.interaction.serializers import InteractionAllService, InteractionSerializer
from applications.user.mixins import IsStudentUser
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated ,AllowAny
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
) 
# Create your views here.
class InteractionAPIView(viewsets.ModelViewSet):
    """
        Servicio para la interacción del estudiante con el Objeto de Aprendizaje.
        La interacción se realiza en base a me gusta sobre un OA
    """
    def get_permissions(self):
        if(self.action=='list' or self.action=='retrieve'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsStudentUser]
        return [permission() for permission in permission_classes]
    def create(self, request, *args, **kwargs):
        """
            Registrar interacción del estudainte con un OA
        """
        serializer = InteractionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.request.user
        learning_object = LearningObjectMetadata.objects.get(pk=serializer.validated_data['learning_object'])
        isLiked = Interaction.objects.filter(
            learning_object__id=serializer.validated_data['learning_object'],
            user__id=user.id
        )
        if isLiked:
            return Response({"message": "Learning Object is already liked"},status=HTTP_400_BAD_REQUEST)

        instance = Interaction.objects.create(
            liked= serializer.validated_data['liked'],
            viewed= serializer.validated_data['viewed'],
            learning_object= learning_object,
            user=user
        )
        instance.save()
        serializer = InteractionAllService(instance)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Actualizar me gusta de un estudiante sobre un OA
        """
        queryset = Interaction.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = InteractionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.liked = request.data['liked']
        instance.save()
        serializer = InteractionAllService(instance)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Obtener el estado de me gusta
        """
        queryset = Interaction.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = InteractionAllService(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def destroy(self, request, pk=None):
        """
            Eliminar me gusta
        """
        queryset = Interaction.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.delete()
        return Response({"message": "success"},status=HTTP_200_OK)

    def list(self, request):
       return Response({"message": "Not found"},status=HTTP_404_NOT_FOUND)


class GetLikedLearningObjetById(APIView):
    """
        Retrieve learning object is liked by user
    """
    permission_classes = [IsAuthenticated, IsStudentUser]
    def get_object(self, pk):
        try:
            return Interaction.objects.get(learning_object__id=pk,user__id=self.request.user.id)
        except Interaction.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        snippet = self.get_object(pk)
        serializer = InteractionAllService(snippet)
        return Response(serializer.data)

