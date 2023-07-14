class Annotation:
        entity = None
        date = None
        description = None
        accessmode = None
        accessmodesufficient = None
        Rol = None

        def __init__(self, entity=None, date=None, description=None, accessmode=None, accessmodesufficient=None, Rol=None):
            self.entity = entity
            self.date = date
            self.description = description
            self.accessmode = accessmode
            self.accessmodesufficient = accessmodesufficient
            self.Rol = Rol
        
        class Entity:
            entity=[]

            def __init__(self, entity=[]):
                self.entity = entity
            
            def addValues(self,atributes):
                self.entity=atributes.get("entity")
                # try:
                #     if isinstance(self.entity[0], list):
                #         self.entity=self.entity[0]
                # except Exception as e: 
                #     print(e)
                    

            def to_xml(self):
                return f"""<entity>{self.entity}</entity>"""

            def __dict__(self):
                return {'entity': self.entity}

        class Date:

            dateTime=[]
            string=[]

            def __init__(self, dateTime=[], string=[]):
                self.dateTime = dateTime
                self.string = string
            
            def addValues(self,atributes):
                self.dateTime=atributes.get("dateTime")
                try:
                    if isinstance(self.dateTime[0], list):
                        self.dateTime=self.dateTime[0]
                except Exception as e: 
                    print(e)

                self.string=atributes.get("description")
                if self.string is None:
                    self.string=atributes.get("string")
                    try:
                        if isinstance(self.string[0], list):
                            self.string=self.string[0]
                    except Exception as e: 
                        print(e)
                    

            def to_xml(self):
                return f"""<date>
                                <dateTime>{self.dateTime}</dateTime>
                                <description>
                                    <string>{self.string}</string>
                                </description>
                            </date>"""

            def __dict__(self):
                return {'dateTime': self.dateTime, 'description': self.string}
        
        class Description:
            Description=[]

            def __init__(self, description=[]):
                self.description = description
                
            
            def addValues(self,atributes):
                #print("Anotations #84 - Descrip - Atrib: ", atributes)
                self.description=atributes.get("description")
                if self.description is None:
                    self.description=atributes.get("#text")
                    if self.description is None:
                        self.description=atributes.get("string")
                    try:
                        if isinstance(self.description[0], list):
                            self.description=self.description[0]
                    except Exception as e: 
                        print(e)
                #print("Anotations #93 - Descrip - Atrib: ", self.description)
                

            def to_xml(self):
                return f"""<description>
                                <string>{self.description}</string>
                            </description>"""

            def __dict__(self):
                return {'description': self.description}
        
        class Accessmode:

            source=[]
            value=[]

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                #print("Anota #116: ", atributes)
                self.source=atributes.get("source")
                #print("Anota #118: Source ", self.source)
                try:
                    if isinstance(self.source[0], list):
                        self.source=self.source[0]
                except Exception as e: 
                    print(e)

                self.value=atributes.get("value")
                try:
                    if isinstance(self.value[0], list):
                        self.value=self.value[0]
                except Exception as e: 
                    print(e)
                    

            def to_xml(self):
                return f"""<accessmode>
                                <source>{self.source}</source>
                                <value>{self.value}</value>
                            </accessmode>"""

            def __dict__(self):
                return {'source': self.source, 'value': self.value}
        
        class Accessmodesufficient:

            source=[]
            value=[]

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                #print("Anota #152: ", atributes)
                self.source=atributes.get("source")
                #print("Anota #154:  ", self.source)
                try:
                    if isinstance(self.source[0], list):
                        self.source=self.source[0]
                except Exception as e: 
                    print(e)

                self.value=atributes.get("value")
                try:
                    if isinstance(self.value[0], list):
                        self.value=self.value[0]
                except Exception as e: 
                    print(e)
                    

            def to_xml(self):
                return f"""<accessmodesufficient>
                                <source>{self.source}</source>
                                <value>{self.value}</value>
                            </accessmodesufficient>"""

            def __dict__(self):
                return {'source': self.source, 'value': self.value}
        
        class CRol:

            source=[]
            value=[]

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get("source")
                try:
                    if isinstance(self.source[0], list):
                        self.source=self.source[0]
                except Exception as e: 
                    print(e)

                self.value=atributes.get("value")
                try:
                    if isinstance(self.value[0], list):
                        self.value=self.value[0]
                except Exception as e: 
                    print(e)
                    

            def to_xml(self):
                return f"""<Rol>
                                <source>{self.source}</source>
                                <value>{self.value}</value>
                            </Rol>"""

            def __dict__(self):
                return {'source': self.source, 'value': self.value}

        def to_xml(self):
            return f"""<annotation>
            {'' if isinstance(self.entity, str) else self.entity.to_xml() if self.entity is not None else ''}
            {'' if isinstance(self.date, str) else self.date.to_xml() if self.date is not None else ''}
            {'' if isinstance(self.description, str) else self.description.to_xml() if self.description is not None else ''}
            {'' if isinstance(self.accessmode, str) else self.accessmode.to_xml() if self.accessmode is not None else ''}
            {'' if isinstance(self.accessmodesufficient, str) else self.accessmodesufficient.to_xml() if self.accessmodesufficient is not None else ''}
            {'' if isinstance(self.Rol, str) else self.Rol.to_xml() if self.Rol is not None else ''}
            </annotation>"""

        def __dict__(self):
            return {'entity': self.entity.__dict__() if self.entity is not None else {'entity': []}, 
                    'date': self.date.__dict__() if self.date is not None else {'dateTime': [], 'description': []}, 
                    'description': self.description.__dict__() if self.description is not None else {'description': []},
                    'accessmode': self.accessmode.__dict__() if self.accessmode is not None else {'source': [], 'value': []},
                    'accessmodesufficient': self.accessmodesufficient.__dict__() if self.accessmodesufficient is not None else {'source': [], 'value': []},
                    'rol': self.Rol.__dict__() if self.Rol is not None else {'source': [], 'value': []}}