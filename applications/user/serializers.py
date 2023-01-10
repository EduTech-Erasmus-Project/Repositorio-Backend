from applications.user.utils import Util
from rest_framework.response import Response
from roabackend.settings import DOMAIN
from rest_framework import serializers, pagination
from rest_framework.validators import UniqueValidator
from applications.education_level.serializers import EducationLevelListSerializer
from applications.knowledge_area.serializers import KnowledgeAreaListSerializer
from applications.preferences.serializers import PreferencesListSerializer, PreferencesListSerializersTest
from applications.profession.serializers import ProfessionListSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import APIException, AuthenticationFailed
from applications.education_level.models import EducationLevel
from applications.knowledge_area.models import KnowledgeArea
from applications.preferences.models import Preferences
from applications.profession.models import Profession

from .models import (
    User, 
    Administrator,
    Student,
    Teacher,
    CollaboratingExpert
    )

class ArrayIntegerSerializer(serializers.ListField):
    children = serializers.IntegerField(required=True)

class ArrayStringSerializer(serializers.ListField):
    child = serializers.CharField(required=True)

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Administrator
        fields = ('__all__')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('__all__')

class UserFullName(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name','last_name')

class UserAdminSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True, validators=[
        UniqueValidator(queryset=User.objects.all(), 
        message="Este correo ya esta registrado.",
        )])
    password = serializers.CharField(required=True,min_length= 8)
    country = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    # image = serializers.ImageField(required=False)
    observation = serializers.CharField(default="")

class UserAdmiUpdatenSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    country = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    # image = serializers.ImageField(required=False)
    is_active = serializers.BooleanField(default=True)
    observation = serializers.CharField(default="")

class UserUpdateSerializer(serializers.Serializer):
    roles = ArrayStringSerializer()
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    # image = serializers.ImageField(required=True)

class UserUpdatePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('image',)

class StudentUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    birthday = serializers.DateField(required=True)
    has_disability = serializers.BooleanField(default=False)
    disability_description = serializers.CharField(default=None)
    education_levels = ArrayIntegerSerializer()
    knowledge_areas = ArrayIntegerSerializer()
    preferences = ArrayIntegerSerializer()
    def validate_education_levels(self,value):
        for i in value:
            if len(EducationLevel.objects.filter(pk=i))==0:
                 raise serializers.ValidationError(f"No existe el nivel de educación con id {i}")
        return value
    def validate_knowledge_areas(self,value):
        for i in value:
            if len(KnowledgeArea.objects.filter(pk=i))==0:
                 raise serializers.ValidationError(f"No existe el area de conocimiento con id {i}")
        return value
    def validate_preferences(self,value):
        for i in value:
            if len(Preferences.objects.filter(pk=i))==0:
                 raise serializers.ValidationError(f"No existe las preferencias con id {i}")
        return value


class TeacherUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    professions = ArrayIntegerSerializer()
    def validate_professions(self,value):
        for i in value:
            if len(Profession.objects.filter(pk=i))==0:
                 raise serializers.ValidationError(f"No existe la profesión con id {i}")
        return value

class CollaboratingExpertUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    expert_level = serializers.CharField(required=True)
    web = serializers.URLField(default=None)
    academic_profile = serializers.CharField(default=None)

class UserListSerializer(serializers.ModelSerializer):
    administrator = AdminSerializer()
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name', 
            'email',
            'image', 
            'image_url',
            'administrator'
        )
    def get_image_url(self, obj):
        if obj.image is not None:
            return DOMAIN+obj.image.url

class UserCommentSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name', 
            'image_url',
        )
    def get_image_url(self, obj):
        if obj.image is not None:
            return DOMAIN+obj.image.url

class RoleSerializer(serializers.Serializer):
    roles = ArrayStringSerializer()
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    image = serializers.ImageField(default='img/user.png')
    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=User.objects.all())])
    password = serializers.CharField(required=True,min_length= 8)

    role_list = []
    def validate_roles(self,value):
        self.role_list.clear()
        for role in value:
            self.role_list.append(role)
        return self.role_list
    def validate_email(self,value):
        if  len(self.role_list)==1 and "student" in self.role_list:
            pass
        # else:
        #     if ".edu" not in value:
        #         raise serializers.ValidationError("El correo debe ser institucionals")
        return value

class StudentCreateSerializer(serializers.Serializer):
    birthday = serializers.DateField(required=True)
    has_disability = serializers.BooleanField(default=False)
    disability_description = serializers.CharField(default=None)
    education_levels = ArrayIntegerSerializer()
    knowledge_areas = ArrayIntegerSerializer()
    preferences = ArrayIntegerSerializer()

    def validate_education_levels(self,value):
        for i in value:
            if len(EducationLevel.objects.filter(pk=i))==0:
                 raise serializers.ValidationError(f"No existe el nivel de educación con id {i}")
        return value
    def validate_knowledge_areas(self,value):
        for i in value:
            if len(KnowledgeArea.objects.filter(pk=i))==0:
                 raise serializers.ValidationError(f"No existe el area de conocimiento con id {i}")
        return value
    def validate_preferences(self,value):
        for i in value:
            if len(Preferences.objects.filter(pk=i))==0:
                 raise serializers.ValidationError(f"No existe las preferencias con id {i}")
        return value

class TeacherCreateSerializer(serializers.Serializer):
    professions = ArrayIntegerSerializer()
    def validate_professions(self,value):
        for i in value:
            if len(Profession.objects.filter(pk=i))==0:
                 raise serializers.ValidationError(f"No existe la profesión con id {i}")
        return value

class CollaboratingExpertCreateSerializer(serializers.Serializer):
    expert_level = serializers.CharField(required=True)
    web = serializers.CharField(default=None)
    academic_profile = serializers.CharField(default=None)

class StudentListSerializer(serializers.ModelSerializer):
    education_levels=EducationLevelListSerializer(many=True)
    knowledge_areas=KnowledgeAreaListSerializer(many=True)
    preferences=PreferencesListSerializer(many=True)
    class Meta:
        model = Student
        fields = (
            'id',
            'birthday',
            'has_disability',
            'disability_description',
            'is_active',
            'education_levels',
            'knowledge_areas',
            'preferences'
        )

# AQUI
class UserListSerializersPreferences(serializers.ModelSerializer):
    preferences=PreferencesListSerializersTest(many=True)
    class Meta:
        model = Student
        fields = (
            'preferences',
        )


class TeacherListSerializer(serializers.ModelSerializer):
    professions=ProfessionListSerializer(many=True)
    class Meta:
        model = Teacher
        fields = (
            'id',
            'professions',
            'is_active'
        )

class ExpertListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollaboratingExpert
        fields = (
            'id',
            'expert_level',
            'web',
            'academic_profile',
            'is_active'
        )

class AdministratorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Administrator
        fields = (
            '__all__'
        )

class GeneralUserListSerializer(serializers.ModelSerializer):
    student=StudentListSerializer()
    teacher=TeacherListSerializer()
    collaboratingExpert=ExpertListSerializer()
    roles = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = (
            'id',
            'roles',
            'first_name', 
            'last_name', 
            'email', 
            'image',
            'student',
            'teacher',
            'collaboratingExpert',
            'created',
            'modified',
            'user_key'
        )
    def get_image(self, obj):
        if obj.image is not None:
            return DOMAIN+obj.image.url
    def get_roles(self,obj):
        role_lis=[]
        if obj.student is not None:
            role_lis.append('student')
        if obj.teacher is not None and obj.teacher.is_active:
            role_lis.append('teacher')
        if obj.collaboratingExpert is not None and obj.collaboratingExpert.is_active:
            role_lis.append('expert')
        return role_lis

class GeneralUserStudent_View_ListSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = (
            'id',
            'roles',
            'first_name',
            'last_name',
            'email',
            'image',

            'created',
            'modified',
        )
    def get_image(self, obj):
        if obj.image is not None:
            return DOMAIN+obj.image.url
    def get_roles(self,obj):
        role_lis=[]
        if obj.student is not None:
            role_lis.append('student')
        if obj.teacher is not None and obj.teacher.is_active:
            role_lis.append('teacher')
        if obj.collaboratingExpert is not None and obj.collaboratingExpert.is_active:
            role_lis.append('expert')
        return role_lis

class UserLoginDataSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = (
            'id',
            'roles',
            'first_name', 
            'last_name', 
            'email', 
            'image',
            'student',
            'teacher',
            'collaboratingExpert',
            'administrator',
        )
    def get_roles(self,obj):
        role_lis=[]
        if obj.student is not None:
            role_lis.append('student')
        if obj.teacher is not None and obj.teacher.is_active:
            role_lis.append('teacher')
        if obj.collaboratingExpert is not None and obj.collaboratingExpert.is_active:
            role_lis.append('expert')
        if obj.administrator is not None and obj.administrator.is_active:
            role_lis.append('administrator')
        if obj.is_superuser:
            role_lis.append('superuser')
        return role_lis


class AdminDisaprovedTeacherCollaboratingExpertSerializer(serializers.ModelSerializer):
    teacher=TeacherListSerializer()
    collaboratingExpert=ExpertListSerializer()
    rol_solicitados = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = (
            'id',
            'rol_solicitados',
            'first_name', 
            'last_name', 
            'email', 
            'image',
            'image_url',
            'teacher',
            'collaboratingExpert',
            'created',
            'modified',
        )
    def get_image_url(self, obj):
        if obj.image is not None:
            return DOMAIN+obj.image.url
    def get_rol_solicitados(self,obj):
        role_lis=[]
        if obj.teacher is not None and obj.teacher.is_active is False:
            role_lis.append('teacher')
        if obj.collaboratingExpert is not None and obj.collaboratingExpert.is_active is False:
            role_lis.append('expert')
        return role_lis

class AdminAprovedTeacherCollaboratingExpertSerializer(serializers.ModelSerializer):
    teacher=TeacherListSerializer()
    collaboratingExpert=ExpertListSerializer()
    rol_aprovados = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = (
            'id',
            'rol_aprovados',
            'first_name', 
            'last_name', 
            'email', 
            'image_url',
            'image',
            'teacher',
            'collaboratingExpert',
            'created',
            'modified',
        )
    def get_image_url(self, obj):
        if obj.image is not None:
            return DOMAIN+obj.image.url
    def get_rol_aprovados(self,obj):
        role_lis=[]
        if obj.teacher is not None and obj.teacher.is_active is True:
            role_lis.append('teacher')
        if obj.collaboratingExpert is not None and obj.collaboratingExpert.is_active is True:
            role_lis.append('expert')
        return role_lis

class AdminStudentListSerializer(serializers.ModelSerializer):
    student = StudentListSerializer()
    # collaboratingExpert=ExpertListSerializer()
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = (
            'id',
            'first_name', 
            'last_name', 
            'email', 
            'image',
            'image_url',
            'student',
            'created',
            'modified',
        )
    def get_image_url(self, obj):
        if obj.image is not None:
            return DOMAIN+obj.image.url

class AdminTeacherListSerializer(serializers.ModelSerializer):
    teacher = TeacherListSerializer()
    class Meta:
        model = User
        fields = (
            'id',
            'first_name', 
            'last_name', 
            'email', 
            'image',
            'teacher',
            'created',
            'modified',
        )
class AdminCollaboratingExpertListSerializer(serializers.ModelSerializer):
    collaboratingExpert=ExpertListSerializer()
    class Meta:
        model = User
        fields = (
            'id',
            'first_name', 
            'last_name', 
            'email', 
            'image',
            'collaboratingExpert',
            'created',
            'modified',
        )
class AdminAdministratorListSerializer(serializers.ModelSerializer):
    administrator=AdministratorListSerializer()
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = (
            'id',
            'first_name', 
            'last_name', 
            'email', 
            'image',
            'image_url',
            'administrator',
            'created',
            'modified',
        )
    def get_image_url(self, obj):
        if obj.image is not None:
            return DOMAIN+obj.image.url

class UpdateTecherCollaboratingExpertDisapprovedSerializer(serializers.Serializer):
    teacher_is_active = serializers.BooleanField(default=False)
    expert_is_active = serializers.BooleanField(default=False)

class UpdateTecherCollaboratingExpertApproveedSerializer(serializers.Serializer):
    teacher_is_active = serializers.BooleanField(default=True)
    expert_is_active = serializers.BooleanField(default=True)

class AdminUpdateStudentSerializer(serializers.Serializer):
    student_is_active = serializers.BooleanField(default=False)

class AdminUpdateCollaboratingExpertSerializer(serializers.Serializer):
    expert_is_active = serializers.BooleanField(default=False)

class AdminUpdateAdministratorSerializer(serializers.Serializer):
    administrator_is_active = serializers.BooleanField(default=False)

class OrcidValidationSerializer(serializers.Serializer):
    orcid = serializers.CharField(max_length=200)
    
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        # token = super(MyTokenObtainPairSerializer, cls).get_token(user)
        # token['email'] = user.email
        if ((user.student is not None and user.student.is_active and user.student.is_account_active) or (user.teacher is not None and user.teacher.is_active and user.teacher.is_account_active) or (user.collaboratingExpert is not None and user.collaboratingExpert.is_active and user.collaboratingExpert.is_account_active)) or user.is_superuser or (user.administrator is not None and user.administrator.is_active):
            token = super().get_token(user)
            return token
        else:
            raise APIException("Inactive user")


class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    old_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('old_password', 'password', 'password2')
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        if attrs['password'] == attrs['old_password']:
            raise serializers.ValidationError({"password": "New password cannot be the same as above."})
        return attrs
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError({"old_password": "Old password is not correct"})
        return value

    # def update(self, instance, validated_data):
    #     print(instance)
    #     print('********')
    #     pk = self.kwargs['pk']
    #     print(pk)

    #     instance.set_password(validated_data['password'])
    #     instance.save()

    #     return Response({"message": "User updated successfully"})

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str,smart_bytes,DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
# from django.contrib.sites.shortcuts import get_current_site
# from django.urls import reverse

class RequestPasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)
    class Meta:
        fields = ['email']

class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=4,max_length=68,write_only=True)
    token = serializers.CharField(min_length=1,write_only=True)
    uidb64 = serializers.CharField(min_length=1,write_only=True)
    class Meta:
        fields = ['password', 'token','uidb64']

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')

            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user,token):
                raise AuthenticationFailed('The reset link is invalid',401) 
            user.set_password(password)
            user.save()
            return user
        except Exception as e:
            raise AuthenticationFailed('The reset link is invalid',401) 

class UserListSerializers(serializers.ModelSerializer):
    student = UserListSerializersPreferences()
    class Meta:
        model = User
        fields = (
            'student',
        )




