class Rights:
        cost = None
        copyrightAndOtherRestrictions = None
        description = None
        access =  None

        def __init__(self, cost=None, copyright_and_other_restrictions=None, description=None, access=None):
            self.cost = cost
            self.copyrightAndOtherRestrictions = copyright_and_other_restrictions
            self.description = description
            self.access = access
        
        class Cost:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                try:
                    if isinstance(self.source, list):
                        self.source=self.source[0]
                except Exception as e: 
                    print(e)

                self.value=atributes.get('value')
                try:
                    if isinstance(self.value, list):
                        self.value=self.value[0]
                except Exception as e: 
                    print(e)
                #print("Rigth #35: "+ self.value)

            def to_xml(self):
                return f"""<cost>
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </cost>"""
            def __dict__(self):
                return {'source': self.source, 'value': self.value}

        
        class Copyrightandotherrestrictions:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                if self.source is None:
                    self.source=atributes.get('lomes:source')
                try:
                    if isinstance(self.source, list):
                        self.source=self.source[0]
                except Exception as e: 
                    print(e)

                self.value=atributes.get('value')
                if self.value is None:
                    self.value=atributes.get('lomes:value')
                try:
                    if isinstance(self.value, list):
                        self.value=self.value[0]
                except Exception as e: 
                    print(e)

            def to_xml(self):
                return f"""<copyrightAndOtherRestrictions>
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </copyrightAndOtherRestrictions>"""
            def __dict__(self):
                return {'source': self.source, 'value': self.value}

        class Description:
            string = []

            def __init__(self, string=[]):
                self.string = string
            
            def addValues(self,atributes):
                self.string=atributes.get('string')
                if self.string is None:
                    self.string=atributes.get('description')
                    if self.string is None:
                        self.string=atributes.get('#text')
                #print("Rights #93: ", self.string)
                try:
                    if isinstance(self.string, list):
                    #if len(self.string) > 0:
                        self.string=[self.string[0]]
                except Exception as e:
                    print(e)

            def to_xml(self):
                return f"""<description>
                                <string>{self.string}</string>
                            </description>"""
            def __dict__(self):
                return {'description': self.string}


        class Access:
            source = []
            value = []
            description = []
            def __init__(self, source=[], value=[], description=[]):
                self.source = source
                self.value = value
                self.description = description
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                if self.source is None:
                    self.source=atributes.get('lomes:source')
                try:
                    if isinstance(self.source[0], list):
                        self.source=self.source[0]
                except Exception as e: 
                    print(e)

                self.value=atributes.get('description')
                if self.value is None:
                    self.value=atributes.get('value')
                if self.value is None:
                    self.value=atributes.get('lomes:value')
                try:
                    if isinstance(self.value[0], list):
                        self.value=self.value[0]
                except Exception as e: 
                    print(e)

                self.description=atributes.get('es')
                if self.description is None:
                    self.description=atributes.get('string')
                    if self.description is None:
                        self.description=atributes.get('lomes:string')
                    try:
                        if len(self.description) > 1:
                            self.description=[atributes.get('string')[1]]
                    except Exception as e:
                        print(e)
                try:
                    if isinstance(self.description[0], list):
                        self.description=self.description[0]
                except Exception as e: 
                    print(e)

            def to_xml(self):
                return f"""<accessType >
                    <source >{self.source}</source>
                    <value >{self.value}</value>
                </accessType>
                <description >
                    <string >{self.description}</string>
                </description>"""
            
            def __dict__(self):
                return {'source': self.source, 'value': self.value, 'description':self.description}

        def to_xml(self):
            return f"""<rights>
            {'' if isinstance(self.cost, str) else self.cost.to_xml() if self.cost is not None else ''}
            {'' if isinstance(self.copyrightAndOtherRestrictions, str) else self.copyrightAndOtherRestrictions.to_xml() if self.copyrightAndOtherRestrictions is not None else ''} 
            {'' if isinstance(self.description, str) else self.description.to_xml() if self.description is not None else ''}
            {'' if isinstance(self.access, str) else self.access.to_xml() if self.access is not None else ''}
            </rights>"""

        def __dict__(self):
            return {'cost': self.cost.__dict__() if self.cost is not None else {'source': [], 'value': []},
                    'copyrightAndOtherRestrictions': self.copyrightAndOtherRestrictions.__dict__() if self.copyrightAndOtherRestrictions is not None else {'source': [], 'value': []},
                    'description': self.description.__dict__() if self.description is not None else {'description': []},
                    'access': self.access.__dict__() if self.access is not None else {'source': [], 'value': [], 'description':[]}}