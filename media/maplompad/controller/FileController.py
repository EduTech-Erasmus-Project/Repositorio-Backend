from media.maplompad.controller import LOMController



def read_manifest(ims_manifest_path):
    """
    Read the ims_manifest XML file by its path.

    param ims_manifest_path: The path of the ims_manifest XML.
    type ims_manifest_path str

    :return:
        A string representing the whole file.
    """
    print("Entra 1: ",ims_manifest_path)
    try:
        import requests
        import sys

        with open(ims_manifest_path,'r',encoding='UTF-8') as file:
            #file=etree.parse(file)
            read=file.readlines()
            file.close()
            return ''.join(read)

    except Exception as e:
        print(e)
        return -1

def load_recursive_model(manifest, booleanLomLomes,hashed_code, is_lompad_exported=False):
    """
    Load LOMPAD XML file into Python Class

    :param manifest: A valid XML string.
    :param is_lompad_exported: Check if manifest comes from lompad application.
    :return: string (as json) representing mapped values.
    """

    lom_controller = LOMController.Controller()
    parsed_dictionary: dict = lom_controller.parse_str_to_dict(manifest)

    lom_controller.__setattr__("_mapped_data", dict())
    lom_controller.__setattr__("_object_dict", dict())
    lom_controller.map_recursively(parsed_dictionary, booleanLomLomes,is_lompad_exported=is_lompad_exported)
    # print(lom_controller.__getattribute__('_mapped_data'))
    new_dict={}

    for key in lom_controller.get_mapped_manifest(hashed_code, booleanLomLomes).keys():
        if "lomes:" in key:
            key2 = key.replace('lomes:', '')
            new_dict[key2]=lom_controller.get_mapped_manifest(hashed_code, booleanLomLomes)[key]
    if bool(new_dict):
        # print(new_dict)
        return new_dict
    # print(lom_controller.get_mapped_manifest(hashed_code, booleanLomLomes))
    return lom_controller.get_mapped_manifest(hashed_code, booleanLomLomes)


