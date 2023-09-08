from rest_framework import generics, status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_404_NOT_FOUND

from applications.settings.models import Email, OptionRegisterEmailExtension, EmailExtensionsTeacher, \
    EmailExtensionsExpert, EmailExtensionsStudent, UserTypeWithOption
from applications.settings.serializers import EmailSerializer, EmailDomainTeacherSerializer, \
    OptionRegisterEmailExtensionSerializer, EmailDomainExpertSerializer, EmailDomainStudentSerializer, \
    UserTypeWithOptionSerializer, EmailDomainTeacherCreateSerializer, EmailDomainExpertCreateSerializer, \
    EmailDomainStudentCreateSerializer, UserTypeWithOptionSerializerList
from applications.user.mixins import IsAdministratorUser, IsGeneralUser
from applications.user.views import mail_aproved


# Create your views here.
class EmailListCreateAPIView(generics.ListCreateAPIView):
    """
        Servicio para servidor de email
    """
    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticated, IsAdministratorUser]  # permisos autenticado y solo de admin

    def get(self, request):
        try:
            email, created = Email.objects.get_or_create()
            serializer = self.serializer_class(email)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": 204, "message": "The company don't have an assigned email"},
                            status=status.HTTP_200_OK)

    def post(self, request):
        try:
            email_obj = Email.objects.first()
            serializer = self.serializer_class(instance=email_obj, data=request.data, partial=True)
            if serializer.is_valid():
                new_password = request.data['password']

                if new_password is not None:
                    hashed_password = email_obj.encrypt_password(new_password)
                    serializer.validated_data['password'] = hashed_password.decode('utf-8')
                else:
                    serializer.validated_data['password'] = email_obj.password

                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response({'message': 'Error', 'error': serializer.error_messages},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": e.__str__(), "data": None},
                            status=status.HTTP_400_BAD_REQUEST)


class EmailDomainListCreateAPIView(generics.ListCreateAPIView):
    """
        Servicio para registrar emails mas dominios para
        registrarlos desde el administrador
    """

    def get_permissions(self):
        permission_classes = None
        if self.request.method == 'POST':
            permission_classes = [IsAuthenticated, IsAdministratorUser ]
        else:
            permission_classes = [AllowAny]

        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        if request.data['type'] == "TEACHER":
            serializer = EmailDomainTeacherCreateSerializer(data=request.data)
            if serializer.is_valid():
                self.perform_create(serializer)
                return Response({'message':'Create Successful', 'code':200}, status=HTTP_200_OK)

        elif request.data['type'] == "EXPERT":
            serializer = EmailDomainExpertCreateSerializer(data=request.data)
            if serializer.is_valid():
                self.perform_create(serializer)
                return Response({'message': 'Create Successful', 'code': 200}, status=HTTP_200_OK)

        elif request.data['type'] == "STUDENT":
            serializer = EmailDomainStudentCreateSerializer(data=request.data)
            if serializer.is_valid():
                self.perform_create(serializer)
                return Response({'message': 'Create Successful', 'code': 200}, status=HTTP_200_OK)
        return Response({'message': 'Create error', 'code': 400}, status=HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        if request.query_params.get('type') == "TEACHER":
            request = EmailExtensionsTeacher.objects.filter(option_register_email=request.query_params.get('option')).order_by('id')
            serializer = EmailDomainTeacherSerializer(request, many=True)
            return Response({'message': 'List Successful', 'code': 200,"data":serializer.data}, status=HTTP_200_OK)
        elif request.query_params.get('type') == "EXPERT":
            request = EmailExtensionsExpert.objects.filter(option_register_email=request.query_params.get('option')).order_by('id')
            serializer = EmailDomainExpertSerializer(request, many=True)
            return Response({'message': 'List Successful', 'code': 200, "data": serializer.data}, status=HTTP_200_OK)
        elif request.query_params.get('type') == "STUDENT":
            request = EmailExtensionsStudent.objects.filter(option_register_email=request.query_params.get('option')).order_by('id')
            serializer = EmailDomainStudentSerializer(request, many=True)
            return Response({'message': 'List Successful', 'code': 200, "data": serializer.data}, status=HTTP_200_OK)
        return Response({'message': 'List error', 'code': 400}, status=HTTP_404_NOT_FOUND)


class EmailDomainListListAPIView(generics.ListAPIView):
    queryset = EmailExtensionsTeacher.objects.filter(is_active=True).order_by('id')
    serializer_class = EmailDomainTeacherSerializer
    permission_classes = [IsAuthenticated, IsAdministratorUser]  # permisos autenticado y solo de admin


class EmailDomainListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdministratorUser]  # permisos autenticado y solo de admin

    def list(self, request, *args, **kwargs):
        if request.query_params.get('type') == "TEACHER":
            instance = EmailExtensionsTeacher.objects.filter(pk=kwargs.get('pk'))
            serializer = EmailDomainTeacherSerializer(instance, many=True)
            return Response({'message':'List successful','code':200, 'data': serializer.data}, status=HTTP_200_OK)
        elif request.query_params.get('type') == "EXPERT":
            instance = EmailExtensionsExpert.objects.filter(pk=kwargs.get('pk'))
            serializer = EmailDomainTeacherSerializer(instance, many=True)
            return Response({'message':'List successful','code':200, 'data': serializer.data}, status=HTTP_200_OK)
        elif request.query_params.get('type') == "STUDENT":
            instance = EmailExtensionsStudent.objects.filter(pk=kwargs.get('pk'))
            serializer = EmailDomainTeacherSerializer(instance, many=True)
            return Response({'message':'List successful','code':200, 'data': serializer.data}, status=HTTP_200_OK)
        else:
            return Response({'message': 'List error', 'code': 400}, status=HTTP_404_NOT_FOUND)


class EmailDomainUpdateView(generics.UpdateAPIView):
    """
        Servicio para actualizar la relacion entre los tipos de roles
        con las apciones de registro
    """
    permission_classes = [IsAuthenticated, IsAdministratorUser]
    #serializer_class = UserTypeWithOptionSerializer
    #queryset = UserTypeWithOption.objects.all()

    def update(self, request, *args, **kwargs):
        if request.query_params.get('type') == "TEACHER":
            instance = EmailExtensionsTeacher.objects.filter(pk=kwargs.get('pk'))
            serializer = EmailDomainTeacherCreateSerializer(instance[0], data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'Successful','data':serializer.data})
        elif request.query_params.get('type') == "EXPERT":
            instance = EmailExtensionsExpert.objects.filter(pk=kwargs.get('pk'))
            serializer = EmailDomainExpertCreateSerializer(instance[0], data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'Successful','data':serializer.data})
        elif request.query_params.get('type') == "STUDENT":
            instance = EmailExtensionsStudent.objects.filter(pk=kwargs.get('pk'))
            serializer = EmailDomainStudentCreateSerializer(instance[0], data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'Successful','data':serializer.data})
        else:
            return Response({'message': 'Update error', 'code': 400}, status=HTTP_404_NOT_FOUND)

class sendEmailTestingConecction(CreateAPIView):
    """
        Clase para la prueba de coneccion de servidor de email
    """
    permission_classes = [IsAuthenticated, IsAdministratorUser]

    def post(self, request, *args, **kwargs):

        try:
            data = request.data
            mail_aproved.sendEmailTesting(data['host'], data['username'], data['password'], data['emailtest'],
                                          data['port'], data['tls'], data['email_from'])

            return Response({'code': 200, 'message': 'Email testing sent successfully'}, status=HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'code': 400, 'message': e.__str__()}, status=HTTP_400_BAD_REQUEST)


class OptionRegisterEmailExtensionView(ListAPIView):
    """
        Servicio que retorna la lista  de las opciones para registrar un
        correo electronico
    """
    permission_classes = [IsAuthenticated, IsAdministratorUser]
    serializer_class = OptionRegisterEmailExtensionSerializer
    queryset = OptionRegisterEmailExtension.objects.all()


class UserTypeOptionView(generics.ListAPIView):
    """
        Servicio para listar la lista de usuarios
    """
    permission_classes = [AllowAny]
    serializer_class = UserTypeWithOptionSerializerList
    queryset = UserTypeWithOption.objects.all()


class UserTypeOptionUpdateView(generics.UpdateAPIView):
    """
        Servicio para actualizar la relacion entre los tipos de roles
        con las apciones de registro
    """
    permission_classes = [IsAuthenticated, IsAdministratorUser]
    def update(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        try:
            object_type_update = UserTypeWithOption.objects.get(pk=pk)
            object_type_update.option_register_id = request.data['option_register']
            object_type_update.save()
            return Response({'message': 'Update Successful', 'code': 200}, status=HTTP_200_OK)
        except Exception as e:
            return Response({'message': 'Error Update', 'code': 400}, status=HTTP_400_BAD_REQUEST)
