"""Vistas para el catálogo de áreas de conocimiento.

El módulo expone un `ViewSet` sencillo con dos rasgos importantes:

- lectura pública del catálogo y escritura restringida a administración
- respuesta de `list()` adaptada por `Accept-Language` para poblar filtros
  bilingües del frontend
"""

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, viewsets
from .models import KnowledgeArea
from .serializers import (
    KnowledgeAreaEnSerializer,
    KnowledgeAreaEsSerializer,
    KnowledgeAreaSerializer,
    KnowledgeAreaListSerializer,
)
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated ,AllowAny
from applications.user.mixins import IsAdministratorUser
from django.shortcuts import get_object_or_404
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK,
    HTTP_406_NOT_ACCEPTABLE
) 


KNOWLEDGE_AREA_TAG = ['Knowledge Area Catalog']

KNOWLEDGE_AREA_ID_PARAMETER = OpenApiParameter(
    name='id',
    type=int,
    location=OpenApiParameter.PATH,
    description='Identificador interno del area de conocimiento.',
)

KnowledgeAreaFilterResponseSerializer = inline_serializer(
    name='KnowledgeAreaFilterResponse',
    fields={
        'key': serializers.CharField(),
        'filter_param_value': serializers.CharField(),
        'name': serializers.CharField(),
        'values': KnowledgeAreaEsSerializer(many=True),
    },
)

KnowledgeAreaMessageSerializer = inline_serializer(
    name='KnowledgeAreaMessage',
    fields={
        'message': serializers.CharField(),
    },
)

@extend_schema_view(
    list=extend_schema(
        tags=KNOWLEDGE_AREA_TAG,
        summary='Listar areas de conocimiento',
        description=(
            'Devuelve el catalogo de areas de conocimiento en formato de filtro. '
            'El idioma se resuelve con el header `Accept-Language`.'
        ),
        parameters=[
            OpenApiParameter(
                name='Accept-Language',
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description='Idioma de la respuesta. Valores esperados: `es` o `en`.',
                enum=['es', 'en'],
            ),
        ],
        responses={
            200: KnowledgeAreaFilterResponseSerializer,
            406: OpenApiResponse(response=KnowledgeAreaMessageSerializer, description='Idioma no disponible.'),
        },
        examples=[
            OpenApiExample(
                'Respuesta en español',
                value={
                    'key': 'knowledge_area',
                    'filter_param_value': 'id',
                    'name': 'Area de conocimiento',
                    'values': [{'id': 1, 'name': 'Educacion', 'name_es': 'Educacion'}],
                },
                response_only=True,
                status_codes=['200'],
            ),
        ],
    ),
    retrieve=extend_schema(
        tags=KNOWLEDGE_AREA_TAG,
        summary='Obtener area de conocimiento',
        description='Devuelve una area de conocimiento por su identificador.',
        parameters=[KNOWLEDGE_AREA_ID_PARAMETER],
        responses={
            200: KnowledgeAreaSerializer,
            404: OpenApiResponse(description='Area de conocimiento no encontrada.'),
        },
    ),
    create=extend_schema(
        tags=KNOWLEDGE_AREA_TAG,
        summary='Crear area de conocimiento',
        description='Crea una area de conocimiento. Requiere permisos de administrador.',
        request=KnowledgeAreaSerializer,
        responses={200: KnowledgeAreaSerializer},
    ),
    update=extend_schema(
        tags=KNOWLEDGE_AREA_TAG,
        summary='Actualizar area de conocimiento',
        description='Reemplaza los datos de una area de conocimiento.',
        parameters=[KNOWLEDGE_AREA_ID_PARAMETER],
        request=KnowledgeAreaSerializer,
        responses={
            200: KnowledgeAreaSerializer,
            404: OpenApiResponse(description='Area de conocimiento no encontrada.'),
        },
    ),
    partial_update=extend_schema(
        tags=KNOWLEDGE_AREA_TAG,
        summary='Actualizar parcialmente area de conocimiento',
        description='Actualiza solo los campos enviados de una area de conocimiento.',
        parameters=[KNOWLEDGE_AREA_ID_PARAMETER],
        request=KnowledgeAreaSerializer,
        responses={
            200: KnowledgeAreaSerializer,
            404: OpenApiResponse(description='Area de conocimiento no encontrada.'),
        },
    ),
    destroy=extend_schema(
        tags=KNOWLEDGE_AREA_TAG,
        summary='Eliminar area de conocimiento',
        description='Elimina una area de conocimiento. Requiere permisos de administrador.',
        parameters=[KNOWLEDGE_AREA_ID_PARAMETER],
        responses={
            200: KnowledgeAreaMessageSerializer,
            404: OpenApiResponse(description='Area de conocimiento no encontrada.'),
        },
    ),
)
class KnowledgeAreaView(viewsets.ViewSet):
    """Gestiona el catálogo bilingüe de áreas de conocimiento."""

    serializer_class = KnowledgeAreaSerializer
    queryset = KnowledgeArea.objects.all()

    # authentication_classes = (TokenAuthentication,)
    def get_permissions(self):
        """Permite lectura pública y restringe escritura a administración."""
        if(self.action=='list' or self.action=='retrieve'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsAdministratorUser]
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        """
        Crea un área de conocimiento nueva.

        El endpoint usa el serializer completo del modelo, por lo que espera
        tanto nombres como descripciones bilingües cuando correspondan.
        """
        serializer = KnowledgeAreaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        serializer = KnowledgeAreaSerializer(instance)
        return Response(serializer.data, status=HTTP_200_OK)
    
    def list(self, request):
        """
        Lista áreas de conocimiento adaptando el idioma según `Accept-Language`.

        La respuesta no es una lista plana: devuelve un objeto con metadatos de
        filtro (`key`, `filter_param_value`, `name`) y una colección `values`
        cuyos nombres salen en español o inglés según el header recibido.
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
                "name":"Area de conocimiento",
                "values":serializer_es.data}, status=HTTP_200_OK)
        elif 'en' in self.request.META.get('HTTP_ACCEPT_LANGUAGE'):
            return Response({
                "key":"knowledge_area",
                "filter_param_value": "id",
                "name":"Knowledge area",
                "values":serializer_en.data}, status=HTTP_200_OK)
        else:
            return Response({"message":"An appropriate representation of the requested resource could not be found on this server."},status=HTTP_406_NOT_ACCEPTABLE)


    def retrieve(self, request, pk=None):
        """
        Recupera una área de conocimiento por identificador.
        """
        queryset = KnowledgeArea.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = KnowledgeAreaSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)
    
    def update(self, request, pk=None, project_pk=None):
        """
        Actualiza todos los campos de una área de conocimiento existente.
        """
        queryset = KnowledgeArea.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = KnowledgeAreaSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTP_200_OK)

    def partial_update(self, request, pk=None):
        """
        Actualiza parcialmente un área de conocimiento.
        """
        queryset = KnowledgeArea.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = KnowledgeAreaSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTP_200_OK)
    
    def destroy(self, request, pk=None):
        """
        Elimina un área de conocimiento por identificador.
        """
        queryset = KnowledgeArea.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.delete()
        return Response({"message": "success"},status=HTTP_200_OK)
