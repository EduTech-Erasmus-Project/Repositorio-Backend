import collections
import logging
import traceback
from collections import OrderedDict
from pprint import pprint
from typing import Container
from fuzzywuzzy import fuzz, process
from .Estructuras.LOM.General import General
from .Estructuras.LOM.LifeCycle import LifeCycle
from .Estructuras.LOM.MetaMEtadata import MetaMetadata
from .Estructuras.LOM.Technical import Technical
from .Estructuras.LOM.Educational import Educational
from .Estructuras.LOM.Rights import Rights
from .Estructuras.LOM.Relation import Relation
from .Estructuras.LOM.Anotation import Annotation
from .Estructuras.LOM.Classification import Classification
from .Estructuras.LOM.Accessibility import Accessibility

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

    General = General()

    LifeCycle = LifeCycle()
    
    MetaMetadata = MetaMetadata()

    Technical = Technical()

    Educational = Educational()

    Rights = Rights()

    Relation = Relation()    

    Annotation = Annotation()

    Classification = Classification()

    Accessibility = Accessibility()    

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
        return {'General': self.general.__dict__() if self.general is not None else self.General().__dict__(),
                'Life Cycle': self.lifeCycle.__dict__() if self.lifeCycle is not None else self.LifeCycle().__dict__(),
                'Meta-Metadata': self.metaMetadata.__dict__() if self.metaMetadata is not None else self.MetaMetadata().__dict__(),
                'Technical': self.technical.__dict__() if self.technical is not None else self.Technical().__dict__(),
                'Educational': self.educational.__dict__() if self.educational is not None else self.Educational().__dict__(),
                'Rights': self.rights.__dict__() if self.rights is not None else self.Rights().__dict__(),
                'Relation': self.relation.__dict__() if self.relation is not None else self.Relation().__dict__(),
                'Annotation': self.annotation.__dict__() if self.annotation is not None else self.Annotation().__dict__(),
                'Classification': self.classification.__dict__() if self.classification is not None else self.Classification().__dict__(),
                'Accessibility': self.accesibility.__dict__() if self.accesibility is not None else self.Accessibility().__dict__()}


def determine_lompad_leaf(dictionary: dict, key: str, is_lompad_exported=False):
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
        for key1 in dispatch.keys():
            if key in key1:
                print(key1)
                try:
                    metodo = dispatch[key1]
                    ejemplo = metodo(dict(dictionary), is_lompad_exported)
                    # print(ejemplo)
                    return ejemplo
                except Exception as e:
                    print("======>")
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
        
        print("===============================================================")
        # print(attributes)
        # print(object_instance)
        hijo=None
        values_labels=[]
        values_labels_dict={}
        # print(data)
        try:
            for key in data:
                print("padre: ", key)
                key_mapping=key.replace('lomes:', '')
                # print(key_mapping)
                if key_mapping == "keyword":
                    key_mapping="keywordd"
                key_mapping_Upper=key_mapping.capitalize()
                if isinstance(data[key], str):
                    # print("hijo1: ", data[key])
                    if data[key] is None:
                        data[key]="None"
                    if key not in values_labels_dict.keys():
                        values_labels_dict[key]=[data[key]]
                    else:
                        values_labels_dict.get(key).append(data[key])
                    values_labels.append(data[key])
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
                                            if containerOfChildren[val2] is None:
                                                containerOfChildren[val2]="None"
                                            elif val2 not in values_labels_dict.keys():
                                                values_labels_dict[val2]=[containerOfChildren[val2]]
                                            else:
                                                values_labels_dict.get(val2).append(containerOfChildren[val2])
                                                values_labels.append(containerOfChildren[val2])
                                        else:
                                            auxContainerofChildren=containerOfChildren[val2]
                                            for valAuxContChildren in auxContainerofChildren:
                                                if isinstance(auxContainerofChildren[valAuxContChildren], str):
                                                    if auxContainerofChildren[valAuxContChildren] is None:
                                                        containerOfChildren[val2]="None"
                                                    elif val2 not in values_labels_dict.keys():
                                                        values_labels_dict[val2]=[auxContainerofChildren[valAuxContChildren]]
                                                    else:
                                                        values_labels_dict.get(val2).append(auxContainerofChildren[valAuxContChildren])
                                                        values_labels.append(auxContainerofChildren[valAuxContChildren])
                                                else:
                                                    containterAux=auxContainerofChildren[valAuxContChildren]
                                                    for auxContainerAux in containterAux:
                                                        if containterAux[auxContainerAux] is None:
                                                            containerOfChildren[val2]="None"
                                                        elif val2 not in values_labels_dict.keys():
                                                            values_labels_dict[val2]=[containterAux[auxContainerAux]]
                                                        else:
                                                            values_labels_dict.get(val2).append(containterAux[auxContainerAux])
                                                            values_labels.append(containterAux[auxContainerAux])
                                else:
                                    # print("data key con object: ", containerOfChildren)
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
                                    if isinstance(containerOfChildren, collections.OrderedDict):
                                        for val2 in containerOfChildren:
                                            if containerOfChildren[val2] is None:
                                                containerOfChildren[val2]="None"
                                            if isinstance(containerOfChildren[val2], collections.OrderedDict):
                                                container_container=containerOfChildren[val2]
                                                for val3 in container_container:
                                                    # print("val val val children: ", container_container[val3])
                                                    if val3 not in values_labels_dict.keys():
                                                        values_labels_dict[val3]=[container_container[val3]]
                                                    else:
                                                        values_labels_dict.get(val3).append(container_container[val3])
                                                    values_labels.append(container_container[val3])
                                            else:
                                                # print("val val  childrens: ", containerOfChildren[val2])
                                                if val2 not in values_labels_dict.keys():
                                                    values_labels_dict[val2]=[containerOfChildren[val2]]
                                                else:
                                                    values_labels_dict.get(val2).append(containerOfChildren[val2])
                                                values_labels.append(containerOfChildren[val2])
                                
                # print(values_labels)
                print(values_labels_dict)
                children_label=object_instance.__getattribute__(key_mapping_Upper)()
                children_label.addValues(values_labels_dict)
                # children_label.getValues()
                values_labels=[]   
                values_labels_dict={}
                if key_mapping == "aggregationLevel":
                    key_mapping="aggregation_level"
                # print(object_instance,": ",key_mapping)
                object_instance.__setattr__(key_mapping, children_label)
        except Exception as e:
            print(e)
    
    return object_instance


def general_leaf(data: dict, is_lom):
    """
    Function to map General Leaf.

    :param data: data from manifest.
    :return: a General class instance. 
    """             
    general_object = map_attributes(data, LOM.General, is_lom)
    return general_object.__dict__(), general_object


def life_cycle_leaf(data: dict, is_lom):
    """
        Function to map Life Cycle Leaf.

        :param data: data from manifest.
        :return: a LifeCycle class instance.
        """
    general_object = map_attributes(data, LOM.LifeCycle, is_lom)

    return general_object.__dict__(), general_object


def meta_metadata_leaf(data: dict, is_lom):
    """
        Function to map Meta MetaData Leaf.

        :param data: data from manifest.
        :return: a MetaMetaData class instance.
        """
    general_object = map_attributes(data, LOM.MetaMetadata, is_lom)

    return general_object.__dict__(), general_object


def technical_leaf(data: dict, is_lom):
    """
        Function to map Technical Leaf.

        :param data: data from manifest.
        :return: a Technical class instance.
        """
    technical_object = map_attributes(data, LOM.Technical, is_lom)

    return technical_object.__dict__(), technical_object


def educational_leaf(data: dict, is_lom):
    """
        Function to map Educational Leaf.

        :param data: data from manifest.
        :return: a Educational class instance.
        """
    educational_object = map_attributes(data, LOM.Educational, is_lom)

    return educational_object.__dict__(), educational_object


def rights_leaf(data: dict, is_lom):
    """
        Function to map Rights Leaf.

        :param data: data from manifest.
        :return: a Rights class instance.
        """
    rights_object = map_attributes(data, LOM.Rights, is_lom)

    return rights_object.__dict__(), rights_object


def relation_leaf(data: dict, is_lom):
    """
        Function to map Relation Leaf.

        :param data: data from manifest.
        :return: a Relation class instance.
        """
    relation_object = map_attributes(data, LOM.Relation, is_lom)

    return relation_object.__dict__(), relation_object


def annotation_leaf(data: dict, is_lom):
    """
        Function to map Annotation Leaf.

        :param data: data from manifest.
        :return: a Annotation class instance.
        """
    annotation_object = map_attributes(data, LOM.Annotation, is_lom)

    return annotation_object.__dict__(), annotation_object


def classification_leaf(data: dict, is_lom):
    """
        Function to map Classification Leaf.

        :param data: data from manifest.
        :return: a Classification class instance.
        """
    classification_object = map_attributes(data, LOM.Classification, is_lom)
    return classification_object.__dict__(), classification_object


def accessibility_leaf(data: dict, is_lom):
    accessibility_object = map_attributes(data, LOM.Accessibility, is_lom)
    return accessibility_object.__dict__(), accessibility_object


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


def update_leaf(leaf, model, data):
    print('UPDATE')
    import json
    data_as_dict = json.loads(data)
    metodo = dispatch_update.get(leaf)
    data = data_as_dict.copy()

    for key in data_as_dict.keys():
        components = str(key).lower().split(' ')
        components = components[0] + ''.join(x.title() for x in components[1:])
        data[components] = data.pop(key)

    model.__setattr__(leaf, metodo(data, True)[1])

    return model
