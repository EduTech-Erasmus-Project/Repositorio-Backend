import json
from applications.user.testMail import SendMail, SendEmailCreateUser, SendEmailCreateUserCheck, SendEmailConfirm, SendEmailCreateUserCheck_Expert, SendEmailCreateUserCheck_Admin_to_Expert
from applications.user.utils import Util
from rest_framework.generics import ListAPIView
from rest_framework import viewsets
from rest_framework.generics import GenericAPIView, RetrieveAPIView, RetrieveUpdateAPIView, UpdateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from .serializers import ChangePasswordSerializer, MyTokenObtainPairSerializer, RequestPasswordResetEmailSerializer, SetNewPasswordSerializer, StudentListSerializer, UpdateTecherCollaboratingExpertApproveedSerializer, UpdateTecherCollaboratingExpertDisapprovedSerializer, UserListSerializers, UserUpdatePictureSerializer
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated ,AllowAny
from django.db.models import Q
from django.shortcuts import get_object_or_404
from applications.education_level.models import EducationLevel
from applications.knowledge_area.models import KnowledgeArea
from applications.preferences.models import Preferences
from applications.profession.models import Profession
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
    OrcidValidationSerializer
)
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED
)
from applications.user.mixins import IsAdministratorUser, IsCollaboratingExpertUser,IsGeneralUser, IsStudentUser, IsTeacherUser
# Create your views here.

class UserAdminView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdministratorUser,]


    def create(self, request, *args, **kwargs):
        """
            Servicio para crear un usuario administrador. Se necesita un token de autenticación como administrador para hacer uso de este servicio
        """
        serializer = UserAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_admin = Administrator.objects.create(
            country= serializer.validated_data['country'],
            city= serializer.validated_data['city'],
            phone= serializer.validated_data['phone'],
            observation= serializer.validated_data['observation'],
        )
        new_admin.is_active = True
        new_admin.save()
        new_user  = User.objects.create_admin_user(
            first_name= serializer.validated_data['first_name'],
            last_name= serializer.validated_data['last_name'],
            email= serializer.validated_data['email'],
            password= serializer.validated_data['password'],
            )
        new_user.administrator = new_admin
        new_user.save()
        serializer = UserListSerializer(new_user)
        return Response(serializer.data,status=HTTP_200_OK)
    def list(self, request):
        """
            Servicio para listar los usuarios administradores. Se necesita un token de autenticación como super usuario para hacer uso de este servicio
        """
        queryset = User.objects.filter(email=self.request.user.email)
        serializer = UserListSerializer(queryset,many=True)
        return Response(serializer.data,status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
            Servicio para actualizar un usuario administrador. Se necesita un token de autenticación como administrador para hacer uso de este servicio
        """
        if int(request.user.id)== int(pk):
            queryset = User.objects.filter().order_by('-pk')
            user = get_object_or_404(queryset, pk=pk)
            serializer = UserListSerializer(user)
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response({"message": "User not found"},status=HTTP_404_NOT_FOUND)

    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actuaizar un usuario administrador. Se necesita un token de autenticación como administrador para hacer uso de este servicio
        """
        if int(request.user.id)== int(pk):
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
            return Response({"message": "User not found"},status=HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        return Response({"message": "Api not found"},status=HTTP_404_NOT_FOUND) 

mail_create = SendEmailCreateUser()
mail_create_check = SendEmailCreateUserCheck()

mail_create_expert = SendEmailCreateUserCheck_Expert()
mail_create_check_expert = SendEmailCreateUserCheck_Admin_to_Expert()
class ManagementUserView(viewsets.ViewSet):

    def get_permissions(self):
        if(self.action=='create'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsGeneralUser,]
        return [permission() for permission in permission_classes]

    def checkEmail(email):
        print(email)
        regex = '^([a-zA-Z0-9]+)@((?!hotmail|gmail|yahoo|outlook)(([a-zA-Z0-9\-]+\.)+))([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)$'
        if (re.search(regex, email)):
            #print("Valid Email")
            return True
        else:
            #print("Invalid Email")
            return False
        return False

    def create(self, request, *args, **kwargs):
        """
            Servicio para crear un nuevo usuario (Estudiante, Dcente, Experto Colaborador).
        """
        """ Validamos el correo del usuario """
        role_serializer = RoleSerializer(data=request.data)
        role_serializer.is_valid(raise_exception=True)
        #print(role_serializer['email'].value)
        new_student = Student()
        new_teacher = Teacher()
        new_expert = CollaboratingExpert()


        for role in role_serializer.validated_data['roles']:

            if role == 'student' and role != 'teacher' and role != 'expert':
                serializer = StudentCreateSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                new_student = Student.objects.create(
                    birthday= serializer.validated_data['birthday'],
                    has_disability= serializer.validated_data['has_disability'],
                    disability_description= serializer.validated_data['disability_description'],
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

                #if not ManagementUserView.checkEmail(request.data['email']):
                 #   value_active = False
                  #  mail_create_check.sendMailCreateCheckAdmin(request.data['email'], request.data['first_name'])
                #else:
                value_active = True
                mail_create.sendMailCreate(request.data['email'], request.data['first_name'])

                new_student.is_active = value_active

                new_student.save()

            if role == 'teacher' and role != 'student' and role != 'expert':
                teacher_serializer = TeacherCreateSerializer(data=request.data)
                teacher_serializer.is_valid(raise_exception=True)

                if not ManagementUserView.checkEmail(request.data['email']):
                    value_active = False
                    mail_create_check.sendMailCreateCheckAdmin(request.data['email'], request.data['first_name'])
                else:
                    value_active = True
                    mail_create.sendMailCreate(request.data['email'], request.data['first_name'])

                new_teacher = Teacher.objects.create(
                    is_active=value_active
                )

                professions = Profession.objects.filter(
                    id__in=teacher_serializer.validated_data['professions']
                )
                for profession in professions:
                    new_teacher.professions.add(profession)

                new_teacher.save()
                # post_save.connect(send_email1, sender=User)
                # request_finished.connect(send_email1(role_serializer.validated_data['first_name'],role_serializer.validated_data['last_name'],role,role_serializer.validated_data['email']))

            if role == 'expert' and role != 'teacher' and role != 'student':
                serializer = CollaboratingExpertCreateSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)

                if not ManagementUserView.checkEmail(request.data['email']):
                    value_active = False
                    mail_create_check_expert.sendMailCreate_Admin_to_Expert(request.data['email'], request.data['first_name'])
                else:
                    value_active = True
                    mail_create_expert.sendMailCreate_Expert(request.data['email'], request.data['first_name'])

                new_expert = CollaboratingExpert.objects.create(
                    expert_level= serializer.validated_data['expert_level'],
                    web= serializer.validated_data['web'],
                    academic_profile= serializer.validated_data['academic_profile'],
                    is_active = value_active
                )
                new_expert.save()

        new_user = User.objects.create_general_user(
            first_name= role_serializer.validated_data['first_name'],
            last_name= role_serializer.validated_data['last_name'],
            email= role_serializer.validated_data['email'],
            password= role_serializer.validated_data['password'],
            )

        new_user.image=role_serializer.validated_data['image']
        if new_student.pk is not None:
            new_user.student = new_student
            new_user.save()
        if new_teacher.pk is not None:
            new_user.teacher = new_teacher
            new_user.save()
        if new_expert.pk is not None:
            new_user.collaboratingExpert = new_expert
            new_user.save()
        serializer = GeneralUserListSerializer(new_user)
        return Response(serializer.data,status=HTTP_200_OK)

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
            return Response({"message": "User not found"},status=HTTP_404_NOT_FOUND)

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
            return Response({"message": "User not found"},status=HTTP_404_NOT_FOUND)

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
            # instance.image = user_serializer.validated_data['image']
            for role in user_serializer.validated_data['roles']:
                if instance.student is not None and role == 'student':
                    serializer = StudentUpdateSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    student_instance = Student.objects.get(pk=instance.student.id)
                    student_instance.birthday= serializer.validated_data['birthday']
                    student_instance.has_disability = serializer.validated_data['has_disability']
                    student_instance.disability_description= serializer.validated_data['disability_description']

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
                        birthday= serializer.validated_data['birthday'],
                        has_disability= serializer.validated_data['has_disability'],
                        disability_description= serializer.validated_data['disability_description'],
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
                    serializer.is_valid(raise_exception=True)
                    collaboratingExpert_instance = CollaboratingExpert.objects.get(pk=instance.collaboratingExpert.id)
                    collaboratingExpert_instance.expert_level = serializer.validated_data['expert_level']
                    collaboratingExpert_instance.web = serializer.validated_data['web']
                    collaboratingExpert_instance.academic_profile = serializer.validated_data['academic_profile']
                    collaboratingExpert_instance.save()

                if instance.collaboratingExpert is None and role == 'expert':
                    serializer = CollaboratingExpertUpdateSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    new_expert = CollaboratingExpert.objects.create(
                        expert_level= serializer.validated_data['expert_level'],
                        web= serializer.validated_data['web'],
                        academic_profile= serializer.validated_data['academic_profile'],
                    )
                    new_expert.save()
                    instance.collaboratingExpert = new_expert
            instance.save()
            serializer = GeneralUserListSerializer(instance)
            return Response({"message": "success update"}, status=HTTP_200_OK)
        else:
            return Response({"message": "User not found"},status=HTTP_404_NOT_FOUND)
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
        status_message =  Response({"message": "success"}, status=HTTP_200_OK)      
        return status_message

mail_aproved = SendEmailConfirm()
class AdminDisaprovedTeacherCollaboratingExpert(viewsets.ViewSet):

    permission_classes = [IsAuthenticated,IsAdministratorUser]

    def list(self, request):
        """
            Servicio para listar Docente y Experto Colaborador no aprobados. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
                Q(teacher__is_active=False) | Q(collaboratingExpert__is_active=False)
        )
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
            Servicio para listar Dcente y Experto Colaborador no aprobados por id. Se necesita autenticación como administrador
        """
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminDisaprovedTeacherCollaboratingExpertSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)
    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar Dcente y Experto Colaborador no aprobados. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = UpdateTecherCollaboratingExpertDisapprovedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.teacher is not None and instance.teacher.is_active is False:
            teacher = get_object_or_404(Teacher, id=instance.teacher.id)
            teacher.is_active = serializer.validated_data['teacher_is_active']
            mail_aproved.sendEmailConfirmAdmin(instance.email, instance.first_name);
            teacher.save()

        if instance.collaboratingExpert is not None and instance.collaboratingExpert.is_active is False:
            collaboratingExpert = get_object_or_404(CollaboratingExpert, id=instance.collaboratingExpert.id)
            collaboratingExpert.is_active = serializer.validated_data['expert_is_active']
            mail_aproved.sendEmailConfirmAdmin(instance.email, instance.first_name);
            collaboratingExpert.save()

        status_message =  Response({"message": "success"}, status=HTTP_200_OK)      
        return status_message

class AdminAprovedTeacherCollaboratingExpert(viewsets.ViewSet):

    permission_classes = [IsAuthenticated,IsAdministratorUser]
    def list(self, request):
        """
            Servicio para listar Dcente y Experto Colaborador no aprobados. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
                Q(teacher__is_active=True) | Q(collaboratingExpert__is_active=True)
        )
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AdminAprovedTeacherCollaboratingExpertSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            serializer = AdminAprovedTeacherCollaboratingExpertSerializer(queryset, many=True)
        return Response(serializer.data,status=HTTP_200_OK)
    def retrieve(self, request, pk=None):
        """
            Servicio para listar Dcente y Experto Colaborador no aprobados por id. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
                Q(teacher__is_active=True) | Q(collaboratingExpert__is_active=True)
        )
        user = get_object_or_404(queryset, pk=pk)
        serializer = AdminAprovedTeacherCollaboratingExpertSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)
    def update(self, request, pk=None, project_pk=None):
        """
            Servicio para actualizar Dcente y Experto Colaborador no aprobados. Se necesita autenticación como administrador
        """
        instance = User.objects.get(pk=pk)
        serializer = UpdateTecherCollaboratingExpertApproveedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.teacher is not None and instance.teacher.is_active is True:
            teacher = get_object_or_404(Teacher, id=instance.teacher.id)
            teacher.is_active = serializer.validated_data['teacher_is_active']
            teacher.save()

        if instance.collaboratingExpert is not None and instance.collaboratingExpert.is_active is True:
            collaboratingExpert = get_object_or_404(CollaboratingExpert, id=instance.collaboratingExpert.id)
            collaboratingExpert.is_active = serializer.validated_data['expert_is_active']
            collaboratingExpert.save()

        status_message =  Response({"message": "success"}, status=HTTP_200_OK)      
        return status_message

class AdminListStudent(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,IsAdministratorUser]
    def list(self, request):
        """
            Servicio para listar estudiantes. Se necesita autenticación como administrador
        """
        user = User.objects.filter(
                Q(student__isnull = False)
        )
        serializer = AdminStudentListSerializer(user,many=True)
        return Response(serializer.data,status=HTTP_200_OK)
    def retrieve(self, request, pk=None):
        """
            Servicio para listar estudiantes por id. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
                Q(student__isnull = False)
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
        status_message =  Response({"message": "success"}, status=HTTP_200_OK)      
        return status_message

class AdminListTeacher(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,IsAdministratorUser]
    def list(self, request):
        """
            Servicio para listar Docentes. Se necesita autenticación como administrador
        """
        user = User.objects.filter(
                Q(teacher__isnull = False)
        )
        serializer = AdminTeacherListSerializer(user,many=True)
        return Response(serializer.data,status=HTTP_200_OK)
    def retrieve(self, request, pk=None):
        """
            Servicio para listar Docentes. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
                Q(teacher__isnull = False)
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
        status_message =  Response({"message": "success"}, status=HTTP_200_OK)      
        return status_message

class AdminListCollaboratingExpert(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,IsAdministratorUser]
    def list(self, request):
        """
            Servicio para listar Expertos Colaboradore. Se necesita autenticación como administrador
        """
        user = User.objects.filter(
                Q(collaboratingExpert__isnull = False)
        )
        serializer = AdminCollaboratingExpertListSerializer(user,many=True)
        return Response(serializer.data,status=HTTP_200_OK)
    def retrieve(self, request, pk=None):
        """
            Servicio para listar Experto Colaborador por id. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
                Q(collaboratingExpert__isnull = False)
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
        status_message =  Response({"message": "success"}, status=HTTP_200_OK)      
        return status_message

class AdminListAdministrador(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,IsAdministratorUser]
    def list(self, request):
        """
            Servicio para listar Usuarios administradores. Se necesita autenticación como usuario administrador
        """
        user = User.objects.filter(
                administrator__isnull = False,
        ).exclude(email = self.request.user.email)
        serializer = AdminAdministratorListSerializer(user,many=True)
        return Response(serializer.data,status=HTTP_200_OK)
    def retrieve(self, request, pk=None):
        """
            Servicio para obtener Usuario administrador. Se necesita autenticación como administrador
        """
        queryset = User.objects.filter(
                Q(administrator__isnull = False)
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
        status_message =  Response({"message": "success"}, status=HTTP_200_OK)      
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
        print(content)
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
        total_student= User.objects.filter(
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
        if(pk==self.request.user.id):
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                instance.set_password(serializer.validated_data['password'])
                instance.save()
                return Response({"message": "User updated successfully","status":"Ok"},status=HTTP_200_OK)
            else:
                return Response({"message": "failed", "details": serializer.errors},status=HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "The user does not have permissions to update."},status=HTTP_400_BAD_REQUEST)

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str,smart_bytes,DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls.base import reverse

mail = SendMail()
class RequestPasswordResetEmail(GenericAPIView):
    """
        Reset contraseña de usuario por correo
    """
    permission_classes = [AllowAny]
    serializer_class = RequestPasswordResetEmailSerializer
    def post(self, request):
        data = {request:request, 'data': request.data}
        email = request.data['email']
        get_object_or_404(User, email=email)
        user = User.objects.get(email=email)
        uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
        token= PasswordResetTokenGenerator().make_token(user)
        absurl = 'https://repositorio.edutech-project.org/#/password-resed/'+uidb64+'/'+token+'/'
        mail.sendMailTest(user.email,absurl,user.first_name)
        return Response({
        "message": "We have send you a link to reset your password",
        'token':token,
        'uidb64':uidb64
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
            return Response({'success':True, 'message':'Credential valid','uidb64':uidb64,'token':token},status=HTTP_200_OK)
        except DjangoUnicodeDecodeError as identifier:
            return Response({"error": "Token is no valid, please request a new one."}, status=HTTP_401_UNAUTHORIZED)

class SetNewPasswordAPIView(GenericAPIView):
    """
        Set new password
    """
    permission_classes = [AllowAny,]
    serializer_class = SetNewPasswordSerializer
    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'status':True,'message':'Password reset succes.'}, status=HTTP_200_OK)

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