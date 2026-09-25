"""Vistas y helpers para carga, extracción e integración de archivos OA.

Este módulo concentra el flujo mas operativo del repositorio:

- recepción de paquetes ZIP IMS/SCORM
- extracción local del contenido y lectura del manifest
- generación de previsualización
- integración con OER Adapt
- borrado de registros y limpieza de archivos asociados
"""

from yaml import serialize
import logging
from applications.user.models import User
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, viewsets
from rest_framework import status
from rest_framework.views import APIView
from media.maplompad.controller import FileController
from .models import LearningObjectFile
from datetime import datetime, timedelta
from .serializers import (
    LearningObjectSerializer, LearningObjectOerAdapt, LearningObjectFileOerSerializer, LearningObjectFileOerDataSerializer
)
from rest_framework.response import Response
import zipfile ,io, urllib3
import os
import shortuuid
from bs4 import BeautifulSoup as bs
from applications.user.mixins import IsTeacherUser, IsAdministratorUser
from roabackend import settings as _settings
from django.conf import settings
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)
from rest_framework.permissions import IsAuthenticated, AllowAny
import shutil
import xmltodict, json
from unipath import Path
from os import remove
from shutil import rmtree
from ..learning_object_metadata.models import LearningObjectMetadata
from applications.learning_object_metadata.views import automaticEvaluation
from xml.dom import minidom
import requests

from ..helpers_functions.beautiful_soup_data import read_html_files, look_for_class_oeradap, generaye_array_paths_img, \
    verify_that_oa_was_made_exelearning
from roabackend.settings import DEBUG
from io import BytesIO
logger = logging.getLogger(__name__)
booleanLomLomes = True  # True representa manifests LOM; False representa LOMES.
from applications.learning_object_file.emailManagerLO import SendMail
import environ
env = environ.Env()
BASE_DIR = Path(__file__).ancestor(3)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


LEARNING_OBJECT_FILE_TAG = ['Learning Object File Management']
LEARNING_OBJECT_FILE_DELETE_TAG = ['Learning Object File Deletion']
LEARNING_OBJECT_OER_TAG = ['Learning Object OER Adapt']

LEARNING_OBJECT_FILE_ID_PARAMETER = OpenApiParameter(
    name='id',
    type=int,
    location=OpenApiParameter.PATH,
    description='Identificador del archivo OA o de la metadata segun el endpoint de borrado usado.',
)
LEARNING_OBJECT_FILE_DELETE_MESSAGE_PARAMETER = OpenApiParameter(
    name='message',
    type=str,
    location=OpenApiParameter.QUERY,
    required=False,
    description='Motivo que administracion envia por correo al docente cuando elimina el OA.',
)
LEARNING_OBJECT_FILE_ERRORS_RESPONSE = inline_serializer(
    name='LearningObjectFileErrorsResponse',
    fields={
        'media': serializers.BooleanField(),
        'scorm': serializers.BooleanField(),
        'web': serializers.BooleanField(),
        'is_exelearning': serializers.BooleanField(),
    },
)
LEARNING_OBJECT_FILE_UPLOAD_RESPONSE = inline_serializer(
    name='LearningObjectFileUploadResponse',
    fields={
        'metadata': serializers.JSONField(help_text='Metadata extraida del manifest IMS/SCORM.'),
        'oa_file': LearningObjectSerializer(),
        'tag_count': serializers.IntegerField(allow_null=True),
        'data': LEARNING_OBJECT_FILE_ERRORS_RESPONSE,
    },
)
LEARNING_OBJECT_FILE_MESSAGE_RESPONSE = inline_serializer(
    name='LearningObjectFileMessageResponse',
    fields={
        'message': serializers.CharField(),
        'code': serializers.IntegerField(required=False),
        'status': serializers.IntegerField(required=False),
        'data': serializers.JSONField(required=False),
    },
)
LEARNING_OBJECT_OER_RESPONSE = inline_serializer(
    name='LearningObjectOerAdaptResponse',
    fields={
        'message': serializers.CharField(),
        'status': serializers.IntegerField(),
        'data': serializers.JSONField(required=False),
    },
)


@extend_schema_view(
    list=extend_schema(
        tags=LEARNING_OBJECT_FILE_TAG,
        summary='Listar archivos OA cargados',
        description='Lista registros `LearningObjectFile`. En el flujo normal se usa principalmente para administracion o depuracion.',
        responses={200: LearningObjectSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=LEARNING_OBJECT_FILE_TAG,
        summary='Consultar archivo OA cargado',
        description='Devuelve el registro del archivo comprimido, su URL de preview, tamanio, carpeta extraida y datos de integracion OER si existen.',
        parameters=[LEARNING_OBJECT_FILE_ID_PARAMETER],
        responses={200: LearningObjectSerializer, 404: OpenApiResponse(description='Archivo OA no encontrado.')},
    ),
    create=extend_schema(
        tags=LEARNING_OBJECT_FILE_TAG,
        summary='Cargar archivo ZIP de objeto de aprendizaje',
        description=(
            'Recibe un paquete ZIP IMS/SCORM cargado por un docente, lo guarda, lo extrae, lee el manifest, '
            'busca el archivo inicial de preview y devuelve la metadata detectada. Si falla la validacion, '
            'revierte el registro y limpia archivos temporales asociados.'
        ),
        request=LearningObjectSerializer,
        responses={
            200: LEARNING_OBJECT_FILE_UPLOAD_RESPONSE,
            400: OpenApiResponse(description='Payload invalido.'),
            404: LEARNING_OBJECT_FILE_MESSAGE_RESPONSE,
        },
    ),
    update=extend_schema(
        tags=LEARNING_OBJECT_FILE_TAG,
        summary='Actualizar registro de archivo OA',
        description='Actualiza completamente el registro `LearningObjectFile`. No ejecuta el flujo de extraccion inicial.',
        request=LearningObjectSerializer,
        responses={200: LearningObjectSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    partial_update=extend_schema(
        tags=LEARNING_OBJECT_FILE_TAG,
        summary='Actualizar parcialmente registro de archivo OA',
        description='Permite modificar campos puntuales del registro `LearningObjectFile`.',
        request=LearningObjectSerializer,
        responses={200: LearningObjectSerializer, 400: OpenApiResponse(description='Payload invalido.')},
    ),
    destroy=extend_schema(
        tags=LEARNING_OBJECT_FILE_DELETE_TAG,
        summary='Eliminar registro de archivo OA',
        description='Elimina el registro del archivo OA usando la operacion estandar del ViewSet.',
        parameters=[LEARNING_OBJECT_FILE_ID_PARAMETER],
        responses={204: OpenApiResponse(description='Archivo OA eliminado.')},
    ),
)
class LearningObjectModelViewSet(viewsets.ModelViewSet):
    """Endpoint principal para cargar un nuevo paquete OA comprimido."""

    permission_classes = [IsAuthenticated, IsTeacherUser]
    serializer_class = LearningObjectSerializer
    queryset = LearningObjectFile.objects.all()

    def create(self, request, *args, **kwargs):
        """Carga un ZIP IMS/SCORM, extrae su metadata y genera preview inicial."""

        global booleanLomLomes

        errorsFeedback={ "media":False,"scorm":False,"web":False, "is_exelearning":False}

        data = any
        serializer = LearningObjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        learningObject = LearningObjectFile.objects.create(
            file=serializer.validated_data['file']
        )
        # Nombre base de respaldo si falla el parseo antes de generar uno dinámico.
        file_name = str(serializer.validated_data['file']).split('.')[0]

        now = datetime.now()
        total_time = timedelta(
            hours=now.hour,
            minutes=now.minute,
            seconds=now.second
        )
        try:
            seconds = int(total_time.total_seconds())
            settings_dir = os.path.dirname(__file__)
            PROJECT_ROOT = os.path.abspath(os.path.dirname(settings_dir))
            file = zipfile.ZipFile(serializer.validated_data['file'], 'r')
            size = sum([zinfo.file_size for zinfo in file.filelist])
            zip_kb = float(size) / 1000  # kB
            vec = file.namelist()
            nombre_oa=str(request.data['file'])
            nombre = nombre_oa.split('.')
            file_name = nombre[0]
            file_name = "%s%s" % (file_name, str(seconds))
            folder_area = "catalog"
            dir_aux = file_name + "/"
            filename = ""
            url = ""
            listNames = [];
            nommbreak = ""

            file, dir_aux, folder_area, file_name, vec, listNames = method_extract_zip_file(file, dir_aux, folder_area, file_name, vec)
            request_host = self.request._current_scheme_host
            filename_index, filename, url = search_file_index(request_host, listNames, folder_area, file_name)

            XMLFILES_FOLDER = filename

            if get_index_imsmanisfest(XMLFILES_FOLDER) != '':
                index = get_index_imsmanisfest(XMLFILES_FOLDER)
            elif get_index_file(filename_index) != '':
                index = get_index_file(filename_index)
                if index.find('website_index.html') == -1:
                    errorsFeedback['web'] = True
                if index.find('index.html') != -1:
                    if verify_that_oa_was_made_exelearning(
                        os.path.join(filename_index, 'imsmanifest.xml').replace('\\','/')
                    ):
                        errorsFeedback['is_exelearning'] = True

            else:
                delete_new_learning_object_fail(file_name, learningObject)
                errorsFeedback['scorm'] = True
                return Response({"message": "Objeto de Aprendizaje aceptados por el repositorio es IMS y SCORM",
                                 "data":errorsFeedback},
                                status=HTTP_404_NOT_FOUND);

            # Condicion para saber si el archivo de metadatos es lom o lomes
            data = get_metadata_imsmanisfest(XMLFILES_FOLDER)

            path_origin_verify = path_origin_check(file_name)

            if XMLFILES_FOLDER is not None:
                URL = url + index
                #URL.replace('http://', 'https://', 1)
                learningObject.url = URL
                learningObject.file_name = nombre[0]
                learningObject.file_size = zip_kb
                learningObject.path_origin = path_origin_verify
                learningObject.save()
            else:
                return Response({"message": "No se encontro metadatos en el Objeto de Aprendizaje"},
                                status=HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception("Error procesando el zip del objeto de aprendizaje")
            delete_new_learning_object_fail(file_name, learningObject)
            errorsFeedback['scorm'] = True
            return Response({"message": "Objetos de Aprendizaje aceptados por el repositorio es IMS y SCORM.","data":errorsFeedback},
                            status=HTTP_404_NOT_FOUND)
        count_tag = None
        try:
            count_tag = generate_preview_information(learningObject, url)
        except Exception as e:
            logger.exception("Error generando informacion de previsualización del objeto de aprendizaje")
            delete_new_learning_object_fail(file_name, learningObject)
            errorsFeedback['media'] = True
            return Response({"message": "Existen problemas con el contenido multimedia.","data":errorsFeedback}, status=HTTP_404_NOT_FOUND);

        serializer = LearningObjectSerializer(learningObject)
        metadata = {
            "metadata": data,
            "oa_file": serializer.data,
            "tag_count": count_tag,
            "data": errorsFeedback
        }
        return Response(metadata, status=HTTP_200_OK)

def delete_new_learning_object_fail(file_name, learningObject):
    """Revierte archivos y registro cuando falla la carga inicial del OA."""

    zip_file_path = None
    try:
        # Ruta física real del archivo en almacenamiento local.
        zip_file_path = learningObject.file.path
    except Exception:
        zip_file = str(learningObject.file)
        zip_file_path = os.path.join(settings.MEDIA_ROOT, zip_file.replace('/', os.sep))

    catalog_path = os.path.join(settings.MEDIA_ROOT, 'catalog', file_name)
    try:
        remove(str(zip_file_path))
    except Exception as e:
        pass

    try:
        rmtree(str(catalog_path))
    except Exception as e:
        pass
    learningObject.delete()

def method_extract_zip_file(file, dir_aux, folder_area, file_name, vec):
    """Extrae el ZIP recibido en el almacenamiento local del repositorio."""


    for archi in sorted(file.namelist()):
        listNames = []
        if archi.find(dir_aux) == -1:
            pathFiles = url_base_media_from_local(True, folder_area, file_name)
        else:
            pathFiles = url_base_media_from_local(False, folder_area, file_name)

        file.extract(archi, pathFiles)

        for nom in vec:
            if nom.endswith(".xml"):
                listNames.append(nom)
    file.close()

    return file, dir_aux, folder_area, file_name, vec, listNames

def extract_zip_file(path, file_name, file):
    """Extrae un ZIP en una ruta concreta preservando la carpeta de origen.
    :param path:
        :param file_name:
        :param file:
        :return:
        """
    var_name = os.path.join(path, file_name)
    if var_name.find('.zip.zip') >= 0:
        test_file_aux = file_name.split('.')[0]
        test_file_aux = test_file_aux.rstrip(".zip")
    else:
        test_file_aux = file_name.split('.')[0]

    directory_origin = os.path.join(path, file_name.split('.')[0], test_file_aux + "_origin")

    with zipfile.ZipFile(file, 'r') as zip_file:
        zip.printdir()
        zip_file.extractall(directory_origin)

def url_base_media_from_local(identify, folder_area,file_name):
    """Resuelve la ruta base donde se descomprime el OA en almacenamiento local."""
    if identify == True:
            pathFiles = os.path.join(settings.MEDIA_ROOT, folder_area, file_name)
    else:
            pathFiles = os.path.join(settings.MEDIA_ROOT)

    return pathFiles

def path_origin_check(file_name):
    """Construye la carpeta local donde queda extraído el OA."""

    return os.path.join(settings.MEDIA_ROOT, 'catalog', file_name)

def generate_preview_information(learningObject, url):
    """Calcula conteos y recursos de preview a partir del contenido extraído."""
    # pocedemos a leer los recursos que tiene el objeto de aprendizaje
    count_general_paragaph, count_general_img, count_general_audio, count_general_video = read_html_files(
        learningObject.path_origin)

    # Lectura del archivo índex para buscar si está adaptado por la herramienta Oeradap
    is_adapted_oer = False
    try:
        with open(os.path.join(learningObject.path_origin, 'index.html')) as file:
            is_adapted_oer = look_for_class_oeradap(os.path.join(learningObject.path_origin, 'index.html'))
    except FileNotFoundError:
        logger.warning('No existe el archivo índex en la carpeta raíz del OA')

    url_img_prev = os.path.join(learningObject.path_origin, 'img-prev.png')
    url_request_host = os.path.join(url, 'img-prev.png')
    url_img_preview = os.path.exists(url_img_prev)

    # Verificamos si existe la imagen de previsualización
    if url_img_preview:
        uuid = str(shortuuid.ShortUUID().random(length=8))
        name = str('img-prev.png')
    else:
        name = ''
        url_request_host = ''

    array_paths_img_view = generaye_array_paths_img(learningObject.path_origin, url)
    count_tag = {
        'paragraph': count_general_paragaph,
        'img': count_general_img,
        'video': count_general_video,
        'audio': count_general_audio,
        'is_adapted_oer': is_adapted_oer,
        "paths_img_preview": array_paths_img_view,
        'img_prev': {
            'exist': url_img_preview,
            'url_img': url_request_host,
            'name': name
        },
    }
    return count_tag
# Funciones para leer los metadatos

def upload_file(_filepath):
    """Carga y normaliza el manifest XML para identificar su perfil."""

    global booleanLomLomes

    _profile = None
    xml_manifest = None

    redundant_elements = [' uniqueElementName="general"', ' uniqueElementName="catalog"', ' uniqueElementName="entry"',
                          ' uniqueElementName="aggregationLevel"', ' uniqueElementName="role"',
                          ' uniqueElementName="dateTime"',
                          ' uniqueElementName="source"', ' uniqueElementName="value"',
                          ' uniqueElementName="metaMetadata"',
                          ' uniqueElementName="rights"', ' uniqueElementName="access"',
                          ' uniqueElementName="accessType"',
                          ' uniqueElementName="source"', ' uniqueElementName="value"', 'uniqueElementName="lifeCycle"',
                          'uniqueElementName="technical"']

    xml_manifest = FileController.read_manifest(_filepath)
    for redundant in redundant_elements:
        xml_manifest = xml_manifest.replace(redundant, '')
    doc = minidom.parse(_filepath)
    childTag = doc.firstChild.tagName
    if (childTag == "lom"):
        booleanLomLomes = True
    elif (childTag == "lomes:lom"):
        booleanLomLomes = False
    else:
        logger.error('El archivo no contiene metadatos reconocibles')

    if xml_manifest == -1:
        _profile = 'IMS'
    elif xml_manifest != -1:
        _profile = 'SCORM'
    else:
        logger.error('El archivo no contiene imslrm.xml ni imsmanifest.xml')
        return None
    if xml_manifest is not None:
        logger.info("Manifest con datos")
    else:
        logger.error('Error intentando parsear el imsmanifest.xml')

    return _profile, _filepath, booleanLomLomes, xml_manifest

def read_file(filepath, profile):
    """Parsea el manifest ya localizado y devuelve la estructura cargada."""

    redundant_elements = [' uniqueElementName="general"', ' uniqueElementName="catalog"', ' uniqueElementName="entry"',
                          ' uniqueElementName="aggregationLevel"', ' uniqueElementName="role"',
                          ' uniqueElementName="dateTime"',
                          ' uniqueElementName="source"', ' uniqueElementName="value"',
                          ' uniqueElementName="metaMetadata"',
                          ' uniqueElementName="rights"', ' uniqueElementName="access"',
                          ' uniqueElementName="accessType"',
                          ' uniqueElementName="source"', ' uniqueElementName="value"', 'uniqueElementName="lifeCycle"',
                          'uniqueElementName="technical"']

    from_lompad = False
    if profile == 'SCORM':
        xml_manifest = FileController.read_manifest(filepath)
        for redundant in redundant_elements:
            xml_manifest = xml_manifest.replace(redundant, '')
        xml_manifest = xml_manifest.replace('lom:', '')
        logger.info("xml correcto")
    else:
        xml_manifest = FileController.read_manifest(filepath)
        for redundant in redundant_elements:
            xml_manifest = xml_manifest.replace(redundant, '')
        xml_manifest = xml_manifest.replace('lom:', '')

    if xml_manifest == -1:
        xml_manifest = FileController.read_manifest(filepath)
        for redundant in redundant_elements:
            xml_manifest = xml_manifest.replace(redundant, '')
        xml_manifest = xml_manifest.replace('lom:', '')
        from_lompad = True

    if xml_manifest == -1:
        logger.error('Archivo de metadatos no encontrado o corrupto')

    if not from_lompad:
        load = FileController.load_recursive_model(xml_manifest, booleanLomLomes, filepath)
        return load, xml_manifest
    else:
        load = FileController.load_recursive_model(xml_manifest, filepath, is_lompad_exported=True)
        return load, xml_manifest

def get_metadata_imsmanisfest(filename):
    """Devuelve la metadata del manifest en formato JSON serializado."""

    global booleanLomLomes
    profile, filepath, booleanLomLomes, xml_manifest = upload_file(filename.replace('\\', '/'))
    load, xml_manifest = read_file(filepath, profile)
    import json
    json_object = json.dumps(load, indent=4, ensure_ascii=False)
    return json_object

def get_metadata_imsmanisfest1(filename):
    """Parser legacy con BeautifulSoup para manifests LOM clásicos."""

    general = {}
    lifecycle = {}
    metaMetadata = {}
    technical = {}
    educational = {}
    rights = {}
    relation = {}
    annotation = {}
    classification = {}
    accesibility = {}
    if (filename.endswith('.xml')):
        soup = bs(open(filename, 'r', encoding="utf-8"), 'lxml')
        for lom in soup.find_all('lom'):
            _general = lom.find('general')
            general = {
                'identifier': {
                    'catalog': validateData(_general.find('identifier').find('catalog')).replace('\n', ''),
                    'entry': validateData(_general.find('identifier').find('entry')).replace('\n', ''),
                },
                'title': validateData(_general.find('title')).replace('\n', ''),
                'language': validateData(_general.find('language')).replace('\n', ''),
                'description': validateData(_general.find('description')).replace('\n', ''),
                'keyword': validateData(_general.find('keyword')).replace('\n', ', '),
                'coverage': validateData(_general.find('coverage')).replace('\n', ''),
                'structure': validateData(_general.find('structure').find('value')).replace('\n', ''),
                'aggregationLevel': validateData(_general.find('aggregationlevel').find('value')).replace('\n', ''),

            }
            _lifecycle = lom.find('lifecycle')
            lifecycle = {
                'version': validateData(_lifecycle.find('version')).replace('\n', ''),
                'status': validateData(_lifecycle.find('status').find('value')).replace('\n', ''),
                'contribute': {
                    'role': validateData(_lifecycle.find('contribute').find('role').find('value')).replace('\n', ''),
                    'entity': validateData(_lifecycle.find('contribute').find('entity')).replace('\n', ' '),
                    'date': {
                        'datetime': validateData(_lifecycle.find('contribute').find('date').find('datetime')).replace(
                            '\n', ''),
                        'description': validateData(
                            _lifecycle.find('contribute').find('date').find('description')).replace('\n', ''),
                    },
                },
            }

            _metaMetadata = lom.find('metametadata')
            metaMetadata = {
                'identifier': {
                    'catalog': validateData(_metaMetadata.find('identifier').find('catalog')).replace('\n', ''),
                    'entry': validateData(_metaMetadata.find('identifier').find('entry')).replace('\n', '')
                },
                'contribute': {
                    'role': validateData(_metaMetadata.find('contribute').find('role').find('value')).replace('\n', ''),
                    'entity': validateData(_metaMetadata.find('contribute').find('entity')).replace('\n', ''),
                    'date': {
                        'datetime': validateData(
                            _metaMetadata.find('contribute').find('date').find('datetime')).replace('\n', ''),
                        'description': validateData(
                            _metaMetadata.find('contribute').find('date').find('description')).replace('\n', ''),
                    },
                    'metadataSchema': validateData(_metaMetadata.find('metadataschema')).replace('\n', ''),
                    'language': validateData(_metaMetadata.find('language')).replace('\n', ''),
                }
            }
            _technical = lom.find('technical')
            technical = {
                'format': validateData(_technical.find('format')).replace('\n', ''),
                'size': validateData(_technical.find('size')).replace('\n', ''),
                'location': validateData(_technical.find('location')).replace('\n', ''),
                'requirement': validateData(_technical.find('requirement').find('value')).replace('\n', ''),
                'installationRemarks': validateData(_technical.find('installationremarks')).replace('\n', ''),
                'otherPlatformRequirements': validateData(_technical.find('otherplatformrequirements')).replace('\n',
                                                                                                                ''),
                'duration': validateData(_technical.find('duration')).replace('\n', ''),

            }
            _educational = lom.find('educational')
            educational = {
                'interactivityType': validateData(_educational.find('interactivitytype')).replace('\n', ''),
                'learningResourceType': validateData(_educational.find('learningresourcetype').find('value')).replace(
                    '\n', ''),
                'interactivityLevel': validateData(_educational.find('interactivitylevel').find('value')).replace('\n',
                                                                                                                  ''),
                'semanticDensity': validateData(_educational.find('semanticdensity').find('value')).replace('\n', ''),
                'intendedEndUserRole': validateData(_educational.find('intendedenduserrole').find('value')).replace(
                    '\n', ''),
                'context': validateData(_educational.find('context').find('value')).replace('\n', ''),
                'typicalAgeRange': validateData(_educational.find('typicalagerange')).replace('\n', ''),
                'difficulty': validateData(_educational.find('difficulty').find('value')).replace('\n', ''),
                'typicalLearningTime': {
                    'duration': validateData(_educational.find('typicallearningtime').find('duration')).replace('\n',
                                                                                                                ''),
                    'description': validateData(_educational.find('typicallearningtime').find('description')).replace(
                        '\n', ''),
                },
                'description': validateData(_educational.find_all('description')[-1].find('string')).replace('\n', ''),
                'language': validateData(_educational.find('language')).replace('\n', ''),
            }
            _rights = lom.find('rights')
            rights = {
                'cost': validateData(_rights.find('cost').find('value')).replace('\n', ''),
                'copyrightAndOtherRestrictions': validateData(
                    _rights.find('copyrightandotherrestrictions').find('value')).replace('\n', ''),
                'description': validateData(_rights.find('description')).replace('\n', ''),
            }
            _relation = lom.find('relation')
            relation = {
                'kind': validateData(_relation.find('kind').find('value')).replace('\n', ''),
                'resource': {
                    'identifier': {
                        'catalog': validateData(_relation.find('identifier').find('catalog')).replace('\n', '')
                    },
                    'description': validateData(_relation.find('description')).replace('\n', ''),
                },
            }
            _annotation = lom.find('annotation')
            annotation = {
                'entity': validateData(_annotation.find('entity')).replace('\n', ''),
                'date': {
                    'datetime': validateData(_annotation.find('date').find('datetime')).replace('\n', ''),
                    'description': validateData(_annotation.find('date').find('description')).replace('\n', ''),
                },
                'description': validateData(_annotation.find_all('description')[-1]).replace('\n', ''),
                'modeaccess': validateData(_annotation.find('modeaccess').find('value')).replace('\n', ''),
                'modeaccesssufficient': validateData(_annotation.find('modeaccesssufficient').find('value')).replace(
                    '\n', ''),
                'Rol': validateData(_annotation.find('rol').find('value')).replace('\n', ''),
            }
            _classification = lom.find('classification')
            classification = {
                'purpose': validateData(_classification.find('purpose').find('value')).replace('\n', ''),
                'taxonPath': {
                    'source': validateData(_classification.find('taxonpath').find('source')).replace('\n', ''),
                    'taxon': validateData(_classification.find('taxonpath').find('taxon').find('entry')).replace('\n',
                                                                                                                 ''),
                },
                'description': validateData(_classification.find('description')).replace('\n', ''),
                'keyword': validateData(_classification.find('keyword')).replace('\n', ', '),
            }
            _accesibility = lom.find('accesibility')
            accesibility = {
                'description': validateData(_accesibility.find('description')).replace('\n', ''),
                'accessibilityfeatures': validateDataBr(
                    _accesibility.find('accessibilityfeatures').find('resourcecontent')),
                'accessibilityhazard': validateDataBr(_accesibility.find('accessibilityhazard').find('properties')),
                'accessibilitycontrol': validateDataBr(_accesibility.find('accessibilitycontrol').find('methods')),
                'accessibilityAPI': validateDataBr(_accesibility.find('accessibilityapi').find('compatibleresource')),
            }
            return {
                'general': general,
                'lifecycle': lifecycle,
                'metaMetadata': metaMetadata,
                'technical': technical,
                'educational': educational,
                'rights': rights,
                'relation': relation,
                'annotation': annotation,
                'classification': classification,
                'accesibility': accesibility,
            }
from bs4 import BeautifulSoup

def get_metadata_imsmanisfest_normal(filename):
    """Parser alterno y más simple para manifests XML legacy."""

    general = {}
    lifecycle = {}
    metaMetadata = {}
    technical = {}
    educational = {}
    rights = {}
    relation = {}
    annotation = {}
    classification = {}
    accesibility = {}
    with open(filename, 'r', encoding="utf-8") as myfile:
        jsondoc = xmltodict.parse(myfile.read())
        data = jsondoc['manifest']
        res = BeautifulSoup(jsondoc)
    return jsondoc

def validateData(data):
    """Extrae texto de un nodo BeautifulSoup o devuelve un placeholder."""

    if data:
        return data.text
    else:
        return "No existe valor"

def validateDataBr(data):
    """Extrae texto reemplazando saltos HTML `<br>` por comas visibles."""

    if data:
        for dat in data.select("br"):
            dat.replace_with("\n")
        dataResponse = data.text.replace('\n', ', ')
        return dataResponse[2:len(dataResponse)]
    else:
        return "No existe valor"

def get_index_file(filepath):
    """Busca un `index.html` o `excursion.html` dentro del OA extraído."""

    file = ""
    index_path = ""
    index_url = ""
    if (filepath != ''):

        for file in os.listdir(filepath):
            if file.endswith("index.html") or file.endswith("excursion.html"):
                index_path = file
        if index_path != "":
            index_url = index_path
        else:
            return Response({"message": "Ocurrio un error al cargar el Objeto de Aprendizaje"})
    return index_url

def get_index_imsmanisfest(filename):
    """Lee el primer recurso listado en el manifest IMS."""

    content = []
    result = ""
    try:
        if (filename[:-1] != BASE_DIR):
            with open(filename, "r") as file:
                content = file.readlines()
                content = "".join(content)
                bs_content = bs(content, "lxml")
                resource = bs_content.find_all("file")
                if bs_content.find_all("file"):
                    result = resource[0]['href']
                else:
                    result = ""
    except Exception as e:
        logger.exception("Error al leer el archivo method1")
    return result

def folder_name(value):
    """Normaliza nombres de áreas a slugs de carpeta heredados."""

    return {
        "Programas generales": "Programas-generales",
        "Educación": "Educacion",
        "Humanidades y artes": "Humanidades-y-artes",
        "Ciencias sociales, educación comercial y derecho": "Ciencias-socilaes-educacion-comercial-derecho",
        "Ciencias": "Ciencias",
        "Ingeniería, industria y construcción": "Ingenieria-industrial-construccion",
        "Agricultura": "Agricultura",
        "Salud y servicios sociales": "Salud-servicios-sociales",
        "Servicios": "Servicios",
        "Sectores desconocidos no especificados": "Otros"
    }[value]

@extend_schema_view(
    destroy=extend_schema(
        tags=LEARNING_OBJECT_FILE_DELETE_TAG,
        summary='Eliminar OA cargado por docente',
        description=(
            'Elimina un archivo de objeto de aprendizaje cargado por el docente autenticado. '
            'Tambien intenta borrar la metadata asociada, el ZIP, el avatar y la carpeta extraida del catalogo local.'
        ),
        parameters=[LEARNING_OBJECT_FILE_ID_PARAMETER],
        responses={
            200: LEARNING_OBJECT_FILE_MESSAGE_RESPONSE,
            400: LEARNING_OBJECT_FILE_MESSAGE_RESPONSE,
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol docente.'),
        },
    )
)
class DeleteLearningObjectViewSet(viewsets.ViewSet):
    """Permite al docente eliminar uno de sus archivos OA cargados."""

    permission_classes = [IsAuthenticated, IsTeacherUser]

    def destroy(self, request, pk=None):
        """Elimina el archivo OA y su metadata asociada si existe."""

        is_not_metadata = False
        learning_object_metadata_instance = None
        learning_object_instance = None
        learning_object_instance = LearningObjectFile.objects.get(pk=pk)

        try:
            learning_object_metadata_instance = LearningObjectMetadata.objects.get(
                learning_object_file_id=learning_object_instance.id)
        except Exception as e:
            is_not_metadata = True

        response = deleteLearningObjectsFile(learning_object_metadata_instance,learning_object_instance,is_not_metadata)
        if response == True:
                learning_object_instance.delete()
                return Response({'message': 'Record deleted successfully', 'code': 200}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Error trying to delete record not found'}, status=status.HTTP_400_BAD_REQUEST)

#Importamos las clases para la mensajería
mail_delete_oa = SendMail()
@extend_schema_view(
    destroy=extend_schema(
        tags=LEARNING_OBJECT_FILE_DELETE_TAG,
        summary='Eliminar OA desde administracion',
        description=(
            'Elimina un OA desde administracion usando el identificador de metadata. '
            'Ademas limpia archivos fisicos y envia un correo al docente con el motivo recibido en `message`.'
        ),
        parameters=[LEARNING_OBJECT_FILE_ID_PARAMETER, LEARNING_OBJECT_FILE_DELETE_MESSAGE_PARAMETER],
        responses={
            200: LEARNING_OBJECT_FILE_MESSAGE_RESPONSE,
            400: LEARNING_OBJECT_FILE_MESSAGE_RESPONSE,
            401: OpenApiResponse(description='No autenticado.'),
            403: OpenApiResponse(description='Requiere rol administrador.'),
        },
    )
)
class DeleteLearningObjectViewSetAdmin(viewsets.ViewSet):
    """Permite a administración eliminar un OA y notificar el motivo."""

    permission_classes = [IsAuthenticated, IsAdministratorUser]

    def destroy(self, request, pk=None):
        """Elimina un OA desde metadata y notifica al docente propietario.

        El `pk` recibido aquí corresponde al registro de metadata, no al
        registro de `LearningObjectFile`.
        """

        is_not_metadata = False
        learning_object_metadata_instance = None
        learning_object_instance = None
        message_body = request.query_params.get('message')
        title_oa = ''
        user_data = None

        try:
            learning_object_metadata_instance = LearningObjectMetadata.objects.get(
                pk=pk)
            title_oa = learning_object_metadata_instance.general_title
            user_data = User.objects.get(id=learning_object_metadata_instance.user_created_id)
            learning_object_instance = LearningObjectFile.objects.get(pk=learning_object_metadata_instance.learning_object_file_id)

        except Exception as e:
            is_not_metadata = True

        response = deleteLearningObjectsFile(learning_object_metadata_instance,learning_object_instance,is_not_metadata)
        if response == True:
                mail_delete_oa.sendMailDeleteOA(user_data.email, user_data.first_name, title_oa, message_body)
                learning_object_instance.delete()
                return Response({'message': 'Record deleted successfully', 'code': 200}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Error trying to delete record not found'}, status=status.HTTP_400_BAD_REQUEST)

def deleteLearningObjectsFile(learning_object_metadata_instance,learning_object_instance,is_not_metadata):
    """Elimina avatar, ZIP y carpeta extraída asociados a un OA."""

    if (learning_object_metadata_instance or learning_object_instance):
        avatar = ''
        avatar_path = None
        if is_not_metadata == False:
            try:
                avatar = str(learning_object_metadata_instance.avatar)
                avatar_path = os.path.join(BASE_DIR, 'media', avatar.replace('/', '\\'))
            except Exception as e:
                avatar = ''
                avatar_path = None
        zip_file = str(learning_object_instance.file)
        zip_file_path = os.path.join(BASE_DIR, 'media', zip_file.replace('/', '\\'))
        path_origin = os.path.join(learning_object_instance.path_origin)

        if learning_object_instance.path_origin and zip_file_path:
            if avatar != '' and avatar_path != None:
                try:
                    remove(str(avatar_path.replace('\\', '/')))
                except Exception as e:
                    pass
            try:
                remove(str(zip_file_path.replace('\\', '/')))
            except Exception as e:
                pass
            try:
                rmtree(str(path_origin.replace('\\', '/')))
            except Exception as e:
                pass
            return True
        else:
            return Response({'message': 'Error loading routes'}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema_view(
    post=extend_schema(
        tags=LEARNING_OBJECT_OER_TAG,
        summary='Crear o refrescar OA desde OER Adapt',
        description=(
            'Recibe datos enviados por OER Adapt para crear una copia integrada del OA o actualizar el ZIP ya integrado. '
            'Valida la llave publica del usuario, descarga el ZIP remoto y mantiene la referencia de retorno hacia ROA/OER.'
        ),
        request=LearningObjectOerAdapt,
        responses={
            200: LEARNING_OBJECT_OER_RESPONSE,
            400: LEARNING_OBJECT_OER_RESPONSE,
        },
    )
)
class getDataNewLearningObject(APIView):
    """Integra o actualiza un OA proveniente desde OER Adapt."""

    permission_classes = [AllowAny]
    def post(self, request):
        """Crea o refresca un OA integrado según el identificador recibido."""

        serializer = LearningObjectOerAdapt(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_exist = validate_user_key(serializer['key'].value)

        if user_exist == False:
            return Response({'message':'The user key is incorrect', 'code':400}, status=status.HTTP_400_BAD_REQUEST)
        learning_object = LearningObjectFile.objects.filter(pk=serializer['IdOa'].value)
        if len(learning_object) == 1 and learning_object[0].oa_integration_id == None:
            is_crete, message_method = create_and_register_new_learning_object(request,self.request._current_scheme_host)
            if is_crete is False:
                return Response({'message':message_method,'status':400}, status=status.HTTP_400_BAD_REQUEST)
            else:
                request.data['roa_ref_url']='https://repositorio.edutech-project.org/#/settings/my-objects'
                return Response({'message': message_method,'status':200, 'data':request.data}, status=status.HTTP_200_OK)
        elif len(learning_object) == 1 and learning_object[0].oa_integration_id != None:
            learning_object_integration = LearningObjectFile.objects.filter(pk=learning_object[0].oa_integration_id)
            file_path_oa_zip =os.path.abspath(os.path.join(_settings.MEDIA_ROOT,str(learning_object_integration[0].file)))
            file_path_catalog = learning_object_integration[0].path_origin
            try:
                data_request=requests.get(request.data['urlZip'])
                with data_request as r:
                    with open(file_path_oa_zip, 'wb') as f:
                       f.write(r.content)

                with zipfile.ZipFile(file_path_oa_zip,'r') as zipfile:
                    zipfile.extractall(file_path_catalog)
                    zipfile.close()
            except Exception as e:
                logger.exception("Error actualizando OA integrado desde OER")
                return Response({'message':e,'status':400}, status=HTTP_400_BAD_REQUEST)
            request.data['roa_ref_url'] = env('DOMAIN_HOST_OER')
            return Response({'message':'Updated successfully','status':200, 'data':request.data}, status=HTTP_200_OK)
        elif len(learning_object) == 0 :
            return Response({'message':'There is an error trying to save the learning object', 'status': 400, 'data':request.data}, status=HTTP_400_BAD_REQUEST)

from django.core.files.storage import default_storage

class funcionDeleteOldFolderAndRegisters(viewsets.ViewSet):
    """Limpia registros huérfanos y carpetas antiguas del catálogo local."""

    permission_classes = [AllowAny]
    def list(self, request):
        """Sincroniza disco y base eliminando carpetas/registros sin pareja."""

        learningObjects = LearningObjectFile.objects.all()
        for learnign in learningObjects:
            metadata = LearningObjectMetadata.objects.filter(learning_object_file_id=learnign.id)
            if len(metadata) == 0:
                zip_file = str(learnign.file.name)
                zip_file_path = os.path.join(BASE_DIR, 'media', zip_file.replace('/', '\\'))
                if learnign.path_origin is not None:
                    path_origin = os.path.join(learnign.path_origin)
                    if learnign.path_origin:
                        try:
                            rmtree(str(path_origin.replace('\\', '/')))
                        except Exception as e:
                            pass
                if zip_file_path:
                    try:
                        remove(str(zip_file_path.replace('\\', '/')))
                    except Exception as e:
                        pass
                learnign.delete()

        learningObjectsNewList = LearningObjectFile.objects.all()
        notDeleteFolders=[]
        contenido_catalog = os.listdir(os.path.join(BASE_DIR, 'media','catalog'))
        for fichero in contenido_catalog:
            for learningObject in learningObjectsNewList:
                longitudArrayLearning = len(learningObject.path_origin.split('\\')) - 1
                nameFolderLearningObject = learningObject.path_origin.split('\\')[longitudArrayLearning]
                if nameFolderLearningObject == fichero:
                    try:
                        if notDeleteFolders.index(fichero):
                           pass
                    except Exception as e:
                        notDeleteFolders.append(fichero)
        for ficheroSearch in contenido_catalog:
                try:
                    if notDeleteFolders.index(ficheroSearch):
                        pass
                except Exception as e:
                    try:
                        path_origin_delete = os.path.join(BASE_DIR,'media','catalog',ficheroSearch)
                        rmtree(str(path_origin_delete.replace('\\', '/')))
                    except Exception as e:
                        pass
        return Response({'message':'Delete folders and registers successfully'}, status= HTTP_200_OK)

@extend_schema_view(
    post=extend_schema(
        tags=LEARNING_OBJECT_OER_TAG,
        summary='Guardar datos de integracion OER',
        description=(
            'Persiste en `LearningObjectFile` las fechas, URLs de preview y enlace de OER Adapt devueltos por la integracion. '
            'El endpoint valida que el usuario exista por `user_key` y que el OA no tenga una integracion previa.'
        ),
        request=LearningObjectFileOerSerializer,
        responses={
            200: LEARNING_OBJECT_OER_RESPONSE,
            400: LEARNING_OBJECT_OER_RESPONSE,
        },
    )
)
class saveDataIntegrationWithOer(APIView):
    """Guarda metadatos de integración devueltos por OER Adapt."""

    permission_classes = [AllowAny]
    def post(self, request):
        """Persiste fechas, previews y URL de integración para un OA."""

        serializer = LearningObjectFileOerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            learning_object = LearningObjectFile.objects.get(pk=serializer['id'].value)
        except Exception as e:
            logger.exception("Error obteniendo LearningObjectFile para integración OER")
            return Response({'message':e,'status':400}, status=HTTP_400_BAD_REQUEST)

        error_status, message=validate_items_before_creating(serializer,learning_object)
        if error_status is True:
            return Response({'message': message, 'status': 400},status=HTTP_400_BAD_REQUEST)

        #procesos de guardado de datos para el objeto de aprendizaje
        learning_object.oa_created_at = serializer['data']['created_at'].value
        learning_object.oa_expires_at = serializer['data']['expires_at'].value
        learning_object.oa_preview_origin = serializer['data']['preview_origin'].value
        learning_object.oa_preview_adapted = serializer['data']['preview_adapted'].value
        learning_object.oa_oer_adap_url = serializer['data']['oer_adap'].value
        learning_object.save()
        return Response({'message':'The data was saved successfully', 'status':200,'data':request.data}, status=HTTP_200_OK)

def validate_items_before_creating(serializer,learning_object):
    """Valida precondiciones antes de crear una integración con OER."""

    if validate_user_key(serializer['user_key'].value) is False:
        return True,'Incorrect data, no action can be executed'
    elif learning_object.oa_integration_id is not None:
        return True,'Cannot create integration'
    elif learning_object.oa_created_at is not None:
        return True,'Cannot create integration'
    return False,''

def validate_user_key(key_user):
    """Comprueba si existe un usuario con la llave publica indicada."""

    user = User.objects.filter(user_key = key_user)
    if len(user) == 0:
        return False
    else:
        return True

def search_file_index(request_host,listNames,folder_area, file_name):
    """Localiza el manifest o índice principal y construye su URL base."""

    filename_index=''
    filename=''
    url=''
    files = ["imslrm.xml", "imsmanifest.xml", "imsmanifest_nuevo.xml", "catalogacionLomes.xml"]
    for fileName in files:
        if fileName in listNames and fileName in listNames:
            filename_index = os.path.join(settings.MEDIA_ROOT, folder_area, file_name)
            filename = os.path.join(settings.MEDIA_ROOT, folder_area, file_name, files[0])
            url = request_host + "/media/" + folder_area + "/" + file_name + "/"
            break
        if files[0] in listNames and files[1] not in listNames and files[2] not in listNames and files[
            3] not in listNames:
            filename_index = os.path.join(settings.MEDIA_ROOT, folder_area, file_name)
            filename = os.path.join(settings.MEDIA_ROOT, folder_area, file_name, files[0])
            url = request_host + "/media/" + folder_area + "/" + file_name + "/"
            break
        if files[0] not in listNames and files[1] in listNames and files[2] not in listNames and files[
            3] not in listNames:
            filename_index = os.path.join(settings.MEDIA_ROOT, folder_area, file_name)
            filename = os.path.join(settings.MEDIA_ROOT, folder_area, file_name, files[1])
            url = request_host + "/media/" + folder_area + "/" + file_name + "/"
            break
        if files[0] not in listNames and files[1] not in listNames and files[2] in listNames and files[
            3] not in listNames:
            filename_index = os.path.join(settings.MEDIA_ROOT, folder_area, file_name)
            filename = os.path.join(settings.MEDIA_ROOT, folder_area, file_name, files[2])
            url = request_host + "/media/" + folder_area + "/" + file_name + "/"
            break
        if files[0] not in listNames and files[1] not in listNames and files[2] not in listNames and files[
            3] in listNames:
            filename_index = os.path.join(settings.MEDIA_ROOT, folder_area, file_name)
            filename = os.path.join(settings.MEDIA_ROOT, folder_area, file_name, files[3])
            url = request_host + "/media/" + folder_area + "/" + file_name + "/"
            break
    return filename_index, filename, url

def read_and_extract_xml_and_zip(file,dir_aux,folder_area,file_name,vec):
    """Extrae el ZIP descargado y devuelve nombres XML detectados."""

    for archi in sorted(file.namelist()):
        listNames = []
        if archi.find(dir_aux) == -1:
            pathFiles = os.path.join(settings.MEDIA_ROOT, folder_area, file_name)
        else:
            pathFiles = os.path.join(settings.MEDIA_ROOT)
        file.extract(archi, pathFiles)
        for nom in vec:
            if nom.endswith(".xml"):
                listNames.append(nom)
                if archi.find(dir_aux) == -1:
                    path = os.path.join(settings.MEDIA_ROOT, folder_area, file_name)
                else:
                    path = os.path.join(settings.MEDIA_ROOT)
    return listNames, pathFiles

def variable_definition_Oa(file_path, file_name):
    """Prepara variables base para procesar un OA integrado desde ZIP."""

    settings_dir = os.path.dirname(__file__)
    PROJECT_ROOT = os.path.abspath(os.path.dirname(settings_dir))
    folder_area = "catalog"
    file = zipfile.ZipFile(file_path, 'r')
    file_name_oa = file_name.split('.')[0]
    dir_aux = file_name_oa + "/"
    vec = file.namelist()
    return file, dir_aux, folder_area, file_name_oa, vec, PROJECT_ROOT

def create_and_register_new_learning_object(request, host):
    """Descarga desde OER, crea el archivo OA y clona su metadata base."""

    file_name = request.data['urlZip'].split('/')[-1]
    file_response = requests.get(request.data['urlZip'])
    file_path = os.path.join(BASE_DIR, 'media', 'oazip', file_name)

    try:
        with open(file_path, 'wb') as f:
            f.write(file_response.content)

        sizefile = os.path.getsize(file_path)
        size = float(sizefile) / 1000  # kb
        path_learning_object = os.path.join('oazip', file_name)
        file, dir_aux, folder_area, file_name_oa, vec, PROJECT_ROOT = variable_definition_Oa(file_path, file_name)
        listNames, pathFiles = read_and_extract_xml_and_zip(file, dir_aux, folder_area, file_name_oa, vec)

        filename_index, filename, url = search_file_index(host, listNames, folder_area,file_name_oa)
        PROJECT_ROOT = os.path.abspath(os.path.dirname(PROJECT_ROOT))
        XMLFILES_FOLDER = os.path.join(PROJECT_ROOT, filename)

        if get_index_imsmanisfest(XMLFILES_FOLDER) != '':
            index = get_index_imsmanisfest(XMLFILES_FOLDER)
        elif get_index_file(filename_index) != '':
            index = get_index_file(filename_index)
        else:
            return Response({"message": "Objeto de Aprendizaje aceptados por el repositorio es IMS y SCORM"},
                            status=HTTP_404_NOT_FOUND)

        file_path_oa = os.path.join(BASE_DIR, 'media', 'catalog', file_name_oa)
        # Condicion para saber si el archivo de metadatos es lom o lomes
        object_metadata = get_metadata_and_evaluation(XMLFILES_FOLDER)
        learningObject=LearningObjectFile.objects.create(
                       file=path_learning_object.replace('\\','/'),
                       file_name=file_name_oa,
                       file_size=size,
                       path_origin=file_path_oa,
                       url=url+index
                       )
        
        #Volcado de datos para la tabla de metadatos
        create_metadata_learning_object(object_metadata, request.data['IdOa'],learningObject.id, pathFiles)
        return True, 'Saved successfully'
    except Exception as err:
        return False, err

def get_metadata_and_evaluation(XMLFILES_FOLDER):
    """Extrae solo los campos de metadata necesarios para OER Adapt."""

    data = get_metadata_imsmanisfest(XMLFILES_FOLDER)
    data_json = json.loads(data)
    accessibilityHazard = data_json['accesibility']['accessibilityHazard']['value']
    accessibilityFeature = data_json['accesibility']['accessibilityFeatures']['value']
    accessibilityControl = data_json['accesibility']['accessibilityControl']['value']
    accessMode = data_json['annotation']['accessmode']['value']
    accessModeSufficient = data_json['annotation']['accessmodesufficient']['value']
    alignment_types = data_json['classification']['purpose']['value']

    object_metadata = {
        'accessibilityHazard': ','.join(str(x) for x in accessibilityHazard),
        'accessibilityFeature': ','.join(str(x) for x in accessibilityFeature),
        'accessibilityControl': ','.join(str(x) for x in accessibilityControl),
        'accessMode': ','.join(str(x) for x in accessMode),
        'accessModeSufficient': ','.join(str(x) for x in accessModeSufficient),
        'alignment_types': ','.join(str(x) for x in alignment_types)
    }

    return object_metadata

def create_metadata_learning_object(object_metadata,id,new_learning_object_file_id,pathFiles):
    """Clona metadata existente a un nuevo `LearningObjectFile` integrado."""

    learning_object_metadata = LearningObjectMetadata.objects.filter(learning_object_file_id=id)
    learning_object_related = LearningObjectFile.objects.get(pk=id)
    learning_object_related.oa_integration_id = new_learning_object_file_id
    learning_object_related.save()
    #Copiamos la imagen de previsualización
    try:
        name_img = 'img-prev_' + generate_characters_random() + '.png'
        shutil.copy(os.path.abspath(os.path.join(pathFiles, 'img-prev.png')),
                    os.path.abspath(os.path.join(_settings.MEDIA_ROOT, 'avatar', name_img)))
    except Exception as e:
        return Response({'message':e, 'status':400},status=HTTP_400_BAD_REQUEST)

    new_learning_object_metadata = LearningObjectMetadata.objects.create(
        adaptation=learning_object_metadata[0].adaptation,
        avatar='avatar/'+name_img,
        author=learning_object_metadata[0].author,
        package_type=learning_object_metadata[0].package_type,
        general_catalog=learning_object_metadata[0].general_catalog,
        general_entry=learning_object_metadata[0].general_entry,
        general_title=learning_object_metadata[0].general_title,
        general_language=learning_object_metadata[0].general_language,
        general_description=learning_object_metadata[0].general_description,
        general_keyword=learning_object_metadata[0].general_keyword,
        general_coverage=learning_object_metadata[0].general_coverage,
        general_structure=learning_object_metadata[0].general_structure,
        general_aggregation_Level=learning_object_metadata[0].general_aggregation_Level,
        life_cycle_version=learning_object_metadata[0].life_cycle_version,
        life_cycle_status=learning_object_metadata[0].life_cycle_status,
        life_cycle_role=learning_object_metadata[0].life_cycle_role,
        life_cycle_entity=learning_object_metadata[0].life_cycle_entity,
        life_cycle_dateTime=learning_object_metadata[0].life_cycle_dateTime,
        life_cycle_description=learning_object_metadata[0].life_cycle_description,
        meta_metadata_catalog=learning_object_metadata[0].meta_metadata_catalog,
        meta_metadata_entry=learning_object_metadata[0].meta_metadata_entry,
        meta_metadata_role=learning_object_metadata[0].meta_metadata_role,
        meta_metadata_entity=learning_object_metadata[0].meta_metadata_entity,
        meta_metadata_dateTime=learning_object_metadata[0].meta_metadata_dateTime,
        meta_metadata_description=learning_object_metadata[0].meta_metadata_description,
        technical_format=learning_object_metadata[0].technical_format,
        technical_size=learning_object_metadata[0].technical_size,
        technical_location=learning_object_metadata[0].technical_location,
        technical_requirement_type=learning_object_metadata[0].technical_requirement_type,
        technical_requirement_name=learning_object_metadata[0].technical_requirement_name,
        technical_requirement_minimumVersion=learning_object_metadata[0].technical_requirement_minimumVersion,
        technical_installationRremarks=learning_object_metadata[0].technical_installationRremarks,
        technical_otherPlatformRequirements=learning_object_metadata[0].technical_otherPlatformRequirements,
        technical_dateTime=learning_object_metadata[0].technical_dateTime,
        technical_description=learning_object_metadata[0].technical_description,
        educational_interactivityType=learning_object_metadata[0].educational_interactivityType,
        educational_learningResourceType=learning_object_metadata[0].educational_learningResourceType,
        educational_interactivityLevel=learning_object_metadata[0].educational_interactivityLevel,
        educational_semanticDensity=learning_object_metadata[0].educational_semanticDensity,
        educational_intendedEndUserRole=learning_object_metadata[0].educational_intendedEndUserRole,
        educational_context=learning_object_metadata[0].educational_context,
        educational_typicalAgeRange=learning_object_metadata[0].educational_typicalAgeRange,
        educational_difficulty=learning_object_metadata[0].educational_difficulty,
        educational_typicalLearningTime_dateTime=learning_object_metadata[0].educational_typicalLearningTime_dateTime,
        educational_typicalLearningTime_description=learning_object_metadata[0].educational_typicalLearningTime_description,
        educational_description=learning_object_metadata[0].educational_description,
        educational_language=learning_object_metadata[0].educational_language,
        educational_procces_cognitve=learning_object_metadata[0].educational_procces_cognitve,
        rights_cost=learning_object_metadata[0].rights_cost,
        rights_copyrightAndOtherRestrictions=learning_object_metadata[0].rights_copyrightAndOtherRestrictions,
        rights_description=learning_object_metadata[0].rights_description,
        relation_kind=learning_object_metadata[0].relation_kind,
        relation_catalog=learning_object_metadata[0].relation_catalog,
        relation_entry=learning_object_metadata[0].relation_entry,
        relation_description=learning_object_metadata[0].relation_description,
        annotation_entity=learning_object_metadata[0].annotation_entity,
        annotation_date_dateTime=learning_object_metadata[0].annotation_date_dateTime,
        annotation_date_description=learning_object_metadata[0].annotation_date_description,
        annotation_description=learning_object_metadata[0].annotation_description,
        annotation_modeaccess=object_metadata['accessMode'],
        annotation_modeaccesssufficient=object_metadata['accessModeSufficient'],
        annotation_rol=learning_object_metadata[0].annotation_rol,
        classification_purpose=object_metadata['alignment_types'],
        classification_taxonPath_source=learning_object_metadata[0].classification_taxonPath_source,
        classification_taxonPath_taxon=learning_object_metadata[0].classification_taxonPath_taxon,
        classification_description=learning_object_metadata[0].classification_description,
        classification_keyword=learning_object_metadata[0].classification_keyword,
        accesibility_summary=learning_object_metadata[0].accesibility_summary,
        accesibility_features=object_metadata['accessibilityFeature'],
        accesibility_hazard=object_metadata['accessibilityHazard'],
        accesibility_control=object_metadata['accessibilityControl'],
        accesibility_api=learning_object_metadata[0].accesibility_api,
        slug=learning_object_metadata[0].slug,
        public=learning_object_metadata[0].public,
        education_levels_id=learning_object_metadata[0].education_levels_id,
        knowledge_area_id=learning_object_metadata[0].knowledge_area_id,
        learning_object_file_id=new_learning_object_file_id,
        license_id=learning_object_metadata[0].license_id,
        user_created_id=learning_object_metadata[0].user_created_id,
        source_file=learning_object_metadata[0].source_file,
        item_a5=learning_object_metadata[0].item_a5,
        item_i6=learning_object_metadata[0].item_i6,
        item_t3=learning_object_metadata[0].item_t3,
        item_t4=learning_object_metadata[0].item_t4,
        item_v1=learning_object_metadata[0].item_v1,
        item_v2=learning_object_metadata[0].item_v2,
        is_adapted_oer=True
    )
    automaticEvaluation(new_learning_object_metadata.id)

def generate_characters_random():
    """Genera un sufijo corto aleatorio para nombres auxiliares de archivos."""

    import string
    import random
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
