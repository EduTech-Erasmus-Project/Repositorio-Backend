class Annotation:
        entity = None
        date = None
        description = None
        modeaccess = None
        modeaccesssufficient = None
        rol = None

        def __init__(self, entity=None, date=None, description=None, modeaccess=None, modeaccesssufficient=None, rol=None):
            self.entity = entity
            self.date = date
            self.description = description
            self.modeaccess = modeaccess
            self.modeaccesssufficient = modeaccesssufficient
            self.rol = rol
        
        class Entity:
            entity=[]

            def __init__(self, entity=[]):
                self.entity = entity
            
            def addValues(self,atributes):
                self.entity=atributes.get("entity")
                    
            def getValues(self):
                print("Entity: ", self.entity)

            def to_xml(self):
                return f"""<entity>{self.entity}</entity>"""

            def __dict__(self):
                return {'Entity': self.entity}

        class Date:

            dateTime=[]
            string=[]

            def __init__(self, dateTime=[], string=[]):
                self.dateTime = dateTime
                self.string = string
            
            def addValues(self,atributes):
                self.dateTime=atributes.get("dateTime")
                self.string=atributes.get("string")
                    

            def to_xml(self):
                return f"""<date>
                                <dateTime>{self.dateTime}</dateTime>
                                <description>
                                    <string>{self.string}</string>
                                </description>
                            </date>"""

            def __dict__(self):
                return {'DateTime': self.dateTime, 'Description': self.string}
        
        class Description:
            Description=[]

            def __init__(self, description=[]):
                self.description = description
            
            def addValues(self,atributes):
                self.description=atributes.get("string")
                    
            def getValues(self):
                print("Description: ", self.description)

            def to_xml(self):
                return f"""<description>
                                <string>{self.description}</string>
                            </description>"""

            def __dict__(self):
                return {'Description': self.description}
        
        class Modeaccess:

            source=[]
            value=[]

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get("source")
                self.value=atributes.get("value")
                    

            def to_xml(self):
                return f"""<modeaccess>
                                <source>{self.source}</source>
                                <value>{self.value}</value>
                            </modeaccess>"""

            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}
        
        class Modeaccesssufficient:

            source=[]
            value=[]

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get("source")
                self.value=atributes.get("value")
                    

            def to_xml(self):
                return f"""<modeaccesssufficient>
                                <source>{self.source}</source>
                                <value>{self.value}</value>
                            </modeaccesssufficient>"""

            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}
        
        class Rol:

            source=[]
            value=[]

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get("source")
                self.value=atributes.get("value")
                    

            def to_xml(self):
                return f"""<Rol>
                                <source>{self.source}</source>
                                <value>{self.value}</value>
                            </Rol>"""

            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}

        def to_xml(self):
            return f"""<annotation>
            {'' if isinstance(self.entity, str) else self.entity.to_xml() if self.entity is not None else ''}
            {'' if isinstance(self.date, str) else self.date.to_xml() if self.date is not None else ''}
            {'' if isinstance(self.description, str) else self.description.to_xml() if self.description is not None else ''}
            {'' if isinstance(self.modeaccess, str) else self.modeaccess.to_xml() if self.modeaccess is not None else ''}
            {'' if isinstance(self.modeaccesssufficient, str) else self.modeaccesssufficient.to_xml() if self.modeaccesssufficient is not None else ''}
            {'' if isinstance(self.rol, str) else self.rol.to_xml() if self.rol is not None else ''}
            </annotation>"""

        def __dict__(self):
            return {'Entity': self.entity.__dict__() if self.entity is not None else [], 
                    'Date': self.date.__dict__() if self.date is not None else [], 
                    'Description': self.description.__dict__() if self.description is not None else [],
                    'Mode Access': self.modeaccess.__dict__() if self.modeaccess is not None else [],
                    'Mode Access Sufficient': self.modeaccesssufficient.__dict__() if self.modeaccesssufficient is not None else [],
                    'Rol': self.rol.__dict__() if self.rol is not None else []}