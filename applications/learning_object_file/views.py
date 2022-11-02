from rest_framework import viewsets
from rest_framework import status

from media.maplompad.controller import FileController
from .models import LearningObjectFile
from datetime import datetime, timedelta
from . serializers import (
    LearningObjectSerializer,
    )
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import zipfile36 as zipfile
import zipfile
import os
import shortuuid
from bs4 import BeautifulSoup as bs
from applications.user.mixins import IsTeacherUser
from roabackend import settings as _settings
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)
import shutil
import xmltodict, json
from unipath import Path
from os import remove
from shutil import rmtree
from ..learning_object_metadata.models import LearningObjectMetadata
from xml.dom import minidom
BASE_DIR = Path(__file__).ancestor(3)
from ..helpers_functions.beautiful_soup_data import read_html_files, look_for_class_oeradap, generaye_array_paths_img
from roabackend.settings import DEBUG
booleanLomLomes=True #If booleanLomLomes is True represents a lom format, and
                     #if booleanLomLomes is False represents a lomes format.



class LearningObjectModelViewSet(viewsets.ModelViewSet):
    # authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAuthenticated,IsTeacherUser]
    serializer_class = LearningObjectSerializer
    queryset = LearningObjectFile.objects.all()

    def create(self, request, *args, **kwargs):
        global booleanLomLomes
        """
        Servicio para cargar un OA comprimido y obtener los metadatos correspontientes al Objeto de Aprendizaje.
        Se necesita estar autenticado como docente.
        """
        data=any
        serializer = LearningObjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        #file_path = os.path.join(BASE_DIR,'media',str(serializer.validated_data['file']))

        learningObject = LearningObjectFile.objects.create(
            file = serializer.validated_data['file']
            # file_name = serializer.validated_data['file_name'],
            # file_size = serializer.validated_data['file_size']
        )

        now = datetime.now()
        total_time =timedelta(
            hours=now.hour, 
            minutes=now.minute, 
            seconds=now.second
        )
        try:
            seconds = int(total_time.total_seconds())
            settings_dir = os.path.dirname(__file__)
            PROJECT_ROOT = os.path.abspath(os.path.dirname(settings_dir))
            file = zipfile.ZipFile(serializer.validated_data['file'],'r')
            size = sum([zinfo.file_size for zinfo in file.filelist])
            zip_kb = float(size) / 1000  # kB
            vec = file.namelist()
            nombre= file.filename.split('.')
            file_name=nombre[0]
            file_name = "%s%s" % (file_name,str(seconds))
            folder_area = "catalog"
            # folder_area = folder_name("catalog")
            pathFiles = os.path.join(_settings.MEDIA_ROOT+"/"+folder_area+"/"+file_name+"/")
            # size = os.path.getsize(pathFiles)
            dir_aux=file_name+"/"
            filename = ""
            filename_index = ""
            url=""
            path = os.path.join(_settings.MEDIA_ROOT+"/"+folder_area+"/"+file_name+"/")
            listNames = [];
            nommbreak = ""
            for archi in sorted(file.namelist()):
                listNames = []
                if archi.find(dir_aux) == -1:
                    pathFiles = os.path.join(_settings.MEDIA_ROOT+"/"+folder_area+"/"+file_name+"/")
                else:
                    pathFiles = os.path.join(_settings.MEDIA_ROOT+"/")
                file.extract(archi,pathFiles)
                for nom in vec:
                    if nom.endswith(".xml"):
                        listNames.append(nom)
                        if archi.find(dir_aux) == -1:
                            path = os.path.join(_settings.MEDIA_ROOT+"/"+folder_area+"/"+file_name+"/")
                        else:
                            path = os.path.join(_settings.MEDIA_ROOT+"/")
            files = ["imslrm.xml","imsmanifest.xml","imsmanifest_nuevo.xml","catalogacionLomes.xml"]
            for fileName in files:
                if fileName in listNames and fileName in listNames:
                    filename_index = "media/"+folder_area+"/"+file_name
                    #filename = "media/"+folder_area+"/"+file_name+"/"+files[0]
                    filename = os.path.join('media', folder_area, file_name, files[0])
                    url=self.request._current_scheme_host+"/media/"+folder_area+"/"+file_name+"/"
                    break
                if files[0] in listNames and files[1] not in listNames and files[2] not in listNames and files[3] not in listNames:
                    filename_index = "media/"+folder_area+"/"+file_name
                    #filename = "media/"+folder_area+"/"+file_name+"/"+files[0]
                    filename = os.path.join('media', folder_area, file_name, files[0])
                    url=self.request._current_scheme_host+"/media/"+folder_area+"/"+file_name+"/"
                    break
                if files[0] not in listNames and files[1] in listNames and files[2] not in listNames and files[3] not in listNames:
                    filename_index = "media/"+folder_area+"/"+file_name
                    #filename = "media/"+folder_area+"/"+file_name+"/"+files[1]
                    filename = os.path.join('media', folder_area, file_name, files[1])
                    url=self.request._current_scheme_host+"/media/"+folder_area+"/"+file_name+"/"
                    break
                if files[0] not in listNames and files[1] not in listNames and files[2] in listNames and files[3] not in listNames:
                    filename_index = "media/"+folder_area+"/"+file_name
                    #filename = "media/"+folder_area+"/"+file_name+"/"+files[2]
                    filename = os.path.join('media', folder_area, file_name, files[2])
                    url=self.request._current_scheme_host+"/media/"+folder_area+"/"+file_name+"/"
                    break
                if files[0] not in listNames and files[1] not in listNames and files[2] not in listNames and files[3] in listNames:
                    filename_index = "media/"+folder_area+"/"+file_name
                    #filename = "media/"+folder_area+"/"+file_name+"/"+files[3]
                    filename = os.path.join('media',folder_area,file_name,files[3])
                    url=self.request._current_scheme_host+"/media/"+folder_area+"/"+file_name+"/"
                    break

            PROJECT_ROOT = os.path.abspath(os.path.dirname(PROJECT_ROOT))
            XMLFILES_FOLDER = os.path.join(PROJECT_ROOT, filename)

            if get_index_imsmanisfest(XMLFILES_FOLDER)!='':
                index=get_index_imsmanisfest(XMLFILES_FOLDER)
            elif get_index_file(filename_index)!='':
                index= get_index_file(filename_index)
            else:
                return Response({"message": "Objeto de Aprendizaje aceptados por el repositorio es IMS y SCORM"}, status=HTTP_404_NOT_FOUND);

            #Condicion para saber si el archivo de metadatos es lom o lomes

            data = get_metadata_imsmanisfest(XMLFILES_FOLDER)

            if XMLFILES_FOLDER is not None:
                URL = url+index
                learningObject.url= URL.replace('http://', 'https://', 1)
                learningObject.file_name= nombre[0]
                learningObject.file_size= zip_kb
                learningObject.path_origin = os.path.join(BASE_DIR,'media','catalog',file_name)
                learningObject.save()
            else:
                return Response({"message": "No se encontro metadatos en el Objeto de Aprendizaje"}, status=HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)
            print(e.args)
            return Response({"message":"Objetos de Aprendizaje aceptados por el repositorio es IMS y SCORM."},status=HTTP_404_NOT_FOUND)

        #pocedemos a leer los recursos que tiene el objeto de aprendizaje
        count_general_paragaph, count_general_img, count_general_audio, count_general_video = read_html_files(learningObject.path_origin)

        #Lectura del archivo index para buscar si esta adaptado por la herramienta Oeradap
        try:
            with open(os.path.join(learningObject.path_origin,'index.html')) as file:
                is_adapted_oer = look_for_class_oeradap(os.path.join(learningObject.path_origin, 'index.html'))
            # No need to close the file
        except FileNotFoundError:
            print('Lo sentimos no existe el archivo index en la carpeta raiz')
            #exit()

        url_img_prev = os.path.join(learningObject.path_origin,'img-prev.png')
        url_request_host = os.path.join(url,'img-prev.png')
        url_img_preview = os.path.exists(url_img_prev)

        #Verificamos si existe la imagen de previsualizacion
        if url_img_preview:
            uuid = str(shortuuid.ShortUUID().random(length=8))
            #name = str('img-prev-' + uuid + '.png')
            name = str('img-prev.png')
        else:
            name = ''
            url_request_host = ''
        array_paths_img_view = []
        array_paths_img_view = generaye_array_paths_img(learningObject.path_origin,url)

        count_tag ={
            'paragraph': count_general_paragaph,
            'img':count_general_img,
            'video':count_general_video,
            'audio':count_general_audio,
            'is_adapted_oer': is_adapted_oer,
            "paths_img_preview": array_paths_img_view,
            'img_prev':{
                'exist':url_img_preview,
                'url_img':url_request_host,
                'name':name
            },
        }

        serializer = LearningObjectSerializer(learningObject)
        metadata ={
            "metadata": data,
            "oa_file": serializer.data,
            "tag_count": count_tag,
        }
        return Response(metadata,status=HTTP_200_OK)

#Funciones para leer los metadatos

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

    #print("profile: ", _profile, " filepath: ", _filepath)
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
    #print("Profile: ", profile)
    if profile == 'SCORM':
        # print("SCORM #227")
        xml_manifest = FileController.read_manifest(filepath)
        # print(xml_manifest)
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

    # print("xml_manifest: ",xml_manifest)

    if not from_lompad:
        load = FileController.load_recursive_model(xml_manifest, booleanLomLomes, filepath)
        # print("Load: ",load)
        return load, xml_manifest
    else:
        load = FileController.load_recursive_model(xml_manifest, filepath, is_lompad_exported=True)
        # print("Load: ",load)
        return load, xml_manifest
#Se terminan las funciones
def get_metadata_imsmanisfest(filename):
    global booleanLomLomes
    #with open(filename, 'r',encoding="utf-8") as myfile:
    #    jsondoc = xmltodict.parse(myfile.read())
    profile, filepath, booleanLomLomes, xml_manifest = upload_file(filename.replace('\\','/'))
    load, xml_manifest = read_file(filepath, profile)
    import json
    json_object = json.dumps(load, indent=4, ensure_ascii=False)
    return json_object


def get_metadata_imsmanisfest1(filename):
    general={}
    lifecycle={}
    metaMetadata={}
    technical={}
    educational={}
    rights={}
    relation={}
    annotation={}
    classification={}
    accesibility={}
    if(filename.endswith('.xml')):
        soup = bs(open(filename , 'r', encoding="utf-8"), 'lxml' )
        for lom in soup.find_all('lom'):
            _general = lom.find('general')
            general={
               'identifier':{
                   'catalog':validateData(_general.find('identifier').find('catalog')).replace('\n', ''),
                   'entry':validateData(_general.find('identifier').find('entry')).replace('\n', ''),
               },
                'title': validateData(_general.find('title')).replace('\n', ''),
                'language':validateData(_general.find('language')).replace('\n', ''),
                'description':validateData(_general.find('description')).replace('\n', ''),
                'keyword':validateData(_general.find('keyword')).replace('\n', ', '),
                'coverage':validateData(_general.find('coverage')).replace('\n', ''),
                'structure':validateData(_general.find('structure').find('value')).replace('\n', ''),
                'aggregationLevel':validateData(_general.find('aggregationlevel').find('value')).replace('\n', ''),

            }
            _lifecycle = lom.find('lifecycle')
            lifecycle = {
                'version':validateData(_lifecycle.find('version')).replace('\n', ''),
                'status':validateData(_lifecycle.find('status').find('value')).replace('\n', ''),
                'contribute':{
                    'role':validateData(_lifecycle.find('contribute').find('role').find('value')).replace('\n', ''),
                    'entity':validateData(_lifecycle.find('contribute').find('entity')).replace('\n', ' '),
                    'date':{
                        'datetime':validateData(_lifecycle.find('contribute').find('date').find('datetime')).replace('\n', ''),
                        'description':validateData(_lifecycle.find('contribute').find('date').find('description')).replace('\n', ''),
                    },
                },
            }
        
            _metaMetadata = lom.find('metametadata')
            metaMetadata={
                'identifier':{
                    'catalog':validateData(_metaMetadata.find('identifier').find('catalog')).replace('\n', ''),
                    'entry':validateData(_metaMetadata.find('identifier').find('entry')).replace('\n', '')
                },
                'contribute':{
                    'role':validateData(_metaMetadata.find('contribute').find('role').find('value')).replace('\n', ''),
                    'entity':validateData(_metaMetadata.find('contribute').find('entity')).replace('\n', ''),
                    'date':{
                        'datetime':validateData(_metaMetadata.find('contribute').find('date').find('datetime')).replace('\n', ''),
                        'description':validateData(_metaMetadata.find('contribute').find('date').find('description')).replace('\n', ''),
                    },
                'metadataSchema': validateData(_metaMetadata.find('metadataschema')).replace('\n', ''),
                'language': validateData(_metaMetadata.find('language')).replace('\n', ''),
                }
            }
            _technical = lom.find('technical')
            technical={
                'format':validateData(_technical.find('format')).replace('\n', ''),
                'size':validateData(_technical.find('size')).replace('\n', ''),
                'location':validateData(_technical.find('location')).replace('\n', ''),
                'requirement':validateData(_technical.find('requirement').find('value')).replace('\n', ''),
                'installationRemarks':validateData(_technical.find('installationremarks')).replace('\n', ''),
                'otherPlatformRequirements':validateData(_technical.find('otherplatformrequirements')).replace('\n', ''),
                'duration':validateData(_technical.find('duration')).replace('\n', ''),
                
            }
            _educational = lom.find('educational')
            educational={
                'interactivityType':validateData(_educational.find('interactivitytype')).replace('\n', ''),
                'learningResourceType':validateData(_educational.find('learningresourcetype').find('value')).replace('\n', ''),
                'interactivityLevel':validateData(_educational.find('interactivitylevel').find('value')).replace('\n', ''),
                'semanticDensity':validateData(_educational.find('semanticdensity').find('value')).replace('\n', ''),
                'intendedEndUserRole':validateData(_educational.find('intendedenduserrole').find('value')).replace('\n', ''),
                'context':validateData(_educational.find('context').find('value')).replace('\n', ''),
                'typicalAgeRange':validateData(_educational.find('typicalagerange')).replace('\n', ''),
                'difficulty':validateData(_educational.find('difficulty').find('value')).replace('\n', ''),
                'typicalLearningTime':{
                    'duration':validateData(_educational.find('typicallearningtime').find('duration')).replace('\n', ''),
                    'description':validateData(_educational.find('typicallearningtime').find('description')).replace('\n', ''),
                },
                'description':validateData(_educational.find_all('description')[-1].find('string')).replace('\n', ''),
                'language':validateData(_educational.find('language')).replace('\n', ''),
            }
            _rights = lom.find('rights')
            rights={
                'cost':validateData(_rights.find('cost').find('value')).replace('\n', ''),
                'copyrightAndOtherRestrictions':validateData(_rights.find('copyrightandotherrestrictions').find('value')).replace('\n', ''),
                'description':validateData(_rights.find('description')).replace('\n', ''),
            }
            _relation = lom.find('relation')
            relation={
               'kind':validateData(_relation.find('kind').find('value')).replace('\n', ''),
               'resource':{
                  'identifier':{
                     'catalog': validateData(_relation.find('identifier').find('catalog')).replace('\n', '')
                  },
               'description':validateData(_relation.find('description')).replace('\n', ''),
               },
            }
            _annotation = lom.find('annotation')
            annotation={
                'entity':validateData(_annotation.find('entity')).replace('\n', ''),
                'date':{
                    'datetime':validateData(_annotation.find('date').find('datetime')).replace('\n', ''),
                    'description':validateData(_annotation.find('date').find('description')).replace('\n', ''),
                },
                'description':validateData(_annotation.find_all('description')[-1]).replace('\n', ''),
                'modeaccess':validateData(_annotation.find('modeaccess').find('value')).replace('\n', ''),
                'modeaccesssufficient':validateData(_annotation.find('modeaccesssufficient').find('value')).replace('\n', ''),
                'Rol':validateData(_annotation.find('rol').find('value')).replace('\n', ''),
            }
            _classification = lom.find('classification')
            classification={
                'purpose':validateData(_classification.find('purpose').find('value')).replace('\n', ''),
                'taxonPath':{
                    'source':validateData(_classification.find('taxonpath').find('source')).replace('\n', ''),
                    'taxon':validateData(_classification.find('taxonpath').find('taxon').find('entry')).replace('\n', ''),
                },
                'description':validateData(_classification.find('description')).replace('\n', ''),
                'keyword':validateData(_classification.find('keyword')).replace('\n', ', '),
            }
            _accesibility = lom.find('accesibility')
            accesibility={
                'description':validateData(_accesibility.find('description')).replace('\n', ''),
                'accessibilityfeatures':validateDataBr(_accesibility.find('accessibilityfeatures').find('resourcecontent')),
                'accessibilityhazard':validateDataBr(_accesibility.find('accessibilityhazard').find('properties')),
                'accessibilitycontrol':validateDataBr(_accesibility.find('accessibilitycontrol').find('methods')),
                'accessibilityAPI':validateDataBr(_accesibility.find('accessibilityapi').find('compatibleresource')),
            }
            return {
                    'general':general,
                    'lifecycle':lifecycle,
                    'metaMetadata':metaMetadata,
                    'technical':technical,
                    'educational':educational,
                    'rights':rights,
                    'relation':relation,
                    'annotation':annotation,
                    'classification':classification,
                    'accesibility':accesibility,
                }
from bs4 import BeautifulSoup
def get_metadata_imsmanisfest_normal(filename):
    general={}
    lifecycle={}
    metaMetadata={}
    technical={}
    educational={}
    rights={}
    relation={}
    annotation={}
    classification={}
    accesibility={}
    with open(filename, 'r',encoding="utf-8") as myfile:
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
    file=""
    index_path=""
    index_url=""
    if(filepath != ''):
        for file in os.listdir(filepath):
            if file.endswith("index.html") or file.endswith("excursion.html"):
                index_path=file
        if index_path !="":
            index_url=index_path
        else:
            return Response({"message": "Ocurrio un error al cargar el Objeto de Aprendizaje"})
    return index_url

def get_index_imsmanisfest(filename):
    content = []
    result = ""
    try:
        if(filename[:-1] != BASE_DIR):
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
        print("Error al leer el archivo")
    return result



def folder_name(value):
    return {
        "Programas generales":"Programas-generales",
        "Educación":"Educacion",
        "Humanidades y artes":"Humanidades-y-artes",
        "Ciencias sociales, educación comercial y derecho":"Ciencias-socilaes-educacion-comercial-derecho",
        "Ciencias":"Ciencias",
        "Ingeniería, industria y construcción":"Ingenieria-industrial-construccion",
        "Agricultura":"Agricultura",
        "Salud y servicios sociales":"Salud-servicios-sociales",
        "Servicios":"Servicios",
        "Sectores desconocidos no especificados":"Otros"  
    }[value]


class DeleteLearningObjectViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsTeacherUser]
    def destroy(self, request, pk=None):
        learning_object_instance =  LearningObjectFile.objects.get(pk=pk)
        learning_object_metadata_instance = LearningObjectMetadata.objects.get(learning_object_file_id = learning_object_instance.id)

        if(learning_object_metadata_instance and learning_object_instance):

            avatar = str(learning_object_metadata_instance.avatar)
            avatar_path = os.path.join(BASE_DIR, 'media',avatar.replace('/', '\\'))
            zip_file = str(learning_object_instance.file)
            zip_file_path = os.path.join(BASE_DIR,'media', zip_file.replace('/', '\\'))
            path_origin = os.path.join(learning_object_instance.path_origin)

            if(learning_object_instance.path_origin and avatar_path and zip_file_path ):
                remove(str(avatar_path.replace('\\', '/')))
                remove(str(zip_file_path.replace('\\', '/')))
                rmtree(str(path_origin.replace('\\', '/')))
                learning_object_instance.delete()

                return Response({'message': 'Record deleted successfully', 'code': 200}, status=status.HTTP_200_OK)

            else:
                return Response({'message': 'Error loading routes'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message':'Error trying to delete record not found'}, status=status.HTTP_400_BAD_REQUEST)


