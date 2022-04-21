class Technical:
    format = None
    size = None,
    location = None
    requirement = None
    installationRemarks = None
    otherPlatformRequirements = None
    duration = None

    def __init__(self, technical_format=None, size=None, location=None, requirement=None, installationRemarks=None,
                    otherPlatformRequirements=None, duration=None):
        self.format = technical_format
        self.size = size
        self.location = location
        self.requirement = requirement
        self.installationRemarks = installationRemarks
        self.otherPlatformRequirements = otherPlatformRequirements
        self.duration = duration

    class Format:

        value = []

        def __init__(self, value=[]):
            self.value = value
        
        def addValues(self,atributes):
            self.value=atributes.get('format')


        def to_xml(self):
            return f"""<format>{self.value}</format>"""

        def __dict__(self):
            return {'Format': self.value}

    class Size:
        value = []

        def __init__(self, value=[]):
            self.value = value
        
        def addValues(self,atributes):
            self.value=atributes.get('size')


        def to_xml(self):
            return f"""<size>{self.value}</size>"""

        def __dict__(self):
            return {'Size': self.value}

    class Location:
        value = []

        def __init__(self, value=[]):
            self.value = value
        
        def addValues(self,atributes):
            self.value=atributes.get('location')


        def to_xml(self):
            return f"""<location>{self.value}</location>"""

        def __dict__(self):
            return {'Location': self.value}

    class Installationremarks:
        value = []

        def __init__(self, value=[]):
            self.value = value
        
        def addValues(self,atributes):
            self.value=atributes.get('@language')
            if self.value is None:
                    self.value=atributes.get('string')
                    if len(self.value) > 1:
                        self.value=[atributes.get('string')[1]]

        def to_xml(self):
            return f"""<installationRemarks>
            <string>{self.value}></string>
            </installationRemarks>"""

        def __dict__(self):
            return {'InstallationRemarks': self.value}

    class Otherplatformrequirements:
        string = []

        def __init__(self, string=[]):
            self.string = string
        
        def addValues(self,atributes):
            self.string=atributes.get('string')


        def to_xml(self):
            return f"""<otherPlatformRequirements>
            <string>{self.string}</string>
            </otherPlatformRequirements>"""

        def __dict__(self):
            return {'OtherPlatformRequirements': self.string}


    class Duration:
        duration = []
        description = []

        def __init__(self, duration=[], description=[]):
            self.duration = duration
            self.description = description
        
        def addValues(self,atributes):
            self.duration=atributes.get('duration')
            self.description=atributes.get('string')

        def to_xml(self):
            return f"""<duration>
                            <duration>{self.duration}</duration>
                            <description>
                                <string>{self.description}</string>
                            </description>
                        </duration>"""

        def __dict__(self):
            return {'Duration': self.duration,
                    'Description': self.description}

    class Requirement:
        
        typeSource = []
        typeValue = []
        nameSource = []
        nameValue = []
        minVersion = []
        maxVersion = []
        
        def __init__(self, typeSource=[], typeValue=[], nameSource=[], nameValue=[], minVersion=[], maxVersion=[]):
            self.typeSource = typeSource
            self.typeValue = typeValue
            self.nameSource = nameSource
            self.nameValue = nameValue
            self.minVersion = minVersion
            self.maxVersion =  maxVersion
        
        def addValues(self,atributes):
            self.typeValue = atributes.get("type")[0]
            self.typeSource = atributes.get("type")[1]
            self.nameValue = atributes.get("name")[0]
            self.nameSource = atributes.get("name")[1]
            self.minVersion = atributes.get("minimumVersion")
            self.maxVersion = atributes.get("maximumVersion")

        def to_xml(self):
            return f"""<requirement>
                <orComposite>
                    <type>
                        <source>{self.typeSource}</source>
                        <value>{self.typeValue}</value>
                    </type>
                    <name>
                        <source>{self.typeSource}</source>
                        <value>{self.typeValue}</value>
                    </name>
                    <minimumVersion>{self.minVersion}</minimumVersion>
                    <maximumVersion>{self.maxVersion}</maximumVersion>
                </orComposite>
            </requirement>"""
        
        def __dict__(self):
            return {'TypeValue': self.typeValue,
                    'TypeSource': self.typeSource,
                    'NameValue': self.nameValue,
                    'NameSource': self.nameSource,
                    'MinVersion': self.minVersion,
                    'MaxVersion': self.maxVersion}

    def to_xml(self):
        return f"""<technical>
        {'' if isinstance(self.format, str) else self.format.to_xml() if self.format is not None else ''}
        {'' if isinstance(self.size, str) else self.size.to_xml() if self.size is not None else ''}
        {'' if isinstance(self.location, str) else self.location.to_xml() if self.location is not None else ''}
        {'' if isinstance(self.installationRemarks, str) else self.installationRemarks.to_xml() if self.installationRemarks is not None else ''}
        {'' if isinstance(self.otherPlatformRequirements, str) else self.otherPlatformRequirements.to_xml() if self.otherPlatformRequirements is not None else ''}
        {'' if isinstance(self.requirement, str) else self.requirement.to_xml() if self.requirement is not None else ''}
        {'' if isinstance(self.duration, str) else self.duration.to_xml() if self.duration is not None else ''}
        </technical>"""

    def __dict__(self):
        return {'Format': self.format.__dict__() if self.format is not None else [],
                'Size': self.size.__dict__() if self.size is not None else [],
                'Location': self.location.__dict__() if self.location is not None else [],
                'Installation Remarks': self.installationRemarks.__dict__() if self.installationRemarks is not None else [],
                'OtherPlatformRequirements': self.otherPlatformRequirements.__dict__() if self.otherPlatformRequirements is not None else [],
                'Requirement': self.requirement.__dict__() if self.requirement is not None else [],
                'Duration': self.duration.__dict__() if self.duration is not None else []}