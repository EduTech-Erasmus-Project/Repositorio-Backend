class Accessibility:

        description = None
        accessibilityfeatures = None
        accessibilityhazard = None
        accessibilitycontrol = None
        accessibilityAPI = None

        def __init__(self, description='', accessibilityfeatures=None, accessibilityhazard=None,
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
                self.description=atributes.get("string")
                    
            def getValues(self):
                print("Description: ", self.description)

            def to_xml(self):
                return f"""<description>
                                <string>{self.description}</string>
                            </description>"""

            def __dict__(self):
                return {'Description': self.description}

        class Accessibilityfeatures:
            br=[]

            def __init__(self, br=[]):
                self.br = br
            
            def addValues(self,atributes):
                self.br=atributes.get("br")[0]

            def to_xml(self):
                return f"""<accessibilityfeatures>
                                <resourcecontent>
                                    <br>{self.br}</br>
                                </resourcecontent>
                            </accessibilityfeatures>"""

            def __dict__(self):
                return {'Accessibilityfeatures': self.br}
        
        class Accessibilityhazard:
            br=[]

            def __init__(self, br=[]):
                self.br = br
            
            def addValues(self,atributes):
                self.br=atributes.get("br")[0]

            def to_xml(self):
                return f"""<accessibilityhazard>
                                <properties>
                                    <br>{self.br}</br>
                                </properties>
                            </accessibilityhazard>"""

            def __dict__(self):
                return {'Accessibilityhazard': self.br}

        class Accessibilitycontrol:
            br=[]

            def __init__(self, br=[]):
                self.br = br
            
            def addValues(self,atributes):
                self.br=atributes.get("br")[0]

            def to_xml(self):
                return f"""<accessibilitycontrol>
                                <methods>
                                    <br>{self.br}</br>
                                </methods>
                            </accessibilitycontrol>"""

            def __dict__(self):
                return {'Accessibilitycontrol': self.br}
        
        class Accessibilityapi:
            br=[]

            def __init__(self, br=[]):
                self.br = br
            
            def addValues(self,atributes):
                self.br=atributes.get("br")[0]

            def to_xml(self):
                return f"""<accessibilityAPI>
                                <compatibleresource>
                                    <br>{self.br}</br>
                                </compatibleresource>
                            </accessibilityAPI>"""

            def __dict__(self):
                return {'Accessibilityapi': self.br}

        def to_xml(self):
            return f"""<accesibility>
            {'' if isinstance(self.description, str) else self.description.to_xml() if self.description is not None else ''}
            {'' if isinstance(self.accessibilityfeatures, str) else self.accessibilityfeatures.to_xml() if self.accessibilityfeatures is not None else ''}
            {'' if isinstance(self.accessibilityhazard, str) else self.accessibilityhazard.to_xml() if self.accessibilityhazard is not None else ''}
            {'' if isinstance(self.accessibilitycontrol, str) else self.accessibilitycontrol.to_xml() if self.accessibilitycontrol is not None else ''}
            {'' if isinstance(self.accessibilityAPI, str) else self.accessibilityAPI.to_xml() if self.accessibilityAPI is not None else ''}
            </accesibility>"""

        def __dict__(self):
            return {'Description': self.description.__dict__() if self.description is not None else [],
                    'Accessibility Features': self.accessibilityfeatures.__dict__() if self.accessibilityfeatures is not None else [], 
                    'Accessibility Hazard': self.accessibilityhazard.__dict__() if self.accessibilityhazard is not None else [], 
                    'Accessibility Control': self.accessibilitycontrol.__dict__() if self.accessibilitycontrol is not None else [], 
                    'Accessibility API': self.accessibilityAPI.__dict__() if self.accessibilityAPI is not None else []}