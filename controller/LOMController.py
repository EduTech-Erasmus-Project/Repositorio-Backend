from collections import OrderedDict
from pprint import pprint
import pickle
import xmltodict
from model import LOMModel, LOMESModel
from lxml import etree


class Controller:
    _leafs = ['lom:general', 'lom:lifeCycle', 'lom:metaMetadata', 'lom:technical', 'lom:educational',
              'lom:rights', 'lom:relation', 'lom:annotation', 'lom:classification', 'accesibility']

    _leafsLomes = ['lomes:general', 'lomes:lifeCycle', 'lomes:metaMetadata', 'lomes:technical', 'lomes:educational',
              'lomes:rights', 'lomes:relation', 'lomes:annotation', 'lomes:classification', 'accesibility']

    _leafsPure = ['general', 'lifeCycle', 'metaMetadata', 'technical', 'educational',
              'rights', 'relation', 'annotation', 'classification', 'accesibility']

    _mapped_data = dict()
    _object_dict = dict()

    def parse_str_to_dict(self, data: str) -> OrderedDict:
        """
        Parse a valid xml (string) to Python OrderedDict class (Subclass of Dict class).

        :param data: A valid XML string.
        :type data str

        :return: An instance of OrderedDict
        """
        return xmltodict.parse(data)

    def map_recursively(self, dictionary: dict, booleanLomLomes,is_lompad_exported=False):
        """
        Based on an OrderedDict this method map recursively the Dictionary to Python Class.

        :param dictionary: A valid Dict or OrderedDict
        :param is_lompad_exported: Check if manifest comes from lompad application.

        :return: None
        """
        if booleanLomLomes==True:
            for key, value in dictionary.items():
                if isinstance(dictionary[key], dict):
                    if any(key in leaf for leaf in self._leafs) and key != 'lom':
                        
                        self._mapped_data[key], self._object_dict[key] = LOMModel.determine_lompad_leaf(dictionary[key], str(key),
                                                                                is_lompad_exported)

                    self.map_recursively(dictionary[key], booleanLomLomes,is_lompad_exported)
        else: 
            for key, value in dictionary.items():
                if isinstance(dictionary[key], dict):
                    if any(key in leaf for leaf in self._leafsLomes) and key != 'lomes:lom':

                        self._mapped_data[key], self._object_dict[key] = LOMESModel.determine_lompad_leaf(dict(dictionary[key]), str(key),
                                                                                is_lompad_exported)
                    
                    self.map_recursively(dictionary[key], booleanLomLomes,is_lompad_exported)

    def get_mapped_manifest(self, object_name, booleanLomLomes):
        self.get_object(object_name, booleanLomLomes)
        return self._mapped_data

    def get_mapped_class(self):
        lom_object = LOMESModel.LOM()
        for key, value in self._object_dict.items():
            lom_object.__setattr__(key, value)
        return lom_object

    def get_object(self, object_name, booleanLomLomes):
        if booleanLomLomes==True:
            lom_object =LOMModel.LOM()
            for key, value in self._object_dict.items():
                key = 'keywordd' if key == 'keyword' else key
                key = 'rol' if key == 'Rol' else key
                lom_object.__setattr__(key, value)

            with open('temp_files/'+object_name+'_exported.xml', 'w') as file:
                file.write(lom_object.to_xml().strip())
                
        else:
            lom_object =LOMESModel.LOM()
            for key, value in self._object_dict.items():
                if "lomes:" in key:
                    key = key.split(':')[1]
                key = 'keywordd' if key == 'keyword' else key
                key = 'rol' if key == 'Rol' else key
                lom_object.__setattr__(key, value)
                # print(key)
                # print(value.__dir__())
                # print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            with open('temp_files/'+object_name+'_exported.xml', 'w') as file:
                file.write(lom_object.to_xml().strip())
