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
            if self.value is None:
                    self.value=atributes.get('#text')

        def to_xml(self):
            return f"""<format>{self.value}</format>"""

        def __dict__(self):
            return {'format': self.value}

    class Size:
        value = []

        def __init__(self, value=[]):
            self.value = value
        
        def addValues(self,atributes):
            #print("Tec 45 size atri: ", atributes)
            self.value=atributes.get('size')
            if self.value is None:
                self.value=atributes.get('#text')
            #print("Tec 45 size atri: ", self.value)


        def to_xml(self):
            return f"""<size>{self.value}</size>"""

        def __dict__(self):
            return {'size': self.value}

    class Location:
        value = []

        def __init__(self, value=[]):
            self.value = value
        
        def addValues(self,atributes):
            self.value=atributes.get('location')
            if self.value is None:
                self.value=atributes.get('#text')

        def to_xml(self):
            return f"""<location>{self.value}</location>"""

        def __dict__(self):
            return {'location': self.value}

    class Installationremarks:
        value = []

        def __init__(self, value=[]):
            self.value = value
        
        def addValues(self,atributes):
            self.value=atributes.get('#text')
            if self.value is None:
                self.value=atributes.get('string')
                try:
                    if len(self.value) > 1:
                        self.value=[atributes.get('string')[1]]
                except Exception as e:
                        print(e)
            if self.value is None:
                    self.value=atributes.get('installationRemarks')
            #print("Tec #92 ",self.value )

        def to_xml(self):
            return f"""<installationRemarks>
            <string>{self.value}</string>
            </installationRemarks>"""

        def __dict__(self):
            return {'installationRemarks': self.value}

    class Otherplatformrequirements:
        string = []

        def __init__(self, string=[]):
            self.string = string
        
        def addValues(self,atributes):
            self.string=atributes.get('string')
            if self.string is None:
                self.string=atributes.get('#text')
                if self.string is None:
                    self.string=atributes.get('otherPlatformRequirements')
            
            #print("Tec #115 ",self.string )


        def to_xml(self):
            return f"""<otherPlatformRequirements>
            <string>{self.string}</string>
            </otherPlatformRequirements>"""

        def __dict__(self):
            return {'otherPlatformRequirements': self.string}

    class Duration:
        duration = []
        description = []

        def __init__(self, duration=[], description=[]):
            self.duration = duration
            self.description = description
        
        def addValues(self,atributes):
            #print("Tec # 136 - Duration: ", atributes)
            self.duration=atributes.get('duration')
            if self.duration is None:
                self.duration=atributes.get('#text')
            try:                
                if isinstance(self.duration[0], list):
                    self.duration=self.duration[0]
            except Exception as e: 
                print(e)

            #print("Tec # 147 - duration: ", self.duration)


            self.description=atributes.get('string')
            if self.description is None:
                    self.description=atributes.get('description')
            try:
                if isinstance(self.description[0], list):
                    self.description=self.description[0]
            except Exception as e: 
                print(e)

        def to_xml(self):
            return f"""<duration>
                            <duration>{self.duration}</duration>
                            <description>
                                <string>{self.description}</string>
                            </description>
                        </duration>"""

        def __dict__(self):
            return {'duration': self.duration,
                    'description': self.description}

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
            
            #print("Tec #178 - Reque - atributos  : ",atributes)
            self.typeValue=atributes.get('type')
            try:
                if self.typeValue is None:
                        self.typeValue = [atributes.get("type")[0]]
                else:
                    if len(self.typeValue)>2:
                        self.typeValue = [atributes.get("type")[2]]
            except Exception as e:
                print(e)

            #print("Tec #186 - type  : ",self.typeValue)

            try:
                if isinstance(self.typeValue[0], list):
                    self.typeValue=self.typeValue[0]
            except Exception as e: 
                print(e)
            
            self.typeSource=atributes.get('typeSource')
            try:
                self.typeSource = [atributes.get("type")[1]]
            except Exception as e:
                print(e)
            
            try:
                if isinstance(self.typeSource[0], list):
                    self.typeSource=self.typeSource[0]
            except Exception as e: 
                print(e)

            self.nameValue=atributes.get('name')
            #print("Tec #210 - name  : ",self.nameValue)
            try:
                if self.nameValue is None:
                    self.nameValue = [atributes.get("name")[0]]
                    if len(self.nameValue)>2:
                        self.nameValue = [atributes.get("name")[2]]
                else:
                    if len(self.nameValue)>2:
                        self.nameValue = [atributes.get("name")[2]]
            except Exception as e:
                print(e)
            #print("Tec #217 - name  : ",self.nameValue)

            try:
                if isinstance(self.nameValue[0], list):
                    self.nameValue=self.nameValue[0]
            except Exception as e: 
                print(e)
            
            #-----------------

            self.nameSource=atributes.get('nameSource')
            try:
                if self.nameSource is None:
                    self.nameSource = [atributes.get("name")[1]]
            except Exception as e:
                print(e)
            try:
                if isinstance(self.nameSource[0], list):
                    self.nameSource=self.nameSource[0]
            except Exception as e: 
                print(e)
            


            try:
                self.minVersion = atributes.get("minimumVersion")
                #print("Tec #257 - name  : ",self.minVersion)
                if isinstance(self.minVersion, list):
                    self.minVersion.remove('minimumVersion')
            except Exception as e:
                print(e)

            if self.minVersion is None:
                self.minVersion=atributes.get('minVersion')
                if isinstance(self.minVersion, list):
                    self.minVersion.remove('minimumVersion')
            #print("Tec #268 - name  : ",self.minVersion)

            #print("Tec #270 - name  : ",self.minVersion)
 
            try:
                self.maxVersion = atributes.get("maximumVersion")
                #print("Tec #274 - name  : ",self.minVersion)
                if isinstance(self.maxVersion, list):
                    self.maxVersion.remove('maximumVersion')
            except Exception as e:
                print(e)
            if self.maxVersion is None:
                self.maxVersion=atributes.get('maxVersion')
                if isinstance(self.axVersion, list):
                    self.maxVersion.remove('maximumVersion')

                

        def to_xml(self):
            return f"""<requirement>
                <orComposite>
                    <type>
                        <source>{self.typeSource}</source>
                        <value>{self.typeValue}</value>
                    </type>
                    <name>
                        <source>{self.nameSource}</source>
                        <value>{self.nameValue}</value>
                    </name>
                    <minimumVersion>{self.minVersion}</minimumVersion>
                    <maximumVersion>{self.maxVersion}</maximumVersion>
                </orComposite>
            </requirement>"""
        
        def __dict__(self):
            return {'typeValue': self.typeValue,
                    'typeSource': self.typeSource,
                    'nameValue': self.nameValue,
                    'nameSource': self.nameSource,
                    'minVersion': self.minVersion,
                    'maxVersion': self.maxVersion}

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
        return {'format': self.format.__dict__() if self.format is not None else {'format': []},
                'size': self.size.__dict__() if self.size is not None else {'size': []},
                'location': self.location.__dict__() if self.location is not None else {'location': []},
                'installationRemarks': self.installationRemarks.__dict__() if self.installationRemarks is not None else {'installationRemarks': []},
                'otherPlatformRequirements': self.otherPlatformRequirements.__dict__() if self.otherPlatformRequirements is not None else {'otherPlatformRequirements': []},
                'requirement': self.requirement.__dict__() if self.requirement is not None else {'typeValue': [],
                    'typeSource': [],
                    'nameValue': [],
                    'nameSource': [],
                    'minVersion': [],
                    'maxVersion': []},
                'duration': self.duration.__dict__() if self.duration is not None else {'duration': [], 'description': []}}