"""Modelos de identidad, perfiles y administración de usuarios.

Este módulo separa el concepto de cuenta principal (`User`) de los perfiles de
dominio que el sistema utiliza por rol (`Student`, `Teacher`,
`CollaboratingExpert`, `Administrator`). La cuenta concentra credenciales,
datos comunes y relaciones de ubicación; cada perfil almacena los
atributos específicos de su flujo de negocio.
"""

import uuid

from django.db.models import BooleanField
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from model_utils.models import TimeStampedModel

from applications.profession.models import Profession
from applications.preferences.models import Preferences
from applications.knowledge_area.models import KnowledgeArea
from applications.education_level.models import EducationLevel
from .managers import UserManager


class Student(TimeStampedModel):
    """Perfil académico del estudiante.

    Este perfil concentra preferencias del OA, nivel educativo y áreas de
    conocimiento de interese usadas tanto en el registro como en flujos posteriores de
    filtrado y recomendación del ROA.
    """

    birthday = models.DateField(
        blank=True,
        null=True,
        help_text="Fecha de nacimiento del estudiante, usada como dato de perfil academico.",
    )
    education_levels = models.ManyToManyField(
        EducationLevel,
        help_text="Niveles educativos asociados al estudiante para filtros y recomendaciones.",
    )
    knowledge_areas = models.ManyToManyField(
        KnowledgeArea,
        help_text="Areas de conocimiento de interes del estudiante.",
    )
    preferences = models.ManyToManyField(
        Preferences,
        related_name='student_preferences',
        help_text="Preferencias de accesibilidad o uso seleccionadas por el estudiante.",
    )
    has_disability = models.BooleanField(
        default=False,
        help_text="Indica si el estudiante declaro una discapacidad o necesidad especifica.",
    )
    disability_description = models.TextField(
        blank=True,
        null=True,
        help_text="Descripcion opcional de la discapacidad o necesidad declarada.",
    )
    # `is_active` representa aprobación/uso operativo del perfil; no equivale
    # a autenticación exitosa ni a activación del correo por si sola.
    is_active = models.BooleanField(
        default=False,
        help_text="Indica si el perfil estudiante esta habilitado operativamente en el sistema.",
    )
    # Este flag separa la activación de cuenta del estado del perfil para no
    # mezclar registro, aprobación y confirmación de correo en un solo campo.
    is_account_active = models.BooleanField(
        default=False,
        help_text="Indica si la cuenta asociada completo el flujo de activacion correspondiente.",
    )

    def __str__(self):
        return str(self.id)


class Teacher(TimeStampedModel):
    """Perfil docente asociado a una cuenta principal."""

    professions = models.ManyToManyField(
        Profession,
        help_text="Profesiones asociadas al docente para validar perfil y clasificar experiencia.",
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Indica si el perfil docente esta aprobado o habilitado para operar.",
    )
    is_account_active = models.BooleanField(
        default=False,
        help_text="Indica si la cuenta del docente completo el flujo de activacion.",
    )

    def __str__(self):
        return str(self.id)


class CollaboratingExpert(TimeStampedModel):
    """Perfil del experto colaborador usado en evaluaciones expertas."""

    EXPERT_LEVEL_CHOICES = (
        ('Alto', 'Alto'),
        ('Medio', 'Medio'),
        ('Bajo', 'Bajo'),
    )
    expert_level = models.CharField(
        max_length=40,
        choices=EXPERT_LEVEL_CHOICES,
        blank=True,
        null=True,
        help_text="Nivel de experiencia declarado para priorizar o clasificar al experto colaborador.",
    )
    web = models.URLField(
        max_length=300,
        blank=True,
        null=True,
        help_text="Sitio web, perfil academico externo o enlace profesional del experto.",
    )
    academic_profile = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Resumen corto del perfil academico del experto colaborador.",
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Indica si el perfil de experto esta aprobado para evaluar objetos de aprendizaje.",
    )
    is_account_active = models.BooleanField(
        default=False,
        help_text="Indica si la cuenta del experto completo el flujo de activacion.",
    )

    def __str__(self):
        return str(self.id) + ' ' + self.expert_level


class Administrator(TimeStampedModel):
    """Perfil administrativo interno del sistema."""

    country = models.CharField(
        max_length=100,
        help_text="Pais registrado para el perfil administrativo.",
    )
    city = models.CharField(
        max_length=150,
        help_text="Ciudad registrada para el perfil administrativo.",
    )
    phone = models.IntegerField(
        blank=True,
        null=True,
        help_text="Telefono de contacto del administrador.",
    )
    observation = models.CharField(
        blank=True,
        null=True,
        max_length=600,
        help_text="Observaciones administrativas sobre la cuenta.",
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Indica si el perfil administrativo esta habilitado.",
    )

    def __str__(self):
        return str(self.id)


class User(AbstractBaseUser, TimeStampedModel):
    """Cuenta principal del sistema.

    `User` concentra credenciales, datos personales y enlaces uno a uno hacia
    los perfiles de negocio. La ubicación académica/geográfica también vive
    aquí porque varios flujos de reportes y filtros la consultan desde la
    cuenta principal, no desde cada perfil.
    """

    # Identificador funcional adicional al PK interno. Se usa en respuestas y
    # flujos externos sin exponer la semántica del id autoincremental.
    # `unique`: antes se generaba con `uuid.uuid4()` y había claves repetidas;
    # en bases antiguas, ejecutar `fix_duplicate_user_keys` antes de migrar.
    user_key = models.UUIDField(
        editable=False,
        primary_key=False,
        unique=True,
        default=uuid.uuid4,
        help_text="Identificador UUID usado para exponer o relacionar usuarios sin depender del id interno.",
    )
    first_name = models.CharField(
        'Nombres',
        max_length=100,
        help_text="Nombres del usuario registrados en la cuenta principal.",
    )
    last_name = models.CharField(
        'Apellidos',
        max_length=100,
        help_text="Apellidos del usuario registrados en la cuenta principal.",
    )
    email = models.EmailField(
        'Correo',
        max_length=50,
        unique=True,
        error_messages={'unique': "Este correo ya esta registrado."},
        help_text="Correo unico usado como credencial principal de autenticacion.",
    )
    image = models.ImageField(
        upload_to='profile',
        max_length=250,
        blank=True,
        null=True,
        default='img/user.png',
        help_text="Imagen de perfil mostrada en respuestas publicas y administrativas.",
    )
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='user_student', blank=True,
                                   null=True,
                                   help_text="Perfil estudiante asociado a la cuenta, cuando el usuario tiene ese rol.")
    teacher = models.OneToOneField(Teacher, on_delete=models.CASCADE, related_name='user_teacher', blank=True,
                                   null=True,
                                   help_text="Perfil docente asociado a la cuenta, cuando el usuario tiene ese rol.")
    collaboratingExpert = models.OneToOneField(CollaboratingExpert, on_delete=models.CASCADE,
                                               related_name='user_collaborating', blank=True, null=True,
                                               help_text="Perfil de experto colaborador asociado a la cuenta.")
    administrator = models.OneToOneField(Administrator, on_delete=models.CASCADE, related_name='user_administrator',
                                         blank=True, null=True,
                                         help_text="Perfil administrativo asociado a la cuenta.")
    is_staff = models.BooleanField(
        default=False,
        help_text="Campo heredado de compatibilidad; el acceso staff real se deriva desde la propiedad is_staff.",
    )
    is_superuser: BooleanField = models.BooleanField(
        default=False,
        help_text="Indica si la cuenta tiene privilegios globales de administracion.",
    )

    # La ubicación se modela en la cuenta principal porque la usan reportes,
    # filtros y contratos del API que no siempre consultan el perfil por rol.
    # Se guarda como texto: el frontend la toma de un catalogo geografico
    # externo (`@countrystatecity/countries-browser`), por lo que se guardan
    # codigos ISO y nombres en lugar de ids, que cambian entre versiones de
    # ese catalogo. La universidad la escribe el usuario.
    country_code = models.CharField(max_length=2, blank=True, default="",
                                    help_text="Codigo ISO 3166-1 alpha-2 del pais (por ejemplo `EC`).")
    country_name = models.CharField(max_length=100, blank=True, default="",
                                    help_text="Nombre del pais seleccionado por el usuario.")
    province_code = models.CharField(max_length=10, blank=True, default="",
                                     help_text="Codigo de la provincia o estado dentro del pais (por ejemplo `P`).")
    province_name = models.CharField(max_length=100, blank=True, default="",
                                     help_text="Nombre de la provincia o estado seleccionado por el usuario.")
    city_name = models.CharField(max_length=150, blank=True, default="",
                                 help_text="Nombre de la ciudad seleccionada por el usuario.")
    university_name = models.CharField(max_length=200, blank=True, default="",
                                       help_text="Nombre de la universidad o institucion escrita por el usuario.")

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f'{self.first_name}, {self.last_name}, {self.student}'

    def has_perm(self, perm, obj=None):
        """Devuelve siempre `True` para mantener el esquema de permisos heredado.

        Este proyecto no usa permisos granulares de Django como mecanismo principal
        de autorizacion. El control de acceso real se resuelve en vistas, mixins y
        validaciones de negocio segun el rol del usuario.
        """

        return True

    def has_module_perms(self, app_label):
        """Permite acceso a módulos según el modelo de permisos heredado."""

        return True

    @property
    def is_staff(self):
        """Deriva acceso staff desde `is_superuser` en tiempo de ejecución.

        Se conserva esta propiedad por compatibilidad con el flujo actual del
        admin y autenticación interna.
        """

        return self.is_superuser




class PublicProfile(TimeStampedModel):
    """Datos opcionales del perfil público de un usuario.

    Vive en una tabla aparte, uno a uno con `User`, para no tocar la tabla de
    autenticación. La fila se crea la primera vez que el usuario guarda su
    perfil; si no existe, el perfil público muestra solo los datos fijos de la
    cuenta. Hoy lo usan los docentes; el diseño sirve también para expertos.
    """

    VISIBILITY_PUBLIC = 'public'
    VISIBILITY_PRIVATE = 'private'
    VISIBILITY_CHOICES = (VISIBILITY_PUBLIC, VISIBILITY_PRIVATE)

    # Campos opcionales cuya visibilidad decide el usuario. Si una clave no está
    # guardada en `field_visibility`, se usa el valor de este diccionario.
    VISIBILITY_DEFAULTS = {
        'headline': VISIBILITY_PUBLIC,
        'faculty': VISIBILITY_PUBLIC,
        'bio': VISIBILITY_PUBLIC,
        'research_lines': VISIBILITY_PUBLIC,
        'subjects': VISIBILITY_PUBLIC,
        'research_group': VISIBILITY_PUBLIC,
    }

    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='public_profile',
        help_text="Cuenta a la que pertenece el perfil publico.",
    )
    headline = models.CharField(
        max_length=120,
        blank=True,
        help_text="Titular corto del perfil, por ejemplo 'Docente de Ingenieria Civil'.",
    )
    faculty = models.CharField(
        max_length=150,
        blank=True,
        help_text="Facultad o carrera en la que trabaja el usuario.",
    )
    bio = models.TextField(
        max_length=600,
        blank=True,
        help_text="Biografia academica en texto plano.",
    )
    research_lines = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de lineas de investigacion (textos cortos).",
    )
    subjects = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de asignaturas que dicta el usuario.",
    )
    research_group = models.CharField(
        max_length=150,
        blank=True,
        help_text="Grupo de investigacion al que pertenece el usuario.",
    )
    field_visibility = models.JSONField(
        default=dict,
        blank=True,
        help_text="Visibilidad por campo opcional: {'campo': 'public' | 'private'}.",
    )
    is_public = models.BooleanField(
        default=True,
        help_text="Indica si el perfil se puede ver publicamente.",
    )

    def __str__(self):
        return str(self.id)

    def get_field_visibility(self):
        """Devuelve la visibilidad de todos los campos opcionales.

        Parte de `VISIBILITY_DEFAULTS` y aplica encima lo guardado. Ignora
        claves o valores fuera de la lista cerrada para que un dato inválido en
        la base nunca exponga un campo por error.
        """

        visibility = dict(self.VISIBILITY_DEFAULTS)
        for field_name, value in (self.field_visibility or {}).items():
            if field_name in self.VISIBILITY_DEFAULTS and value in self.VISIBILITY_CHOICES:
                visibility[field_name] = value
        return visibility

    def is_field_public(self, field_name):
        """Indica si un campo opcional está marcado como público."""

        return self.get_field_visibility().get(field_name) == self.VISIBILITY_PUBLIC

    def get_highest_degree(self, only_visible=True):
        """Devuelve el nivel del título más alto, o `None` si no hay títulos.

        El grado académico no se guarda aparte para no duplicar datos: se
        calcula desde `AcademicDegree`. Recorre `degrees.all()` para
        aprovechar un `prefetch_related` si la vista lo hizo.
        """

        # Un perfil sin guardar (usuario que aún no lo editó) no tiene títulos.
        if self.pk is None:
            return None
        levels = [
            degree.level
            for degree in self.degrees.all()
            if degree.is_visible or not only_visible
        ]
        if not levels:
            return None
        return max(levels, key=AcademicDegree.LEVEL_RANK.__getitem__)


class UserLink(TimeStampedModel):
    """Enlace académico o profesional del perfil público (uno por tipo)."""

    TYPES = (
        ('orcid', 'ORCID'),
        ('scholar', 'Google Scholar'),
        ('scopus', 'Scopus Author ID'),
        ('researchgate', 'ResearchGate'),
        ('linkedin', 'LinkedIn'),
        ('institutional', 'Pagina institucional'),
        ('website', 'Web personal'),
    )

    profile = models.ForeignKey(
        PublicProfile,
        on_delete=models.CASCADE,
        related_name='links',
        help_text="Perfil publico al que pertenece el enlace.",
    )
    type = models.CharField(
        max_length=20,
        choices=TYPES,
        help_text="Tipo de enlace; solo puede haber uno de cada tipo por perfil.",
    )
    url = models.URLField(
        max_length=300,
        help_text="URL https del enlace.",
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Posicion del enlace en el perfil, definida por el usuario.",
    )
    is_visible = models.BooleanField(
        default=True,
        help_text="Indica si el enlace se muestra en el perfil publico.",
    )

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(fields=['profile', 'type'], name='unique_link_type_per_profile'),
        ]

    def __str__(self):
        return str(self.id)


class AcademicDegree(TimeStampedModel):
    """Título académico del perfil público."""

    # Niveles de educación superior del Reglamento de Régimen Académico (CES),
    # de menor a mayor. Diplomados y cursos no son títulos: no van aquí.
    LEVELS = (
        ('technical', 'Técnico o tecnólogo superior'),
        ('third', 'Tercer nivel de grado'),
        ('specialty', 'Especialización'),
        ('master', 'Magister'),
        ('phd', 'PhD'),
    )
    # Rango de cada nivel para calcular el grado más alto.
    LEVEL_RANK = {
        'technical': 1,
        'third': 2,
        'specialty': 3,
        'master': 4,
        'phd': 5,
    }

    profile = models.ForeignKey(
        PublicProfile,
        on_delete=models.CASCADE,
        related_name='degrees',
        help_text="Perfil publico al que pertenece el titulo.",
    )
    level = models.CharField(
        max_length=10,
        choices=LEVELS,
        help_text="Nivel del titulo: tecnico o tecnologo superior, tercer nivel, especializacion, magister o PhD.",
    )
    title = models.CharField(
        max_length=200,
        help_text="Nombre del titulo obtenido.",
    )
    institution = models.CharField(
        max_length=200,
        help_text="Institucion que otorgo el titulo.",
    )
    year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Anio en que se obtuvo el titulo.",
    )
    is_visible = models.BooleanField(
        default=True,
        help_text="Indica si el titulo se muestra en el perfil publico.",
    )

    class Meta:
        ordering = ['-year']

    def __str__(self):
        return str(self.id)
