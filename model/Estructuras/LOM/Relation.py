class Relation:
        kind = None
        resource = None

        def __init__(self, kind='', resource=None):
            self.kind = kind
            self.resource = resource
        
        class Kind:
            source = []
            value = []

            def __init__(self, source=[], value=[]):
                self.source = source
                self.value = value
            
            def addValues(self,atributes):
                self.source=atributes.get('source')
                self.value=atributes.get('value')

            def to_xml(self):
                return f"""<kind>
                                <source>{self.source}</source>
                                <value>{self.value}</value>
                            </kind>"""
            def __dict__(self):
                return {'Source': self.source, 'Value': self.value}

        class Resource:
            catalog = []
            entry = []
            string = []

            def __init__(self, catalog=[], entry=[], string=[]):
                self.catalog = catalog
                self.entry = entry
                self.string = string

            def addValues(self,atributes):
                self.catalog=atributes.get('catalog')
                self.entry=atributes.get('entry')
                self.string=atributes.get('string')

            def to_xml(self):
                return f"""<resource>
                                <identifier>
                                    <catalog>{self.catalog}</catalog>
                                    <entry>{self.entry}</entry>
                                </identifier>
                                <description>
                                    <string>{self.string}</string>
                                </description>
                            </resource>"""

            def __dict__(self):
                return {'Catalog': self.catalog, 'Entry': self.entry, 'Description':self.string}

        def to_xml(self):
            return f"""<relation>
            {'' if isinstance(self.kind, str) else self.kind.to_xml() if self.kind is not None else ''}
            {'' if isinstance(self.resource, str) else self.resource.to_xml() if self.resource is not None else ''}
            </relation>"""

        def __dict__(self):
            return {'Kind': self.kind.__dict__() if self.kind is not None else [],
                    'Resource': self.resource.__dict__() if self.resource is not None else []}