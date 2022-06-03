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
                if self.source is None:
                    self.source=atributes.get('lomes:source')
                self.value=atributes.get('value')
                if self.value is None:
                    self.value=atributes.get('lomes:value')

            def to_xml(self):
                return f"""<learningResourceType >
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </learningResourceType>"""

            def __dict__(self):
                return {'source': self.source, 'value': self.value}
        
        class Intendedenduserrole:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                if self.source is None:
                    self.source=atributes.get('lomes:source')
                self.value=atributes.get('value')
                if self.value is None:
                    self.value=atributes.get('lomes:value')

            def to_xml(self):
                return f"""<intendedEndUserRole >
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </intendedEndUserRole>"""

            def __dict__(self):
                return {'source': self.source, 'value': self.value}
        
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
                return {'source': self.source, 'value': self.value}
        
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
                return {'source': self.source, 'value': self.value}
        
        class Context:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                if self.source is None:
                    self.source=atributes.get('lomes:source')
                self.value=atributes.get('value')
                if self.value is None:
                    self.value=atributes.get('lomes:value')

            def to_xml(self):
                return f"""<context>
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </context>"""

            def __dict__(self):
                return {'source': self.source, 'value': self.value}
        
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
                return {'source': self.source, 'value': self.value}
        
        class Typicallearningtime:
            duration = []
            string = []

            def __init__(self, duration=[], string=[]):
                self.duration = duration
                self.string = string
            
            def addValues(self,atributes):
                self.duration=atributes.get('duration')
                if self.duration is None:
                        self.duration=atributes.get('#text')

                #print("Edu 180 - duration: ",self.duration )
                
                self.string=atributes.get('description')
                if self.string is None:
                    self.string=atributes.get('string')
                #print("Edu 180 - description: ",self.string )
                

            def to_xml(self):
                return f"""<typicalLearningTime>
                                <duration>{self.duration}</duration>
                                <description>
                                    <string>{self.string}</string>
                                </description>
                            </typicalLearningTime>"""

            def __dict__(self):
                return {'duration': self.duration, 'description': self.string}

        class Description:
            description = []

            def __init__(self, description=[]):
                self.description = description
            
            def addValues(self,atributes):
                self.description=atributes.get('description')
                if self.description is None:
                    self.description=atributes.get('string')
                if self.description is None:
                    self.description=atributes.get('#text')
                if self.description is None:
                    self.description=atributes.get("@language")
            def to_xml(self):
                return f"""<description>
                <string>{self.description}</string>
                </description>"""

            def __dict__(self):
                return {'description': self.description}
        
        class Typicalagerange:
            string = []
           
            def __init__(self, string=[]):
                self.string = string
            
            def addValues(self,atributes):
                #print("Educational #223 - Atributes", atributes)
                self.string=atributes.get('typicalAgeRange')
                if self.string is None:
                    self.string=atributes.get('string')
                    if self.string is None:
                        self.string=atributes.get('#text')
                #print("Educational #227 - Age", self.string)

                


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
                if self.language is None:
                    self.language=atributes.get('lomes:language')

            def to_xml(self):
                return f"""<language >{self.language}</language>"""

            def __dict__(self):
                return {'language': self.language}
        
        class Interactivitytype:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                if isinstance(atributes, dict):
                    self.source=atributes.get('source')
                    self.value=atributes.get('value')

            def to_xml(self):
                return f"""<interactivityType >
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </interactivityType>"""

            def __dict__(self):
                return {'source': self.source, 'value': self.value}

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
            return {'interactivityType': self.interactivityType.__dict__() if self.interactivityType is not None else [],
                    'learningResourceType': self.learningResourceType.__dict__() if self.learningResourceType is not None else {'source': [], 'value': []},
                    'interactivityLevel': self.interactivityLevel.__dict__() if self.interactivityLevel is not None else {'source': [], 'value': []},
                    'intendedEndUserRole': self.intendedEndUserRole.__dict__() if self.intendedEndUserRole is not None else {'source': [], 'value': []},
                    'semanticDensity': self.semanticDensity.__dict__() if self.semanticDensity is not None else {'source': [], 'value': []},
                    'context': self.context.__dict__() if self.context is not None else {'source': [], 'value': []},
                    'difficulty': self.difficulty.__dict__() if self.difficulty is not None else {'source': [], 'value': []},
                    'description': self.description.__dict__() if self.description is not None else {'description': []},
                    'typicalAgeRange': self.typicalAgeRange.__dict__() if self.typicalAgeRange is not None else {'typicalAgeRange': []},
                    'typicalLearningTime': self.typicalLearningTime.__dict__() if self.typicalLearningTime is not None else {'duration': [], 'description': []},
                    'language': self.language.__dict__() if self.language is not None else {'language': []}}