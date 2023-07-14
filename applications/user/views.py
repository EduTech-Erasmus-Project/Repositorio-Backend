import json
import math
from webbrowser import get

from django_filters.rest_framework import DjangoFilterBackend

from applications.user.emailManager import SendMail, SendEmailCreateUser, SendEmailCreateUserCheck, SendEmailConfirm, \
    SendEmailCreateUserCheck_Expert, SendEmail_activation_email, SendEmailCreateUserCheck_Admin_to_Expert, \
    SendEmailAdminCreateUser
from applications.user.utils import Util
from rest_framework.generics import ListAPIView, CreateAPIView, DestroyAPIView
from rest_framework import viewsets
from rest_framework.generics import GenericAPIView, RetrieveAPIView, RetrieveUpdateAPIView, UpdateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from .serializers import ChangePasswordSerializer, MyTokenObtainPairSerializer, RequestPasswordResetEmailSerializer, \
    SetNewPasswordSerializer, StudentListSerializer, UpdateTecherCollaboratingExpertApproveedSerializer, \
    UpdateTecherCollaboratingExpertDisapprovedSerializer, UserListSerializers, UserUpdatePictureSerializer, \
    UserReportSerializer, AdminAprovedTeacherCollaboratingExpertWithOaSerializer
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from django.shortcuts import get_object_or_404
from applications.education_level.models import EducationLevel
from applications.knowledge_area.models import KnowledgeArea
from applications.preferences.models import Preferences
from applications.profession.models import Profession
from applications.settings.models import Email, EmailExtensionsTeacher, UserTypeWithOption, OptionRegisterEmailExtension
import urllib3
import re
from .models import (
    User,
    Student,
    Teacher,
    CollaboratingExpert,
    Administrator
)
from .serializers import (
    UserAdminSerializer,
    UserListSerializer,
    UserAdmiUpdatenSerializer,
    StudentCreateSerializer,
    TeacherCreateSerializer,
    RoleSerializer,
    GeneralUserListSerializer,
    UserLoginDataSerializer,
    UserUpdateSerializer,
    StudentUpdateSerializer,
    TeacherUpdateSerializer,
    CollaboratingExpertCreateSerializer,
    CollaboratingExpertUpdateSerializer,
    AdminDisaprovedTeacherCollaboratingExpertSerializer,
    AdminAprovedTeacherCollaboratingExpertSerializer,
    AdminStudentListSerializer,
    AdminUpdateStudentSerializer,
    AdminTeacherListSerializer,
    AdminUpdateStudentSerializer,
    AdminCollaboratingExpertListSerializer,
    AdminUpdateCollaboratingExpertSerializer,
    AdminAdministratorListSerializer,
    AdminUpdateAdministratorSerializer,
    OrcidValidationSerializer,
    EmailContacSerializer,
)
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED
)
from applications.user.mixins import IsAdministratorUser, IsCollaboratingExpertUser, IsGeneralUser, IsStudentUser, \
    IsTeacherUser
from roabackend.settings import DOMAIN
import jwt
from rest_framework import generics
from datetime import datetime, timezone, timedelta
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls.base import reverse
# Create your views here.
import os
from unipath import Path
# Coneccion con los entornos virtuales
import environ
import threading

from ..address.models import Country, Province, City, University, Campus

"""
Definicion de las clases para envio de correos 
"""

mail_create = SendEmailCreateUser()
mail_create_check = SendEmailCreateUserCheck()
mail_create_expert = SendEmailCreateUserCheck_Expert()
mail_create_check_expert = SendEmailCreateUserCheck_Admin_to_Expert()
mail_confirm_email = SendEmail_activation_email()
mail_account_not_active = SendEmailAdminCreateUser()

env = environ.Env()
BASE_DIR = Path(__file__).ancestor(3)
# Set the project base directory
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


class UserAdminView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdministratorUser, ]

    def create(self, request, *args, **kwargs):
        """
            Servicio para crear un usuario administrador. Se necesita un token de autenticación como administrador para hacer uso de este servicio
        """
        serializer = UserAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_admin = Administrator.objects.create(
            country=serializer.validated_data['country'],
            city=serializer.validated_data['city'],
            phone=serializer.validated_data['phone'],
            observation=serializer.validated_data['observation'],
        )
        new_admin.is_active = True
        new_admin.save()
        new_user = User.objects.create_admin_user(
            first_name=serializer.validated_data['first_name'],
            last_name=serializer.validated_data['last_name'],
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )
        new_user.administrator = new_admin
        new_user.save()
        serializer = UserListSerializer(new_user)
        return Response(serializer.data, status=HTTP_200_OK)

    def list(self, request):
        """
            Servicio para listar los usuarios administradores. Se necesita un token de autenticación como super usuario para hacer uso de este servicio
        """
        queryset = User.objects.filter(email=self.request.user.email)
        serializer = UserListSerializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para actualizar un usuario administrador. Se necesita un token de autenticación como administrador para hacer uso de este servicio
        """
        if int(request.user.id) == int(pk):
            queryset = User.objects.filter().order_by('-pk')
            user = get_object_or_404(queryset, pk=pk)
            serializer = UserListSerializer(user)
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response({"message": "User not found"}, status=HTTP_404_NOT_FOUND)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actuaizar un usuario administrador. Se necesita un token de autenticación como administrador para hacer uso de este servicio
        """
        if int(request.user.id) == int(pk):
            queryset = User.objects.filter(administrator__is_active=True).order_by('-pk')
            instance = get_object_or_404(queryset, pk=pk)
            instance_admin = Administrator.objects.get(pk=instance.administrator.id)
            serializer = UserAdmiUpdatenSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance.first_name = serializer.validated_data['first_name']
            instance.last_name = serializer.validated_data['last_name']
            instance_admin.country = serializer.validated_data['country']
            instance_admin.city = serializer.validated_data['city']
            instance_admin.phone = serializer.validated_data['phone']
            # instance.image = serializer.validated_data['image']
            instance_admin.is_active = serializer.validated_data['is_active']
            instance_admin.observation = serializer.validated_data['observation']
            instance.save()
            instance_admin.save()
            return Response({"message": "success"}, status=HTTP_200_OK)
        else:
            return Response({"message": "User not found"}, status=HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        return Response({"message": "Api not found"}, status=HTTP_404_NOT_FOUND)




class ManagementUserView(viewsets.ViewSet):
    """
        Clase para crear listar usuario
    """
    def get_permissions(self):
        if (self.action == 'create'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsGeneralUser, ]
        return [permission() for permission in permission_classes]

    def asing_array_filter_only_all(self, emails_extension,email_string, option_value):
        """
            Funcion que filtra los correos electronicos dependiendo
             la opcion de registro
        """
        emails_domain = []
        for email in emails_extension:
            emails_domain = email.domain
        email_split = email_string.split('@')
        if option_value == 'ONLY':
            if email_split[-1] in emails_domain:
                return True
            else:
                return False
        elif option_value == 'EXCEPT':
            if email_split[-1] in emails_domain:
                return False
            else:
                return True
        elif option_value == "ALL":
            return True

    def checkEmail(self, email_string):
        """
            Función para validar el dominio de los correos registrados por el
            administrador
        """

        typeRolExtension = UserTypeWithOption.objects.get(description='TEACHER')
        option_register = OptionRegisterEmailExtension.objects.get(id=typeRolExtension.option_register.id)

        emails_extension = None
        if option_register.type_option == 'EXCEPT':
            emails_extension = EmailExtensionsTeacher.objects.filter(option_register_id=typeRolExtension.option_register.id,is_active=True)
            self.asing_array_filter_only_all(emails_extension, email_string, 'EXCEPT')
        elif option_register.type_option == 'ONLY':
            emails_extension = EmailExtensionsTeacher.objects.filter(option_register_id=typeRolExtension.option_register.id, is_active=True)
            self.asing_array_filter_only_all(emails_extension,email_string, 'ONLY')

        else:
            emails_extension = EmailExtensionsTeacher.objects.filter(is_active=True)
            self.asing_array_filter_only_all(emails_extension, email_string, 'ALL')

    def create(self, request, *args, **kwargs):
        """
            Servicio para crear un nuevo usuario (Estudiante, Dcente, Experto Colaborador).
        """
        """ Validamos el correo del usuario """
        # print(request.data)
        dataRes = request.data

        role_serializer = RoleSerializer(data=request.data)
        role_serializer.is_valid(raise_exception=True)
        # print(role_serializer['email'].value)
        new_student = Student()
        new_teacher = Teacher()
        new_expert = CollaboratingExpert()

        for role in role_serializer.validated_data['roles']:

            if role == 'student' and role != 'teacher' and role != 'expert':
                serializer = StudentCreateSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                new_student = Student.objects.create(
                    birthday=serializer.validated_data['birthday'],
                    has_disability=serializer.validated_data['has_disability'],
                    disability_description=serializer.validated_data['disability_description'],
                )
                education_levels = EducationLevel.objects.filter(
                    id__in=serializer.validated_data['education_levels']
                )
                knowledge_areas = KnowledgeArea.objects.filter(
                    id__in=serializer.validated_data['knowledge_areas']
                )
                preferences = Preferences.objects.filter(
                    id__in=serializer.validated_data['preferences']
                )
                for education_level in education_levels:
                    new_student.education_levels.add(education_level)
                for knowledge_area in knowledge_areas:
                    new_student.knowledge_areas.add(knowledge_area)
                for preference in preferences:
                    new_student.preferences.add(preference)

                # if not ManagementUserView.checkEmail(request.data['email']):
                #   value_active = False
                #  mail_create_check.sendMailCreateCheckAdmin(request.data['email'], request.data['first_name'])
                # else:
                value_active = True
                new_student.is_active = value_active

                if serializer.validated_data['has_disability'] is False:
                    self.set_email_conform(new_student.id, request, "student")

                    # new_student.is_account_active = True

                else:
                    new_student.is_account_active = True
                    mail_create.sendMailCreate(request.data['email'], request.data['first_name'])

                new_student.save()

            if role == 'teacher' and role != 'student' and role != 'expert':
                teacher_serializer = TeacherCreateSerializer(data=request.data)
                teacher_serializer.is_valid(raise_exception=True)
                if not self.checkEmail(request.data['email']):
                    value_active = False
                    # Buscar datos del administrador para enviar los correos de revision
                    users_admin = User.objects.filter(is_superuser=True)
                    for user_admin in users_admin:
                        user_email = user_admin.email
                        user_name = user_admin.first_name + " " + user_admin.last_name
                        name_user_account = role_serializer.validated_data['first_name'] + " " + \
                                            role_serializer.validated_data['last_name']
                        mail_account_not_active.sendMail_validate_account_teacher_Admin(user_email, user_name,
                                                                                        name_user_account)
                    # mail_create_check.sendMailCreateCheckAdmin(request.data['email'], request.data['first_name'])
                else:
                    value_active = True
                    # mail_create.sendMailCreate(request.data['email'], request.data['first_name'])

                new_teacher = Teacher.objects.create(
                    is_active=value_active,
                )

                professions = Profession.objects.filter(
                    id__in=teacher_serializer.validated_data['professions']
                )
                for profession in professions:
                    new_teacher.professions.add(profession)

                self.set_email_conform(new_teacher.id, request, "teacher")
                new_teacher.save()
                # post_save.connect(send_email1, sender=User)
                # request_finished.connect(send_email1(role_serializer.validated_data['first_name'],role_serializer.validated_data['last_name'],role,role_serializer.validated_data['email']))

            if role == 'expert' and role != 'teacher' and role != 'student':
                serializer = CollaboratingExpertCreateSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)

                if not self.checkEmail(request.data['email']):
                    value_active = False
                    users_admin = User.objects.filter(is_superuser=True)
                    for user_admin in users_admin:
                        user_email = user_admin.email
                        user_name = user_admin.first_name + " " + user_admin.last_name
                        name_user_account = role_serializer.validated_data['first_name'] + " " + \
                                            role_serializer.validated_data['last_name']
                        mail_account_not_active.sendMail_validate_account_expert_Admin(user_email, user_name,
                                                                                       name_user_account)
                    # mail_create_check_expert.sendMailCreate_Admin_to_Expert(request.data['email'], request.data['first_name'])
                else:
                    value_active = True
                    # mail_create_expert.sendMailCreate_Expert(request.data['email'], request.data['first_name'])

                new_expert = CollaboratingExpert.objects.create(
                    expert_level=serializer.validated_data['expert_level'],
                    web=serializer.validated_data['web'],
                    academic_profile=serializer.validated_data['academic_profile'],
                    is_active=value_active,
                    # is_account_active = True
                )
                self.set_email_conform(new_expert.id, request, "expert")
                new_expert.save()

        # Se agrega el campo del pais en base a la ciudad

        new_user = User.objects.create_general_user(
            first_name=role_serializer.validated_data['first_name'],
            last_name=role_serializer.validated_data['last_name'],
            email=role_serializer.validated_data['email'],
            password=role_serializer.validated_data['password'],
        )

        # print("country id", country.id)

        new_user.image = role_serializer.validated_data['image']
        if new_student.pk is not None:
            new_user.student = new_student
            new_user.save()
        if new_teacher.pk is not None:
            countryObj = Country.objects.get(province__city__id=dataRes["city"])
            provinceObj = Province.objects.get(city__id=dataRes["city"])
            cityObj = City.objects.get(id=dataRes["city"])
            universityObj = University.objects.get(id=dataRes["university"])
            campusObj = Campus.objects.get(id=dataRes["campus"])

            new_user.teacher = new_teacher
            new_user.country = countryObj
            new_user.province = provinceObj
            new_user.city = cityObj
            new_user.university = universityObj
            new_user.campus = campusObj
            new_user.save()
        if new_expert.pk is not None:
            new_user.collaboratingExpert = new_expert
            new_user.save()
        serializer = GeneralUserListSerializer(new_user)
        return Response(serializer.data, status=HTTP_200_OK)

    def set_email_conform(self, id_user, request, role):
        token = jwt.encode({"id": id_user, "role": role, "exp": datetime.now(tz=timezone.utc) + timedelta(hours=24)},
                           "secreto", algorithm="HS256")
        try:

            mail_confirm_email.send_email_confirm_email(request.data['email'], request.data['first_name'], token)
            # mail_confirm_email.test_mail_sent(request.data['email'], request.data['first_name'], token)
        except Exception as e:
            print(e)

    def list(self, request):
        """
            Servicio para listar el usuario autentidado (Estudiante, Dcente, Experto Colaborador).
        """
        user = self.request.user
        if int(request.user.id) == int(user.pk):
            queryset = User.objects.filter(
                Q(student__is_active=True) | Q(teacher__is_active=True) | Q(collaboratingExpert__is_active=True)
            )
            user = get_object_or_404(queryset, pk=user.pk)
            serializer = GeneralUserListSerializer(user)
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response({"message": "User not found"}, status=HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk=None):
        """
            Servicio para listar el usuario autentidado (Estudiante, Dcente, Experto Colaborador).
        """
        if int(request.user.id) == int(pk):
            queryset = User.objects.filter(
                Q(student__is_active=True) | Q(teacher__is_active=True) | Q(collaboratingExpert__is_active=True)
            )
            user = get_object_or_404(queryset, pk=pk)
            serializer = GeneralUserListSerializer(user)
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response({"message": "User not found"}, status=HTTP_404_NOT_FOUND)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar el usuario se necesita estar autenticado como (Estudiante, Dcente, Experto Colaborador).
        """
        if int(request.user.id) == int(pk):
            queryset = User.objects.filter(
                Q(student__is_active=True) | Q(teacher__is_active=True) | Q(collaboratingExpert__is_active=True)
            )

            instance = get_object_or_404(queryset, pk=pk)
            user_serializer = UserUpdateSerializer(data=request.data)
            user_serializer.is_valid(raise_exception=True)
            instance.first_name = user_serializer.validated_data['first_name']
            instance.last_name = user_serializer.validated_data['last_name']

            instance.city_id = int(request.data['city'])
            instance.university_id = int(request.data['university'])
            instance.campus_id = int(request.data['campus'])

            # instance.image = user_serializer.validated_data['image']
            for role in user_serializer.validated_data['roles']:
                if instance.student is not None and role == 'student':
                    serializer = StudentUpdateSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    student_instance = Student.objects.get(pk=instance.student.id)
                    student_instance.birthday = serializer.validated_data['birthday']
                    student_instance.has_disability = serializer.validated_data['has_disability']
                    student_instance.disability_description = serializer.validated_data['disability_description']

                    education_levels = EducationLevel.objects.filter(
                        id__in=serializer.validated_data['education_levels']
                    )
                    knowledge_areas = KnowledgeArea.objects.filter(
                        id__in=serializer.validated_data['knowledge_areas']
                    )
                    preferences = Preferences.objects.filter(
                        id__in=serializer.validated_data['preferences']
                    )
                    student_instance.education_levels.clear()
                    student_instance.knowledge_areas.clear()
                    student_instance.preferences.clear()
                    for education_level in education_levels:
                        student_instance.education_levels.add(education_level)
                    for knowledge_area in knowledge_areas:
                        student_instance.knowledge_areas.add(knowledge_area)
                    for preference in preferences:
                        student_instance.preferences.add(preference)
                    student_instance.save()

                if instance.student is None and role == "student":
                    serializer = StudentUpdateSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    new_student = Student.objects.create(
                        birthday=serializer.validated_data['birthday'],
                        has_disability=serializer.validated_data['has_disability'],
                        disability_description=serializer.validated_data['disability_description'],
                    )
                    education_levels = EducationLevel.objects.filter(
                        id__in=serializer.validated_data['education_levels']
                    )
                    knowledge_areas = KnowledgeArea.objects.filter(
                        id__in=serializer.validated_data['knowledge_areas']
                    )
                    preferences = Preferences.objects.filter(
                        id__in=serializer.validated_data['preferences']
                    )
                    for education_level in education_levels:
                        new_student.education_levels.add(education_level)
                    for knowledge_area in knowledge_areas:
                        new_student.knowledge_areas.add(knowledge_area)
                    for preference in preferences:
                        new_student.preferences.add(preference)
                    new_student.save()
                    instance.student = new_student

                if instance.teacher is not None and role == 'teacher':
                    serializer = TeacherUpdateSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    teacher_instance = Teacher.objects.get(pk=instance.teacher.id)
                    professions = Profession.objects.filter(
                        id__in=serializer.validated_data['professions']
                    )
                    teacher_instance.professions.clear()
                    for profession in professions:
                        teacher_instance.professions.add(profession)
                    teacher_instance.save()
                    # else:
                    #     return Response({"message": "Debe tener un email institucional"}, status=HTTP_400_BAD_REQUEST)

                if instance.teacher is None and role == "teacher":
                    # if ".edu" in instance.email:
                    serializer = TeacherUpdateSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    new_teacher = Teacher.objects.create(
                        is_active=False
                    )
                    professions = Profession.objects.filter(
                        id__in=serializer.validated_data['professions']
                    )
                    for profession in professions:
                        new_teacher.professions.add(profession)
                    new_teacher.save()
                    instance.teacher = new_teacher
                    # else:
                    #     return Response({"message": "Debe tener un email institucional"}, status=HTTP_400_BAD_REQUEST)

                if instance.collaboratingExpert is not None and role == 'expert':
                    serializer = CollaboratingExpertUpdateSerializer(data=request.data)
                    collaboratingExpert_instance = CollaboratingExpert.objects.get(pk=instance.collaboratingExpert.id)

                    collaboratingExpert_instance.expert_level = serializer.validated_data['expert_level']
                    collaboratingExpert_instance.web = serializer.validated_data['web']
                    collaboratingExpert_instance.academic_profile = serializer.validated_data['academic_profile']
                    collaboratingExpert_instance.save()

                if instance.collaboratingExpert is None and role == 'expert':
                    serializer = CollaboratingExpertUpdateSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    new_expert = CollaboratingExpert.objects.create(
                        expert_level=serializer.validated_data['expert_level'],
                        web=serializer.validated_data['web'],
                        academic_profile=serializer.validated_data['academic_profile'],
                    )
                    new_expert.save()
                    instance.collaboratingExpert = new_expert
            instance.save()
            serializer = GeneralUserListSerializer(instance)
            return Response({"message": "success update"}, status=HTTP_200_OK)
        else:
            return Response({"message": "User not found"}, status=HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        """
            Servicio para eliminar el usuario se necesita estar autenticado como (Estudiante, Dcente, Experto Colaborador).
        """
        instance = User.objects.get(pk=pk)
        serializer = UserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for role in serializer.validated_data['roles']:
            if instance.student is not None and role == 'student':
                student = get_object_or_404(Student, id=instance.student.id)
                student.is_active = False
                student.save()

            if instance.teacher is not None and role == 'teacher':
                teacher = get_object_or_404(Teacher, id=instance.teacher.id)
                teacher.is_active = False
                teacher.save()

            if instance.collaboratingExpert is not None and role == 'expert':
                collaboratingExpert = get_object_or_404(CollaboratingExpert, id=instance.collaboratingExpert.id)
                collaboratingExpert.is_active = False
                collaboratingExpert.save()
        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message


class set_new_token_verify(APIView):
    """
    Enviar nuevo enlace con el token para confirmar el correo electrónico
    """
    permission_classes = []

    def post(self, request):
        try:
            user = get_object_or_404(User, email=request.data['email'])
        except:
            return Response({"message": "Correo no registrado", "status": 400}, status=HTTP_400_BAD_REQUEST)
        if user:
            user_role, user_id = self.role(user)
            self.set_email_conform_new_token(user_id, request.data['email'], user.first_name, user_role)
            return Response({"message": "Nuevo enlace creado", "status": 200}, status=HTTP_200_OK)
        else:
            return Response({"message": "Correo no registrado", "status": 400}, status=HTTP_400_BAD_REQUEST)

    def role(self, user):
        if user.collaboratingExpert_id is not None:
            return 'expert', user.collaboratingExpert_id
        elif user.student_id is not None:
            return 'student', user.student_id
        elif user.teacher_id is not None:
            return 'teacher', user.teacher_id

    def set_email_conform_new_token(self, id_user, email_user, name_user, role):
        token = jwt.encode({"id": id_user, "role": role, "exp": datetime.now(tz=timezone.utc) + timedelta(hours=24)},
                           "secreto", algorithm="HS256")
        mail_confirm_email.send_email_confirm_email(email_user, name_user,
                                                    token)


class VerifyEmail(generics.GenericAPIView):
    """
    Verificación de correo electrónico, en esta función enviamos el token al correo electrónico
    """
    permission_classes = []

    def get(self, request, token, email):
        try:
            """user_user = User.objects.filter(email=email)
            if user_user:
                role_user, id_user = roleUser(user_user[0])
                if role_user == 'student':
                    student = Student.objects.get(pk=id_user);
                    if student.is_account_active is True:
                        return Response({'email': 'Activado satisfactoriamente'}, status=HTTP_200_OK)
                if role_user == 'teacher':
                    teacher = Teacher.objects.get(pk=id_user);
                    if teacher.is_account_active:
                        return Response({'email': 'Activado satisfactoriamente'}, status=HTTP_200_OK)
                if role_user == 'expert':
                    expert = CollaboratingExpert.objects.get(pk=id);
                    if expert.is_account_active is True:
                        return Response({'email': 'Activado satisfactoriamente'}, status=HTTP_200_OK)
            else:
                return Response({'error': 'Token invalido'}, status=HTTP_400_BAD_REQUEST)"""

            payload = jwt.decode(token, "secreto", algorithms=["HS256"])
            role = payload['role']
            id = payload['id']
            if role == 'student':
                try:
                    student = Student.objects.get(pk=id);
                    user = User.objects.get(student_id=student.id);
                    if student.is_account_active is True:
                        return Response({'error': 'Token invalido'}, status=HTTP_400_BAD_REQUEST)
                except:
                    return Response({'error': 'Token invalido'}, status=HTTP_400_BAD_REQUEST)
                student.is_account_active = True
                mail_create.sendMailCreate(user.email, user.first_name)
                student.save()
                return Response({'email': 'Activado satisfactoriamente'}, status=HTTP_200_OK)
            if role == 'teacher':
                try:
                    teacher = Teacher.objects.get(pk=id);
                    user = User.objects.get(teacher_id=teacher.id);
                    if teacher.is_account_active is True:
                        return Response({'error': 'Token invalido'}, status=HTTP_400_BAD_REQUEST)
                    teacher.is_account_active = True
                except:
                    return Response({'error': 'Token invalido'}, status=HTTP_400_BAD_REQUEST)

                if teacher.is_active is False:
                    mail_create_check.sendMailCreateCheckAdmin(user.email, user.first_name)
                else:
                    mail_create.sendMailCreate(user.email, user.first_name)
                teacher.save()
                return Response({'email': 'Activado satisfactoriamente'}, status=HTTP_200_OK)
            if role == 'expert':
                try:
                    expert = CollaboratingExpert.objects.get(pk=id);
                    user = User.objects.get(collaboratingExpert_id=expert.id);
                    if expert.is_account_active is True:
                        return Response({'error': 'Token invalido'}, status=HTTP_400_BAD_REQUEST)
                except:
                    return Response({'error': 'Token invalido'}, status=HTTP_400_BAD_REQUEST)
                expert.is_account_active = True
                if expert.is_active is False:
                    mail_create_check_expert.sendMailCreate_Admin_to_Expert(user.email, user.first_name)
                else:
                    mail_create_expert.sendMailCreate_Expert(user.email, user.first_name)
                expert.save()
                return Response({'email': 'Activado satisfactoriamente'}, status=HTTP_200_OK)

        except jwt.ExpiredSignatureError as identifier:
            return Response({'error': 'Activacion expirada'}, status=HTTP_400_BAD_REQUEST)
        except jwt.InvalidTokenError as error:
            return Response({'error': 'Token invalido'}, status=HTTP_400_BAD_REQUEST)


mail_aproved = SendEmailConfirm()


def roleUser(user):
    if user.collaboratingExpert_id is not None:
        return 'expert', user.collaboratingExpert_id
    elif user.student_id is not None:
        return 'student', user.student_id
    elif user.teacher_id is not None:
        return 'teacher', user.teacher_id


class AdminDisaprovedTeacher(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdministratorUser]
    def list(self, request):
        """
            Servicio para listar Docente no aprobados. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(teacher__is_active=False)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AdminDisaprovedTeacherCollaboratingExpertSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            serializer = AdminDisaprovedTeacherCollaboratingExpertSerializer(queryset, many=True)
            return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para listar Dcente  no aprobados por id. Se necesita autenticación como administrador
        """
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminDisaprovedTeacherCollaboratingExpertSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar Dcente no aprobados. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = UpdateTecherCollaboratingExpertDisapprovedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.teacher is not None and instance.teacher.is_active is False:
            teacher = get_object_or_404(Teacher, id=instance.teacher.id)
            teacher.is_active = serializer.validated_data['teacher_is_active']
            mail_aproved.sendEmailConfirmAdmin(instance.email, instance.first_name);
            teacher.save()

        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message
class AdminDisaprovedTeacherDelete(DestroyAPIView):
    """
        Servicio para eliminar un usuario con el rol de docente
    """
    permission_classes =  [IsAuthenticated, IsAdministratorUser]
    def delete(self, request, pk=None):
        """
            Servicio para eliminar el usuario existente
        """
        try:
            user = User.objects.get(id=pk)
            user_teacher = Teacher.objects.get(pk=user.teacher_id)
            user.delete()
            user_teacher.delete()
            return Response({'message': 'User deleted successfully', 'code':200}, status= HTTP_200_OK)
        except Exception as e :
            print(e)
            return Response({'message':'Error deleting record from database', 'code':400}, status= HTTP_400_BAD_REQUEST)

class AdminDisaprovedCollaboratingExpert(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdministratorUser]

    def list(self, request):
        """
            Servicio para listar Experto Colaborador no aprobados. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(collaboratingExpert__is_active=False)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AdminDisaprovedTeacherCollaboratingExpertSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            serializer = AdminDisaprovedTeacherCollaboratingExpertSerializer(queryset, many=True)
            return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para listar Experto Colaborador no aprobados por id. Se necesita autenticación como administrador
        """
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminDisaprovedTeacherCollaboratingExpertSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar Experto Colaborador no aprobados. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = UpdateTecherCollaboratingExpertDisapprovedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.collaboratingExpert is not None and instance.collaboratingExpert.is_active is False:
            collaboratingExpert = get_object_or_404(CollaboratingExpert, id=instance.collaboratingExpert.id)
            collaboratingExpert.is_active = serializer.validated_data['expert_is_active']
            mail_aproved.sendEmailConfirmAdmin(instance.email, instance.first_name);
            collaboratingExpert.save()

        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message

class AdminDisaprovedCollaboratingExpertDelete(DestroyAPIView):
    """
        Servicio para eliminar el usuario de tipo experto colaborador
    """
    permission_classes = [IsAuthenticated, IsAdministratorUser]
    def delete(self, request, pk=None):
        """
            Eliminar usuario de tipo Experto Colaborador
        """
        try:
            user = User.objects.get(pk=pk)
            user_collaborating_expert = CollaboratingExpert.objects.get(pk =user.collaboratingExpert_id)
            user.delete()
            user_collaborating_expert.delete()
            return Response({'message':'User deleted successfully', 'code':200}, status= HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'message':'Error to delete User', 'code':400}, status=HTTP_400_BAD_REQUEST)

class AdminAprovedTeacher(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdministratorUser]

    def list(self, request):
        """
            Servicio para listar Dcente no aprobados. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(teacher__is_active=True)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AdminAprovedTeacherCollaboratingExpertSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            serializer = AdminAprovedTeacherCollaboratingExpertSerializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para listar Dcente no aprobados por id. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(teacher__is_active=True)
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminAprovedTeacherCollaboratingExpertWithOaSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar Dcente no aprobados. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = UpdateTecherCollaboratingExpertApproveedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.teacher is not None and instance.teacher.is_active is True:
            teacher = get_object_or_404(Teacher, id=instance.teacher.id)
            teacher.is_active = serializer.validated_data['teacher_is_active']
            teacher.save()

        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message


class AdminAprovedCollaboratingExpert(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdministratorUser]

    def list(self, request):
        """
            Servicio para listar Experto Colaborador no aprobados. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(collaboratingExpert__is_active=True)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AdminAprovedTeacherCollaboratingExpertSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            serializer = AdminAprovedTeacherCollaboratingExpertSerializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para listar Experto Colaborador no aprobados por id. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(collaboratingExpert__is_active=True)
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminAprovedTeacherCollaboratingExpertSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar Experto Colaborador no aprobados. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = UpdateTecherCollaboratingExpertApproveedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.collaboratingExpert is not None and instance.collaboratingExpert.is_active is True:
            collaboratingExpert = get_object_or_404(CollaboratingExpert, id=instance.collaboratingExpert.id)
            collaboratingExpert.is_active = serializer.validated_data['expert_is_active']
            collaboratingExpert.save()

        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message


class AdminListStudent(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdministratorUser]

    def list(self, request):
        """
            Servicio para listar estudiantes. Se necesita autenticación como administrador
        """
        user = User.objects.filter(
            Q(student__isnull=False)
        )
        serializer = AdminStudentListSerializer(user, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para listar estudiantes por id. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
            Q(student__isnull=False)
        )
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminStudentListSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar registro de un estudiante. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = AdminUpdateStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.student is not None:
            student = get_object_or_404(Student, id=instance.student.id)
            student.is_active = serializer.validated_data['student_is_active']
            student.save()
        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message


class AdminListTeacher(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdministratorUser]

    def list(self, request):
        """
            Servicio para listar Docentes. Se necesita autenticación como administrador
        """
        user = User.objects.filter(
            Q(teacher__isnull=False)
        )
        serializer = AdminTeacherListSerializer(user, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para listar Docentes. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
            Q(teacher__isnull=False)
        )
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminTeacherListSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar Docente. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = AdminUpdateStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.teacher is not None:
            teacher = get_object_or_404(Teacher, id=instance.teacher.id)
            teacher.is_active = serializer.validated_data['teacher_is_active']
            teacher.save()
        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message


class AdminListCollaboratingExpert(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdministratorUser]

    def list(self, request):
        """
            Servicio para listar Expertos Colaboradore. Se necesita autenticación como administrador
        """
        user = User.objects.filter(
            Q(collaboratingExpert__isnull=False)
        )
        serializer = AdminCollaboratingExpertListSerializer(user, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para listar Experto Colaborador por id. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
            Q(collaboratingExpert__isnull=False)
        )
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminCollaboratingExpertListSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar Experto Colaborador. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = AdminUpdateCollaboratingExpertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.collaboratingExpert is not None:
            collaboratingExpert = get_object_or_404(CollaboratingExpert, id=instance.collaboratingExpert.id)
            collaboratingExpert.is_active = serializer.validated_data['expert_is_active']
            collaboratingExpert.save()
        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message


class AdminListAdministrador(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdministratorUser]

    def list(self, request):
        """
            Servicio para listar Usuarios administradores. Se necesita autenticación como usuario administrador
        """
        user = User.objects.filter(
            administrator__isnull=False,
        ).exclude(email=self.request.user.email)
        serializer = AdminAdministratorListSerializer(user, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para obtener Usuario administrador. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
            Q(administrator__isnull=False)
        )
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminAdministratorListSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar Usuario admiistrador. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = AdminUpdateAdministratorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.administrator is not None:
            administrator = get_object_or_404(Administrator, id=instance.administrator.id)
            administrator.is_active = serializer.validated_data['administrator_is_active']
            administrator.save()
        status_message = Response({"message": "success"}, status=HTTP_200_OK)
        return status_message


class UserCountView(APIView):
    """Este servicio muestra el total del los usuarios que existe registrado en la plataforma."""
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        students = User.objects.filter(student__isnull=False).count()
        teacher = User.objects.filter(
            teacher__isnull=False
        ).exclude(
            teacher__is_active=False
        ).count()

        result = {
            "total_student": students,
            "total_teacher": teacher
        }
        return Response(result, status=HTTP_200_OK)


import urllib.request
from bs4 import BeautifulSoup
import requests


class VerifyOrcid(APIView):
    """Verificador de ORCID"""
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = OrcidValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        orcid = serializer.validated_data['orcid']
        """
            Servicio para verificar si el ORCID es valido.
        """
        url = 'https://orcid.org/0000-0002-9659-7109'
        opener = urllib.request.FancyURLopener({})
        f = opener.open(url)
        content = f.read()
        # http = urllib3.PoolManager()
        # response = http.request('GET', url)
        # data = response.data.decode("utf-8")
        # datos = urllib.request.urlopen(url).read().decode()
        # soup =  BeautifulSoup(datos)
        # tags = soup('title')
        # r = requests.get(url, allow_redirects=True)
        # # print(r)
        # print(r.headers.get('content-type'))
        # print(tags)
        # html_tables = data.find("body")

        # print(data)
        # print(r.status)
        # print(r.data)
        # url = requests.get("https://orcid.org/0000-0003-3250-6156")
        try:
            return Response({"message": "OK"}, status=HTTP_200_OK)
        except:
            return Response({"message": "invalid"}, status=HTTP_200_OK)


class TotalExpertTeacher(APIView):
    """Este servicio devuelve el total de los expertos colaboradores en la plataforma."""
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        total_expert_approved = User.objects.filter(
            collaboratingExpert__isnull=False,
        ).exclude(
            collaboratingExpert__is_active=False
        ).count()
        total_expert_disapproved = User.objects.filter(
            collaboratingExpert__isnull=False,
        ).exclude(
            collaboratingExpert__is_active=True
        ).count()
        total_teacher_approved = User.objects.filter(
            teacher__isnull=False,
        ).exclude(
            teacher__is_active=False
        ).count()
        total_teacher_disapproved = User.objects.filter(
            teacher__isnull=False,
        ).exclude(
            teacher__is_active=True
        ).count()
        total_student = User.objects.filter(
            student__isnull=False,
        ).count()

        result = {
            "total_expert_approved": total_expert_approved,
            "total_expert_disapproved": total_expert_disapproved,
            "total_teacher_approved": total_teacher_approved,
            "total_teacher_disapproved": total_teacher_disapproved,
            "total_student": total_student,
        }
        return Response(result, status=HTTP_200_OK)


class MyObtainTokenPairView(TokenObtainPairView):
    """
        Login de usuarios.
        Parametros requeridos correo y contraseña
    """
    permission_classes = (AllowAny,)
    serializer_class = MyTokenObtainPairSerializer


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class UserAPIView(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserLoginDataSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(UpdateAPIView):
    """
        Cambiar contraseña del usuario
    """
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer
    lookup_field = 'pk'

    def update(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        if (pk == self.request.user.id):
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                instance.set_password(serializer.validated_data['password'])
                instance.save()
                return Response({"message": "User updated successfully", "status": "Ok"}, status=HTTP_200_OK)
            else:
                return Response({"message": "failed", "details": serializer.errors}, status=HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "The user does not have permissions to update."}, status=HTTP_400_BAD_REQUEST)


mail = SendMail()


class RequestPasswordResetEmail(GenericAPIView):
    """
        Reset contraseña de usuario por correo
    """
    permission_classes = [AllowAny]
    serializer_class = RequestPasswordResetEmailSerializer

    def post(self, request):
        data = {request: request, 'data': request.data}
        email = request.data['email']
        get_object_or_404(User, email=email)
        user = User.objects.get(email=email)
        if user.student_id is not None:
            student = Student.objects.get(id=user.student_id)
            if student.has_disability is True:
                date_birthday = student.birthday
                email = user.email
                email_name = email.split("@")
                user.set_password(str(email_name[0]) + str(date_birthday))
                user.save()
                return Response({"message": " Reset password successful", "status": 201}, status=HTTP_200_OK)

        uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
        token = PasswordResetTokenGenerator().make_token(user)
        absurl = env('DOMAIN_HOST_ROA') + '/#/password-resed/' + uidb64 + '/' + token + '/'
        mail.sendMailTest(user.email, absurl, user.first_name)
        return Response({
            "message": "We have send you a link to reset your password",
            'token': token,
            'uidb64': uidb64
        }, status=HTTP_200_OK)


class PasswordTokenCkeckAPI(GenericAPIView):
    """
        Password token ckeck
    """
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({"error": "Token is no valid, please request a new one"}, status=HTTP_401_UNAUTHORIZED)
            return Response({'success': True, 'message': 'Credential valid', 'uidb64': uidb64, 'token': token},
                            status=HTTP_200_OK)
        except DjangoUnicodeDecodeError as identifier:
            return Response({"error": "Token is no valid, please request a new one."}, status=HTTP_401_UNAUTHORIZED)


class SetNewPasswordAPIView(GenericAPIView):
    """
        Set new password
    """
    permission_classes = [AllowAny, ]
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'status': True, 'message': 'Password reset succes.'}, status=HTTP_200_OK)


class UpdateUserProfilePicture(RetrieveUpdateAPIView):
    """
        Actualizar foto de perfil de un usurio
    """
    permission_classes = [IsAuthenticated, (IsStudentUser | IsTeacherUser | IsCollaboratingExpertUser)]
    serializer_class = UserUpdatePictureSerializer
    queryset = User.objects.all()


class GetStudentPreferences(RetrieveAPIView):
    """
        Obtener preferencias de un estudiante
    """

    lookup_field = 'email'
    permission_classes = [AllowAny]
    serializer_class = UserListSerializers

    def get_queryset(self):
        email = self.kwargs['email']
        obj = User.objects.filter(email=email)
        return obj
    # def get(self, request):
    #     print(request.user.email)
    #     preferences = User.objects.get(email=request.user.email)
    #     print(preferences)
    #     serializer = UserListSerializers(preferences)
    #     return Response(serializer.data, status=HTTP_200_OK)


class ReportListAPIView(ListAPIView):
    permission_classes = [AllowAny, ]
    # permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = UserReportSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        # "first_name": ["icontains"],
        # "last_name": ["icontains"],
        # "email": ["icontains"],
        # "university_id": ["exact"],
        # "campus_id": ["exact"]
    }

    def get_queryset(self):

        """ 
        if date_init is None or date_end is None:
            return LearningObjectMetadata.objects.filter(public=public).order_by('-pk')

        return LearningObjectMetadata.objects.filter(public=public, created__range=[date_init, date_end]).order_by(
            '-pk')
        """
        upload = self.request.query_params.get("upload")
        query = self.request.query_params.get("query")
        city = self.request.query_params.get("city")
        university = self.request.query_params.get("university")
        campus = self.request.query_params.get("campus")

        users = User.objects.filter(
            teacher_id__isnull=False
        )

        if upload == "upload":
            users = users.filter(
                metadata_created__isnull=False
            )
        elif upload == "not_upload":
            users = User.objects.filter(
                metadata_created__isnull=True
            )

        if query is not None or query != "":
            users = users.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__exact=query),
            )

        if city is not None and city.isnumeric():
            users = users.filter(
                city_id=int(city)
            )

        if university is not None and university.isnumeric():
            users = users.filter(
                university_id=int(university)
            )

        if campus is not None and campus.isnumeric():
            users = users.filter(
                campus_id=int(campus)
            )
        return users.order_by('-pk').distinct('id')


class sendEmailContact(CreateAPIView):
    """
    Clase para enviar los emails a los administradores desde la pagina de contacto
    """
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = EmailContacSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        users_admin = User.objects.filter(is_superuser=True)
        for user_admin in users_admin:
            try:
                mail_aproved.sendEmailContactAdmin(user_admin.email, user_admin.first_name + ' ' + user_admin.last_name,
                                                   serializer['name'].value, serializer['email'].value,
                                                   serializer['content'].value)
            except Exception as e:
                print(e)
                return Response({'code': 400, 'message': 'Failed to send email'}, status=HTTP_400_BAD_REQUEST)
        return Response({'code': 200, 'message': 'Email sent successfully'}, status=HTTP_200_OK)
