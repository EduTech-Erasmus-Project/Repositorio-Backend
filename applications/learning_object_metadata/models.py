from applications.license.models import License
from applications.preferences.models import Preferences
from applications.learning_object_metadata.managers import LearningObjectManager
from django.db import models
from django.conf import settings
from django.template.defaultfilters import default, slugify
from applications.learning_object_file.models import LearningObjectFile
from applications.education_level.models import EducationLevel
from applications.knowledge_area.models import KnowledgeArea
from datetime import datetime, timedelta
from model_utils.models import TimeStampedModel
from django.contrib.postgres.fields import ArrayField
# Create your models here.

class LearningObjectMetadata(TimeStampedModel):
    learning_object_file = models.OneToOneField(LearningObjectFile,on_delete=models.CASCADE, related_name='metadata_learning_object')
    # Metadatos de adaptabilidad
    adaptation = models.CharField(max_length=10)
    # Metadatos complementarios
    avatar = models.ImageField(null=False, blank=False, upload_to = "avatar")

    source_file = models.FileField(null=True, blank=True, upload_to="sourceFile")

    #Items para guardar las respuestas de cada una de las preguntas
    """item_v1 = models.CharField(null=True, blank=True, max_length=40)
    item_v2 = models.CharField(null=True, blank=True, max_length=40)
    item_t3 = models.CharField(null=True, blank=True, max_length=40)
    item_t4 = models.CharField(null=True, blank=True, max_length=40)
    item_a5 = models.CharField(null=True, blank=True, max_length=40)
    item_i6 = models.CharField(null=True, blank=True, max_length=40)"""

    #Guarda una variable si el obejto de aprendizaje ya fue adaptado
    is_adapted_oer = models.BooleanField(default=False)

    author = models.CharField(max_length=100, blank=True, null=True)
    package_type = models.CharField(max_length=50,blank=True, null=True)

    # Preferencias de usuario
    # preferences = models.ManyToManyField(Preferences,related_name="preferences_learning_object")
    # Metadatos Generales del Objeto de aprendizaje
    general_catalog = models.TextField(blank=True, null=True)
    general_entry = models.TextField(blank=True, null=True)
    general_title = models.TextField(blank=True, null=True)
    general_language = models.CharField(max_length=40) 
    general_description = models.TextField(blank=True, null=True)
    general_keyword = models.TextField(blank=True, null=True)
    general_coverage = models.TextField(blank=True, null=True)
    general_structure = models.TextField(blank=True, null=True)
    general_aggregation_Level = models.TextField(blank=True, null=True)
    # Metadatos de ciclo de vida
    life_cycle_version = models.TextField(blank=True, null=True)
    life_cycle_status = models.TextField(blank=True, null=True)
    life_cycle_role = models.TextField(blank=True, null=True)
    life_cycle_entity = models.TextField(blank=True, null=True)
    life_cycle_dateTime = models.TextField(blank=True, null=True)
    life_cycle_description = models.TextField(blank=True, null=True)
    # Metadatos Meta-Metadata
    meta_metadata_catalog = models.TextField(blank=True, null=True)
    meta_metadata_entry = models.TextField(blank=True, null=True)
    meta_metadata_role = models.TextField(blank=True, null=True)
    meta_metadata_entity= models.TextField(blank=True, null=True)
    meta_metadata_dateTime = models.TextField(blank=True, null=True)
    meta_metadata_description = models.TextField(blank=True, null=True)
    # Metadatos técnico
    technical_format = models.TextField(blank=True, null=True)
    technical_size = models.TextField(blank=True, null=True)
    technical_location = models.TextField(blank=True, null=True)
    technical_requirement_type = models.TextField(blank=True, null=True)
    technical_requirement_name = models.TextField(blank=True, null=True)
    technical_requirement_minimumVersion = models.TextField(blank=True, null=True)
    technical_installationRremarks = models.TextField(blank=True, null=True)
    technical_otherPlatformRequirements = models.TextField(blank=True, null=True)
    technical_dateTime = models.TextField(blank=True, null=True)
    technical_description = models.TextField(blank=True, null=True)
    # Metadatos educativa
    educational_interactivityType = models.TextField(blank=True, null=True)
    educational_learningResourceType = models.TextField(blank=True, null=True)
    educational_interactivityLevel = models.TextField(blank=True, null=True)
    educational_semanticDensity = models.TextField(blank=True, null=True)
    educational_intendedEndUserRole = models.TextField(blank=True, null=True)
    educational_context = models.TextField(blank=True, null=True)
    educational_typicalAgeRange= models.TextField(blank=True, null=True)
    educational_difficulty= models.TextField(blank=True, null=True)
    educational_typicalLearningTime_dateTime = models.TextField(blank=True, null=True)
    educational_typicalLearningTime_description= models.TextField(blank=True, null=True)
    educational_description= models.TextField(blank=True, null=True)
    educational_language= models.TextField(blank=True, null=True)
    educational_procces_cognitve= models.TextField(blank=True, null=True)#Revisar
    # Metadatos derechos
    rights_cost = models.TextField(blank=True, null=True)
    rights_copyrightAndOtherRestrictions = models.TextField(blank=True, null=True)
    rights_description = models.TextField(blank=True, null=True)
    # Matadatos relación
    relation_kind = models.TextField(blank=True, null=True)
    relation_catalog = models.TextField(blank=True, null=True)
    relation_entry = models.TextField(blank=True, null=True)
    relation_description = models.TextField(blank=True, null=True)
    # Matadatos anotación
    annotation_entity = models.TextField(blank=True, null=True)
    annotation_date_dateTime = models.TextField(blank=True, null=True)
    annotation_date_description = models.TextField(blank=True, null=True)
    annotation_description = models.TextField(blank=True, null=True)
    annotation_modeaccess = models.TextField(blank=True, null=True)
    annotation_modeaccesssufficient = models.TextField(blank=True, null=True)
    annotation_rol = models.TextField(blank=True, null=True)
    # Matadatos Clasificación
    classification_purpose = models.TextField(blank=True, null=True)
    classification_taxonPath_source = models.TextField(blank=True, null=True)
    classification_taxonPath_taxon = models.TextField(blank=True, null=True)
    classification_description = models.TextField(blank=True, null=True)
    classification_keyword = models.TextField(blank=True, null=True)
    # Metadatos de accesibilidad
    accesibility_summary = models.TextField(blank=True, null=True)
    accesibility_features = models.TextField(blank=True, null=True)
    accesibility_hazard = models.TextField(blank=True, null=True)
    accesibility_control = models.TextField(blank=True, null=True)
    accesibility_api = models.TextField(blank=True, null=True)

    # tags = models.TextField()
    education_levels = models.ForeignKey(EducationLevel,on_delete=models.CASCADE)
    knowledge_area = models.ForeignKey(
        KnowledgeArea,
        on_delete=models.CASCADE,
        related_name='knowledge_learningobject'
        )
    # age = models.PositiveIntegerField(default=0)
    license = models.ForeignKey(
        License,
        on_delete=models.CASCADE,
        related_name='license_learningobject'
        ) 

    slug = models.SlugField(max_length=100, unique=True, editable=False)
    public = models.BooleanField(default=False)
    user_created = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="metadata_created",
        blank=True, null=True
    )
    objects = LearningObjectManager()
    # created = models.DateTimeField(auto_now_add=True)
    REQUIRED_FIELDS = ['learning_object','general_title','general_description','adaptation','education_level',
    'knowledge_area','license','user_created']
    def save(self, *args, **kwargs):
        now = datetime.now()
        total_time =timedelta(
            hours=now.hour, 
            minutes=now.minute, 
            seconds=now.second
        )
        seconds = int(total_time.total_seconds())
        slug_unique = "%s%s" % (self.general_title, str(seconds))

        self.slug = slugify(slug_unique)
        super(LearningObjectMetadata, self).save(*args, **kwargs)
    def __str__(self):
        return str(self.id) +' - '+ self.general_title

class Commentary(TimeStampedModel):
    description= models.CharField(max_length=1000)
    learning_object = models.ForeignKey(LearningObjectMetadata,on_delete=models.CASCADE, blank=True, null=True, related_name="oa_comment")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_comment",
        blank=True, null=True
    )