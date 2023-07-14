class Accessibility:

        description = None
        accessibility_features = None
        accessibility_hazard = None
        accessibility_control = None
        accessibility_api = None

        def __init__(self, description='', accesibility_features=None, accessibility_hazard=None,
                     accessibility_control=None, accessibility_api=None):
            self.description = description
            self.accessibility_features = accesibility_features
            self.accessibility_hazard = accessibility_hazard
            self.accessibility_control = accessibility_control
            self.accessibility_api = accessibility_api

        class AccessibilityFeatures:
            resource_content = None

            def __init__(self, resource_content=''):
                self.resource_content = resource_content

            def __dict__(self):
                return {'Resource Content': self.resource_content}

            def get_resource_content(self):
                content = ""
                if type(self.resource_content) is OrderedDict and type(self.resource_content.get('br')) is list:
                    for resource in self.resource_content.get('br'):
                        content += f"<br>{resource}</br>\n"
                    return content
                else:
                    return self.resource_content.get('br')

            def to_xml(self):
                return f"""<accessibilityfeatures>
                <resourcecontent>
                {self.get_resource_content()}
                </resourcecontent>
                </accessibilityfeatures>"""

        class AccessibilityHazard:
            properties = None

            def __init__(self, properties=''):
                self.properties = properties

            def __dict__(self):
                return {'Properties': self.properties}

            def get_properties(self):
                content = ""
                if type(self.properties) is OrderedDict and type(self.properties.get('lomes:br')) is list:
                    for resource in self.properties.get('lomes:br'):
                        content += f"<lomes:br>{resource}</lomes:br>\n"
                    return content
                else:
                    return self.properties.get('lomes:br')

            def to_xml(self):
                return f"""<accessibilityhazard>
                <properties>
                {self.get_properties()}
                </properties>
                </accessibilityhazard>"""

        class AccessibilityControl:
            methods = None

            def __init__(self, methods=''):
                self.methods = methods

            def __dict__(self):
                return {'Methods': self.methods}

            def get_methods(self):
                content = ""
                if type(self.methods) is OrderedDict and type(self.methods.get('br')) is list:
                    for resource in self.methods.get('br'):
                        content += f"<br>{resource}</br>\n"
                    return content
                else:
                    return self.methods.get('br')

            def to_xml(self):
                return f"""<accessibilitycontrol>
                <methods>
                {self.get_methods()}
                </methods>
                </accessibilitycontrol>"""

        class AccessibilityAPI:
            compatible_resource = None

            def __init__(self, compatible_resource=''):
                self.compatible_resource = compatible_resource

            def __dict__(self):
                return {'Compatible Resource': self.compatible_resource}

            def get_compatible_resources(self):
                content = ""
                if type(self.compatible_resource) is OrderedDict and type(self.compatible_resource.get('br')) is list:
                    for resource in self.compatible_resource.get('br'):
                        content += f"<br>{resource}</br>\n"
                    return content
                else:
                    return self.compatible_resource.get('br')

            def to_xml(self):
                return f"""<accessibilityAPI>
                <compatibleresource>
                {self.get_compatible_resources()}
                </compatibleresource>
                </accessibilityAPI>"""

        def to_xml(self):
            return f"""<accesibility>
            <description><string language="en">{self.description}</string></description>
            {self.accessibility_features.to_xml() if self.accessibility_features is not None else ''}
            {self.accessibility_hazard.to_xml() if self.accessibility_hazard is not None else ''}
            {self.accessibility_control.to_xml() if self.accessibility_control is not None else ''}
            {self.accessibility_api.to_xml() if self.accessibility_api is not None else ''}
            </accesibility>"""

        def __dict__(self):
            return {'Description': self.description, 'Accessibility Features': self.accessibility_features.__dict__()
                    if self.accessibility_features is not None else self.AccessibilityFeatures().__dict__(),
                    'Accessibility Hazard': self.accessibility_hazard.__dict__() if self.accessibility_hazard is not None
                    else self.AccessibilityHazard().__dict__(),
                    'Accessibility Control': self.accessibility_control.__dict__() if self.accessibility_control is not None
                    else self.AccessibilityControl().__dict__(),
                    'Accessibility API': self.accessibility_api.__dict__() if self.accessibility_api is not None
                    else self.AccessibilityAPI().__dict__()}