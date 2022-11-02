import collections
import logging
import traceback
from collections import OrderedDict
from pprint import pprint
from typing import Container
from fuzzywuzzy import fuzz, process
from media.maplompad.model.Estructuras.General import General
from media.maplompad.model.Estructuras.LifeCycle import LifeCycle
from media.maplompad.model.Estructuras.MetaMEtadata import MetaMetadata
from media.maplompad.model.Estructuras.Accessibility import Accessibility
from media.maplompad.model.Estructuras.Technical import Technical
from media.maplompad.model.Estructuras.Educational import Educational
from media.maplompad.model.Estructuras.Rights import Rights
from media.maplompad.model.Estructuras.Relation import Relation
from media.maplompad.model.Estructuras.Anotation import Annotation
from media.maplompad.model.Estructuras.Classification import Classification
from media.maplompad.model.Estructuras.Accessibility import Accessibility

class LOM:
    

    def __init__(self, general=None, life_cycle=None, meta_metadata=None, technical=None, educational=None, rights=None,
                 relation=None, annotation=None, classification=None, accessibility=None):
        logging.basicConfig(filename='logger.log')
        
        self.general = general
        self.lifeCycle = life_cycle
        self.metaMetadata = meta_metadata
        self.technical = technical
        self.educational = educational
        self.rights = rights
        self.relation = relation
        self.annotation = annotation
        self.classification = classification
        self.accesibility = accessibility  

    def to_xml(self):
        return f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <lom xmlns="http://ltsc.ieee.org/xsd/LOM" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://ltsc.ieee.org/xsd/LOM http://ltsc.ieee.org/xsd/lomv1.0/lom.xsd">
            {self.general.to_xml() if self.general is not None else ''}
            {self.lifeCycle.to_xml() if self.lifeCycle is not None else ''}
            {self.metaMetadata.to_xml() if self.metaMetadata is not None else ''}
            {self.technical.to_xml() if self.technical is not None else ''}
            {self.educational.to_xml() if self.educational is not None else ''}
            {self.rights.to_xml() if self.rights is not None else ''}
            {self.relation.to_xml() if self.relation is not None else ''}
            {self.annotation.to_xml() if self.annotation is not None else ''}
            {self.classification.to_xml() if self.classification is not None else ''}
            {self.accesibility.to_xml() if self.accesibility is not None else ''}
        </lom>
        """

    def __dict__(self):
        return {'General': self.general.__dict__() if self.general is not None else General().__dict__(),
                'Life Cycle': self.lifeCycle.__dict__() if self.lifeCycle is not None else LifeCycle().__dict__(),
                'Meta-Metadata': self.metaMetadata.__dict__() if self.metaMetadata is not None else MetaMetadata().__dict__(),
                'Technical': self.technical.__dict__() if self.technical is not None else Technical().__dict__(),
                'Educational': self.educational.__dict__() if self.educational is not None else Educational().__dict__(),
                'Rights': self.rights.__dict__() if self.rights is not None else Rights().__dict__(),
                'Relation': self.relation.__dict__() if self.relation is not None else Relation().__dict__(),
                'Annotation': self.annotation.__dict__() if self.annotation is not None else Annotation().__dict__(),
                'Classification': self.classification.__dict__() if self.classification is not None else Classification().__dict__(),
                'Accessibility': self.accesibility.__dict__() if self.accesibility is not None else Accessibility().__dict__()}


def determine_lompad_leaf(dictionary: dict, key: str, is_lompad_exported=False, booleanLomLomes=True):
    """
    Determine which lompad leaf should be mapped.

    :param dictionary: A Dict instance in representation of data to being parsed.
    :param key: Represents the key of LOM standard.
    :param is_lompad_exported: Check if manifest comes from lompad application.

    :return: a dict representing the object mapped.
    :except If key was not found or couldn't invoke a function (by reflection) catch an exception and prints its
    traceback.
    """
    try:
        # Search the key inside dispatch dict.
        if booleanLomLomes:
            for key1 in dispatch.keys():
                if key in key1:
                    # print(key1)
                    try:
                        metodo = dispatch[key1]
                        ejemplo = metodo(dict(dictionary), is_lompad_exported, True)
                        # print(ejemplo)
                        return ejemplo
                    except Exception as e:
                        # print("======>")
                        print(e)
        else:
            for key1 in dispatchLomes.keys():
                if key in key1:
                    try:
                        metodo = dispatchLomes[key1]
                        ejemplo = metodo(dict(dictionary), is_lompad_exported, True)
                        # print(ejemplo)
                        return ejemplo
                    except Exception as e:
                        # print("======>")
                        print(e)
    except KeyError as ke:
        logging.error(f' Unexpected key {key}, ignoring key, error {ke}')
    except Exception as ex:
        logging.error(f' Error: {ex}')
        print(traceback.format_exc())


def get_keywords(object_data: list):
    """
    Special case function.
    The can be many keywords inside general leaf, so this function get its value and stores it inside a list.

    :param object_data: List of OrderedDict.
    :return: extracted values.
    """
    values = []
    for value in object_data:
        if type(value) is OrderedDict and 'string' in value.keys() and '#text' in value['string'].keys():
            values.append(value['string']['#text'])
        elif type(value) is OrderedDict and '#text' in value.keys():
            values.append(value['#text'])
    return values


def set_values_to_dict(data, key, key2,values_labels_dict:dict, type_values):

    if type_values == "str":
        if data[key] is None:
            data[key]="None"
        if key not in values_labels_dict.keys():
            values_labels_dict[key]=[data[key]]
        else:
            values_labels_dict.get(key).append(data[key])
    else:
        if data[key2] is None:
            data[key2]="None"
        if key not in values_labels_dict.keys():
            values_labels_dict[key]=[data[key2]]
        else:
            values_labels_dict.get(key).append(data[key2])


def map_attributes(data_original: dict, object_instance, is_lom):

    data_original=collections.OrderedDict(data_original)
    data = data_original.copy()
    """
    What a nice function, isn't it? (Just kidding).

    Extracts meaningful information from dict nodes and stores inside an object instance, inside nodes can be different
    types of information:
    - String
    - Date (as string)

    There are different ways that ExeLearning saves a string that's the why of too many ifs.

    :param data: An ordered dict which contains the information to be extracted.
    :param object_instance: An instance of Any LOM leaf class or its subclasses.
    :return: an object containing parsed information.
    """
    values_labels_dict={}

    if data is not None and not isinstance(data, list):
        attributes = object_instance.__dir__()
        
        #print("===============================================================")
        # print(attributes)
        # print(object_instance)
        hijo=None
        values_labels=[]
        values_labels_dict={}
        # print(data)
        #print("Datos #177: ",data)
        try:
            for key in data:
                #print("padre: ", key)
                key_mapping=key.replace('lomes:', '')
                # print(key_mapping)
                if key_mapping == "keyword":
                    key_mapping="keywordd"
                key_mapping_Upper=key_mapping.capitalize()
                if key_mapping_Upper == "Rol":
                    key_mapping_Upper="CRol"
                if isinstance(data[key], str):
                    set_values_to_dict(data, key,key,values_labels_dict,"str")
                    #print("LOM Model #190: ",values_labels_dict)
                else:
                    for childrens in data[key]:
                        # print("hijo: ",childrens)
                        if isinstance(childrens, str):
                            containerOfFather=data[key]
                            for val in containerOfFather:
                                # print("nieto: ", containerOfFather[val])
                                containerOfChildren=containerOfFather[val]
                                if isinstance(containerOfChildren, collections.OrderedDict):
                                    for val2 in containerOfChildren:
                                        # print("objeto de objeto: ", containerOfChildren[val2])
                                        if isinstance(containerOfChildren[val2], str) or isinstance(containerOfChildren[val2], list):
                                            set_values_to_dict(containerOfChildren, val2,val2,values_labels_dict,"str")
                                        else:
                                            auxContainerofChildren=containerOfChildren[val2]
                                            for valAuxContChildren in auxContainerofChildren:
                                                if isinstance(auxContainerofChildren[valAuxContChildren], str):
                                                    set_values_to_dict(auxContainerofChildren, val2,valAuxContChildren,values_labels_dict,"for")
                                                else:
                                                    containterAux=auxContainerofChildren[valAuxContChildren]
                                                    for auxContainerAux in containterAux:
                                                        set_values_to_dict(containterAux, val2,auxContainerAux,values_labels_dict,"for")
                                    #print("LOM Model #213: ",values_labels_dict)
                                else:
                                    # print("data key con object: ", containerOfChildren)
                                    #print("LOM Model #216: ",values_labels_dict)
                                    if containerOfChildren is None:
                                            containerOfChildren="None"
                                    elif val not in values_labels_dict.keys():
                                        values_labels_dict[val]=[containerOfChildren]
                                        values_labels.append(containerOfChildren)
                                    else:
                                        values_labels_dict.get(val).append(containerOfChildren)
                                        values_labels.append(containerOfChildren)
                            break
                        else:
                            for val_children in childrens:
                                # print("val childrens: ", childrens[val_children])
                                if isinstance(childrens[val_children],str):
                                    if childrens[val_children] is None:
                                            childrens[val_children]="None"
                                    if val_children not in values_labels_dict.keys():
                                        values_labels_dict[val_children]=[childrens[val_children]]
                                    else:
                                        values_labels_dict.get(val_children).append(childrens[val_children])
                                    values_labels.append(childrens[val_children])
                                elif childrens[val_children] is None:
                                    if childrens[val_children] is None:
                                            childrens[val_children]="None"
                                    if val_children not in values_labels_dict.keys():
                                        values_labels_dict[val_children]=[childrens[val_children]]
                                    else:
                                        values_labels_dict.get(val_children).append(childrens[val_children])
                                    values_labels.append(childrens[val_children])
                                else:
                                    containerOfChildren=childrens[val_children]
                                    # print("no se que poner: ",containerOfChildren)
                                    if isinstance(containerOfChildren, collections.OrderedDict):
                                        for val2 in containerOfChildren:
                                            if containerOfChildren[val2] is None:
                                                containerOfChildren[val2]="None"
                                            if isinstance(containerOfChildren[val2], collections.OrderedDict):
                                                container_container=containerOfChildren[val2]
                                                for val3 in container_container:
                                                    # print("val val val children: ", container_container[val3])
                                                    
                                                    if isinstance(container_container[val3], str):
                                                        if val3 not in values_labels_dict.keys():
                                                            values_labels_dict[val3]=[container_container[val3]]
                                                        else:
                                                            values_labels_dict.get(val3).append(container_container[val3])
                                                        values_labels.append(container_container[val3])
                                                    else:
                                                        aux_container_container=container_container[val3]
                                                        for val_aux_container_container in aux_container_container:
                                                            if val_aux_container_container not in values_labels_dict.keys():
                                                                values_labels_dict[val_aux_container_container]=[aux_container_container[val_aux_container_container]]
                                                            else:
                                                                values_labels_dict.get(val_aux_container_container).append(aux_container_container[val_aux_container_container])
                                                            values_labels.append(aux_container_container[val_aux_container_container])
                                            else:
                                                # print("val val  childrens: ", containerOfChildren[val2])
                                                if val2 not in values_labels_dict.keys():
                                                    values_labels_dict[val2]=[containerOfChildren[val2]]
                                                else:
                                                    values_labels_dict.get(val2).append(containerOfChildren[val2])
                                                values_labels.append(containerOfChildren[val2])
                                
                # print(values_labels)
                # print(values_labels_dict)
                #print("LOM Model #278: ",values_labels_dict)
                #print("LOM Model #279: ",key_mapping_Upper)
                #print("LOM Model #280: ",key_mapping)
                children_label=object_instance.__getattribute__(key_mapping_Upper)()
                children_label.addValues(values_labels_dict)
                #print("Datos: #283 ",values_labels_dict.get('value'))
                values_labels=[]   
                values_labels_dict={}
                if key_mapping == "aggregationLevel":
                    key_mapping="aggregation_level"
                #print("Datos: #287",key_mapping," : ", children_label.get('version'))
                object_instance.__setattr__(key_mapping, children_label)
                #print("=================================")
        except Exception as e:
            print("Error:", e)
    
    return object_instance


def general_leaf(data: dict, is_lom, is_read_or_upload):
    """
    Function to map General Leaf.

    :param data: data from manifest.
    :return: a General class instance. 
    """             

    # print(data)

    from .Estructuras.General import General

    cGeneral= General()
    if is_read_or_upload:
        general_object = map_attributes(data, cGeneral, is_lom)
        del cGeneral
        return general_object.__dict__(), general_object
    else:
        for val in data.keys():
            val2=val
            val2=val2.capitalize()
            if val2=="Keyword":
                val2="Keywordd"
            clase=cGeneral.__getattribute__(val2)()
            clase.addValues(data.get(val))
            if val == "aggregationLevel":
                    val="aggregation_level"
            if val=="keyword":
                val="keywordd"
            cGeneral.__setattr__(val, clase)
        return cGeneral

def life_cycle_leaf(data: dict, is_lom, is_read_or_upload):
    """
        Function to map Life Cycle Leaf.

        :param data: data from manifest.
        :return: a LifeCycle class instance.
        """
    from .Estructuras.LifeCycle import LifeCycle

    cLifeCycle=LifeCycle()

    if is_read_or_upload:
        general_object = map_attributes(data, cLifeCycle, is_lom)
        #print("Data: #338", general_object.__dict__().get('version'))
        del cLifeCycle
        return general_object.__dict__(), general_object
    else:
        for val in data.keys():
            #print("Val #342: ",val )
            val2=val
            val2=val2.capitalize()
            clase=cLifeCycle.__getattribute__(val2)()
            clase.addValues(data.get(val))
            cLifeCycle.__setattr__(val, clase)
        return cLifeCycle

def meta_metadata_leaf(data: dict, is_lom, is_read_or_upload):
    """
        Function to map Meta MetaData Leaf.

        :param data: data from manifest.
        :return: a MetaMetaData class instance.
        """
    from .Estructuras.MetaMEtadata import MetaMetadata

    cMetaMetadata= MetaMetadata()
    if is_read_or_upload:
        general_object = map_attributes(data, cMetaMetadata, is_lom)
        del cMetaMetadata
        return general_object.__dict__(), general_object
    else:
        for val in data.keys():
            val2=val
            val2=val2.capitalize()
            clase=cMetaMetadata.__getattribute__(val2)()
            clase.addValues(data.get(val))
            cMetaMetadata.__setattr__(val, clase)
        return cMetaMetadata


def technical_leaf(data: dict, is_lom, is_read_or_upload):
    """
        Function to map Technical Leaf.

        :param data: data from manifest.
        :return: a Technical class instance.
        """
    from .Estructuras.Technical import Technical
    
    cTechnical = Technical()  
    if is_read_or_upload:
        general_object = map_attributes(data, cTechnical, is_lom)
        del cTechnical
        return general_object.__dict__(), general_object
    else:
        for val in data.keys():
            val2=val
            val2=val2.capitalize()
            if val2=="Keyword":
                val2="Keywordd"
            clase=cTechnical.__getattribute__(val2)()
            clase.addValues(data.get(val))
            cTechnical.__setattr__(val, clase)
        return cTechnical


def educational_leaf(data: dict, is_lom, is_read_or_upload):
    """
        Function to map Educational Leaf.

        :param data: data from manifest.
        :return: a Educational class instance.
        """
    from .Estructuras.Educational import Educational

    cEducational=Educational()
    if is_read_or_upload:
        general_object = map_attributes(data, cEducational, is_lom)
        del cEducational
        return general_object.__dict__(), general_object
    else:
        for val in data.keys():
            val2=val
            val2=val2.capitalize()
            if val2=="Keyword":
                val2="Keywordd"
            clase=cEducational.__getattribute__(val2)()
            clase.addValues(data.get(val))
            cEducational.__setattr__(val, clase)
        return cEducational


def rights_leaf(data: dict, is_lom, is_read_or_upload):
    """
        Function to map Rights Leaf.

        :param data: data from manifest.
        :return: a Rights class instance.
        """
    from .Estructuras.Rights import Rights

    cRights = Rights()
    if is_read_or_upload:
        general_object = map_attributes(data, cRights, is_lom)
        del cRights
        return general_object.__dict__(), general_object
    else:
        for val in data.keys():
            val2=val
            val2=val2.capitalize()
            clase=cRights.__getattribute__(val2)()
            clase.addValues(data.get(val))
            #if val2=="Cost":
                #print("Rights #446: ",clase.__getattribute__("value"))
            cRights.__setattr__(val, clase)
        return cRights

def relation_leaf(data: dict, is_lom, is_read_or_upload):
    """
        Function to map Relation Leaf.

        :param data: data from manifest.
        :return: a Relation class instance.
        """
    from .Estructuras.Relation import Relation

    cRelation=Relation()
    if is_read_or_upload:
        general_object = map_attributes(data, cRelation, is_lom)
        del cRelation
        return general_object.__dict__(), general_object
    else:
        for val in data.keys():
            val2=val
            val2=val2.capitalize()
            if val2=="Keyword":
                val2="Keywordd"
            clase=cRelation.__getattribute__(val2)()
            clase.addValues(data.get(val))
            cRelation.__setattr__(val, clase)
        return cRelation


def annotation_leaf(data: dict, is_lom, is_read_or_upload):

    """
        Function to map Annotation Leaf.

        :param data: data from manifest.
        :return: a Annotation class instance.
        """
    from .Estructuras.Anotation import Annotation

    cAnnotation=Annotation()
    #print("LOM ES # 496: ", data)
    if is_read_or_upload:
        general_object = map_attributes(data, cAnnotation, is_lom)
        del cAnnotation
        return general_object.__dict__(), general_object
    else:
        for val in data.keys():
            val2=val
            #print("LOMEs #504 - Val2: ", val2)
            val2=val2.capitalize()
            #print("LOMEs #504 - Val2: ", val2)
            if val2=="Rol":
                val2="CRol"
            if val2=="AccessMode":
                val2="accessmode"
            if val2=="AccessModeSufficient":
                val2="accessmodesufficient"
            clase=cAnnotation.__getattribute__(val2)()
            clase.addValues(data.get(val))
            if val=="rol":
                val="Rol"
            if val=="accessmode":
                val="accessMode"
            if val=="accessModeSufficient":
                val="accessmodesufficient"
            cAnnotation.__setattr__(val, clase)
        return cAnnotation


def classification_leaf(data: dict, is_lom, is_read_or_upload):
    """
        Function to map Classification Leaf.

        :param data: data from manifest.
        :return: a Classification class instance.
        """
    from .Estructuras.Classification import Classification

    cClassification=Classification()
    if is_read_or_upload:
        general_object = map_attributes(data, cClassification, is_lom)
        del cClassification
        return general_object.__dict__(), general_object
    else:
        for val in data.keys():
            val2=val
            val2=val2.capitalize()
            if val2=="Keyword":
                val2="Keywordd"
            clase=cClassification.__getattribute__(val2)()
            clase.addValues(data.get(val))
            cClassification.__setattr__(val, clase)
        return cClassification


def accessibility_leaf(data: dict, is_lom, is_read_or_upload):
    from .Estructuras.Accessibility import Accessibility

    cAccessibility=Accessibility()
    if is_read_or_upload:
        general_object = map_attributes(data, cAccessibility, is_lom)
        del cAccessibility
        return general_object.__dict__(), general_object
    else:
        for val in data.keys():
            val2=val
            val2=val2.capitalize()
            if val2=="AccessibilityFeatures":
                val2="Accessibilityfeatures"
            if val2=="AccessibilityHazard":
                val2="Accessibilityhazard"
            if val2=="AccessibilityControl":
                val2="Accessibilitycontrol"
            if val2=="AccessibilityApi":
                val2="Accessibilityapi"
            clase=cAccessibility.__getattribute__(val2)()
            clase.addValues(data.get(val))
            if val=="accessibilityFeatures":
                val="accessibilityfeatures"
            if val=="accessibilityHazard":
                val="accessibilityhazard"
            if val=="accessibilityControl":
                val="accessibilitycontrol"
            if val=="accessibilityApi":
                val="accessibilityapi"
            cAccessibility.__setattr__(val, clase)
        return cAccessibility

dispatch = {
    'general': general_leaf, 'lifeCycle': life_cycle_leaf, 'metaMetadata': meta_metadata_leaf,
    'technical': technical_leaf, 'educational': educational_leaf,
    'rights': rights_leaf, 'relation': relation_leaf, 'annotation': annotation_leaf,
    'classification': classification_leaf, 'accesibility': accessibility_leaf
}

dispatch_update = {
    'general': general_leaf, 'lifeCycle': life_cycle_leaf, 'metaMetadata': meta_metadata_leaf,
    'technical': technical_leaf, 'educational': educational_leaf,
    'rights': rights_leaf, 'relation': relation_leaf, 'annotation': annotation_leaf,
    'classification': classification_leaf, 'accesibility': accessibility_leaf
}

dispatchLomes = {
    'lomes:general': general_leaf, 'lomes:lifeCycle': life_cycle_leaf, 'lomes:metaMetadata': meta_metadata_leaf,
    'lomes:technical': technical_leaf, 'lomes:educational': educational_leaf,
    'lomes:rights': rights_leaf, 'lomes:relation': relation_leaf, 'lomes:annotation': annotation_leaf,
    'lomes:classification': classification_leaf, 'accesibility': accessibility_leaf
}

dispatch_updateLomes = {
    'lomes:general': general_leaf, 'lomes:lifeCycle': life_cycle_leaf, 'lomes:metaMetadata': meta_metadata_leaf,
    'lomes:technical': technical_leaf, 'lomes:educational': educational_leaf,
    'lomes:rights': rights_leaf, 'lomes:relation': relation_leaf, 'lomes:annotation': annotation_leaf,
    'lomes:classification': classification_leaf, 'accesibility': accessibility_leaf
}


def update_leaf(leaf, model, data):
    # print('UPDATE')
    # print(data)
    data=data.replace('[null]','[]')
    data=data.replace(';','')
    data=data.replace("\n",'')
    data=data.replace("\\n",'')
    data=data.replace("\n ",'')
    data=data.replace("\\n ",'')
    data=data.replace("  ",' ')
    import json
    data_as_dict = json.loads(data)
    # print(data_as_dict)
    metodo = dispatch_update.get(leaf)
    model.__setattr__(leaf, metodo(data_as_dict, True, False))
    return model
