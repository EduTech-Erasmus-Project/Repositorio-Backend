
"""Parser legacy de metadata LOM para objetos de aprendizaje.

Este archivo mantiene una lectura directa del XML usando BeautifulSoup y
devuelve la estructura histórica que esperan otros puntos del proyecto.

No intenta validar el esquema completo del manifest. Su responsabilidad es
extraer valores puntuales desde un XML tipo `lom` y acomodarlos en el formato
de diccionario que luego consumen vistas y procesos de carga.
"""

from bs4 import BeautifulSoup as bs
class GetLearningObjectMetadata():
    """Extrae metadata LOM y la expone en la estructura legacy del proyecto.

    Esta clase mantiene estado por sección para reflejar el shape de salida
    esperado por el flujo de carga:

    - `general`
    - `lifecycle`
    - `metaMetadata`
    - `technical`
    - `educational`
    - `rights`
    - `relation`
    - `annotation`
    - `classification`
    - `accesibility`
    """

    def __init__(self,filename):
        """Prepara el nombre del archivo XML y los contenedores de salida.

        Cada atributo de instancia representa una sección del manifest que se
        va poblando cuando `get_metadata_imsmanisfest()` encuentra un nodo
        `lom` valido.
        """

        self.filename=filename
        self.general={}
        self.lifecycle={}
        self.metaMetadata={}
        self.technical={}
        self.educational={}
        self.rights={}
        self.relation={}
        self.annotation={}
        self.classification={}
        self.accesibility={}
    def get_metadata_imsmanisfest(self):
        """Lee el XML y arma la estructura heredada de metadata del OA.

        Entrada:
        - `self.filename`: ruta a un archivo XML con estructura LOM.

        Comportamiento:
        - abre el archivo con BeautifulSoup
        - busca la primera etiqueta `lom`
        - extrae nodos hijos conocidos por sección
        - limpia saltos de línea y normaliza algunos campos multilínea

        Salida:
        - un diccionario con la clave `metadata`
        - dentro de ella, las secciones `general`, `lifecycle`,
          `metaMetadata`, `technical`, `educational`, `rights`, `relation`,
          `annotation`, `classification` y `accesibility`

        Limitación:
        - si el XML no termina en `.xml` o no contiene una etiqueta `lom`,
          el método no construye una salida útil.
        """

        if(self.filename.endswith('.xml')):
            soup = bs(open(self.filename , 'r', encoding="utf-8"), 'lxml' )
            for lom in soup.find_all('lom'):
                _general = lom.find('general')
                self.general={
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
                self.lifecycle = {
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
                self.metaMetadata={
                    'identifier':{
                        'catalog':validateData(_metaMetadata.find('identifier').find('catalog')).replace('\n', ''),
                        'entry':validateData(_metaMetadata.find('identifier').find('entry')).replace('\n', '')
                    },
                    'contribute':{
                        'role':validateData(_metaMetadata.find('contribute').find('role')).replace('\n', ''),
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
                self.technical={
                    'format':validateData(_technical.find('format')).replace('\n', ''),
                    'size':validateData(_technical.find('size')).replace('\n', ''),
                    'location':validateData(_technical.find('location')).replace('\n', ''),
                    'requirement':validateData(_technical.find('requirement').find('value')).replace('\n', ''),
                    'installationRemarks':validateData(_technical.find('installationremarks')).replace('\n', ''),
                    'otherPlatformRequirements':validateData(_technical.find('otherplatformrequirements')).replace('\n', ''),
                    'duration':validateData(_technical.find('duration')).replace('\n', ''),

                }
                _educational = lom.find('educational')
                self.educational={
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
                self.rights={
                    'cost':validateData(_rights.find('cost').find('value')).replace('\n', ''),
                    'copyrightAndOtherRestrictions':validateData(_rights.find('copyrightandotherrestrictions').find('value')).replace('\n', ''),
                    'description':validateData(_rights.find('description')).replace('\n', ''),
                }
                _relation = lom.find('relation')
                self.relation={
                   'kind':validateData(_relation.find('kind').find('value')).replace('\n', ''),
                   'resource':{
                      'identifier':{
                         'catalog': validateData(_relation.find('identifier').find('catalog')).replace('\n', '')
                      },
                   'description':validateData(_relation.find('description')).replace('\n', ''),
                   },
                }
                _annotation = lom.find('annotation')
                self.annotation={
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
                self.classification={
                    'purpose':validateData(_classification.find('purpose').find('value')).replace('\n', ''),
                    'taxonPath':{
                        'source':validateData(_classification.find('taxonpath').find('source')).replace('\n', ''),
                        'taxon':validateData(_classification.find('taxonpath').find('taxon').find('entry')).replace('\n', ''),
                    },
                    'description':validateData(_classification.find('description')).replace('\n', ''),
                    'keyword':validateData(_classification.find('keyword')).replace('\n', ', '),
                }
                _accesibility = lom.find('accesibility')
                self.accesibility={
                    'description':validateData(_accesibility.find('description')).replace('\n', ''),
                    'accessibilityfeatures':validateDataBr(_accesibility.find('accessibilityfeatures').find('resourcecontent')),
                    'accessibilityhazard':validateDataBr(_accesibility.find('accessibilityhazard').find('properties')),
                    'accessibilitycontrol':validateDataBr(_accesibility.find('accessibilitycontrol').find('methods')),
                    'accessibilityAPI':validateDataBr(_accesibility.find('accessibilityapi').find('compatibleresource')),
                }
                return {
                    'metadata':{
                        'general':self.general,
                        'lifecycle':self.lifecycle,
                        'metaMetadata':self.metaMetadata,
                        'technical':self.technical,
                        'educational':self.educational,
                        'rights':self.rights,
                        'relation':self.relation,
                        'annotation':self.annotation,
                        'classification':self.classification,
                        'accesibility':self.accesibility,
                        }
                    }

def validateData(data):
    """Extrae el texto crudo de un nodo BeautifulSoup.

    Si el nodo no existe, devuelve el string `"No existe valor"` para conservar
    el contrato heredado del parser y evitar `AttributeError` inmediatos en el
    armado del diccionario.
    """

    if data:
        return data.text
    else:
        return "No existe valor"


def validateDataBr(data):
    """Extrae texto de nodos con `<br>` y los vuelve una lista visual.

    El helper reemplaza cada `<br>` por salto de línea, luego compacta el texto
    resultante en una cadena separada por comas. Se usa sobre todo en campos
    de accesibilidad que suelen venir como listas HTML incrustadas.
    """

    if data:
        for dat in data.select("br"):
            dat.replace_with("\n")
        dataResponse = data.text.replace('\n', ', ')
        return dataResponse[2:len(dataResponse)]
    else:
        return "No existe valor"