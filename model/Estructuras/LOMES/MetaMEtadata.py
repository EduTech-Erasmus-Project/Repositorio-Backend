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
                self.catalog=atributes.get('lomes:catalog')
                self.entry=atributes.get('lomes:entry')


            def to_xml(self):
                return f"""<identifier>
                <catalog>{self.catalog}</catalog>
                <entry>{self.entry}</entry>
                </identifier>"""

            def __dict__(self):
                return {'Catalog': self.catalog, 'Entry': self.entry}
        
        class Metadataschema:

            value = []

            def __init__(self, value=[]):
                self.value = value
            
            def addValues(self,atributes):
                self.value=atributes.get('lomes:metadataSchema')


            def to_xml(self):
                return f"""<metadataSchema>{self.value}</metadataSchema>"""

            def __dict__(self):
                return {'Values': self.value}
        
        class Language:
            value = []

            def __init__(self, value=[]):
                self.value = value
            
            def addValues(self,atributes):
                self.value=atributes.get('lomes:language')


            def to_xml(self):
                return f"""<language>{self.value}</language>"""

            def __dict__(self):
                return {'Values': self.value}


        class Contribute:
            role = None
            entity = None
            date = None

            def __init__(self, role='', entity='', date=''):
                self.role = role
                self.entity = entity
                self.date = date

            def to_xml(self):
                return f"""<contribute>
                <role>
                <source>LOMv1.0</source>
                <value>{self.role}</value>
                </role>
                <entity>
                <![CDATA[{self.entity}]]>
                </entity>
                <date>
                <dateTime>{self.date}</dateTime>
                <description>
                <string language="en">EMPTY</string>
                </description>
                </date>
                </contribute>"""

            def __dict__(self):
                return {'Role': self.role, 'Entity': self.entity, 'Date': self.date}

        def to_xml(self):
            return f"""<metaMetadata>
            {'' if isinstance(self.identifier, str) else self.identifier.to_xml() if self.identifier is not None else ''}
            {'' if isinstance(self.metadataSchema, str) else self.metadataSchema.to_xml() if self.metadataSchema is not None else ''}
            {'' if isinstance(self.language, str) else self.language.to_xml() if self.language is not None else ''}
            </metaMetadata>"""

        def __dict__(self):
            return {
                'Identifier': self.identifier.__dict__() if self.identifier is not None else self.Identifier().__dict__(),
                'MetadataSchema': self.metadataSchema.__dict__() if self.metadataSchema is not None else self.Metadataschema().__dict__(),
                'Language': self.language.__dict__() if self.language is not None else self.Language().__dict__()}