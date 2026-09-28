"""Vistas del catálogo de licencias y endpoints auxiliares de filtros.

Este módulo expone el CRUD de licencias y un endpoint pequeño que devuelve
las URLs base de algunos catálogos usados por el frontend para construir
filtros. La lectura del catálogo es pública; la escritura queda restringida
al rol administrador.
"""

from django.http.response import Http404
from django.shortcuts import render
import json
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view, inline_serializer
from rest_framework import exceptions, serializers, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_406_NOT_ACCEPTABLE
from rest_framework.views import APIView
from applications.user.mixins import IsAdministratorUser, IsTeacherUser
from .serializers import (
    LicenseEnSerializer,
    LicenseEsSerializer,
    LicenseSerializer,
    LicenseRegisterSerializer,
)
from .models import License


LICENSE_TAG = ['License Catalog']
LICENSE_FILTER_TAG = ['License Filters']

LICENSE_ID_PARAMETER = OpenApiParameter(
    'id',
    int,
    OpenApiParameter.PATH,
    description='Identificador interno de la licencia.',
)

LicenseFilterResponseSerializer = inline_serializer(
    name='LicenseFilterResponse',
    fields={
        'key': serializers.CharField(),
        'filter_param_value': serializers.CharField(),
        'name': serializers.CharField(),
        'values': LicenseEsSerializer(many=True),
    },
)

EndpointFilterItemSerializer = inline_serializer(
    name='EndpointFilterItem',
    fields={
        'name': serializers.CharField(),
        'endpoint': serializers.URLField(),
    },
    many=True,
)

LicenseMessageSerializer = inline_serializer(
    name='LicenseMessage',
    fields={
        'message': serializers.CharField(),
    },
)


@extend_schema_view(
    list=extend_schema(
        tags=LICENSE_TAG,
        summary='Listar licencias',
        description=(
            'Devuelve el catalogo de licencias en formato de filtro. '
            'El idioma de los nombres se resuelve con el header `Accept-Language`.'
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
            200: LicenseFilterResponseSerializer,
            406: OpenApiResponse(response=LicenseMessageSerializer, description='Idioma no disponible.'),
        },
        examples=[
            OpenApiExample(
                'Respuesta en español',
                value={
                    'key': 'license',
                    'filter_param_value': 'value',
                    'name': 'Licencia',
                    'values': [{'id': 1, 'value': 'cc-by', 'name': 'Creative Commons'}],
                },
                response_only=True,
                status_codes=['200'],
            ),
        ],
    ),
    retrieve=extend_schema(
        tags=LICENSE_TAG,
        summary='Obtener licencia',
        description='Devuelve una licencia por su identificador.',
        parameters=[LICENSE_ID_PARAMETER],
        responses={
            200: LicenseSerializer,
            404: OpenApiResponse(description='Licencia no encontrada.'),
        },
    ),
    create=extend_schema(
        tags=LICENSE_TAG,
        summary='Crear licencia',
        description='Crea una licencia del catalogo. Requiere permisos de administrador.',
        request=LicenseRegisterSerializer,
        responses={201: LicenseRegisterSerializer},
    ),
    update=extend_schema(
        tags=LICENSE_TAG,
        summary='Actualizar licencia',
        description='Reemplaza los datos de una licencia. Requiere permisos de administrador.',
        parameters=[LICENSE_ID_PARAMETER],
        request=LicenseRegisterSerializer,
        responses={
            200: LicenseRegisterSerializer,
            404: OpenApiResponse(description='Licencia no encontrada.'),
        },
    ),
    partial_update=extend_schema(
        tags=LICENSE_TAG,
        summary='Actualizar parcialmente licencia',
        description='Actualiza solo los campos enviados de una licencia.',
        parameters=[LICENSE_ID_PARAMETER],
        request=LicenseRegisterSerializer,
        responses={
            200: LicenseRegisterSerializer,
            404: OpenApiResponse(description='Licencia no encontrada.'),
        },
    ),
    destroy=extend_schema(
        tags=LICENSE_TAG,
        summary='Eliminar licencia',
        description='Elimina una licencia del catalogo. Requiere permisos de administrador.',
        parameters=[LICENSE_ID_PARAMETER],
        responses={
            204: OpenApiResponse(description='Licencia eliminada.'),
            404: OpenApiResponse(description='Licencia no encontrada.'),
        },
    ),
)
class LicenseView(viewsets.ModelViewSet):
    """CRUD del catálogo de licencias con lectura pública y escritura admin.

    El listado no devuelve una lista plana del modelo: arma una estructura de
    filtro para el frontend y adapta `name` según `Accept-Language`.
    """

    def get_permissions(self):
        """Restringe escritura a administradores y deja lectura pública."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsAdministratorUser]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    serializer_class = LicenseSerializer
    queryset = License.objects.all()
    action_serializers = {
        'create': LicenseRegisterSerializer,
        'update': LicenseRegisterSerializer,
        'partial_update': LicenseRegisterSerializer,
    }

    def get_serializer_class(self):
        """Usa el serializer de escritura solo en acciones de mutación."""
        if hasattr(self, 'action_serializers'):
            return self.action_serializers.get(self.action, self.serializer_class)
        return super(LicenseView, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """Devuelve el catálogo en formato de filtro y según el idioma pedido.

        El frontend consume esta respuesta como parte de la configuración de
        filtros, por eso el payload incluye `key`, `filter_param_value`,
        `name` y `values` en lugar de una lista plana de licencias.
        """
        if self.request.META.get('HTTP_ACCEPT_LANGUAGE') is None:
            return Response({"message": "Accept Language in header is required"}, status=HTTP_200_OK)

        queryset = License.objects.all().order_by('id')
        serializer_es = LicenseEsSerializer(queryset, many=True)
        serializer_en = LicenseEnSerializer(queryset, many=True)
        if 'es' in self.request.META.get('HTTP_ACCEPT_LANGUAGE'):
            return Response({
                "key": "license",
                "filter_param_value": "value",
                "name": "Licencia",
                "values": serializer_es.data}, status=HTTP_200_OK)
        elif 'en' in self.request.META.get('HTTP_ACCEPT_LANGUAGE'):
            return Response({
                "key": "license",
                "filter_param_value": "value",
                "name": "License",
                "values": serializer_en.data}, status=HTTP_200_OK)
        else:
            return Response({"message": "An appropriate representation of the requested resource could not be found on this server."}, status=HTTP_406_NOT_ACCEPTABLE)


class EndpontFilter(APIView):
    """Lista las URLs base de catálogos usados por la UI de filtros.

    Este endpoint no devuelve datos del catálogo en sí, sino metadatos con el
    nombre visible y la URL que el frontend puede consultar después.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=LICENSE_FILTER_TAG,
        summary='Listar endpoints de filtros',
        description=(
            'Devuelve las URLs base de catalogos relacionados con filtros: licencia, nivel educativo '
            'y area de conocimiento. La respuesta se adapta al header `Accept-Language`.'
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
            200: EndpointFilterItemSerializer,
            406: LicenseMessageSerializer,
        },
    )
    def get(self, request, format=None):
        """Devuelve el listado en español o inglés según `Accept-Language`."""
        if self.request.META.get('HTTP_ACCEPT_LANGUAGE') is None:
            return Response({"message": "Accept Language in header is required"}, status=HTTP_200_OK)
        value_es = [
                    {
                          "name": "Licencia",
                          "endpoint": "https://repositorio.edutech-project.org/api/v1/license",
                    },
                    {
                          "name": "Nivel educativo",
                          "endpoint": "https://repositorio.edutech-project.org/api/v1/education-level",
                    },
                    {
                          "name": "Area de conocimiento",
                          "endpoint": "https://repositorio.edutech-project.org/api/v1/knowledge-area",
                    }
                ]
        value_en = [
                    {
                          "name": "License",
                          "endpoint": "https://repositorio.edutech-project.org/api/v1/license",
                    },
                    {
                          "name": "Education Level",
                          "endpoint": "https://repositorio.edutech-project.org/api/v1/education-level",
                    },
                    {
                          "name": "Knowledge area",
                          "endpoint": "https://repositorio.edutech-project.org/api/v1/knowledge-area",
                    }
                ]
        if 'es' in self.request.META.get('HTTP_ACCEPT_LANGUAGE'):
            return Response(value_es, status=HTTP_200_OK)
        return Response(value_en, status=HTTP_200_OK)


class EndpontFilterLegacy(EndpontFilter):
    """Alias legacy sin slash final para conservar compatibilidad del frontend."""

    @extend_schema(
        tags=LICENSE_FILTER_TAG,
        operation_id='api_v1_endpoint_filter_legacy_retrieve',
        summary='Listar endpoints de filtros legacy',
        description='Alias sin slash final de `endpoint-filter/` para clientes legacy.',
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
        responses={200: EndpointFilterItemSerializer},
    )
    def get(self, request, format=None):
        return super().get(request, format=format)
