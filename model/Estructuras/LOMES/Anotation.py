class Annotation:
        entity = None
        date = None
        description = None
        mode_access = None
        mode_access_sufficient = None
        rol = None

        def __init__(self, entity='', date='', description='', mode_access='', mode_access_sufficient='', rol=''):
            self.entity = entity
            self.date = date
            self.description = description
            self.mode_access = mode_access
            self.mode_access_sufficient = mode_access_sufficient
            self.rol = rol

        def to_xml(self):
            return f"""<annotation>
            <entity>
            <![CDATA[{self.entity}]]>
            </entity>
            <date>
            <dateTime>{self.date}</dateTime>
            <description>
            <string></string>
            </description>
            </date>
            <description>
            <string>{self.description}</string>
            </description>
            <modeaccess>
            <source>LOMv1.0</source>
            <value>{self.mode_access}</value>
            </modeaccess>
            <modeaccesssufficient>
            <source>LOMv1.0</source>
            <value>{self.mode_access_sufficient}</value>
            </modeaccesssufficient>
            <Rol>
            <source>LOMv1.0</source>
            <value>{self.rol}</value>
            </Rol>
            </annotation>"""

        def __dict__(self):
            return {'Entity': self.entity, 'Date': self.date, 'Description': self.description,
                    'Mode Access': self.mode_access, 'Mode Access Sufficient': self.mode_access_sufficient,
                    'Rol': self.rol}