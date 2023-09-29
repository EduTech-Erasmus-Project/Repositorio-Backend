import shortuuid
from django.db.models import Count
from django.http.response import Http404
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView, CreateAPIView, ListCreateAPIView
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.interaction.models import Interaction, ViewInteraction
from applications.interaction.serializers import InteractionAllService, InteractionSerializer, InteractionMostLiked, \
    InteractionViewCreateSerializer, InteractionViewSerializer, UserRefSerializer
from applications.learning_object_metadata.serializers import LearningObjectMetadataAllSerializer
from applications.user.mixins import IsStudentUser, IsTeacherUser, IsCollaboratingExpertUser
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated ,AllowAny
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)
from roabackend.settings import env

# Create your views here.
class InteractionAPIView(viewsets.ModelViewSet):
    """
        Servicio para la interacción del estudiante con el Objeto de Aprendizaje.
        La interacción se realiza en base a me gusta sobre un OA
    """


    def get_permissions(self):
        if self.action=='list' or self.action=='retrieve':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsStudentUser | IsTeacherUser | IsCollaboratingExpertUser]
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


class GetUpdateDownloadNumber(RetrieveUpdateAPIView):
    """
        Funcion para actualizar el numero de descargar y para
        retornar el numero de descargas que existen dentro del objeto de aprendizaje
    """

    def get_permissions(self):
        permission_classes = None
        if self.request.method == 'PUT':
            permission_classes = [IsAuthenticated, IsStudentUser | IsTeacherUser | IsCollaboratingExpertUser]
        else:
            permission_classes = [AllowAny]

        return [permission() for permission in permission_classes]

    def update(self, request, *args, **kwargs):
        serializer = InteractionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.request.user
        interaction_update = Interaction.objects.filter(learning_object_id = kwargs.get('pk'), user__id=user.id)
        if interaction_update:
            number_downloaded = serializer.validated_data['downloaded']
            number_downloaded = int(number_downloaded) + 1
            interaction_update[0].downloaded = number_downloaded
            interaction_update[0].save()
            serializer = InteractionAllService(interaction_update, many=True)
            return Response(serializer.data, status=HTTP_200_OK)
        return Response({'message':'Error update Count Download'}, status=HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        interactions = Interaction.objects.filter(learning_object_id = kwargs.get('pk'))
        number_downloaded = 0
        if len(interactions) > 1 :
            for interaction in interactions:
                number_downloaded = number_downloaded + int(interaction.downloaded)
        elif len(interactions) == 1:
            number_downloaded = interactions[0].downloaded

        return Response({'message': 'success', 'number': number_downloaded},status=HTTP_200_OK)


class GetLikedLearningObjetById(APIView):
    """
        Retrieve learning object is liked by user
    """
    permission_classes = [IsAuthenticated,  IsStudentUser | IsTeacherUser | IsCollaboratingExpertUser]

    def get_object(self, pk):
        try:
            return Interaction.objects.get(learning_object__id=pk,user__id=self.request.user.id)
        except Interaction.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        snippet = self.get_object(pk)
        serializer = InteractionAllService(snippet)
        return Response(serializer.data)


class CreateDownload(CreateAPIView):
    """
    Funcion para crear la lista de contadores de descargas
    """

    permission_classes = [IsAuthenticated, IsStudentUser | IsTeacherUser | IsCollaboratingExpertUser]

    def create(self, request, *args, **kwargs):
        serializer = InteractionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.request.user

        learning_object = LearningObjectMetadata.objects.get(pk=serializer.validated_data['learning_object'])

        exist_liked = Interaction.objects.filter(
            learning_object__id=serializer.validated_data['learning_object'],
            user__id=user.id
        )

        if exist_liked:
            exist_liked[0].downloaded =serializer.validated_data['downloaded']
            exist_liked[0].save()
            serializer = InteractionAllService(exist_liked,many=True)
            return Response(serializer.data, status=HTTP_200_OK)

        instance = Interaction.objects.create(
            downloaded=serializer.validated_data['downloaded'],
            learning_object=learning_object,
            user=user
        )
        instance.save()
        serializer = InteractionAllService(instance)
        return Response(serializer.data, status=HTTP_200_OK)


class MostLikeLearningObjects(ListAPIView):
    """
    Servicio para devolver los mas gustados
    """
    permission_classes = [AllowAny]
    serializer_class = LearningObjectMetadataAllSerializer

    def get_queryset(self):
        interaction_liked = Interaction.objects.filter(liked=True)
        interactions = interaction_liked.values('learning_object_id').annotate(total=Count('learning_object_id')).order_by('-total')[:4]
        array_learning_objects = []
        for interaction in interactions:
            array_learning_objects.append(int(interaction.get('learning_object_id')))
        learning_object_metadata_query = LearningObjectMetadata.objects.filter(id__in=array_learning_objects)
        return learning_object_metadata_query


class LearingObjectLike(ListAPIView):
    """
     Servicio que devuelve la puntuación en likes del objeto de aprendizaje por el ID el objeto de aprendizaje
    """
    permission_classes = [AllowAny]
    serializer_class = InteractionMostLiked

    def get_queryset(self):
        interaction = Interaction.objects.filter(learning_object_id=self.kwargs['pk'], liked=True)
        interaction_filter = interaction.values('learning_object_id').annotate(total=Count('learning_object_id')).order_by('-total')
        return interaction_filter


class CreateViewInteraction(CreateAPIView):
    """
        Funcion para crear las interaccion de las vistas
        dentro del objeto de aprendizaje
    """
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = InteractionViewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interaction_view = ViewInteraction.objects.create(
            view=serializer.validated_data['view'],
            learning_object=serializer.validated_data['learning_object']
        )
        interaction_view.save()
        view_interaction_s = InteractionViewSerializer(interaction_view)
        return Response(view_interaction_s.data, status=HTTP_200_OK)


class GetUpdateViewNumberView(RetrieveUpdateAPIView):
    """
        Funcion para actualizar el numero de descargar y para
        retornar el numero de vistas que existen dentro del objeto de aprendizaje
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        view_interaction = ViewInteraction.objects.filter(learning_object=kwargs.get('pk'))
        if len(view_interaction) > 0:
            serializer = InteractionViewSerializer(view_interaction, many=True);
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response({'message': 'error'}, status=HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        serializer = InteractionViewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = ViewInteraction.objects.filter(learning_object=serializer.validated_data['learning_object'])
        if len(instance) > 0:
            instance[0].view = serializer.validated_data['view']
            instance[0].save()
            serializer_data = InteractionViewSerializer(instance, many=True)
            return Response(serializer_data.data, status=HTTP_200_OK)
        return Response({'message': 'error'}, status= HTTP_400_BAD_REQUEST)


class UserRefTokenInteraction(ListCreateAPIView):
    """
    Esta clase se usara para generar los tokens para controlar las visualizaciones de los recursos
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserRefSerializer(data=request.data)
        if serializer.is_valid():
            if serializer.validated_data['key_ref'] == env('KEY_REF'):
                user_token = str(shortuuid.ShortUUID().random(length=64))
                return Response({'message':'successful', 'code':200,'reference':user_token},status= HTTP_200_OK)
        return Response({'message':'Error', 'code':400}, status= HTTP_404_NOT_FOUND)
