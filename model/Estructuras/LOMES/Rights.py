class Rights:
        cost = None
        copyrightAndOtherRestrictions = None
        description = None
        access =  None

        def __init__(self, cost='', copyright_and_other_restrictions='', description='', access=None):
            self.cost = cost
            self.copyrightAndOtherRestrictions = copyright_and_other_restrictions
            self.description = description
            self.access = access
        
        class Copyrightandotherrestrictions:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('lomes:source')
                self.value=atributes.get('lomes:value')

            def to_xml(self):
                return f"""<copyrightAndOtherRestrictions >
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </copyrightAndOtherRestrictions>"""
            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}

        class Access:
            source = []
            value = []
            description = []
            def __init__(self, source=[], value=[], description=[]):
                self.source = source
                self.value = value
                self.description = description
            
            def addValues(self,atributes):
                self.source=atributes.get('lomes:source')
                self.value=atributes.get('lomes:value')
                self.description=atributes.get('lomes:string')

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
            {'' if isinstance(self.copyrightAndOtherRestrictions, str) else self.copyrightAndOtherRestrictions.to_xml() if self.copyrightAndOtherRestrictions is not None else ''}
            {'' if isinstance(self.access, str) else self.access.to_xml() if self.access is not None else ''}
            </rights>"""

        def __dict__(self):
            return {'Copyrightandotherrestrictions': self.copyrightAndOtherRestrictions.__dict__() if self.copyrightAndOtherRestrictions is not None else self.Copyrightandotherrestrictions().__dict__(),
                    'Access': self.access.__dict__() if self.access is not None else self.Access().__dict__()}