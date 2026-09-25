"""Vistas para el catálogo de niveles educativos.

El módulo expone un `ModelViewSet` sencillo, pero con dos particularidades
importantes para el contrato del frontend:

- `list` y `retrieve` son públicos, mientras que escribir requiere admin
- `list` adapta el idioma según `Accept-Language` y envuelve la respuesta
  en una estructura pensada para filtros
"""

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import EducationLevel
from rest_framework.response import Response
from .serializers import (
    EducationLevelEnSerializer,
    EducationLevelEsSerializer,
    EducationLevelListSerializer,
    EducationLevelRegisterSerializer,
)
from applications.user.mixins import IsAdministratorUser
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK,
    HTTP_406_NOT_ACCEPTABLE
)


EDUCATION_LEVEL_TAG = ['Education Level Catalog']

EDUCATION_LEVEL_ID_PARAMETER = OpenApiParameter(
    name='id',
    type=int,
    location=OpenApiParameter.PATH,
    description='Identificador interno del nivel educativo.',
)

EducationLevelFilterResponseSerializer = inline_serializer(
    name='EducationLevelFilterResponse',
    fields={
        'key': serializers.CharField(),
        'filter_param_value': serializers.CharField(),
        'name': serializers.CharField(),
        'values': inline_serializer(
            name='EducationLevelFilterValue',
            fields={
                'id': serializers.IntegerField(),
                'name_es': serializers.CharField(required=False),
                'name': serializers.CharField(),
            },
            many=True,
        ),
    },
)

EducationLevelMessageSerializer = inline_serializer(
    name='EducationLevelMessage',
    fields={
        'message': serializers.CharField(),
    },
)


@extend_schema_view(
    list=extend_schema(
        tags=EDUCATION_LEVEL_TAG,
        summary='Listar niveles educativos',
        description=(
            'Devuelve el catalogo de niveles educativos en formato de filtro. '
            'El idioma de los nombres se resuelve con el header '
            '`Accept-Language`: use `es` para español o `en` para ingles.'
        ),
        parameters=[
            OpenApiParameter(
                name='Accept-Language',
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description='Idioma de la respuesta. Valores esperados: `es` o `en`.',
                enum=['es', 'en'],
            )
        ],
        responses={
            200: EducationLevelFilterResponseSerializer,
            406: OpenApiResponse(
                response=EducationLevelMessageSerializer,
                description='El idioma solicitado no esta disponible.',
            ),
        },
        examples=[
            OpenApiExample(
                'Respuesta en español',
                value={
                    'key': 'education_levels',
                    'filter_param_value': 'id',
                    'name': 'Nivel de educación',
                    'values': [
                        {'id': 1, 'name_es': 'Educacion primaria', 'name': 'Educacion primaria'},
                        {'id': 2, 'name_es': 'Educacion secundaria', 'name': 'Educacion secundaria'},
                    ],
                },
                response_only=True,
                status_codes=['200'],
            ),
            OpenApiExample(
                'Respuesta en ingles',
                value={
                    'key': 'education_levels',
                    'filter_param_value': 'id',
                    'name': 'Education Level',
                    'values': [
                        {'id': 1, 'name_es': 'Educacion primaria', 'name': 'Primary education'},
                        {'id': 2, 'name_es': 'Educacion secundaria', 'name': 'Secondary education'},
                    ],
                },
                response_only=True,
                status_codes=['200'],
            ),
        ],
    ),
    retrieve=extend_schema(
        tags=EDUCATION_LEVEL_TAG,
        summary='Obtener nivel educativo',
        description='Devuelve un nivel educativo por su identificador.',
        parameters=[EDUCATION_LEVEL_ID_PARAMETER],
        responses={
            200: EducationLevelListSerializer,
            404: OpenApiResponse(description='Nivel educativo no encontrado.'),
        },
    ),
    create=extend_schema(
        tags=EDUCATION_LEVEL_TAG,
        summary='Crear nivel educativo',
        description=(
            'Crea un registro bilingue del catalogo de niveles educativos. '
            'Requiere autenticacion y permisos de administrador.'
        ),
        request=EducationLevelRegisterSerializer,
        responses={201: EducationLevelRegisterSerializer},
    ),
    update=extend_schema(
        tags=EDUCATION_LEVEL_TAG,
        summary='Actualizar nivel educativo',
        description=(
            'Reemplaza los nombres en español e ingles de un nivel educativo. '
            'Requiere autenticacion y permisos de administrador.'
        ),
        parameters=[EDUCATION_LEVEL_ID_PARAMETER],
        request=EducationLevelRegisterSerializer,
        responses={
            200: EducationLevelRegisterSerializer,
            404: OpenApiResponse(description='Nivel educativo no encontrado.'),
        },
    ),
    partial_update=extend_schema(
        tags=EDUCATION_LEVEL_TAG,
        summary='Actualizar parcialmente nivel educativo',
        description=(
            'Actualiza uno o mas campos del nivel educativo. Requiere '
            'autenticacion y permisos de administrador.'
        ),
        parameters=[EDUCATION_LEVEL_ID_PARAMETER],
        request=EducationLevelRegisterSerializer,
        responses={
            200: EducationLevelRegisterSerializer,
            404: OpenApiResponse(description='Nivel educativo no encontrado.'),
        },
    ),
    destroy=extend_schema(
        tags=EDUCATION_LEVEL_TAG,
        summary='Eliminar nivel educativo',
        description=(
            'Elimina un nivel educativo del catalogo. Requiere autenticacion '
            'y permisos de administrador.'
        ),
        parameters=[EDUCATION_LEVEL_ID_PARAMETER],
        responses={
            204: OpenApiResponse(description='Nivel educativo eliminado.'),
            404: OpenApiResponse(description='Nivel educativo no encontrado.'),
        },
    ),
)
class EducationLevelView(viewsets.ModelViewSet):
    """Gestiona el catálogo bilingue de niveles educativos.

    El recurso permite lectura pública del catálogo y reserva la escritura para
    administración. Además, el listado devuelve una estructura preparada para
    filtros del frontend en lugar de una lista plana del modelo.
    """

    def get_permissions(self):
        """Permite lectura pública y restringe escritura a administración."""
        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsAdministratorUser]
        return [permission() for permission in permission_classes]

    serializer_class = EducationLevelListSerializer
    queryset = EducationLevel.objects.all()
    action_serializers = {
        'create': EducationLevelRegisterSerializer,
        'update': EducationLevelRegisterSerializer,
        'partial_update': EducationLevelRegisterSerializer,
    }

    def get_serializer_class(self):
        """Usa serializers de escritura solo en acciones que modifican datos."""
        if hasattr(self, 'action_serializers'):
            return self.action_serializers.get(self.action, self.serializer_class)
        return super(EducationLevelView, self).get_serializer_class()

    def list(self, request):
        """Lista niveles educativos adaptando el idioma según `Accept-Language`.

        La respuesta no es una lista plana: devuelve un objeto con metadatos de
        filtro (`key`, `filter_param_value`, `name`) y una colección `values`
        cuyos nombres salen en español o inglés según el header recibido.
        """
        if self.request.META.get('HTTP_ACCEPT_LANGUAGE') is None:
            return Response({"message": "Accept Language in header is required"}, status=HTTP_200_OK)

        queryset = EducationLevel.objects.all().order_by('id')
        serializer_en = EducationLevelEnSerializer(queryset, many=True)
        serializer_es = EducationLevelEsSerializer(queryset, many=True)

        if 'es' in self.request.META.get('HTTP_ACCEPT_LANGUAGE'):
            return Response({
                "key": "education_levels",
                "filter_param_value": "id",
                "name": "Nivel de educación",
                "values": serializer_es.data
            }, status=HTTP_200_OK)
        elif 'en' in self.request.META.get('HTTP_ACCEPT_LANGUAGE'):
            return Response({
                "key": "education_levels",
                "filter_param_value": "id",
                "name": "Education Level",
                "values": serializer_en.data
            }, status=HTTP_200_OK)
        else:
            return Response({
                "message": "An appropriate representation of the requested resource could not be found on this server."
            }, status=HTTP_406_NOT_ACCEPTABLE)
