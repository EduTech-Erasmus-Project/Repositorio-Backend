class Technical:
        format = None
        size = None,
        location = None
        requirement = None
        installationRemarks = None
        other_platform_requirements = None
        duration = None

        def __init__(self, technical_format='', size='', location='', requirement=None, installationRemarks='',
                     other_platform_requirements='', duration=''):
            self.format = technical_format
            self.size = size,
            self.location = location
            self.requirement = requirement
            self.installationRemarks = installationRemarks
            self.other_platform_requirements = other_platform_requirements
            self.duration = duration
        
        class Location:
            value = []

            def __init__(self, value=[]):
                self.value = value
            
            def addValues(self,atributes):
                self.value=atributes.get('lomes:location')


            def to_xml(self):
                return f"""<location>{self.value}</location>"""

            def __dict__(self):
                return {'Values': self.value}
        
        class Installationremarks:
            language = []

            def __init__(self, language=[]):
                self.language = language
            
            def addValues(self,atributes):
                self.language=atributes.get('@language')


            def to_xml(self):
                return f"""<installationRemarks>
                <string  language="{self.language}"></string>
                </installationRemarks>"""

            def __dict__(self):
                return {'Language': self.language}

        class Requirement:
            or_composite = None

            def __init__(self, or_composite=None):
                self.or_composite = or_composite

            class OrComposite:
                composite_type = None
                name = None
                minimum_version = None
                maximum_version = None

                def __init__(self, composite_type='', name='', minimum_version='', maximum_version=''):
                    self.composite_type = composite_type
                    self.name = name
                    self.minimum_version = minimum_version
                    self.maximum_version = maximum_version

                def to_xml(self):
                    return f"""<orComposite>
                    <type>
                    <source>LOMv1.0</source>
                    <value>{self.composite_type}</value>
                    </type>
                    <name>
                    <source>LOMv1.0></source>
                    <value>{self.name}</value>
                    </name>
                    <minimumVersion>{self.minimum_version}</minimumVersion>
                    <maximumVersion>{self.maximum_version}</maximumVersion>
                    </orComposite>"""

                def __dict__(self):
                    return {'Type': self.composite_type, 'Name': self.name, 'Minimum Version': self.minimum_version,
                            'Maximum Version': self.maximum_version}

            def to_xml(self):
                return f"""<requirement>
                {self.or_composite.to_xml() if self.or_composite is not None else ''}
                </requirement>"""

            def __dict__(self):
                return {
                    'OrComposite': self.or_composite.__dict__() if self.or_composite is not None
                    else self.OrComposite().__dict__()}

        def to_xml(self):
            return f"""<technical>
            {'' if isinstance(self.location, str) else self.location.to_xml() if self.location is not None else ''}
            {'' if isinstance(self.installationRemarks, str) else self.installationRemarks.to_xml() if self.installationRemarks is not None else ''}
            </technical>"""

        def __dict__(self):
            return {'Installation Remarks': self.installationRemarks.__dict__() if self.installationRemarks is not None else self.Installationremarks().__dict__(),
                    'Location': self.location.__dict__() if self.location is not None else self.Location().__dict__()}