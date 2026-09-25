"""Vistas para catálogos de dirección e institución.

El módulo mezcla dos grupos de endpoints:

- catálogos públicos filtrados por `is_active`
- CRUD básico de países, provincias, ciudades, universidades y campus

Varios `ListCreateAPIView` devuelven serializers más completos en `GET` que en
`POST`, por eso conviene documentar cada vista aunque la lógica sea corta.
"""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.permissions import AllowAny
from rest_framework import generics, status
from applications.address.models import City, University, Campus, Country, Province
from applications.address.serializers import CitiesSerializer, UniversitySerializer, CampusSerializer, \
    CountrySerializer, ProvinceSerializer, CitySerializer, ProvinceSerializerWithCountry, \
    UniversitySerializerWithCountry, FullCampusSerializer
from rest_framework.response import Response


ADDRESS_COUNTRY_TAG = ['Address Countries']
ADDRESS_PROVINCE_TAG = ['Address Provinces']
ADDRESS_CITY_TAG = ['Address Cities']
ADDRESS_UNIVERSITY_TAG = ['Address Universities']
ADDRESS_CAMPUS_TAG = ['Address Campus']


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_COUNTRY_TAG,
        summary='Listar paises activos',
        description=(
            'Devuelve los paises activos del catalogo. Este endpoint se usa en '
            'formularios publicos y filtros donde no deben mostrarse registros '
            'deshabilitados.'
        ),
        responses={200: CountrySerializer(many=True)},
    )
)
class GetAddressCountriesActiveListAPIView(generics.ListAPIView):
    """Lista los países activos disponibles en el catálogo público."""

    queryset = Country.objects.filter(is_active=True).order_by('id')
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_CITY_TAG,
        summary='Listar ciudades activas',
        description=(
            'Devuelve las ciudades activas e incluye la provincia asociada para '
            'que el cliente pueda mostrar el contexto geografico sin hacer otra '
            'consulta.'
        ),
        responses={200: CitiesSerializer(many=True)},
    )
)
class GetAddressCitiesListAPIView(generics.ListAPIView):
    """Lista las ciudades activas junto con su provincia anidada."""

    queryset = City.objects.filter(is_active=True).order_by('id')
    serializer_class = CitiesSerializer
    permission_classes = [AllowAny]


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_UNIVERSITY_TAG,
        summary='Listar universidades activas por pais',
        description=(
            'Recibe el identificador de un pais y devuelve las universidades '
            'activas asociadas a ese pais.'
        ),
        parameters=[
            OpenApiParameter(
                name='pk',
                type=int,
                location=OpenApiParameter.PATH,
                description='Identificador del pais usado para filtrar universidades.',
            )
        ],
        responses={200: UniversitySerializer(many=True)},
    )
)
class GetUniversitiesByCountryListAPIView(generics.ListAPIView):
    """Lista universidades activas filtradas por país."""

    queryset = University.objects.filter(is_active=True).order_by('id')
    serializer_class = UniversitySerializer
    permission_classes = [AllowAny]

    def get(self, request, pk):
        """Filtra universidades activas por `country_id`."""
        query = self.queryset.filter(country_id=pk).order_by('id')
        serializer = self.serializer_class(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_UNIVERSITY_TAG,
        summary='Listar universidades activas por ciudad',
        description=(
            'Recibe una ciudad, resuelve el pais al que pertenece y devuelve las '
            'universidades activas de ese pais. No filtra directamente por '
            'campus o sede de la ciudad.'
        ),
        parameters=[
            OpenApiParameter(
                name='pk',
                type=int,
                location=OpenApiParameter.PATH,
                description='Identificador de la ciudad usada para resolver el pais.',
            )
        ],
        responses={
            200: UniversitySerializer(many=True),
            404: OpenApiResponse(description='Ciudad o pais no encontrado.'),
        },
    )
)
class GetUniversitiesByCityListAPIView(generics.ListAPIView):
    """Lista universidades usando la ciudad como punto de entrada.

    La consulta no filtra por ciudad de campus, sino por el país al que
    pertenece la ciudad recibida en la URL.
    """

    queryset = University.objects.filter(is_active=True)
    serializer_class = UniversitySerializer
    permission_classes = [AllowAny]

    def get(self, request, pk):
        """Resuelve el país de la ciudad y devuelve sus universidades activas."""
        country = get_object_or_404(Country, province__city__id=pk)
        query = self.queryset.filter(country_id=country.id).order_by('id')
        serializer = self.serializer_class(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_UNIVERSITY_TAG,
        summary='Listar universidades activas',
        description='Devuelve todas las universidades activas del catalogo publico.',
        responses={200: UniversitySerializer(many=True)},
    )
)
class GetUniversitiesListAPIView(generics.ListAPIView):
    """Lista todas las universidades activas del catálogo público."""

    queryset = University.objects.filter(is_active=True)
    serializer_class = UniversitySerializer
    permission_classes = [AllowAny]


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_CAMPUS_TAG,
        summary='Listar campus activos',
        description='Devuelve todos los campus activos registrados en el catalogo.',
        responses={200: CampusSerializer(many=True)},
    )
)
class GetCampusListAPIView(generics.ListAPIView):
    """Lista todos los campus activos."""

    queryset = Campus.objects.filter(is_active=True)
    serializer_class = CampusSerializer
    permission_classes = [AllowAny]


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_CAMPUS_TAG,
        summary='Listar campus activos por universidad',
        description='Devuelve los campus activos asociados a una universidad.',
        parameters=[
            OpenApiParameter(
                name='pk',
                type=int,
                location=OpenApiParameter.PATH,
                description='Identificador de la universidad usada para filtrar campus.',
            )
        ],
        responses={200: CampusSerializer(many=True)},
    )
)
class GetCampusByUniversityListAPIView(generics.ListAPIView):
    """Lista campus activos filtrados por universidad."""

    queryset = Campus.objects.filter(is_active=True).order_by('id')
    serializer_class = CampusSerializer
    permission_classes = [AllowAny]

    def get(self, request, pk):
        """Filtra campus activos por `university_id`."""
        query = self.queryset.filter(university_id=pk).order_by('id')
        serializer = self.serializer_class(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_COUNTRY_TAG,
        summary='Listar paises',
        description='Devuelve todos los paises del catalogo, activos e inactivos.',
        responses={200: CountrySerializer(many=True)},
    ),
    post=extend_schema(
        tags=ADDRESS_COUNTRY_TAG,
        summary='Crear pais',
        description='Crea un pais del catalogo usando los campos del modelo Country.',
        request=CountrySerializer,
        responses={201: CountrySerializer},
    ),
)
class CountryListCreateAPIView(generics.ListCreateAPIView):
    """CRUD básico de países.

    Aunque el comentario legado habla de permisos admin, hoy la vista está en
    `AllowAny`; por eso conviene revisar permisos antes de endurecer el acceso.
    """

    queryset = Country.objects.all().order_by('id')
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_COUNTRY_TAG,
        summary='Consultar pais',
        description='Devuelve el detalle de un pais por identificador.',
        responses={200: CountrySerializer, 404: OpenApiResponse(description='Pais no encontrado.')},
    ),
    put=extend_schema(
        tags=ADDRESS_COUNTRY_TAG,
        summary='Actualizar pais',
        description='Reemplaza los datos de un pais existente.',
        request=CountrySerializer,
        responses={200: CountrySerializer, 404: OpenApiResponse(description='Pais no encontrado.')},
    ),
    patch=extend_schema(
        tags=ADDRESS_COUNTRY_TAG,
        summary='Actualizar parcialmente pais',
        description='Actualiza solo los campos enviados de un pais existente.',
        request=CountrySerializer,
        responses={200: CountrySerializer, 404: OpenApiResponse(description='Pais no encontrado.')},
    ),
    delete=extend_schema(
        tags=ADDRESS_COUNTRY_TAG,
        summary='Eliminar pais',
        description='Elimina un pais por identificador.',
        responses={204: OpenApiResponse(description='Pais eliminado.')},
    ),
)
class CountryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, actualiza o elimina un país por identificador."""

    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_PROVINCE_TAG,
        summary='Listar provincias',
        description=(
            'Devuelve todas las provincias del catalogo. La respuesta de lectura '
            'incluye el pais anidado para mostrar el contexto geografico.'
        ),
        responses={200: ProvinceSerializerWithCountry(many=True)},
    ),
    post=extend_schema(
        tags=ADDRESS_PROVINCE_TAG,
        summary='Crear provincia',
        description='Crea una provincia usando el identificador del pais en el cuerpo de la solicitud.',
        request=ProvinceSerializer,
        responses={201: ProvinceSerializer},
    ),
)
class ProvinceListCreateAPIView(generics.ListCreateAPIView):
    """CRUD básico de provincias.

    En lectura usa una representación mas completa que anida el país.
    """

    queryset = Province.objects.all().order_by('id')
    serializer_class = ProvinceSerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin

    def get(self, request):
        """Lista provincias usando el serializer que incluye país anidado."""
        serializer = ProvinceSerializerWithCountry(self.queryset.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_PROVINCE_TAG,
        summary='Consultar provincia',
        description='Devuelve el detalle plano de una provincia por identificador.',
        responses={200: ProvinceSerializer, 404: OpenApiResponse(description='Provincia no encontrada.')},
    ),
    put=extend_schema(
        tags=ADDRESS_PROVINCE_TAG,
        summary='Actualizar provincia',
        description='Reemplaza los datos de una provincia existente.',
        request=ProvinceSerializer,
        responses={200: ProvinceSerializer, 404: OpenApiResponse(description='Provincia no encontrada.')},
    ),
    patch=extend_schema(
        tags=ADDRESS_PROVINCE_TAG,
        summary='Actualizar parcialmente provincia',
        description='Actualiza solo los campos enviados de una provincia existente.',
        request=ProvinceSerializer,
        responses={200: ProvinceSerializer, 404: OpenApiResponse(description='Provincia no encontrada.')},
    ),
    delete=extend_schema(
        tags=ADDRESS_PROVINCE_TAG,
        summary='Eliminar provincia',
        description='Elimina una provincia por identificador.',
        responses={204: OpenApiResponse(description='Provincia eliminada.')},
    ),
)
class ProvinceRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, actualiza o elimina una provincia por identificador."""

    queryset = Province.objects.all()
    serializer_class = ProvinceSerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_PROVINCE_TAG,
        summary='Listar provincias por pais',
        description='Devuelve las provincias asociadas al pais recibido en la URL.',
        parameters=[
            OpenApiParameter(
                name='pk',
                type=int,
                location=OpenApiParameter.PATH,
                description='Identificador del pais usado para filtrar provincias.',
            )
        ],
        responses={200: ProvinceSerializerWithCountry(many=True)},
    ),
    post=extend_schema(
        tags=ADDRESS_PROVINCE_TAG,
        summary='Crear provincia desde ruta filtrada',
        description=(
            'Operacion heredada por ListCreateAPIView. Crea una provincia con el '
            'cuerpo enviado; el pais debe venir en el payload.'
        ),
        request=ProvinceSerializer,
        responses={201: ProvinceSerializer},
    ),
)
class ProvinceByCountry(generics.ListCreateAPIView):
    """Lista provincias filtradas por país."""

    queryset = Province.objects.all().order_by('id')
    serializer_class = ProvinceSerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin

    def get(self, request, pk):
        """Filtra provincias por `country_id` usando salida con país anidado."""
        query = self.queryset.filter(country_id=pk).order_by('id')
        serializer = ProvinceSerializerWithCountry(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_CITY_TAG,
        summary='Listar ciudades',
        description=(
            'Devuelve todas las ciudades del catalogo. La respuesta de lectura '
            'incluye la provincia anidada.'
        ),
        responses={200: CitiesSerializer(many=True)},
    ),
    post=extend_schema(
        tags=ADDRESS_CITY_TAG,
        summary='Crear ciudad',
        description='Crea una ciudad usando el identificador de la provincia en el cuerpo de la solicitud.',
        request=CitySerializer,
        responses={201: CitySerializer},
    ),
)
class CityListCreateAPIView(generics.ListCreateAPIView):
    """CRUD básico de ciudades.

    En lectura devuelve la provincia anidada para evitar consultas extra del
    cliente.
    """

    queryset = City.objects.all().order_by('id')
    serializer_class = CitySerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin

    def get(self, request):
        """Lista ciudades usando el serializer que incluye provincia anidada."""
        serializer = CitiesSerializer(self.queryset.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_CITY_TAG,
        summary='Consultar ciudad',
        description='Devuelve el detalle plano de una ciudad por identificador.',
        responses={200: CitySerializer, 404: OpenApiResponse(description='Ciudad no encontrada.')},
    ),
    put=extend_schema(
        tags=ADDRESS_CITY_TAG,
        summary='Actualizar ciudad',
        description='Reemplaza los datos de una ciudad existente.',
        request=CitySerializer,
        responses={200: CitySerializer, 404: OpenApiResponse(description='Ciudad no encontrada.')},
    ),
    patch=extend_schema(
        tags=ADDRESS_CITY_TAG,
        summary='Actualizar parcialmente ciudad',
        description='Actualiza solo los campos enviados de una ciudad existente.',
        request=CitySerializer,
        responses={200: CitySerializer, 404: OpenApiResponse(description='Ciudad no encontrada.')},
    ),
    delete=extend_schema(
        tags=ADDRESS_CITY_TAG,
        summary='Eliminar ciudad',
        description='Elimina una ciudad por identificador.',
        responses={204: OpenApiResponse(description='Ciudad eliminada.')},
    ),
)
class CityRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, actualiza o elimina una ciudad por identificador."""

    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_UNIVERSITY_TAG,
        summary='Listar universidades',
        description=(
            'Devuelve todas las universidades del catalogo. La respuesta de '
            'lectura incluye el pais anidado.'
        ),
        responses={200: UniversitySerializerWithCountry(many=True)},
    ),
    post=extend_schema(
        tags=ADDRESS_UNIVERSITY_TAG,
        summary='Crear universidad',
        description='Crea una universidad usando el identificador del pais en el cuerpo de la solicitud.',
        request=UniversitySerializer,
        responses={201: UniversitySerializer},
    ),
)
class UniversityListCreateAPIView(generics.ListCreateAPIView):
    """CRUD básico de universidades.

    En lectura devuelve el país anidado para que el frontend tenga contexto
    geográfico sin resolver relaciones por separado.
    """

    queryset = University.objects.all().order_by('id')
    serializer_class = UniversitySerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin

    def get(self, request):
        """Lista universidades usando el serializer que incluye país anidado."""
        serializer = UniversitySerializerWithCountry(self.queryset.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_UNIVERSITY_TAG,
        summary='Consultar universidad',
        description='Devuelve el detalle plano de una universidad por identificador.',
        responses={200: UniversitySerializer, 404: OpenApiResponse(description='Universidad no encontrada.')},
    ),
    put=extend_schema(
        tags=ADDRESS_UNIVERSITY_TAG,
        summary='Actualizar universidad',
        description='Reemplaza los datos de una universidad existente.',
        request=UniversitySerializer,
        responses={200: UniversitySerializer, 404: OpenApiResponse(description='Universidad no encontrada.')},
    ),
    patch=extend_schema(
        tags=ADDRESS_UNIVERSITY_TAG,
        summary='Actualizar parcialmente universidad',
        description='Actualiza solo los campos enviados de una universidad existente.',
        request=UniversitySerializer,
        responses={200: UniversitySerializer, 404: OpenApiResponse(description='Universidad no encontrada.')},
    ),
    delete=extend_schema(
        tags=ADDRESS_UNIVERSITY_TAG,
        summary='Eliminar universidad',
        description='Elimina una universidad por identificador.',
        responses={204: OpenApiResponse(description='Universidad eliminada.')},
    ),
)
class UniversityRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, actualiza o elimina una universidad por identificador."""

    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_CAMPUS_TAG,
        summary='Listar campus',
        description=(
            'Devuelve todos los campus del catalogo. La respuesta de lectura '
            'incluye universidad y ciudad anidadas.'
        ),
        responses={200: FullCampusSerializer(many=True)},
    ),
    post=extend_schema(
        tags=ADDRESS_CAMPUS_TAG,
        summary='Crear campus',
        description='Crea un campus usando los identificadores de universidad y ciudad en el cuerpo.',
        request=CampusSerializer,
        responses={201: CampusSerializer},
    ),
)
class CampusListCreateAPIView(generics.ListCreateAPIView):
    """CRUD básico de campus o sedes.

    En lectura expone universidad y ciudad anidadas porque el campus suele
    mostrarse junto con ambas relaciones.
    """

    queryset = Campus.objects.all().order_by('id')
    serializer_class = CampusSerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin

    def get(self, request):
        """Lista campus usando el serializer completo con universidad y ciudad."""
        serializer = FullCampusSerializer(self.queryset.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=ADDRESS_CAMPUS_TAG,
        summary='Consultar campus',
        description='Devuelve el detalle plano de un campus por identificador.',
        responses={200: CampusSerializer, 404: OpenApiResponse(description='Campus no encontrado.')},
    ),
    put=extend_schema(
        tags=ADDRESS_CAMPUS_TAG,
        summary='Actualizar campus',
        description='Reemplaza los datos de un campus existente.',
        request=CampusSerializer,
        responses={200: CampusSerializer, 404: OpenApiResponse(description='Campus no encontrado.')},
    ),
    patch=extend_schema(
        tags=ADDRESS_CAMPUS_TAG,
        summary='Actualizar parcialmente campus',
        description='Actualiza solo los campos enviados de un campus existente.',
        request=CampusSerializer,
        responses={200: CampusSerializer, 404: OpenApiResponse(description='Campus no encontrado.')},
    ),
    delete=extend_schema(
        tags=ADDRESS_CAMPUS_TAG,
        summary='Eliminar campus',
        description='Elimina un campus por identificador.',
        responses={204: OpenApiResponse(description='Campus eliminado.')},
    ),
)
class CampusRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, actualiza o elimina un campus por identificador."""

    queryset = Campus.objects.all()
    serializer_class = CampusSerializer
    permission_classes = [AllowAny]  # permisos autenticado y solo de admin
