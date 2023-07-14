class Relation:
        kind = None
        resource = None

        def __init__(self, kind='', resource=None):
            self.kind = kind
            self.resource = resource

        class Resource:
            description = None
            identifier = None

            def __init__(self, identifier=None, description=''):
                self.description = description
                self.identifier = identifier

            class Identifier:
                catalog = None
                entry = None

                def __init__(self, catalog='', entry=''):
                    self.catalog = catalog
                    self.entry = entry

                def __dict__(self):
                    return {'Catalog': self.catalog, 'Entry': self.entry}

                def to_xml(self):
                    return f"""<identifier>
                    <catalog>{self.catalog}</catalog>
                    <entry>{self.entry}</entry>
                    </identifier>"""

            def to_xml(self):
                return f"""<resource>
                {self.identifier.to_xml() if self.identifier is not None else ''}
                <description>
                <string language="en">{self.description}</string>
                </description>
                </resource>"""

            def __dict__(self):
                return {'Identifier': self.identifier.__dict__() if self.identifier is not None
                else self.Identifier().__dict__(),
                        'Description': self.description}

        def to_xml(self):
            return f"""<relation>
            <kind>
            <source>LOMv1.0</source>
            <value>{self.kind}</value>
            </kind>
            {self.resource.to_xml() if self.resource is not None else ''}
            </relation>"""

        def __dict__(self):
            return {'Kind': self.kind, 'Resource': self.resource.__dict__() if self.resource is not None
            else self.Resource().__dict__()}