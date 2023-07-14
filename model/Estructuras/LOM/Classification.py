class Classification:
        purpose = None  # purpose
        taxonPath = None  # taxon_path
        description = None  # description
        keywordd = None  # keywordd

        def __init__(self, purpose='', taxonPath=None, description='', keywordd=''):
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
                self.source=atributes.get("source")
                self.value=atributes.get("value")
                    

            def to_xml(self):
                return f"""<purpose>
                                <source>{self.source}</source>
                                <value>{self.value}</value>
                            </purpose>"""

            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}
                
        class Taxonpath:
            string = []
            id = []
            entry = []
            def __init__(self, string=[], id=[], entry=[]):
                self.string = string
                self.id = id
                self.entry = entry
            
            def addValues(self,atributes):
                self.string=atributes.get('string')
                self.id=atributes.get('id')
                self.entry=atributes.get('entry')

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
                return {'Source': self.string, 'Id': self.id, 'Entry':self.entry}
        
        class Description:
            string = []

            def __init__(self, string=[]):
                self.string = string
            
            def addValues(self,atributes):
                self.string=atributes.get('string')

            def to_xml(self):
                return f"""<description>
                                <string>{self.string}</string>
                            </description>"""
            def __dict__(self):
                return {'Description': self.string}

        class Keywordd:

            language=[]
            keywordd=[]

            def __init__(self, language=[], keywordd=[]):
                self.language = language
                self.keywordd = keywordd
            
            def addValues(self,atributes):
                self.language=atributes.get('@language')
                self.keywordd=atributes.get('string')

            def getValues(self):
                print("Languaje: ", self.language)
                print("Keyword: ", self.keywordd)

            def to_xml(self):
                return f"""<string  language="{self.language}">{self.keywordd}</string>"""

            def __dict__(self):
                return {'Language': self.language, 'Keyword': self.keywordd}


        def to_xml(self):
            return f"""<classification>
            {'' if isinstance(self.purpose, str) else self.purpose.to_xml() if self.purpose is not None else ''}
            {'' if isinstance(self.taxonPath, str) else self.taxonPath.to_xml() if self.taxonPath is not None else ''}
            {'' if isinstance(self.description, str) else self.description.to_xml() if self.description is not None else ''}
            {'' if isinstance(self.keywordd, str) else self.keywordd.to_xml() if self.keywordd is not None else ''}
            </classification>"""

        def __dict__(self):
            return {'Purpose': self.purpose.__dict__() if self.purpose is not None else [], 
                    'Taxon Path': self.taxonPath.__dict__() if self.taxonPath is not None else [], 
                    'Description': self.description.__dict__() if self.description is not None else [], 
                    'Keyword': self.keywordd.__dict__() if self.keywordd is not None else []}