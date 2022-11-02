import string


class Accessibility:

        description = None
        accessibilityfeatures = None
        accessibilityhazard = None
        accessibilitycontrol = None
        accessibilityAPI = None

        def __init__(self, description=None, accessibilityfeatures=None, accessibilityhazard=None,
                     accessibilitycontrol=None, accessibilityAPI=None):
            self.description = description
            self.accessibilityfeatures = accessibilityfeatures
            self.accessibilityhazard = accessibilityhazard
            self.accessibilitycontrol = accessibilitycontrol
            self.accessibilityAPI = accessibilityAPI
        
        class Description:
            Description=[]

            def __init__(self, description=[]):
                self.description = description
            
            def addValues(self,atributes):
                #print("*1*1*1 Accesi #24 ",atributes)
                self.description=atributes.get("description")
                if self.description is None:
                    self.description=atributes.get("string")
                    if self.description is None:
                        self.description=atributes.get("#text")
                    try:
                        if isinstance(self.description[0], list):
                            self.description=self.description[0]
                    except Exception as e: 
                        print(e)
                    

            def to_xml(self):
                return f"""<description>
                                <string>{self.description}</string>
                            </description>"""

            def __dict__(self):
                return {'description': self.description}

        class Accessibilityfeatures:
            br=[]

            def __init__(self, br=[]):
                self.br = br
            
            def addValues(self,atributes):
                self.br=atributes.get("value")
                try:
                    if isinstance(self.br[0], list):
                        self.br=self.br[0]
                except Exception as e: 
                    print(e)

            def to_xml(self):

                aux= f"""<accessibilityfeatures>"""
                aux2=""
                for val in self.br:
                    aux2=aux2+f"""<value>{val}</value>"""
                aux3=aux+aux2+f"""</accessibilityfeatures>"""
                #print("+-+- Acc 72: ", aux3)   

                return aux3

            def __dict__(self):
                return {'value': self.br}
        
        class Accessibilityhazard:
            br=[]

            def __init__(self, br=[]):
                self.br = br
            
            def addValues(self,atributes):
                #print("*** Accesi Hazard #79 ",atributes)
                self.br=atributes.get("value")
                try:
                    if isinstance(self.br[0], list):
                        self.br=self.br[0]
                except Exception as e: 
                    print(e)

            def to_xml(self):
                aux= f"""<accessibilityhazard>"""
                aux2=f""""""
                
                for val in self.br:
                    aux2=aux2+f"""<value>{val}</value>"""               
                aux3=aux+aux2+f"""</accessibilityhazard>"""
                #print("+-+- Acc 72: ", aux3)   

                return aux3

            def __dict__(self):
                return {'value': self.br}

        class Accessibilitycontrol:
            br=[]

            def __init__(self, br=[]):
                self.br = br
            
            def addValues(self,atributes):
                #print("*** Accesi control #106 ",atributes)
                self.br=atributes.get("value")
                try:
                    if isinstance(self.br[0], list):
                        self.br=self.br[0]
                except Exception as e: 
                    print(e)

            def to_xml(self): 
                aux= f"""<accessibilitycontrol>"""
                aux2=""
                for val in self.br:
                    aux2=aux2+f"""<value>{val}</value>"""
                
                aux3=aux+aux2+f"""</accessibilitycontrol>"""
                #print("+-+- Acc 72: ", aux3)   

                return aux3

            def __dict__(self):
                return {'value': self.br}
        
        class Accessibilityapi:
            br=[]

            def __init__(self, br=[]):
                self.br = br
            
            def addValues(self,atributes):
                #print("*** Accesi #133 Api ",atributes)
                self.br=atributes.get("value")
                try:
                    if isinstance(self.br[0], list):
                        self.br=self.br[0]
                except Exception as e: 
                    print(e)
               
            def to_xml(self):
                aux= f"""<accessibilityAPI>"""
                aux2=""
                for val in self.br:
                    aux2=aux2+f"""<value>{val}</value>"""
                
                aux3=aux+aux2+f"""</accessibilityAPI>"""
                #print("+-+- Acc 72: ", aux3)   

                return aux3

            def __dict__(self):
                return {'value': self.br}

        def to_xml(self):
            return f"""<accesibility>
            {'' if isinstance(self.description, str) else self.description.to_xml() if self.description is not None else ''}
            {'' if isinstance(self.accessibilityfeatures, str) else self.accessibilityfeatures.to_xml() if self.accessibilityfeatures is not None else ''}
            {'' if isinstance(self.accessibilityhazard, str) else self.accessibilityhazard.to_xml() if self.accessibilityhazard is not None else ''}
            {'' if isinstance(self.accessibilitycontrol, str) else self.accessibilitycontrol.to_xml() if self.accessibilitycontrol is not None else ''}
            {'' if isinstance(self.accessibilityAPI, str) else self.accessibilityAPI.to_xml() if self.accessibilityAPI is not None else ''}
            </accesibility>"""

        def __dict__(self):
            return {'description': self.description.__dict__() if self.description is not None else {'description': []},
                    'accessibilityFeatures': self.accessibilityfeatures.__dict__() if self.accessibilityfeatures is not None else {'value': []}, 
                    'accessibilityHazard': self.accessibilityhazard.__dict__() if self.accessibilityhazard is not None else {'value': []}, 
                    'accessibilityControl': self.accessibilitycontrol.__dict__() if self.accessibilitycontrol is not None else {'value': []}, 
                    'accessibilityApi': self.accessibilityAPI.__dict__() if self.accessibilityAPI is not None else {'value': []}}