class Classification:
        purpose = None  # purpose
        taxonPath = None  # taxon_path
        description = None  # description
        keywordd = None  # keywordd

        def __init__(self, purpose=None, taxonPath=None, description=None, keywordd=None):
            self.purpose = purpose
            self.taxonPath = taxonPath
            self.description = description
            self.keywordd = keywordd
        
        class Purpose:

            source=[]
            value=[]

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                try:
                    self.source=atributes.get('source')
                except Exception as e:
                    print(e)
                if self.source is None:
                    self.source=atributes.get('lomes:source')
                try:
                    if isinstance(self.source[0], list):
                        self.source=self.source[0]
                except Exception as e: 
                    print(e)

                try:
                    self.value=atributes.get('value')
                except Exception as e:
                    print(e)
                if self.value is None:
                    self.value=atributes.get('lomes:value')
                try:
                    if isinstance(self.value[0], list):
                        self.value=self.value[0]
                except Exception as e: 
                    print(e)
                    

            def to_xml(self):
                return f"""<purpose>
                                <source>{self.source}</source>
                                <value>{self.value}</value>
                            </purpose>"""

            def __dict__(self):
                return {'source': self.source, 'value': self.value}
                
        class Taxonpath:
            string = []
            id = []
            entry = []
            def __init__(self, string=[], id=[], entry=[]):
                self.string = string
                self.id = id
                self.entry = entry
            
            def addValues(self,atributes):

                self.string=atributes.get('source')
                if self.string is None:
                    self.string=atributes.get('string')
                if self.string is None:
                    self.string=[atributes.get('#text')[0]]
                try:
                    if isinstance(self.string[0], list):
                        self.string=self.string[0]
                except Exception as e: 
                    print(e)

                self.id=atributes.get('id')
                if self.id is None:
                    self.id=atributes.get('lomes:id')
                try:
                    if isinstance(self.id[0], list):
                        self.id=self.id[0]
                except Exception as e: 
                    print(e)


                self.entry=atributes.get('entry')
                #print(" ** Class # 90  Desc ",self.entry)
                if self.entry is None:
                    self.entry=atributes.get('#text')
                    #print(" ** Class # 92  Desc ",self.entry)
                
                try:
                    #print(" ** Class # 96  Desc ",self.entry)
                    if isinstance(self.entry, list):
                        if(self.string[0]=='es'):
                            self.entry.remove('es')
                        #print(" ** Class # 100  Desc ",self.entry)
                except Exception as e: 
                    print(e)
                #print(" ** Class # 103  Desc ",self.entry)

            def to_xml(self):
                return f"""<taxonPath>
                                <source>
                                    <string>{self.string}</string>
                                </source>
                                <taxon>
                                    <id>{self.id}</id>
                                    <entry>
                                        <string>{self.entry}</string>
                                    </entry>
                                </taxon>
                            </taxonPath>"""
            
            def __dict__(self):
                return {'source': self.string, 'id': self.id, 'entry':self.entry}
        
        class Description:
            string = []

            def __init__(self, string=[]):
                self.string = string
            
            def addValues(self,atributes):

                self.string=atributes.get('description')
                if self.string is None:
                    self.string=atributes.get('#text')
                    if self.string is None:
                        self.string=atributes.get('string')
                
                try:
                    if isinstance(self.string[0], list):
                        self.string=self.string[0]
                except Exception as e: 
                    print(e)

            def to_xml(self):
                return f"""<description>
                                <string>{self.string}</string>
                            </description>"""
            def __dict__(self):
                return {'description': self.string}

        class Keywordd:

            language=[]
            keywordd=[]

            def __init__(self, language=[], keywordd=[]):
                self.language = language
                self.keywordd = keywordd
            
            def addValues(self,atributes):

                self.language=atributes.get('language')
                if self.language is None:
                    self.language=atributes.get('@language')
                try:
                    if isinstance(self.language[0], list):
                        self.language=self.language[0]
                except Exception as e: 
                    print(e)
                
                self.keywordd=atributes.get('keyword')
                if self.keywordd is None:
                    self.keywordd=atributes.get('string')
                try:
                    if isinstance(self.keywordd[0], list):
                        self.keywordd=self.keywordd[0]
                except Exception as e: 
                    print(e)

            def to_xml(self):
                return f"""<string  language="{self.language}">{self.keywordd}</string>"""

            def __dict__(self):
                return {'language': self.language, 'keyword': self.keywordd}


        def to_xml(self):
            return f"""<classification>
            {'' if isinstance(self.purpose, str) else self.purpose.to_xml() if self.purpose is not None else ''}
            {'' if isinstance(self.taxonPath, str) else self.taxonPath.to_xml() if self.taxonPath is not None else ''}
            {'' if isinstance(self.description, str) else self.description.to_xml() if self.description is not None else ''}
            {'' if isinstance(self.keywordd, str) else self.keywordd.to_xml() if self.keywordd is not None else ''}
            </classification>"""

        def __dict__(self):
            return {'purpose': self.purpose.__dict__() if self.purpose is not None else {'source': [], 'value': []}, 
                    'taxonPath': self.taxonPath.__dict__() if self.taxonPath is not None else {'source': [], 'id': [], 'entry':[]}, 
                    'description': self.description.__dict__() if self.description is not None else {'description': []}, 
                    'keyword': self.keywordd.__dict__() if self.keywordd is not None else {'language': [], 'keyword': []}}