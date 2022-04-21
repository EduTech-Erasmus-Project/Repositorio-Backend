class Educational:
        interactivityType = None
        learningResourceType = None
        interactivityLevel = None
        semanticDensity = None
        intendedEndUserRole = None
        context = None
        typicalAgeRange = None
        difficulty = None
        typicalLearningTime = None
        description = None
        language = None

        def __init__(self, interactivityType=None, learningResourceType=None, interactivityLevel=None,
                     semanticDensity=None, intendedEndUserRole=None, context=None, typicalAgeRange=None, difficulty=None,
                     typicalLearningTime=None, description=None, language=None):
            self.interactivityType = interactivityType
            self.learningResourceType = learningResourceType
            self.interactivityLevel = interactivityLevel
            self.semanticDensity = semanticDensity
            self.intendedEndUserRole = intendedEndUserRole
            self.context = context
            self.typicalAgeRange = typicalAgeRange
            self.difficulty = difficulty
            self.typicalLearningTime = typicalLearningTime
            self.description = description
            self.language = language
        
        class Learningresourcetype:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                self.value=atributes.get('value')

            def to_xml(self):
                return f"""<learningResourceType >
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </learningResourceType>"""

            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}
        
        class Intendedenduserrole:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                self.value=atributes.get('value')

            def to_xml(self):
                return f"""<intendedEndUserRole >
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </intendedEndUserRole>"""

            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}
        
        class Interactivitylevel:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                self.value=atributes.get('value')

            def to_xml(self):
                return f"""<interactivityLevel>
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </interactivityLevel>"""

            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}
        
        class Semanticdensity:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                self.value=atributes.get('value')

            def to_xml(self):
                return f"""<semanticDensity>
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </semanticDensity>"""

            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}
        
        class Context:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                self.value=atributes.get('value')

            def to_xml(self):
                return f"""<context>
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </context>"""

            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}
        
        class Difficulty:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                self.value=atributes.get('value')

            def to_xml(self):
                return f"""<Difficulty>
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </Difficulty>"""

            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}
        
        class Typicallearningtime:
            duration = []
            string = []

            def __init__(self, duration=[], string=[]):
                self.duration = duration
                self.string = string
            
            def addValues(self,atributes):
                self.source=atributes.get('duration')
                self.value=atributes.get('string')

            def to_xml(self):
                return f"""<typicalLearningTime>
                                <duration>{self.duration}</duration>
                                <description>
                                    <string>{self.string}</string>
                                </description>
                            </typicalLearningTime>"""

            def __dict__(self):
                return {'Duration': self.source, 'Description': self.value}

        class Description:
            description = []

            def __init__(self, description=[]):
                self.description = description
            
            def addValues(self,atributes):
                self.description=atributes.get('string')
                if self.description is None:
                    self.description=atributes.get('#text')
            def to_xml(self):
                return f"""<description>
                <string>{self.description}</description>
                </description>"""

            def __dict__(self):
                return {'Description': self.description}
        
        class Typicalagerange:
            string = []

            def __init__(self, string=[]):
                self.string = string
            
            def addValues(self,atributes):
                self.string=atributes.get('string')


            def to_xml(self):
                return f"""<typicalAgeRange>
                                <string>{self.string}</string>
                            </typicalAgeRange>"""

            def __dict__(self):
                return {'typicalAgeRange': self.string}
        
        class Language:
            language = []

            def __init__(self, language=[]):
                self.language = language
            
            def addValues(self,atributes):
                self.language=atributes.get('language')


            def to_xml(self):
                return f"""<language >{self.language}</language>"""

            def __dict__(self):
                return {'Language': self.language}
        
        class Interactivitytype:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                self.value=atributes.get('value')

            def to_xml(self):
                return f"""<interactivityType >
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </interactivityType>"""

            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}

        def to_xml(self):
            return f"""<educational>
            {'' if isinstance(self.interactivityType, str) else self.interactivityType.to_xml() if self.interactivityType is not None else ''}
            {'' if isinstance(self.learningResourceType, str) else self.learningResourceType.to_xml() if self.learningResourceType is not None else ''}
            {'' if isinstance(self.interactivityLevel, str) else self.interactivityLevel.to_xml() if self.interactivityLevel is not None else ''}
            {'' if isinstance(self.semanticDensity, str) else self.semanticDensity.to_xml() if self.semanticDensity is not None else ''}
            {'' if isinstance(self.intendedEndUserRole, str) else self.intendedEndUserRole.to_xml() if self.intendedEndUserRole is not None else ''}
            {'' if isinstance(self.context, str) else self.context.to_xml() if self.context is not None else ''}
            {'' if isinstance(self.typicalAgeRange, str) else self.typicalAgeRange.to_xml() if self.typicalAgeRange is not None else ''}
            {'' if isinstance(self.difficulty, str) else self.difficulty.to_xml() if self.difficulty is not None else ''}
            {'' if isinstance(self.typicalLearningTime, str) else self.typicalLearningTime.to_xml() if self.typicalLearningTime is not None else ''}
            {'' if isinstance(self.description, str) else self.description.to_xml() if self.description is not None else ''}
            {'' if isinstance(self.language, str) else self.language.to_xml() if self.language is not None else ''}
            </educational>"""

        def __dict__(self):
            return {'Interactivity Type': self.interactivityType.__dict__() if self.interactivityType is not None else [],
                    'Learning Resource Type': self.learningResourceType.__dict__() if self.learningResourceType is not None else [],
                    'Interactivity Level': self.interactivityLevel.__dict__() if self.interactivityLevel is not None else [],
                    'Intended End UserRole': self.intendedEndUserRole.__dict__() if self.intendedEndUserRole is not None else [],
                    'Semantic Density': self.semanticDensity.__dict__() if self.semanticDensity is not None else [],
                    'Context': self.context.__dict__() if self.context is not None else [],
                    'Difficulty': self.difficulty.__dict__() if self.difficulty is not None else [],
                    'Description': self.description.__dict__() if self.description is not None else [],
                    'Typical Age Range': self.typicalAgeRange.__dict__() if self.typicalAgeRange is not None else [],
                    'Typical Learning Time': self.typicalLearningTime.__dict__() if self.typicalLearningTime is not None else [],
                    'Language': self.language.__dict__() if self.language is not None else []}