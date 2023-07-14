class General:
        identifier = None
        title = None
        language = None
        description = None
        keywordd = None
        coverage = None
        structure = None
        aggregation_level = None

        def __init__(self, identifier=None, title=None, language=None, description=None, keywordd=None, coverage=None,
                     structure=None, aggregation_level=None):
            self.identifier = identifier
            self.title = title
            self.language = language
            self.description = description
            self.keywordd = keywordd
            self.coverage = coverage
            self.structure = structure
            self.aggregation_level = aggregation_level

        class Identifier:
            catalog = []
            entry = []

            def __init__(self, catalog=[], entry=[]):
                self.catalog = catalog
                self.entry = entry
            
            def addValues(self,atributes):
                self.catalog=atributes.get('lomes:catalog')
                self.entry=atributes.get('lomes:entry')
                    
            def getValues(self):
                print("Catalog: ", self.catalog)
                print("Entry: ", self.entry)

            def to_xml(self):
                return f"""<identifier>
                <catalog>{self.catalog}</catalog>
                <entry>{self.entry}</entry>
                </identifier>"""

            def __dict__(self):
                return {'Catalog': self.catalog, 'Entry': self.entry}

        class Title:
            language=[]
            title=[]

            def __init__(self, language=[], title=[]):
                self.language = language
                self.title = title
            
            def addValues(self,atributes):
                self.language=atributes.get('@language')
                self.title=atributes.get('#text')
                    
            def getValues(self):
                print("Language: ", self.language)
                print("Title: ", self.title)

            def to_xml(self):
                return f"""<title>
                <string language="{self.language}">{self.title}</string>
                </title>"""

            def __dict__(self):
                return {'Language': self.language, 'Title': self.title}
        
        class Language:
            language=[]

            def __init__(self, language=[]):
                self.language = language
            
            def addValues(self,atributes):
                    self.language=atributes.get('lomes:language')
                    
            def getValues(self):
                print("Language: ", self.language)
            

            def to_xml(self):
                return f"""<language>{self.language}</language>"""

            def __dict__(self):
                return {'Language': self.language}
        
        class Description:

            language=[]
            description=[]

            def __init__(self, language=[], description=[]):
                self.language = language
                self.description = description
            
            def addValues(self,atributes):
                self.language=atributes.get('@language')
                self.description=atributes.get('#text')
                    
            def getValues(self):
                print("Languaje: ", self.language)
                print("Description: ", self.description)

            def to_xml(self):
                return f"""<description>
                <string language="{self.language}">{self.description}</string>
                </description>"""

            def __dict__(self):
                return {'Language': self.language, 'Description': self.description}
        
        class Keywordd:

            language=[]
            keywordd=[]

            def __init__(self, language=[], keywordd=[]):
                self.language = language
                self.keywordd = keywordd
            
            def addValues(self,atributes):
                self.language=atributes.get('@language')
                self.keywordd=atributes.get('#text')
            def getValues(self):
                print("Languaje: ", self.language)
                print("Keyword: ", self.keywordd)

            def to_xml(self):
                return f"""<string  language="{self.language}">{self.keywordd}</string>"""

            def __dict__(self):
                return {'Language': self.language, 'Keyword': self.keywordd}
        
        class Aggregationlevel:

            source=[]
            value=[]

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                for i in range(len(atributes)):
                    if i%2==0:
                        self.source.append(atributes[i])
                    else:
                        self.value.append(atributes[i])
                    
            def getValues(self):
                print("Source: ", self.source)
                print("Value: ", self.value)

            def to_xml(self):
                return f"""<aggregationLevel>
                <source>{self.source}</source>
                <value>{self.value}</value>
                </aggregationLevel>"""

            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}

        def get_keyword(self):
            if type(self.keywordd) is list:
                elements = []
                for element in self.keywordd:
                    elements.append(f'{element},')
                return elements
            else:
                return self.keywordd

        def get_xml_keywords(self):
            if type(self.keywordd) is list:
                content = ""
                for key in self.keywordd:
                    content += f"""<lomes:string language="en">{key}</lomes:string>\n"""
                return content
            else:
                return self.keywordd
        
        class Coverage:

            language=[]
            coverage=[]

            def __init__(self, language=[], coverage=[]):
                self.language = language
                self.coverage = coverage
            
            def addValues(self,atributes):
                for i in range(len(atributes)):
                    if i%2==0:
                        self.language.append(atributes[i])
                    else:
                        self.coverage.append(atributes[i])
                    
            def getValues(self):
                print("Language: ", self.language)
                print("Coverage: ", self.coverage)

            def to_xml(self):
                return f"""<coverage>
                <string language="{self.language}">{self.coverage}</string>
                </coverage>"""

            def __dict__(self):
                return {'Language': self.language, 'Coverage': self.coverage}
        
        class Structure:
            source=[]
            value=[]

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                for i in range(len(atributes)):
                    if i%2==0:
                        self.source.append(atributes[i])
                    else:
                        self.value.append(atributes[i])
                    
            def getValues(self):
                print("Source: ", self.language)
                print("Value: ", self.coverage)

            def to_xml(self):
                return f""" <structure>
                <source>{self.source}</source>
                <value>{self.value}</value>
                </structure>"""

            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}

        def to_xml(self):
            return f"""<general>
                {'' if isinstance(self.identifier, str) else self.identifier.to_xml() if self.identifier is not None else ''}
                {'' if isinstance(self.title, str) else self.title.to_xml() if self.title is not None else ''}
                {'' if isinstance(self.language, str) else self.language.to_xml() if self.language is not None else ''}
                {'' if isinstance(self.description, str) else self.description.to_xml() if self.description is not None else ''}
                {'' if isinstance(self.keywordd, str) else self.keywordd.to_xml() if self.keywordd is not None else ''}
                {'' if isinstance(self.coverage, str) else self.coverage.to_xml() if self.coverage is not None else ''}
                {'' if isinstance(self.structure, str) else self.structure.to_xml() if self.structure is not None else ''}
                {'' if isinstance(self.aggregation_level, str) else self.aggregation_level.to_xml() if self.aggregation_level is not None else ''}
            </general>"""

        def __dict__(self):
            return {'Identifier': self.identifier.__dict__() if self.identifier is not None else [],
                    'Title': self.title.__dict__() if self.title is not None else [], 
                    'Language': self.language.__dict__() if self.language is not None else [],
                    'Description': self.description.__dict__() if self.description is not None else [],
                    'keyword': self.keywordd.__dict__() if self.keywordd is not None else [],
                    'Coverage': self.coverage.__dict__() if self.coverage is not None else [],
                    'Structure': self.structure.__dict__() if self.structure is not None else [],
                    'Aggregation Level': self.aggregation_level.__dict__() if self.aggregation_level is not None else []}
