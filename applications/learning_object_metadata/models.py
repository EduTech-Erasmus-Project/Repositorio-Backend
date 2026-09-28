"""Modelos de metadata y comentarios para objetos de aprendizaje.

Este módulo concentra el registro canónico de metadata de cada OA. Aquí viven
los campos descriptivos heredados del esquema LOM, junto con banderas
operativas como `public`, `slug` y la referencia al usuario que cargo el
recurso.
"""

from datetime import datetime, timedelta

from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from model_utils.models import TimeStampedModel

from applications.education_level.models import EducationLevel
from applications.knowledge_area.models import KnowledgeArea
from applications.learning_object_file.models import LearningObjectFile
from applications.learning_object_metadata.managers import LearningObjectManager
from applications.license.models import License


class LearningObjectMetadata(TimeStampedModel):
    """Metadata principal asociada a un archivo OA cargado en la plataforma.

    El modelo mezcla dos responsabilidades heredadas del proyecto:

    - persistir los metadatos descriptivos del recurso educativo
    - almacenar banderas operativas usadas por publicación y filtrado

    La mayoría de los atributos replica secciones del esquema LOM que el
    backend importa o normaliza a partir del paquete del OA.
    """

    learning_object_file = models.OneToOneField(
        LearningObjectFile,
        on_delete=models.CASCADE,
        related_name="metadata_learning_object",
        help_text="Archivo OA al que pertenece esta metadata. Cada archivo debe tener una sola ficha de metadata.",
    )
    # Sección de adaptabilidad y archivos complementarios.
    adaptation = models.CharField(
        max_length=10,
        help_text="Codigo o marca que indica si el OA fue adaptado dentro del flujo de la plataforma.",
    )
    avatar = models.ImageField(
        null=False,
        blank=False,
        upload_to="avatar",
        help_text="Imagen principal usada como portada del objeto de aprendizaje en listados publicos.",
    )
    source_file = models.FileField(
        null=True,
        blank=True,
        upload_to="sourceFile",
        help_text="Archivo fuente opcional del OA, usado cuando se conserva material editable adicional.",
    )
    is_adapted_oer = models.BooleanField(
        default=False,
        help_text="Indica si el OA corresponde a un recurso educativo abierto adaptado desde otro material.",
    )

    author = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Autor declarado en la metadata del paquete o ingresado durante la carga.",
    )
    package_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Tipo de paquete detectado o declarado para el OA, por ejemplo HTML, SCORM o eXeLearning.",
    )

    # Sección general del OA.
    general_catalog = models.TextField(blank=True, null=True, help_text="Catalogo de identificacion general del OA segun metadata LOM.")
    general_entry = models.TextField(blank=True, null=True, help_text="Entrada o identificador del OA dentro del catalogo general.")
    general_title = models.TextField(blank=True, null=True, help_text="Titulo visible del objeto de aprendizaje.")
    general_language = models.CharField(max_length=40, help_text="Idioma principal del contenido educativo.")
    general_description = models.TextField(blank=True, null=True, help_text="Descripcion general que resume el objetivo y contenido del OA.")
    general_keyword = models.TextField(blank=True, null=True, help_text="Palabras clave usadas para busqueda, filtros y recomendacion.")
    general_coverage = models.TextField(blank=True, null=True, help_text="Alcance geografico, temporal o contextual del OA, si aplica.")
    general_structure = models.TextField(blank=True, null=True, help_text="Estructura pedagogica o tecnica declarada para el recurso.")
    general_aggregation_Level = models.TextField(blank=True, null=True, help_text="Nivel de agregacion LOM que indica granularidad del OA.")

    # Sección ciclo de vida.
    life_cycle_version = models.TextField(blank=True, null=True, help_text="Version del recurso declarada en el ciclo de vida del OA.")
    life_cycle_status = models.TextField(blank=True, null=True, help_text="Estado del OA dentro de su ciclo de vida, por ejemplo borrador o final.")
    life_cycle_role = models.TextField(blank=True, null=True, help_text="Rol de la entidad que intervino en el ciclo de vida del recurso.")
    life_cycle_entity = models.TextField(blank=True, null=True, help_text="Persona u organizacion asociada al ciclo de vida del OA.")
    life_cycle_dateTime = models.TextField(blank=True, null=True, help_text="Fecha declarada para el evento del ciclo de vida.")
    life_cycle_description = models.TextField(blank=True, null=True, help_text="Detalle adicional sobre el evento del ciclo de vida.")

    # Sección meta-metadata.
    meta_metadata_catalog = models.TextField(blank=True, null=True, help_text="Catalogo que identifica la metadata, no el contenido educativo.")
    meta_metadata_entry = models.TextField(blank=True, null=True, help_text="Entrada o identificador de la metadata dentro de su catalogo.")
    meta_metadata_role = models.TextField(blank=True, null=True, help_text="Rol de quien creo, valido o actualizo la metadata.")
    meta_metadata_entity = models.TextField(blank=True, null=True, help_text="Entidad responsable de la metadata del OA.")
    meta_metadata_dateTime = models.TextField(blank=True, null=True, help_text="Fecha asociada a la creacion o actualizacion de la metadata.")
    meta_metadata_description = models.TextField(blank=True, null=True, help_text="Descripcion adicional sobre la metadata registrada.")

    # Sección tecnica.
    technical_format = models.TextField(blank=True, null=True, help_text="Formato tecnico del paquete o contenido, por ejemplo text/html o application/zip.")
    technical_size = models.TextField(blank=True, null=True, help_text="Tamano declarado del recurso o paquete.")
    technical_location = models.TextField(blank=True, null=True, help_text="Ubicacion tecnica del recurso dentro del paquete o repositorio.")
    technical_requirement_type = models.TextField(blank=True, null=True, help_text="Tipo de requisito tecnico necesario para ejecutar el OA.")
    technical_requirement_name = models.TextField(blank=True, null=True, help_text="Nombre del software, navegador o componente requerido.")
    technical_requirement_minimumVersion = models.TextField(blank=True, null=True, help_text="Version minima requerida del componente tecnico.")
    technical_installationRremarks = models.TextField(blank=True, null=True, help_text="Indicaciones de instalacion o preparacion tecnica del OA.")
    technical_otherPlatformRequirements = models.TextField(blank=True, null=True, help_text="Otros requisitos de plataforma no cubiertos por los campos anteriores.")
    technical_dateTime = models.TextField(blank=True, null=True, help_text="Fecha tecnica declarada en la metadata.")
    technical_description = models.TextField(blank=True, null=True, help_text="Descripcion tecnica adicional del recurso.")

    # Sección educativa.
    educational_interactivityType = models.TextField(blank=True, null=True, help_text="Tipo de interactividad educativa del OA.")
    educational_learningResourceType = models.TextField(blank=True, null=True, help_text="Tipo de recurso de aprendizaje declarado.")
    educational_interactivityLevel = models.TextField(blank=True, null=True, help_text="Nivel de interactividad esperado para el estudiante.")
    educational_semanticDensity = models.TextField(blank=True, null=True, help_text="Densidad semantica o complejidad conceptual del contenido.")
    educational_intendedEndUserRole = models.TextField(blank=True, null=True, help_text="Rol del usuario final previsto, por ejemplo estudiante o docente.")
    educational_context = models.TextField(blank=True, null=True, help_text="Contexto educativo recomendado para usar el OA.")
    educational_typicalAgeRange = models.TextField(blank=True, null=True, help_text="Rango de edad recomendado para los usuarios del recurso.")
    educational_difficulty = models.TextField(blank=True, null=True, help_text="Nivel de dificultad pedagogica declarado.")
    educational_typicalLearningTime_dateTime = models.TextField(blank=True, null=True, help_text="Tiempo tipico de aprendizaje en formato de metadata.")
    educational_typicalLearningTime_description = models.TextField(blank=True, null=True, help_text="Descripcion del tiempo esperado de aprendizaje.")
    educational_description = models.TextField(blank=True, null=True, help_text="Descripcion pedagogica adicional del OA.")
    educational_language = models.TextField(blank=True, null=True, help_text="Idioma educativo declarado para el proceso de aprendizaje.")
    educational_procces_cognitve = models.TextField(blank=True, null=True, help_text="Proceso cognitivo asociado al OA, usado por filtros y recomendacion.")

    # Sección derechos.
    rights_cost = models.TextField(blank=True, null=True, help_text="Indica si el uso del OA implica costo segun la metadata de derechos.")
    rights_copyrightAndOtherRestrictions = models.TextField(blank=True, null=True, help_text="Indica si existen restricciones de copyright u otros derechos.")
    rights_description = models.TextField(blank=True, null=True, help_text="Descripcion de condiciones de uso, licencia o restricciones del OA.")

    # Sección relación.
    relation_kind = models.TextField(blank=True, null=True, help_text="Tipo de relacion del OA con otro recurso educativo.")
    relation_catalog = models.TextField(blank=True, null=True, help_text="Catalogo del recurso relacionado.")
    relation_entry = models.TextField(blank=True, null=True, help_text="Identificador del recurso relacionado dentro de su catalogo.")
    relation_description = models.TextField(blank=True, null=True, help_text="Descripcion de la relacion con otro recurso.")

    # Sección anotación.
    annotation_entity = models.TextField(blank=True, null=True, help_text="Entidad que registro una anotacion sobre el OA.")
    annotation_date_dateTime = models.TextField(blank=True, null=True, help_text="Fecha de la anotacion registrada en la metadata.")
    annotation_date_description = models.TextField(blank=True, null=True, help_text="Descripcion textual de la fecha o contexto de la anotacion.")
    annotation_description = models.TextField(blank=True, null=True, help_text="Comentario o anotacion descriptiva sobre el uso del OA.")
    annotation_modeaccess = models.TextField(blank=True, null=True, help_text="Modos de acceso soportados, usados por filtros de accesibilidad.")
    annotation_modeaccesssufficient = models.TextField(blank=True, null=True, help_text="Indica si los modos de acceso declarados son suficientes para el recurso.")
    annotation_rol = models.TextField(blank=True, null=True, help_text="Rol asociado a la anotacion registrada.")

    # Sección clasificación.
    classification_purpose = models.TextField(blank=True, null=True, help_text="Proposito de la clasificacion del OA.")
    classification_taxonPath_source = models.TextField(blank=True, null=True, help_text="Fuente de la taxonomia usada para clasificar el OA.")
    classification_taxonPath_taxon = models.TextField(blank=True, null=True, help_text="Taxon o categoria especifica asignada al OA.")
    classification_description = models.TextField(blank=True, null=True, help_text="Descripcion de la clasificacion aplicada al recurso.")
    classification_keyword = models.TextField(blank=True, null=True, help_text="Palabras clave de clasificacion usadas para busqueda y filtros.")

    # Sección accesibilidad.
    accesibility_summary = models.TextField(blank=True, null=True, help_text="Resumen de accesibilidad del OA.")
    accesibility_features = models.TextField(blank=True, null=True, help_text="Caracteristicas de accesibilidad disponibles en el recurso.")
    accesibility_hazard = models.TextField(blank=True, null=True, help_text="Riesgos de accesibilidad declarados, por ejemplo parpadeos o sonido.")
    accesibility_control = models.TextField(blank=True, null=True, help_text="Controles de accesibilidad o mecanismos de navegacion disponibles.")
    accesibility_api = models.TextField(blank=True, null=True, help_text="Informacion de compatibilidad con APIs o tecnologias de accesibilidad.")

    # Taxonomias operativas usadas por filtros públicos y recomendación.
    education_levels = models.ForeignKey(
        EducationLevel,
        on_delete=models.CASCADE,
        help_text="Nivel educativo al que esta dirigido el OA y por el que se filtra en catalogos.",
    )
    knowledge_area = models.ForeignKey(
        KnowledgeArea,
        on_delete=models.CASCADE,
        related_name="knowledge_learningobject",
        help_text="Area de conocimiento asociada al OA para filtros, busquedas y recomendaciones.",
    )
    license = models.ForeignKey(
        License,
        on_delete=models.CASCADE,
        related_name="license_learningobject",
        help_text="Licencia bajo la que se publica o comparte el objeto de aprendizaje.",
    )

    # `public` gobierna si el OA puede aparecer en listados y búsquedas públicas.
    slug = models.SlugField(
        max_length=200,
        unique=True,
        editable=False,
        help_text="Identificador amigable generado automaticamente desde el titulo y la hora de guardado.",
    )
    public = models.BooleanField(
        default=False,
        help_text="Controla si el OA aparece en catalogos, busquedas y endpoints publicos.",
    )
    user_created = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="metadata_created",
        blank=True,
        null=True,
        help_text="Usuario que cargo o registro el OA en la plataforma.",
    )

    objects = LearningObjectManager()
    REQUIRED_FIELDS = [
        "learning_object",
        "general_title",
        "general_description",
        "adaptation",
        "education_level",
        "knowledge_area",
        "license",
        "user_created",
    ]

    def save(self, *args, **kwargs):
        """Genera el slug usando el título y los segundos transcurridos del día.

        Cada guardado recalcula `slug` a partir de `general_title` y la hora actual.
        Esto intenta reducir colisiones sin usar UUID, pero también implica que el
        slug puede cambiar entre guardados del mismo objeto.
        """

        now = datetime.now()
        total_time = timedelta(
            hours=now.hour,
            minutes=now.minute,
            seconds=now.second,
        )
        seconds = int(total_time.total_seconds())
        slug_unique = "%s%s" % (self.general_title, str(seconds))

        self.slug = slugify(slug_unique)
        super(LearningObjectMetadata, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.id) + " - " + self.general_title


class Commentary(TimeStampedModel):
    """Comentario asociado a un OA por parte de un usuario autenticado."""

    description = models.CharField(
        max_length=1000,
        help_text="Texto del comentario publicado sobre el objeto de aprendizaje.",
    )
    learning_object = models.ForeignKey(
        LearningObjectMetadata,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="oa_comment",
        help_text="Objeto de aprendizaje al que pertenece el comentario.",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_comment",
        blank=True,
        null=True,
        help_text="Usuario autenticado que escribio el comentario.",
    )
