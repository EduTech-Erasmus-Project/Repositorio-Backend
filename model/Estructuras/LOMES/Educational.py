class Educational:
        interactivity_type = None
        learningResourceType = None
        interactivity_level = None
        semantic_density = None
        intendedEndUserRole = None
        context = None
        typical_age_range = None
        difficulty = None
        typical_learning_time = None
        description = None
        language = None

        def __init__(self, interactivity_type='', learningResourceType='', interactivity_level='',
                     semantic_density='', intendedEndUserRole='', context='', typical_age_range='', difficulty='',
                     typical_learning_time='', description='', language=''):
            self.interactivity_type = interactivity_type
            self.learningResourceType = learningResourceType
            self.interactivity_level = interactivity_level
            self.semantic_density = semantic_density
            self.intendedEndUserRole = intendedEndUserRole
            self.context = context
            self.typical_age_range = typical_age_range
            self.difficulty = difficulty
            self.typical_learning_time = typical_learning_time
            self.description = description
            self.language = language
        
        class Learningresourcetype:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('lomes:source')
                self.value=atributes.get('lomes:value')

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
                self.source=atributes.get('lomes:source')
                self.value=atributes.get('lomes:value')

            def to_xml(self):
                return f"""<intendedEndUserRole >
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </intendedEndUserRole>"""

            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}
        
        class Context:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('lomes:source')
                self.value=atributes.get('lomes:value')

            def to_xml(self):
                return f"""<context >
                                <source >{self.source}</source>
                                <value >{self.value}</value>
                            </context>"""

            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}

        class Description:
            language = []

            def __init__(self, language=[]):
                self.language = language
            
            def addValues(self,atributes):
                self.language=atributes.get('@language')


            def to_xml(self):
                return f"""<description>
                <string  language="{self.language}"></description>
                </description>"""

            def __dict__(self):
                return {'Language': self.language}
        
        class Language:
            language = []

            def __init__(self, language=[]):
                self.language = language
            
            def addValues(self,atributes):
                self.language=atributes.get('lomes:language')


            def to_xml(self):
                return f"""<language >{self.language}</language>"""

            def __dict__(self):
                return {'Language': self.language}

        def to_xml(self):
            return f"""<educational>
            {'' if isinstance(self.learningResourceType, str) else self.learningResourceType.to_xml() if self.learningResourceType is not None else ''}
            {'' if isinstance(self.intendedEndUserRole, str) else self.intendedEndUserRole.to_xml() if self.intendedEndUserRole is not None else ''}
            {'' if isinstance(self.context, str) else self.context.to_xml() if self.context is not None else ''}
            {'' if isinstance(self.description, str) else self.description.to_xml() if self.description is not None else ''}
            {'' if isinstance(self.language, str) else self.language.to_xml() if self.language is not None else ''}
            </educational>"""

        def __dict__(self):
            return {'Interactivity Type': self.interactivity_type,
                    'Learning Resource Type': self.learningResourceType.__dict__() if self.learningResourceType is not None else self.Learningresourcetype().__dict__(),
                    'Interactivity Level': self.interactivity_level, 'Semantic Density': self.semantic_density,
                    'Intended End User Roles': self.intendedEndUserRole.__dict__() if self.intendedEndUserRole is not None else self.Intendedenduserrole().__dict__(), 
                    'Context': self.context.__dict__() if self.context is not None else self.Context().__dict__(),
                    'Typical Age Range': self.typical_age_range, 'Difficulty': self.difficulty,'Typical Learning Time': self.typical_learning_time, 
                    'Description': self.description.__dict__() if self.description is not None else self.Description().__dict__(),
                    'Language':self.language.__dict__() if self.language is not None else self.Language().__dict__()}