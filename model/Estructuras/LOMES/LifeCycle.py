class LifeCycle:
        version = None
        status = None
        contribute = None

        def __init__(self, version='', status='', contribute=None):
            self.version = version
            self.status = status
            self.contribute = contribute

        class Contribute:
            source = []
            value = []
            entity = []
            datetime = []
            description_string = []

            def __init__(self, source=[], value=[], entity=[], datetime=[], description_string=[]):
                self.source=source
                self.value=value
                self.entity=entity
                self.datetime=datetime
                self.description_string=description_string
            
            def addValues(self,atributes):
                self.source=atributes.get('lomes:source')
                self.value=atributes.get('lomes:value')
                self.entity=atributes.get('lomes:entity')
                self.datetime=atributes.get('lomes:dateTime')
                self.description_string=atributes.get('lomes:string')

            def __dict__(self):
                return {'Source': self.source, 'Role': self.value, 'Entity': self.entity, 'Datetime': self.datetime, 'Description': self.description_string}

            def to_xml(self):
                return f"""<contribute>
                <role>
                <source>{self.source}</source>
                <value>{self.value}</value>
                </role>
                <entity>{self.entity}</entity>
                <date>
                <dateTime>{self.datetime}</dateTime>
                <description>
                <string>{self.description_string}</string>
                </description>
                </date>
                </contribute>"""
        class Version:
            string=[]

            def __init__(self, string=[]):
                self.string = string
            
            def addValues(self,atributes):
                self.string=atributes.get('lomes:string')


            def to_xml(self):
                return f"""<version>
                <string"{self.string}"></string>
                </version>"""

            def __dict__(self):
                return {'String': self.string}

        class Status:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('lomes:source')
                self.value=atributes.get('lomes:value')

            def to_xml(self):
                return f"""<status>
                                <source>{self.source}</source>
                                <value>{self.value}</value>
                            </status>"""

            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}

        def __dict__(self):
            return {'Version': self.version.__dict__() if self.version is not None else [],
                    'Status': self.status.__dict__() if self.status is not None else [],
                    'Contribute': self.contribute.__dict__() if self.contribute is not None else []}

        def to_xml(self):
            return f"""<lifeCycle>
                {'' if isinstance(self.contribute, str) else self.contribute.to_xml() if self.contribute is not None else ''}
                {'' if isinstance(self.status, str) else self.status.to_xml() if self.status is not None else ''}
                {'' if isinstance(self.version, str) else self.version.to_xml() if self.version is not None else ''}
            </lifeCycle>"""