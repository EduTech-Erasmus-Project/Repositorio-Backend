class LifeCycle:
        version = None
        status = None
        contribute = None

        def __init__(self, version=None, status=None, contribute=None):
            self.version = version
            self.status = status
            self.contribute = contribute

        class Contribute:
            source = []
            value = []
            entity = []
            datetime = []
            description_string = []

            def __init__(self, source=[], value=[], entity=[], datetime=[], description_string=[]):
                self.source=source
                self.value=value
                self.entity=entity
                self.datetime=datetime
                self.description_string=description_string
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                if self.source is None:
                    self.source=atributes.get('lomes:source')
                
                self.value=atributes.get('value')
                if self.value is None:
                    self.value=atributes.get('lomes:value')
                if self.value is None:
                    self.value=atributes.get('role')
                
                self.entity=atributes.get('entity')
                if self.entity is None:
                    self.entity=atributes.get('lomes:entity')

                self.datetime=atributes.get('dateTime')
                if self.datetime is None:
                    self.datetime=atributes.get('lomes:dateTime')
                    
                self.description_string=atributes.get('es')
                if self.description_string is None:
                    self.description_string=atributes.get('description')
                    if self.description_string is None:
                         self.description_string=atributes.get('lomes:string')
                    elif len(self.description_string) > 1:
                        self.description_string=[atributes.get('description')[1]]

            def __dict__(self):
                return {'source': self.source, 'role': self.value, 'entity': self.entity, 'dateTime': self.datetime, 'description': self.description_string}

            def to_xml(self):
                return f"""<contribute>
                <role>
                <source>{self.source}</source>
                <value>{self.value}</value>
                </role>
                <entity>{self.entity}</entity>
                <date>
                <dateTime>{self.datetime}</dateTime>
                <description>
                <string>{self.description_string}</string>
                </description>
                </date>
                </contribute>"""
        
        class Version:
            string=[]

            def __init__(self, string=[]):
                self.string = string
            
            def addValues(self,atributes):
                #print("life: #77",atributes )
                self.string=atributes.get('#text')
                #print("Life #78 ",atributes.get('#text'))
                if self.string is None:
                    self.string=atributes.get('version')
                elif self.string is None:
                    self.string=atributes.get('string')

            def to_xml(self):
                return f"""<version>
                <string>{self.string}</string>
                </version>"""

            def __dict__(self):
                return {'version': self.string}

        class Status:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                ##print("Life #100 ",atributes.get('value'))
                self.value=atributes.get('value')

            def to_xml(self):
                return f"""<status>
                                <source>{self.source}</source>
                                <value>{self.value}</value>
                            </status>"""

            def __dict__(self):
                return {'source': self.source, 'value': self.value}
        
        def __dict__(self):
            return {'version': self.version.__dict__() if self.version is not None else {'version': []},
                    'status': self.status.__dict__() if self.status is not None else {'source': [], 'value': []},
                    'contribute': self.contribute.__dict__() if self.contribute is not None else {'source': [], 'role': [], 'entity': [], 'dateTime': [], 'description': []}}

        def to_xml(self):
            return f"""<lifeCycle>
                {'' if isinstance(self.version, str) else self.version.to_xml() if self.version is not None else ''}               
                {'' if isinstance(self.status, str) else self.status.to_xml() if self.status is not None else ''}
                {'' if isinstance(self.contribute, str) else self.contribute.to_xml() if self.contribute is not None else ''}
            </lifeCycle>"""