import string


class Relation:
        kind = None
        resource = None

        def __init__(self, kind=None, resource=None):
            self.kind = kind
            self.resource = resource
        
        class Kind:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                try:
                    if isinstance(self.source[0], list):
                        self.source=self.source[0]
                except Exception as e: 
                    print(e)

                self.value=atributes.get('value')
                try:
                    if isinstance(self.value[0], list):
                        self.value=self.value[0]
                except Exception as e: 
                    print(e)

            def to_xml(self):
                return f"""<kind>
                                <source>{self.source}</source>
                                <value>{self.value}</value>
                            </kind>"""
            def __dict__(self):
                return {'source': self.source, 'value': self.value}

        class Resource:
            catalog = []
            entry = []
            string = []

            def __init__(self, catalog=[], entry=[], string=[]):
                self.catalog = catalog
                self.entry = entry
                self.string = string

            def addValues(self,atributes):
                self.catalog=atributes.get('catalog')
                try:
                    if isinstance(self.catalog[0], list):
                        self.catalog=self.catalog[0]
                except Exception as e: 
                    print(e)

                self.entry=atributes.get('entry')
                try:
                    if isinstance(self.entry[0], list):
                        self.entry=self.entry[0]
                except Exception as e: 
                    print(e)

                self.string=atributes.get('description')
                #print("Rela #69 - Resource - atribites: ",atributes)
                #print("Rela #70 - Resource - atribites: ",self.string)
                if self.string is None:
                    self.string=atributes.get('#text')
                    if self.string is None:
                        self.string=atributes.get('string')
                        #print("Rela #75 - Resource - atribites: ",self.string)
                #print("Rela #76 - Resource - atribites: ",self.string)
                try:
                    if isinstance(self.string, list):
                        if(self.string[0]=='es'):
                            self.string.remove('es')
                        #print("Rela #80 - Resource - atribites: ",self.string)
                except Exception as e: 
                    print(e)
                    #print("*-/-/ Error Rela #83")
                #print("Rela #84 description ",self.string)

            def to_xml(self):
                return f"""<resource>
                                <identifier>
                                    <catalog>{self.catalog}</catalog>
                                    <entry>{self.entry}</entry>
                                </identifier>
                                <description>
                                    <string>{self.string}</string>
                                </description>
                            </resource>"""

            def __dict__(self):
                return {'catalog': self.catalog, 'entry': self.entry, 'description':self.string}

        def to_xml(self):
            return f"""<relation>
            {'' if isinstance(self.kind, str) else self.kind.to_xml() if self.kind is not None else ''}
            {'' if isinstance(self.resource, str) else self.resource.to_xml() if self.resource is not None else ''}
            </relation>"""

        def __dict__(self):
            return {'kind': self.kind.__dict__() if self.kind is not None else {'source': [], 'value': []},
                    'resource': self.resource.__dict__() if self.resource is not None else {'catalog': [], 'entry': [], 'description':[]}}