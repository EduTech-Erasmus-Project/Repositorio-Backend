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
                self.value=atributes.get('value')

            def to_xml(self):
                return f"""<Cost>
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </Cost>"""
            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}

        
        class Copyrightandotherrestrictions:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                self.value=atributes.get('value')

            def to_xml(self):
                return f"""<copyrightAndOtherRestrictions>
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </copyrightAndOtherRestrictions>"""
            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}

        class Description:
            string = []

            def __init__(self, string=[]):
                self.string = string
            
            def addValues(self,atributes):
                self.string=atributes.get('string')
                if self.string is None:
                    self.string=atributes.get('description')
                    if len(self.source) > 1:
                        self.string=[atributes.get('description')[1]]
            def to_xml(self):
                return f"""<description>
                                <string>{self.string}</string>
                            </description>"""
            def __dict__(self):
                return {'Description': self.string}


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
                self.value=atributes.get('value')
                self.description=atributes.get('es')
                if self.description is None:
                    self.description=atributes.get('string')
                    if len(self.description) > 1:
                        self.description=[atributes.get('string')[1]]

            def to_xml(self):
                return f"""<accessType >
                    <source >{self.source}</source>
                    <value >{self.value}</value>
                </accessType>
                <description >
                    <string >{self.description}</string>
                </description>"""
            
            def __dict__(self):
                return {'Source': self.source, 'Value': self.value, 'Description':self.description}

        def to_xml(self):
            return f"""<rights>
            {'' if isinstance(self.cost, str) else self.cost.to_xml() if self.cost is not None else ''}
            {'' if isinstance(self.copyrightAndOtherRestrictions, str) else self.copyrightAndOtherRestrictions.to_xml() if self.copyrightAndOtherRestrictions is not None else ''} 
            {'' if isinstance(self.description, str) else self.description.to_xml() if self.description is not None else ''}
            {'' if isinstance(self.access, str) else self.access.to_xml() if self.access is not None else ''}
            </rights>"""

        def __dict__(self):
            return {'Cost': self.cost.__dict__() if self.cost is not None else [],
                    'CopyrightAndOtherRestrictions': self.copyrightAndOtherRestrictions.__dict__() if self.copyrightAndOtherRestrictions is not None else [],
                    'Description': self.description.__dict__() if self.description is not None else [],
                    'Access': self.access.__dict__() if self.access is not None else []}