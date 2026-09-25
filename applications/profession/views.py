"""Vistas del catálogo de profesiones.

Este módulo expone un CRUD pequeño sobre `Profession`. La lectura del catálogo
es pública porque otros formularios, especialmente los del perfil docente,
necesitan consultar estas opciones. La escritura queda reservada a usuarios
administradores.
"""

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, viewsets
from .models import Profession
from .serializers import ProfessionSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from rest_framework.status import (
    HTTP_200_OK
)
from applications.user.mixins import IsAdministratorUser


PROFESSION_TAG = ['Profession Catalog']
PROFESSION_ID_PARAMETER = OpenApiParameter(
    name='id',
    type=int,
    location=OpenApiParameter.PATH,
    description='Identificador interno de la profesión dentro del catálogo.',
)


@extend_schema_view(
    list=extend_schema(
        tags=PROFESSION_TAG,
        summary='Listar profesiones',
        description=(
            'Devuelve todas las profesiones registradas en el catalogo. La '
            'lectura es publica porque se usa para llenar formularios de perfil '
            'docente y otros campos de seleccion.'
        ),
        responses={200: ProfessionSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=PROFESSION_TAG,
        summary='Consultar profesion',
        description='Devuelve una profesion especifica del catalogo por su identificador.',
        parameters=[PROFESSION_ID_PARAMETER],
        responses={
            200: ProfessionSerializer,
            404: OpenApiResponse(description='Profesion no encontrada.'),
        },
    ),
    create=extend_schema(
        tags=PROFESSION_TAG,
        summary='Crear profesion',
        description=(
            'Crea una nueva opcion del catalogo de profesiones. Requiere usuario '
            'autenticado con rol administrador.'
        ),
        request=ProfessionSerializer,
        responses={
            200: ProfessionSerializer,
            400: OpenApiResponse(description='Datos invalidos o descripcion duplicada.'),
        },
    ),
    update=extend_schema(
        tags=PROFESSION_TAG,
        summary='Actualizar profesion',
        description=(
            'Actualiza la descripcion de una profesion existente. Esta operacion '
            'solo modifica el catalogo, no reasigna profesiones de docentes.'
        ),
        parameters=[PROFESSION_ID_PARAMETER],
        request=ProfessionSerializer,
        responses={
            200: ProfessionSerializer,
            400: OpenApiResponse(description='Datos invalidos o descripcion duplicada.'),
            404: OpenApiResponse(description='Profesion no encontrada.'),
        },
    ),
    destroy=extend_schema(
        tags=PROFESSION_TAG,
        summary='Eliminar profesion',
        description=(
            'Elimina una profesion del catalogo por identificador. La respuesta '
            'mantiene el mensaje legacy `success` usado por el frontend.'
        ),
        parameters=[PROFESSION_ID_PARAMETER],
        responses={
            200: inline_serializer(
                name='ProfessionDeleteResponse',
                fields={'message': serializers.CharField()},
            ),
            404: OpenApiResponse(description='Profesion no encontrada.'),
        },
    ),
)
class ProfessionView(viewsets.ViewSet):
    """CRUD del catálogo de profesiones asociado al perfil docente."""

    def get_permissions(self):
        """Permite lectura pública y reserva escritura a administradores."""
        if(self.action=='list' or self.action=='retrieve'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated,IsAdministratorUser,]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        """Crea una nueva profesión dentro del catálogo administrativo.

        La vista valida el payload con `ProfessionSerializer`, persiste la
        descripción y devuelve el registro creado. Este endpoint no crea una
        relación con usuarios; solo amplia el catálogo reutilizable por ellos.
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
        """Lista todas las profesiones disponibles del catálogo.

        La respuesta se mantiene pública para que formularios o pantallas del
        sistema puedan poblar selects sin requerir autenticación administrativa.
        """
        queryset = Profession.objects.all()
        serializer = ProfessionSerializer(queryset,many=True)
        return Response(serializer.data,status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Recupera una profesión concreta por su identificador."""
        queryset = Profession.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = ProfessionSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """Actualiza la descripción de una profesión existente.

        Igual que `create`, esta operación solo afecta el catálogo base y no la
        asignación de profesiones a docentes ya existentes.
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
        """Elimina una profesión del catálogo por id."""
        queryset = Profession.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        instance.delete()
        return Response({"message": "success"},status=HTTP_200_OK)
