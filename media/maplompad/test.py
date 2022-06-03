from controller import FileController
from xml.dom import minidom

booleanLomLomes=True #If booleanLomLomes is True represents a lom format, and
                     #if booleanLomLomes is False represents a lomes format.



def upload_file(_filepath):

    global booleanLomLomes

    _profile = None
    xml_manifest = None

    redundant_elements = [' uniqueElementName="general"', ' uniqueElementName="catalog"',' uniqueElementName="entry"',
                          ' uniqueElementName="aggregationLevel"', ' uniqueElementName="role"', ' uniqueElementName="dateTime"',
                          ' uniqueElementName="source"',' uniqueElementName="value"', ' uniqueElementName="metaMetadata"', 
                          ' uniqueElementName="rights"', ' uniqueElementName="access"', ' uniqueElementName="accessType"', 
                          ' uniqueElementName="source"', ' uniqueElementName="value"','uniqueElementName="lifeCycle"',
                          'uniqueElementName="technical"']

    xml_manifest = FileController.read_manifest(_filepath)
    for redundant in redundant_elements:
        xml_manifest = xml_manifest.replace(redundant, '')
    doc = minidom.parse(_filepath)
    childTag = doc.firstChild.tagName
    if(childTag == "lom"):
        booleanLomLomes=True
    elif(childTag == "lomes:lom"):
        booleanLomLomes=False
    else:
        print('Error, the file does not contain metadata')

    if xml_manifest == -1:
        _profile = 'IMS'
    elif xml_manifest != -1:
        _profile = 'SCORM'
    else:
        return  print('Error, the file does not contain imslrm.xml nor imsmanifest.xml files.')     
    if xml_manifest is not None:
        print("Manifest con datos")
    else:
        print('Error trying to parse the imsmanifest.xml')
    
    print("profile: ",_profile, " filepath: ",_filepath)
    return _profile,_filepath, booleanLomLomes, xml_manifest


def read_file(filepath, profile):

    redundant_elements = [' uniqueElementName="general"', ' uniqueElementName="catalog"',' uniqueElementName="entry"',
                          ' uniqueElementName="aggregationLevel"', ' uniqueElementName="role"', ' uniqueElementName="dateTime"',
                          ' uniqueElementName="source"',' uniqueElementName="value"', ' uniqueElementName="metaMetadata"', 
                          ' uniqueElementName="rights"', ' uniqueElementName="access"', ' uniqueElementName="accessType"', 
                          ' uniqueElementName="source"', ' uniqueElementName="value"','uniqueElementName="lifeCycle"',
                          'uniqueElementName="technical"']


    from_lompad = False
    print("Profile: ",profile)
    if profile == 'SCORM':
        #print("SCORM #227")
        xml_manifest = FileController.read_manifest(filepath)
        #print(xml_manifest)
        for redundant in redundant_elements:
                xml_manifest = xml_manifest.replace(redundant,'')
        xml_manifest = xml_manifest.replace('lom:', '')
        print("xml correcto")
        #print(xml_manifest)
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

    #print("xml_manifest: ",xml_manifest)

    if not from_lompad:
        load = FileController.load_recursive_model(xml_manifest, booleanLomLomes, filepath)
        #print("Load: ",load)
        return load,xml_manifest
    else:
        print ("Termina 256")
        load = FileController.load_recursive_model(xml_manifest, filepath, is_lompad_exported=True)
        #print("Load: ",load)
        return load , xml_manifest

    
if __name__ == '__main__':
    _filepath = "imslrm.xml"
    profile, filepath, booleanLomLomes, xml_manifest=upload_file(_filepath)
    load , xml_manifest=read_file(filepath, profile)
    import json 
    json_object = json.dumps(load, indent = 4,ensure_ascii=False)
    print(json_object)