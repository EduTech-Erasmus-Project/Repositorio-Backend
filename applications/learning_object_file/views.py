from yaml import serialize

from applications.user.models import User
from rest_framework import viewsets
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

from ..helpers_functions.beautiful_soup_data import read_html_files, look_for_class_oeradap, generaye_array_paths_img
from roabackend.settings import DEBUG
from io import BytesIO
booleanLomLomes = True  # If booleanLomLomes is True represents a lom format, and
# if booleanLomLomes is False represents a lomes format.
from applications.learning_object_file.emailManagerLO import SendMail
#Para la coneccion con S3
import environ
env = environ.Env()
BASE_DIR = Path(__file__).ancestor(3)
#Set the project base directory
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


class LearningObjectModelViewSet(viewsets.ModelViewSet):
    # authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAuthenticated, IsTeacherUser]
    serializer_class = LearningObjectSerializer
    queryset = LearningObjectFile.objects.all()

    def create(self, request, *args, **kwargs):
        global booleanLomLomes
        """
        Servicio para cargar un OA comprimido y obtener los metadatos correspontientes al Objeto de Aprendizaje.
        Se necesita estar autenticado como docente.
        """
        #variable para manejo de errores
        errorsFeedback={ "media":False,"scorm":False,"web":False}

        data = any
        serializer = LearningObjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # file_path = os.path.join(BASE_DIR,'media',str(serializer.validated_data['file']))

        learningObject = LearningObjectFile.objects.create(
            file=serializer.validated_data['file']
            # file_name = serializer.validated_data['file_name'],
            # file_size = serializer.validated_data['file_size']
        )

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

            PROJECT_ROOT = os.path.abspath(os.path.dirname(PROJECT_ROOT))
            XMLFILES_FOLDER = os.path.join(PROJECT_ROOT, filename)

            if get_index_imsmanisfest(XMLFILES_FOLDER) != '':
                index = get_index_imsmanisfest(XMLFILES_FOLDER)
            elif get_index_file(filename_index) != '':
                index = get_index_file(filename_index)
                if index.find('website_index.html') == -1:
                    delete_new_learning_object_fail(file_name, learningObject)
                    errorsFeedback['web'] = True
                    return Response({"message": "Su objeto de aprendizaje no contiene los ficheros exportados como Sitio web ",
                                     "data": errorsFeedback},status=HTTP_404_NOT_FOUND)
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
                learningObject.url = URL.replace('http://', 'https://', 1)
                learningObject.file_name = nombre[0]
                learningObject.file_size = zip_kb
                learningObject.path_origin = path_origin_verify
                learningObject.save()
            else:
                return Response({"message": "No se encontro metadatos en el Objeto de Aprendizaje"},
                                status=HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)
            delete_new_learning_object_fail(file_name, learningObject)
            errorsFeedback['scorm'] = True
            return Response({"message": "Objetos de Aprendizaje aceptados por el repositorio es IMS y SCORM.","data":errorsFeedback},
                            status=HTTP_404_NOT_FOUND)
        count_tag = None
        try:
            count_tag = generate_preview_information(learningObject, url)
        except Exception as e:
            print(e)
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
    zip_file = str(learningObject.file)
    zip_file_path = os.path.join(BASE_DIR, 'media', zip_file.replace('/', '\\'))
    catalog_path = os.path.join(BASE_DIR, 'media','catalog',file_name)
    try:
        remove(str(zip_file_path.replace('\\', '/')))
    except Exception as e:
        pass

    try:
        rmtree(str(catalog_path.replace('\\', '/')))
    except Exception as e:
        pass
    learningObject.delete()

def method_extract_zip_file(file, dir_aux, folder_area, file_name, vec):
    """
        Metodo para extraer el archivo zip
        y guardarlo en S3 o media/ local
    """


    for archi in sorted(file.namelist()):
        listNames = []
        if archi.find(dir_aux) == -1:
            pathFiles = url_base_media_from_local(True, folder_area, file_name)
        else:
            pathFiles = url_base_media_from_local(False, folder_area, file_name)
            # pathFiles = url_base_media_from_s3_local(False, folder_area, file_name)

        file.extract(archi, pathFiles)

        for nom in vec:
            if nom.endswith(".xml"):
                listNames.append(nom)
                # if archi.find(dir_aux) == -1:
                #   path = os.path.join(_settings.MEDIA_ROOT + "/" + folder_area + "/" + file_name + "/")
                # else:
                #   path = os.path.join(_settings.MEDIA_ROOT + "/")
    file.close()

    return file, dir_aux, folder_area, file_name, vec, listNames

def extract_zip_file(path, file_name, file):
    """
        Extrae un archivo zip en una ruta determinada
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
    """
        Metodo para devolver las URLs, para descomprimir el OA validando las rutas locales
        o las rutas de S3 (Amazon)
    """
    if identify == True:
            pathFiles = os.path.join(_settings.MEDIA_ROOT + folder_area + "/" + file_name + "/")
    else:
            pathFiles = os.path.join(_settings.MEDIA_ROOT)

    return pathFiles

def path_origin_check(file_name):
    return os.path.join(BASE_DIR, 'media', 'catalog', file_name)

def generate_preview_information(learningObject, url):
    """
        Metodo que extrae informacion del objeto de aprendizaje
        , verifica si el objeto esta adaptado por la herramienta
        OerAdap
    """
    # pocedemos a leer los recursos que tiene el objeto de aprendizaje
    count_general_paragaph, count_general_img, count_general_audio, count_general_video = read_html_files(
        learningObject.path_origin)

    # Lectura del archivo index para buscar si esta adaptado por la herramienta Oeradap
    is_adapted_oer = False
    try:
        with open(os.path.join(learningObject.path_origin, 'index.html')) as file:
            is_adapted_oer = look_for_class_oeradap(os.path.join(learningObject.path_origin, 'index.html'))
        # No need to close the file
    except FileNotFoundError:
        print('Lo sentimos no existe el archivo index en la carpeta raiz')
        # exit()

    url_img_prev = os.path.join(learningObject.path_origin, 'img-prev.png')
    url_request_host = os.path.join(url, 'img-prev.png')
    url_img_preview = os.path.exists(url_img_prev)

    # Verificamos si existe la imagen de previsualizacion
    if url_img_preview:
        uuid = str(shortuuid.ShortUUID().random(length=8))
        # name = str('img-prev-' + uuid + '.png')
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
        print('Error, the file does not contain metadata')

    if xml_manifest == -1:
        _profile = 'IMS'
    elif xml_manifest != -1:
        _profile = 'SCORM'
    else:
        return print('Error, the file does not contain imslrm.xml nor imsmanifest.xml files.')
    if xml_manifest is not None:
        print("Manifest con datos")
    else:
        print('Error trying to parse the imsmanifest.xml')

    # print("profile: ", _profile, " filepath: ", _filepath)
    return _profile, _filepath, booleanLomLomes, xml_manifest

def read_file(filepath, profile):
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
        print("xml correcto")
        # print(xml_manifest)
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
        print('Error, file not found or corrupted.')

    if not from_lompad:
        load = FileController.load_recursive_model(xml_manifest, booleanLomLomes, filepath)
        # print("Load: ",load)
        return load, xml_manifest
    else:
        load = FileController.load_recursive_model(xml_manifest, filepath, is_lompad_exported=True)
        # print("Load: ",load)
        return load, xml_manifest

# Se terminan las funciones
def get_metadata_imsmanisfest(filename):
    global booleanLomLomes
    # with open(filename, 'r',encoding="utf-8") as myfile:
    #    jsondoc = xmltodict.parse(myfile.read())
    profile, filepath, booleanLomLomes, xml_manifest = upload_file(filename.replace('\\', '/'))
    load, xml_manifest = read_file(filepath, profile)
    import json
    json_object = json.dumps(load, indent=4, ensure_ascii=False)
    return json_object

def get_metadata_imsmanisfest1(filename):
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
        # title = data.find('metadata').find('general').find('title').find('string')
        res = BeautifulSoup(jsondoc)
    return jsondoc

def validateData(data):
    if data:
        return data.text
    else:
        return "No existe valor"

def validateDataBr(data):
    if data:
        for dat in data.select("br"):
            dat.replace_with("\n")
        dataResponse = data.text.replace('\n', ', ')
        return dataResponse[2:len(dataResponse)]
    else:
        return "No existe valor"

def get_index_file(filepath):
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
        print(e)
        print("Error al leer el archivo method1")
    return result

def folder_name(value):
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

class DeleteLearningObjectViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsTeacherUser]

    def destroy(self, request, pk=None):
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

#Importamos las clases para la mesajeria
mail_delete_oa = SendMail()
class DeleteLearningObjectViewSetAdmin(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdministratorUser]

    def destroy(self, request, pk=None):
        """
            Funcion para eliminar desde el Admin los objetos de aprendizaje
            El id que viene es el id de la tabla de metadatos, no de la tabla de learning Object
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
    """
        Función que nos permite eliminar el objeto de aprendizaje enviando como parámetro los datos que se van a eliminar
        params: learning_object_metadata_instance, learning_object_instance, is_not_metadata

    """
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

class getDataNewLearningObject(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
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
                request.data['roa_ref_url']='https://roa.ups.edu.ec/#/settings/my-objects'
                return Response({'message': message_method,'status':200, 'data':request.data}, status=status.HTTP_200_OK)
        elif len(learning_object) == 1 and learning_object[0].oa_integration_id != None:
            learning_object_integration = LearningObjectFile.objects.filter(pk=learning_object[0].oa_integration_id)
            file_path_oa_zip =os.path.abspath(os.path.join(_settings.MEDIA_ROOT,str(learning_object_integration[0].file)))
            #file_response = requests.get(request.data['urlZip'])
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
                print(e)
                return Response({'message':e,'status':400}, status=HTTP_400_BAD_REQUEST)
            request.data['roa_ref_url'] = env('DOMAIN_HOST_OER')
            return Response({'message':'Updated successfully','status':200, 'data':request.data}, status=HTTP_200_OK)
        elif len(learning_object) == 0 :
            return Response({'message':'There is an error trying to save the learning object', 'status': 400, 'data':request.data}, status=HTTP_400_BAD_REQUEST)

from django.core.files.storage import default_storage

class funcionDeleteOldFolderAndRegisters(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def list(self, request):
        learningObjects = LearningObjectFile.objects.all()
        for learnign in learningObjects:
            metadata = LearningObjectMetadata.objects.filter(learning_object_file_id=learnign.id)
            if len(metadata) == 0:
                #print('APTH',str(learnign.path_origin))
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

class saveDataIntegrationWithOer(APIView):
    permission_classes = [AllowAny]
    #permission_classes = [IsAuthenticated, IsTeacherUser]
    def post(self, request):
        serializer = LearningObjectFileOerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            learning_object = LearningObjectFile.objects.get(pk=serializer['id'].value)
        except Exception as e:
            print(e)
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
    #if len(learning_object) == 0:
      #  return True,'No relationship found with the id entered'
    #el
    if validate_user_key(serializer['user_key'].value) is False:
        return True,'Incorrect data, no action can be executed'
    elif learning_object.oa_integration_id is not None:
        return True,'Cannot create integration'
    elif learning_object.oa_created_at is not None:
        return True,'Cannot create integration'
    return False,''

def validate_user_key(key_user):
    user = User.objects.filter(user_key = key_user)
    if len(user) == 0:
        return False
    else:
        return True

def search_file_index(request_host,listNames,folder_area, file_name):
    filename_index=''
    filename=''
    url=''
    files = ["imslrm.xml", "imsmanifest.xml", "imsmanifest_nuevo.xml", "catalogacionLomes.xml"]
    for fileName in files:
        if fileName in listNames and fileName in listNames:
            filename_index = "media/" + folder_area + "/" + file_name
            filename = os.path.join('media', folder_area, file_name, files[0])
            url = request_host + "/media/" + folder_area + "/" + file_name + "/"
            break
        if files[0] in listNames and files[1] not in listNames and files[2] not in listNames and files[
            3] not in listNames:
            filename_index = "media/" + folder_area + "/" + file_name
            filename = os.path.join('media', folder_area, file_name, files[0])
            url = request_host + "/media/" + folder_area + "/" + file_name + "/"
            break
        if files[0] not in listNames and files[1] in listNames and files[2] not in listNames and files[
            3] not in listNames:
            filename_index = "media/" + folder_area + "/" + file_name
            filename = os.path.join('media', folder_area, file_name, files[1])
            url = request_host + "/media/" + folder_area + "/" + file_name + "/"
            break
        if files[0] not in listNames and files[1] not in listNames and files[2] in listNames and files[
            3] not in listNames:
            filename_index = "media/" + folder_area + "/" + file_name
            filename = os.path.join('media', folder_area, file_name, files[2])
            url = request_host + "/media/" + folder_area + "/" + file_name + "/"
            break
        if files[0] not in listNames and files[1] not in listNames and files[2] not in listNames and files[
            3] in listNames:
            filename_index = "media/" + folder_area + "/" + file_name
            filename = os.path.join('media', folder_area, file_name, files[3])
            url = request_host + "/media/" + folder_area + "/" + file_name + "/"
            break
    return filename_index, filename, url

def read_and_extract_xml_and_zip(file,dir_aux,folder_area,file_name,vec):
    for archi in sorted(file.namelist()):
        listNames = []
        if archi.find(dir_aux) == -1:
            pathFiles = os.path.join(_settings.MEDIA_ROOT + "/" + folder_area + "/" + file_name + "/")
        else:
            pathFiles = os.path.join(_settings.MEDIA_ROOT + "/")
        file.extract(archi, pathFiles)
        for nom in vec:
            if nom.endswith(".xml"):
                listNames.append(nom)
                if archi.find(dir_aux) == -1:
                    path = os.path.join(_settings.MEDIA_ROOT + "/" + folder_area + "/" + file_name + "/")
                else:
                    path = os.path.join(_settings.MEDIA_ROOT + "/")
    return listNames, pathFiles

def variable_definition_Oa(file_path, file_name):
    settings_dir = os.path.dirname(__file__)
    PROJECT_ROOT = os.path.abspath(os.path.dirname(settings_dir))
    folder_area = "catalog"
    file = zipfile.ZipFile(file_path, 'r')
    file_name_oa = file_name.split('.')[0]
    dir_aux = file_name_oa + "/"
    vec = file.namelist()
    return file, dir_aux, folder_area, file_name_oa, vec, PROJECT_ROOT

def create_and_register_new_learning_object(request, host):

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
        #learningObject.save()
        """Volcado de datos para la tabla de metadatos"""
        create_metadata_learning_object(object_metadata, request.data['IdOa'],learningObject.id, pathFiles)
        return True, 'Saved successfully'
    except Exception as err:
        return False, err

def get_metadata_and_evaluation(XMLFILES_FOLDER):
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
    learning_object_metadata = LearningObjectMetadata.objects.filter(learning_object_file_id=id)
    learning_object_related = LearningObjectFile.objects.get(pk=id)
    learning_object_related.oa_integration_id = new_learning_object_file_id
    learning_object_related.save()
    #Copiamos la imagen de previsualizacion
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
    import string
    import random
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))