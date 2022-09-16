from applications.profession.models import Profession
from applications.preferences.models import Preferences
from applications.knowledge_area.models import KnowledgeArea
from applications.education_level.models import EducationLevel
from django.db import models

# Create your models here.
from model_utils.models import TimeStampedModel
from django.db import models
from django.contrib.auth.models import (  
    AbstractBaseUser, 
    )
from .managers import UserManager

# Create your models here.
class Student(TimeStampedModel):
    birthday = models.DateField(blank=True, null=True)
    education_levels = models.ManyToManyField(EducationLevel)
    knowledge_areas = models.ManyToManyField(KnowledgeArea)
    preferences = models.ManyToManyField(Preferences, related_name='student_preferences')
    has_disability = models.BooleanField(default=False)
    disability_description = models.TextField(blank=True,null=True)
    is_active = models.BooleanField(default=False)
    is_account_active = models.BooleanField(default=False)
    def __str__(self):
        return str(self.id)

class Teacher(TimeStampedModel):
    professions = models.ManyToManyField(Profession)
    is_active = models.BooleanField(default=False)
    is_account_active = models.BooleanField(default=False)
    def __str__(self):
        return str(self.id)

class CollaboratingExpert(TimeStampedModel):
    EXPERT_LEVEL_CHOICES = (
        ('Alto', 'Alto'),
        ('Medio', 'Medio'),
        ('Bajo', 'Bajo'),
    )
    expert_level = models.CharField(max_length=40, choices=EXPERT_LEVEL_CHOICES, blank=True, null=True)
    web = models.URLField(max_length=300, blank=True, null=True)
    academic_profile = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_account_active = models.BooleanField(default=False)
    def __str__(self):
        return str(self.id)+' '+self.expert_level

class Administrator(TimeStampedModel):
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=150)
    phone = models.IntegerField(blank=True, null=True)
    observation = models.CharField(blank=True, null=True,max_length=600)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

class User(AbstractBaseUser, TimeStampedModel):
    first_name = models.CharField('Nombres',max_length=100)
    last_name = models.CharField('Apellidos',max_length=100)
    email = models.EmailField('Correo',max_length=50, unique=True, error_messages={'unique':"Este correo ya esta registrado."})
    image = models.ImageField(upload_to='profile', max_length=250, blank=True, null=True, default='img/user.png')
    student = models.OneToOneField(Student,on_delete=models.CASCADE, related_name='user_student',blank=True, null=True)
    teacher = models.OneToOneField(Teacher,on_delete=models.CASCADE, related_name='user_teacher',blank=True, null=True)
    collaboratingExpert = models.OneToOneField(CollaboratingExpert,on_delete=models.CASCADE, related_name='user_collaborating',blank=True, null=True)
    administrator = models.OneToOneField(Administrator,on_delete=models.CASCADE, related_name='user_administrator',blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name','last_name']

    def __str__(self):
        return f'{self.first_name}, {self.last_name}, {self.student}'

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True
    @property
    def is_staff(self):
        return self.is_superuser


