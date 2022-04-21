class Classification:
        purpose = None  # purpose
        taxon_path = None  # taxon_path
        description = None  # description
        keywordd = None  # keywordd

        def __init__(self, purpose='', taxon_path=None, description='', keywordd=''):
            self.purpose = purpose
            self.taxon_path = taxon_path
            self.description = description
            self.keywordd = keywordd

        class TaxonPath:
            source = None
            taxon = None

            def __init__(self, source='', taxon=None):
                self.source = source
                self.taxon = taxon

            class Taxon:
                taxon_id = None
                entry = None

                def __init__(self, taxon_id='', entry=''):
                    self.taxon_id = taxon_id
                    self.entry = entry

                def __dict__(self):
                    return {'Id': self.taxon_id, 'Entry': self.entry}

                def to_xml(self):
                    return f"""<taxon>
                    <id>{self.taxon_id}</id>
                    <entry>
                    <string language="en">{self.entry}</string>
                    </entry>
                    </taxon>"""

            def to_xml(self):
                return f"""<taxonPath>
                <source>
                <string language="en">{self.source}</string>
                </source>
                {self.taxon.to_xml() if self.taxon is not None else ''}
                </taxonPath>"""

            def __dict__(self):
                return {'Source': self.source, 'Taxon': self.taxon.__dict__() if self.taxon is not None
                else self.Taxon().__dict__()}

        def to_xml(self):
            return f"""<classification>
            <purpose>
            <source>LOMv1.0</source>
            <value>{self.purpose}</value>
            </purpose>
            {self.taxon_path.to_xml() if self.taxon_path is not None else ''}
            <description>
            <string language="en">{self.description}</string>
            </description>
            <keyword>
            <string language="en">{self.keywordd}</string>
            </keyword>
            </classification>"""

        def __dict__(self):
            return {'Purpose': self.purpose, 'Taxon Path': self.taxon_path.__dict__() if self.taxon_path is not None
            else self.TaxonPath().__dict__(), 'Description': self.description, 'Keyword': self.keywordd}