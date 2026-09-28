"""Vistas del catálogo de preferencias y sus filtros auxiliares.

Este módulo expone dos familias de endpoints:
- CRUDs administrativos para preferencias y sus áreas
- listados públicos usados por el frontend para construir filtros o mostrar
  el catálogo ya agrupado

La mayor parte de la lógica aquí no transforma datos complejos, pero si define
que respuestas son públicas, cuales requieren administrador y que serializer se
usa según el caso de lectura o escritura.
"""

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from .models import Preferences, PreferencesArea, PreferencesFilter, PreferencesFilterArea
from rest_framework.permissions import IsAuthenticated ,AllowAny
from .serializers import PreferencesAreaFilterSerializer, PreferencesAreaListSerializer, PreferencesByAreaSerializer, PreferencesSerializer
from applications.user.mixins import IsAdministratorUser, IsCollaboratingExpertUser, IsStudentUser, IsTeacherUser


PREFERENCES_TAG = ['Preferences Catalog']
PREFERENCES_FILTERS_TAG = ['Preferences Filters']

PREFERENCE_ID_PARAMETER = OpenApiParameter(
    'id',
    int,
    OpenApiParameter.PATH,
    description='Identificador interno de la preferencia.',
)
PREFERENCE_AREA_ID_PARAMETER = OpenApiParameter(
    'id',
    int,
    OpenApiParameter.PATH,
    description='Identificador interno del area de preferencias.',
)


@extend_schema_view(
    list=extend_schema(
        tags=PREFERENCES_TAG,
        summary='Listar preferencias',
        description='Devuelve el catalogo completo de preferencias individuales.',
        responses={200: PreferencesSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=PREFERENCES_TAG,
        summary='Obtener preferencia',
        description='Devuelve una preferencia individual por su identificador.',
        parameters=[PREFERENCE_ID_PARAMETER],
        responses={
            200: PreferencesSerializer,
            404: OpenApiResponse(description='Preferencia no encontrada.'),
        },
    ),
    create=extend_schema(
        tags=PREFERENCES_TAG,
        summary='Crear preferencia',
        description='Crea una preferencia del catalogo. Requiere permisos de administrador.',
        request=PreferencesSerializer,
        responses={201: PreferencesSerializer},
    ),
    update=extend_schema(
        tags=PREFERENCES_TAG,
        summary='Actualizar preferencia',
        description='Reemplaza los datos de una preferencia. Requiere permisos de administrador.',
        parameters=[PREFERENCE_ID_PARAMETER],
        request=PreferencesSerializer,
        responses={
            200: PreferencesSerializer,
            404: OpenApiResponse(description='Preferencia no encontrada.'),
        },
    ),
    partial_update=extend_schema(
        tags=PREFERENCES_TAG,
        summary='Actualizar parcialmente preferencia',
        description='Actualiza solo los campos enviados de una preferencia.',
        parameters=[PREFERENCE_ID_PARAMETER],
        request=PreferencesSerializer,
        responses={
            200: PreferencesSerializer,
            404: OpenApiResponse(description='Preferencia no encontrada.'),
        },
    ),
    destroy=extend_schema(
        tags=PREFERENCES_TAG,
        summary='Eliminar preferencia',
        description='Elimina una preferencia del catalogo. Requiere permisos de administrador.',
        parameters=[PREFERENCE_ID_PARAMETER],
        responses={
            204: OpenApiResponse(description='Preferencia eliminada.'),
            404: OpenApiResponse(description='Preferencia no encontrada.'),
        },
    ),
)
class UserPrefrencesView(viewsets.ModelViewSet):
    """Administra el catálogo base de preferencias individuales.

    Las operaciones de lectura son públicas para que otras vistas o clientes
    puedan consultar el catálogo. Crear, editar o borrar preferencias queda
    restringido al rol administrador.
    """

    def get_permissions(self):
        """Permite lectura pública y reserva escritura a administradores."""

        if(self.action=='list' or self.action=='retrieve'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated,IsAdministratorUser]
        return [permission() for permission in permission_classes]

    serializer_class = PreferencesSerializer
    queryset = Preferences.objects.all()


@extend_schema_view(
    list=extend_schema(
        tags=PREFERENCES_TAG,
        summary='Listar areas de preferencias',
        description=(
            'Devuelve las areas del catalogo con sus preferencias anidadas. Esta respuesta '
            'se usa para construir formularios agrupados en registro, perfil o filtros.'
        ),
        responses={200: PreferencesByAreaSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=PREFERENCES_TAG,
        summary='Obtener area de preferencias',
        description='Devuelve un area de preferencias por su identificador.',
        parameters=[PREFERENCE_AREA_ID_PARAMETER],
        responses={
            200: PreferencesAreaListSerializer,
            404: OpenApiResponse(description='Area de preferencias no encontrada.'),
        },
    ),
    create=extend_schema(
        tags=PREFERENCES_TAG,
        summary='Crear area de preferencias',
        description='Crea un area para agrupar preferencias. Requiere permisos de administrador.',
        request=PreferencesAreaListSerializer,
        responses={201: PreferencesAreaListSerializer},
    ),
    update=extend_schema(
        tags=PREFERENCES_TAG,
        summary='Actualizar area de preferencias',
        description='Reemplaza los datos de un area de preferencias.',
        parameters=[PREFERENCE_AREA_ID_PARAMETER],
        request=PreferencesAreaListSerializer,
        responses={
            200: PreferencesAreaListSerializer,
            404: OpenApiResponse(description='Area de preferencias no encontrada.'),
        },
    ),
    partial_update=extend_schema(
        tags=PREFERENCES_TAG,
        summary='Actualizar parcialmente area de preferencias',
        description='Actualiza solo los campos enviados de un area de preferencias.',
        parameters=[PREFERENCE_AREA_ID_PARAMETER],
        request=PreferencesAreaListSerializer,
        responses={
            200: PreferencesAreaListSerializer,
            404: OpenApiResponse(description='Area de preferencias no encontrada.'),
        },
    ),
    destroy=extend_schema(
        tags=PREFERENCES_TAG,
        summary='Eliminar area de preferencias',
        description='Elimina un area de preferencias. Requiere permisos de administrador.',
        parameters=[PREFERENCE_AREA_ID_PARAMETER],
        responses={
            204: OpenApiResponse(description='Area de preferencias eliminada.'),
            404: OpenApiResponse(description='Area de preferencias no encontrada.'),
        },
    ),
)
class PrefrencesAreaView(viewsets.ModelViewSet):
    """Gestiona las áreas que agrupan preferencias del catálogo.

    En escritura usa el serializer plano del modelo. En `list` cambia a una
    salida anidada para devolver cada área junto con las preferencias que
    contiene, que es la forma más útil para el frontend.
    """

    def get_permissions(self):
        """Permite lectura pública y reserva escritura a administradores."""

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
        """Usa salida agrupada solo cuando se lista el catálogo por área."""

        if hasattr(self, 'action_serializers'):
            return self.action_serializers.get(self.action, self.serializer_class)
        return super(PrefrencesAreaView, self).get_serializer_class()


@extend_schema(
    tags=PREFERENCES_FILTERS_TAG,
    summary='Listar areas de filtros de preferencias',
    description=(
        'Devuelve la estructura auxiliar de filtros de preferencias agrupada por area. '
        'No es el catalogo de preferencias del perfil; es el mapping usado para construir '
        'filtros de objetos de aprendizaje.'
    ),
    responses={200: PreferencesAreaFilterSerializer(many=True)},
)
class AreaFilters(ListAPIView):
    """Lista áreas de filtros auxiliares con sus mappings anidados.

    Este endpoint no devuelve las preferencias del perfil del estudiante, sino
    la estructura de `PreferencesFilterArea` y `PreferencesFilter` que otras
    capas reutilizan para traducir o agrupar valores de búsqueda.
    """

    permission_classes = [AllowAny]
    pagination_class=None
    serializer_class = PreferencesAreaFilterSerializer
    queryset = PreferencesFilterArea.objects.all()


@extend_schema(
    tags=PREFERENCES_FILTERS_TAG,
    summary='Listar preferencias para usuario autenticado',
    description=(
        'Devuelve areas de filtros de preferencias para usuarios autenticados con rol '
        'estudiante, docente o experto colaborador. El nombre heredado de la vista no '
        'implica que actualmente filtre por correo.'
    ),
    responses={200: PreferencesAreaFilterSerializer(many=True)},
)
class PreferencesByEmail(ListAPIView):
    """Expone filtros de preferencias a usuarios autenticados no administradores.

    Aunque el nombre heredado del endpoint sugiere una busqueda por correo,
    hoy la vista simplemente devuelve el mismo queryset de areas de filtros y
    exige que el usuario autenticado pertenezca a alguno de los roles finales
    del sistema.
    """

    permission_classes = [IsAuthenticated, (IsStudentUser | IsTeacherUser | IsCollaboratingExpertUser)]
    serializer_class = PreferencesAreaFilterSerializer
    queryset = PreferencesFilterArea.objects.all()


@extend_schema(
    tags=PREFERENCES_TAG,
    summary='Listar preferencias planas',
    description='Devuelve el catalogo plano de preferencias sin agrupar por area.',
    responses={200: PreferencesSerializer(many=True)},
)
class SerachPreferencesApiView(ListAPIView):
    """Lista preferencias planas para consumo público o filtros simples.

    Esta vista devuelve el queryset completo de `Preferences` sin agruparlo por
    área. Es útil cuando el cliente necesita trabajar con el catálogo plano y
    no con la estructura jerárquica usada en otras rutas del módulo.
    """

    permission_classes = [AllowAny]
    pagination_class=None
    serializer_class = PreferencesSerializer
    queryset = Preferences.objects.all()
