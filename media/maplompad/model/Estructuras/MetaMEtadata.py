class MetaMetadata:

        identifier = None
        contribute = None
        metadataSchema = None
        language = None

        def __init__(self, identifier=None, contribute=None, metadataSchema=None, language=None):
            self.identifier = identifier
            self.contribute = contribute
            self.metadataSchema = metadataSchema
            self.language = language

        class Identifier:
            catalog = []
            entry = []
            
            def __init__(self, catalog=[], entry=[]):
                self.catalog=catalog
                self.entry=entry
            
            def addValues(self,atributes):
                self.catalog=atributes.get('catalog')
                if self.catalog is None:
                    self.catalog=atributes.get('lomes:catalog')
                try:
                    if isinstance(self.catalog[0], list):
                        self.catalog=self.catalog[0]
                except Exception as e: 
                    print(e)

                self.entry=atributes.get('entry')
                if self.entry is None:
                    self.entry=atributes.get('lomes:entry')
                try:
                    if isinstance(self.entry[0], list):
                        self.entry=self.entry[0]
                except Exception as e: 
                    print(e)

            def to_xml(self):
                return f"""<identifier>
                <catalog>{self.catalog}</catalog>
                <entry>{self.entry}</entry>
                </identifier>"""

            def __dict__(self):
                return {'catalog': self.catalog, 'entry': self.entry}
        
        class Metadataschema:

            value = []

            def __init__(self, value=[]):
                self.value = value
            
            def addValues(self,atributes):
                self.value=atributes.get('metadataSchema')
                if self.value is None:
                    self.value=atributes.get('lomes:metadataSchema')
                try:
                    if isinstance(self.value[0], list):
                        self.value=self.value[0]
                except Exception as e: 
                    print(e)

            def to_xml(self):
                return f"""<metadataSchema>{self.value}</metadataSchema>"""

            def __dict__(self):
                return {'metadataSchema': self.value}
        
        class Language:
            value = []

            def __init__(self, value=[]):
                self.value = value
            
            def addValues(self,atributes):
                self.value=atributes.get('language')
                if self.value is None:
                    self.value=atributes.get('lomes:language')
                try:
                    if isinstance(self.value[0], list):
                        self.value=self.value[0]
                except Exception as e: 
                    print(e)

            def to_xml(self):
                return f"""<language>{self.value}</language>"""

            def __dict__(self):
                return {'language': self.value}


        class Contribute:
            source=[]
            value=[]
            entity=[]
            dateTime=[]
            description=[]

            def __init__(self, source=[], value=[], entity=[], dateTime=[], description=[]):
                self.source = source
                self.value = value
                self.entity = entity
                self.dateTime = dateTime
                self.description = description
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                if self.source is None:
                    self.source=atributes.get('contribute')
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

                self.entity=atributes.get('entity')
                try:
                    if isinstance(self.entity[0], list):
                        self.entity=self.entity[0]
                except Exception as e: 
                    print(e)

                self.dateTime=atributes.get('dateTime')
                if self.dateTime is None:
                    self.dateTime=atributes.get('date')
                try:
                    if isinstance(self.dateTime[0], list):
                        self.dateTime=self.dateTime[0]
                except Exception as e: 
                    print(e)

                self.description=atributes.get('description')
                try:
                    if isinstance(self.description[0], list):
                        self.description=self.description[0]
                except Exception as e: 
                    print(e)

            def to_xml(self):
                return f"""<contribute>
                <role>
                <source>{self.source}</source>
                <value>{self.value}</value>
                </role>
                <entity>{self.entity}
                </entity>
                <date>
                <dateTime>{self.dateTime}</dateTime>
                <description>
                <string>{self.description}</string>
                </description>
                </date>
                </contribute>"""

            def __dict__(self):
                return {'source': self.source, 'value': self.value, 'entity': self.entity, 
                'date': self.dateTime, 'description':self.description}

        def to_xml(self):
            return f"""<metaMetadata>
            {'' if isinstance(self.identifier, str) else self.identifier.to_xml() if self.identifier is not None else ''}
            {'' if isinstance(self.metadataSchema, str) else self.metadataSchema.to_xml() if self.metadataSchema is not None else ''}
            {'' if isinstance(self.language, str) else self.language.to_xml() if self.language is not None else ''}
            {'' if isinstance(self.contribute, str) else self.contribute.to_xml() if self.contribute is not None else ''}
            </metaMetadata>"""

        def __dict__(self):
            return {
                'identifier': self.identifier.__dict__() if self.identifier is not None else {'catalog': [], 'entry': []},
                'metadataSchema': self.metadataSchema.__dict__() if self.metadataSchema is not None else {'metadataSchema': []},
                'language': self.language.__dict__() if self.language is not None else {'language': []},
                'contribute': self.contribute.__dict__() if self.contribute is not None else {'source': [], 'value': [], 'entity': [], 'date': [], 'description':[]}}