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
from ..address.models import Country, Province, City, University, Campus


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
    user_key = models.UUIDField(
        editable=False,
        primary_key=False,
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
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, related_name="user_country", null=True,
                                blank=True,
                                help_text="Pais asociado a la cuenta para reportes y filtros geograficos.")
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, related_name="user_province", null=True,
                                 blank=True,
                                 help_text="Provincia asociada a la cuenta para segmentacion geografica.")
    city = models.ForeignKey(City, on_delete=models.SET_NULL, related_name="user_city", null=True, blank=True,
                             help_text="Ciudad asociada a la cuenta para reportes y filtros.")
    university = models.ForeignKey(University, on_delete=models.SET_NULL, related_name="user_university", null=True,
                                   blank=True,
                                   help_text="Universidad asociada al usuario para reportes academicos.")
    campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, related_name="user_campus", null=True, blank=True,
                               help_text="Campus asociado al usuario dentro de la universidad.")

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


