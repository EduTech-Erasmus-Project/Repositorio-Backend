# from bs4 import BeautifulSoup as bs
# import xmltodict, json
# content = []
# # Read the XML file
# with open("imsmanifest1.xml", "r") as file:
#     # Read each line in the file, readlines() returns a list of lines
#     content = file.readlines()
#     # Combine the lines in the list into a string
#     content = "".join(content)
#     # bs_content = bs(content, "lxml")
#     # result = bs_content.find("resource")
#     obj = xmltodict.parse(content)
#     # print(obj['manifest']['metadata']['lomes:lom']['lomes:general']['lomes:title']['lomes:string']['#text'])
#     # print(obj['manifest']['metadata']['lomes:lom']['lomes:general']['lomes:description']['lomes:string']['#text'])
#     for keyword in obj['manifest']['metadata']['lomes:lom']['lomes:general']['lomes:keyword']:
#         print(keyword['lomes:string']['#text'])
# from bs4 import BeautifulSoup as bs

# def get_metadata_imsmanisfest(filename):
#     general={}
#     lifecycle={}
#     metaMetadata={}
#     technical={}
#     educational={}
#     rights={}
#     relation={}
#     annotation={}
#     classification={}
#     accesibility={}
#     if(filename.endswith('.xml')):
#         soup = bs(open(filename , 'r', encoding="utf-8"), 'lxml' )
#         for lom in soup.find_all('lom'):
#             _general = lom.find('general')
#             general={
#                'identifier':{
#                    'catalog':validateData(_general.find('identifier').find('catalog')).replace('\n', ''),
#                    'entry':validateData(_general.find('identifier').find('entry')).replace('\n', ''),
#                },
#                 'title': validateData(_general.find('title')).replace('\n', ''),
#                 'language':validateData(_general.find('language')).replace('\n', ''),
#                 'description':validateData(_general.find('description')).replace('\n', ''),
#                 'keyword':validateData(_general.find('keyword')).replace('\n', ', '),
#                 'coverage':validateData(_general.find('coverage')).replace('\n', ''),
#                 'structure':validateData(_general.find('structure').find('value')).replace('\n', ''),
#                 'aggregationLevel':validateData(_general.find('aggregationlevel').find('value')).replace('\n', ''),

#             }
#             _lifecycle = lom.find('lifecycle')
#             lifecycle = {
#                 'version':validateData(_lifecycle.find('version')).replace('\n', ''),
#                 'status':validateData(_lifecycle.find('status').find('value')).replace('\n', ''),
#                 'contribute':{
#                     'role':validateData(_lifecycle.find('contribute').find('role').find('value')).replace('\n', ''),
#                     'entity':validateData(_lifecycle.find('contribute').find('entity')).replace('\n', ' '),
#                     'date':{
#                         'datetime':validateData(_lifecycle.find('contribute').find('date').find('datetime')).replace('\n', ''),
#                         'description':validateData(_lifecycle.find('contribute').find('date').find('description')).replace('\n', ''),
#                     },
#                 },
#             }
        
#             _metaMetadata = lom.find('metametadata')
#             metaMetadata={
#                 'identifier':{
#                     'catalog':validateData(_metaMetadata.find('identifier').find('catalog')).replace('\n', ''),
#                     'entry':validateData(_metaMetadata.find('identifier').find('entry')).replace('\n', '')
#                 },
#                 'contribute':{
#                     'role':validateData(_metaMetadata.find('contribute').find('role')).replace('\n', ''),
#                     'entity':validateData(_metaMetadata.find('contribute').find('entity')).replace('\n', ''),
#                     'date':{
#                         'datetime':validateData(_metaMetadata.find('contribute').find('date').find('datetime')).replace('\n', ''),
#                         'description':validateData(_metaMetadata.find('contribute').find('date').find('description')).replace('\n', ''),
#                     },
#                 'metadataSchema': validateData(_metaMetadata.find('metadataschema')).replace('\n', ''),
#                 'language': validateData(_metaMetadata.find('language')).replace('\n', ''),
#                 }
#             }
#             _technical = lom.find('technical')
#             technical={
#                 'format':validateData(_technical.find('format')).replace('\n', ''),
#                 'size':validateData(_technical.find('size')).replace('\n', ''),
#                 'location':validateData(_technical.find('location')).replace('\n', ''),
#                 'requirement':validateData(_technical.find('requirement').find('value')).replace('\n', ''),
#                 'installationRemarks':validateData(_technical.find('installationremarks')).replace('\n', ''),
#                 'otherPlatformRequirements':validateData(_technical.find('otherplatformrequirements')).replace('\n', ''),
#                 'duration':validateData(_technical.find('duration')).replace('\n', ''),
                
#             }
#             _educational = lom.find('educational')
#             educational={
#                 'interactivityType':validateData(_educational.find('interactivitytype')).replace('\n', ''),
#                 'learningResourceType':validateData(_educational.find('learningresourcetype').find('value')).replace('\n', ''),
#                 'interactivityLevel':validateData(_educational.find('interactivitylevel').find('value')).replace('\n', ''),
#                 'semanticDensity':validateData(_educational.find('semanticdensity').find('value')).replace('\n', ''),
#                 'intendedEndUserRole':validateData(_educational.find('intendedenduserrole').find('value')).replace('\n', ''),
#                 'context':validateData(_educational.find('context').find('value')).replace('\n', ''),
#                 'typicalAgeRange':validateData(_educational.find('typicalagerange')).replace('\n', ''),
#                 'difficulty':validateData(_educational.find('difficulty').find('value')).replace('\n', ''),
#                 'typicalLearningTime':{
#                     'duration':validateData(_educational.find('typicallearningtime').find('duration')).replace('\n', ''),
#                     'description':validateData(_educational.find('typicallearningtime').find('description')).replace('\n', ''),
#                 },
#                 'description':validateData(_educational.find_all('description')[-1].find('string')).replace('\n', ''),
#                 'language':validateData(_educational.find('language')).replace('\n', ''),
#             }
#             _rights = lom.find('rights')
#             rights={
#                 'cost':validateData(_rights.find('cost').find('value')).replace('\n', ''),
#                 'copyrightAndOtherRestrictions':validateData(_rights.find('copyrightandotherrestrictions').find('value')).replace('\n', ''),
#                 'description':validateData(_rights.find('description')).replace('\n', ''),
#             }
#             _relation = lom.find('relation')
#             relation={
#                'kind':validateData(_relation.find('kind').find('value')).replace('\n', ''),
#                'resource':{
#                   'identifier':{
#                      'catalog': validateData(_relation.find('identifier').find('catalog')).replace('\n', '')
#                   },
#                'description':validateData(_relation.find('description')).replace('\n', ''),
#                },
#             }
#             _annotation = lom.find('annotation')
#             annotation={
#                 'entity':validateData(_annotation.find('entity')).replace('\n', ''),
#                 'date':{
#                     'datetime':validateData(_annotation.find('date').find('datetime')).replace('\n', ''),
#                     'description':validateData(_annotation.find('date').find('description')).replace('\n', ''),
#                 },
#                 'description':validateData(_annotation.find_all('description')[-1]).replace('\n', ''),
#                 'modeaccess':validateData(_annotation.find('modeaccess').find('value')).replace('\n', ''),
#                 'modeaccesssufficient':validateData(_annotation.find('modeaccesssufficient').find('value')).replace('\n', ''),
#                 'Rol':validateData(_annotation.find('rol').find('value')).replace('\n', ''),
#             }
#             _classification = lom.find('classification')
#             classification={
#                 'purpose':validateData(_classification.find('purpose').find('value')).replace('\n', ''),
#                 'taxonPath':{
#                     'source':validateData(_classification.find('taxonpath').find('source')).replace('\n', ''),
#                     'taxon':validateData(_classification.find('taxonpath').find('taxon').find('entry')).replace('\n', ''),
#                 },
#                 'description':validateData(_classification.find('description')).replace('\n', ''),
#                 'keyword':validateData(_classification.find('keyword')).replace('\n', ', '),
#             }
#             _accesibility = lom.find('accesibility')
#             accesibility={
#                 'description':validateData(_accesibility.find('description')).replace('\n', ''),
#                 'accessibilityfeatures':validateDataBr(_accesibility.find('accessibilityfeatures').find('resourcecontent')),
#                 'accessibilityhazard':validateDataBr(_accesibility.find('accessibilityhazard').find('properties')),
#                 'accessibilitycontrol':validateDataBr(_accesibility.find('accessibilitycontrol').find('methods')),
#                 'accessibilityAPI':validateDataBr(_accesibility.find('accessibilityapi').find('compatibleresource')),
#             }
#             return {
#                 'metadata':{
#                     'general':general,
#                     'lifecycle':lifecycle,
#                     'metaMetadata':metaMetadata,
#                     'technical':technical,
#                     'educational':educational,
#                     'rights':rights,
#                     'relation':relation,
#                     'annotation':annotation,
#                     'classification':classification,
#                     'accesibility':accesibility,
#                     }
#                 }

# def validateData(data):
#     if data:
#         return data.text
#     else:
#         return "No existe valor"


# def validateDataBr(data):
#     if data:
#         for dat in data.select("br"):
#             dat.replace_with("\n")
#         dataResponse = data.text.replace('\n', ', ')
#         return dataResponse[2:len(dataResponse)]
#     else:
#         return "No existe valor"

# resp=get_metadata_imsmanisfest('D:/TESIS/ROA/roabackend/media/Educacion/El_sistema_financiero-IMS_CPIEEE LOM66057/El_sistema_financiero-IMS_CP - IEEE LOM/imsmanifest.xml')
# print(resp)
# from applications.learning_object_file.get_metadata import GetLearningObjectMetadata
# from metadata import GetLearningObjectMetadata
# metatdat=GetLearningObjectMetadata('D:/TESIS/ROA/roabackend/media/Educacion/El_sistema_financiero-IMS_CPIEEE_LOM84330/El_sistema_financiero-IMS_CP - IEEE LOM/imsmanifest.xml')
# response=metatdat.get_metadata_imsmanisfest()
# print(response)
import os
def get_index_from_file(filename):
    file_name=""
    for file in os.listdir(filename):
        file_name=filename+'/'+file
    for file in os.listdir(file_name):
        if file.endswith("index.html"):
            print(file)
            index_path=os.path.abspath(file)
    return index_path

resp=get_index_from_file('D:/TESIS/ROA/roabackend/media/Educacion/El_sistema_financieroIMS33019')
print(resp)