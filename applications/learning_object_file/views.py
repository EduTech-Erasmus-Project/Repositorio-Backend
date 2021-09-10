from rest_framework import viewsets
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
from bs4 import BeautifulSoup as bs
from applications.user.mixins import IsTeacherUser
from roabackend import settings as _settings
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
) 
import xmltodict, json

    
class LearningObjectModelViewSet(viewsets.ModelViewSet):
    # authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAuthenticated,IsTeacherUser]
    serializer_class = LearningObjectSerializer
    queryset = LearningObjectFile.objects.all()
    def create(self, request, *args, **kwargs):
        """
        Servicio para cargar un OA comprimido y obtener los metadatos correspontientes al Objeto de Aprendizaje.
        Se necesita estar autenticado como docente.
        """
        data=any
        serializer = LearningObjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        learningObject = LearningObjectFile.objects.create(
            file = serializer.validated_data['file']
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
            vec = file.namelist()
            nombre= file.filename.split('.')
            file_name=nombre[0]
            file_name = "%s%s" % (file_name,str(seconds))
            folder_area = "catalog"
            # folder_area = folder_name("catalog")
            pathFiles = os.path.join(_settings.MEDIA_ROOT+"/"+folder_area+"/"+"/"+file_name+"/")
            dir_aux=file_name+"/"
            filename = ""
            filename_index = ""
            url=""
            for archi in sorted(file.namelist()):
                if archi.find(dir_aux) == -1:
                    pathFiles = os.path.join(_settings.MEDIA_ROOT+"/"+folder_area+"/"+"/"+file_name+"/")
                else:
                    pathFiles = os.path.join(_settings.MEDIA_ROOT+"/")
                file.extract(archi,pathFiles)
                for nom in vec:
                    if nom.endswith(".xml"):
                        if archi.find(dir_aux) == -1:
                            path = os.path.join(_settings.MEDIA_ROOT+"/"+folder_area+"/"+"/"+file_name+"/")
                        else:
                            path = os.path.join(_settings.MEDIA_ROOT+"/")
                    if 'imsmanifest_nuevo' in nom or 'imsmanifest' in nom or 'contentv3' in nom or 'catalogacionLomes' in nom:
                        filename_index = "media/"+folder_area+"/"+file_name
                        filename = "media/"+folder_area+"/"+file_name+"/"+nom
                        url=self.request._current_scheme_host+"/media/"+folder_area+"/"+file_name+"/"
            PROJECT_ROOT = os.path.abspath(os.path.dirname(PROJECT_ROOT))
            XMLFILES_FOLDER = os.path.join(PROJECT_ROOT, filename)
            index = ""
            if get_index_imsmanisfest(XMLFILES_FOLDER)!='':
                index=get_index_imsmanisfest(XMLFILES_FOLDER)
            elif get_index_file(filename_index)!='':
                index= get_index_file(filename_index)
            else:
                 return Response({"message": "Ocurrio un error al subir el Objeto de Aprendizaje"}, status=HTTP_404_NOT_FOUND)
            data = get_metadata_imsmanisfest(XMLFILES_FOLDER)
            if XMLFILES_FOLDER is not None:
                URL = url+index 
                learningObject.url= URL.replace('http://', 'https://', 1)
                learningObject.save()
            else:
                return Response({"message": "Ocurrio un error al subir el Objeto de Aprendizaje"}, status=HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)
            return Response({"message":"Ocurrio un error al subir el Objeto de Aprendizaje"},status=HTTP_404_NOT_FOUND)
        serializer = LearningObjectSerializer(learningObject)
        metadata ={
            "metadata": data,
            "oa_file": serializer.data
        }
        return Response(metadata,status=HTTP_200_OK)

def get_metadata_imsmanisfest(filename):
    with open(filename, 'r',encoding="utf-8") as myfile:
        jsondoc = xmltodict.parse(myfile.read())
    jsondata=json.dumps(jsondoc)
    return jsondoc


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
    filename=""
    index_path=""
    index_url=""
    for file in os.listdir(filepath):
        filename=file
        file=filepath+'/'+file
    for file in os.listdir(file):
        if file.endswith("index.html") or file.endswith("excursion.html"):
            index_path=file
    if index_path !="":
        index_url=filename+'/'+index_path
    else:
        return Response({"message": "Ocurrio un error al cargar el Objeto de Aprendizaje"})
    return index_url

def get_index_imsmanisfest(filename):
    content = []
    result = ""
    try:
        with open(filename, "r") as file:
            content = file.readlines()
            content = "".join(content)
            bs_content = bs(content, "lxml")
            resource = bs_content.find_all("file")
            if bs_content.find_all("file"):
                result = resource[0]['href']
            else:
                result = ""
    except ValueError:
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

    