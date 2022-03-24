'''
Copyright 2022 Airbus SAS

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

from sos_ontology.core.sos_entities.sos_entity import SoSEntity


class SoSDiscipline(SoSEntity):
    def __init__(
        self,
        id: str,
        label: str,
        repository,
        pythonModulePath: str,
        definition: str,
        validated: str,
        maturity: str,
        icon: str,
        documentation: str,
        last_modification_date: str,
        validated_by: str,
        pythonClassInheritance: str,
        pythonClass: str,
        source: str,
        category: str,
        version: str,
    ) -> None:
        super().__init__(id, label)

        self.id = id
        self.label = label
        self.repository = repository
        self.pythonModulePath = pythonModulePath
        self.definition = definition
        self.validated = validated
        self.maturity = maturity
        self.icon = icon
        self.documentation = documentation
        self.last_modification_date = last_modification_date
        self.validated_by = validated_by
        self.pythonClassInheritance = pythonClassInheritance
        self.pythonClass = pythonClass
        self.source = source
        self.category = category
        self.version = version
        self.inputParameterUsagesList = []
        self.outputParameterUsagesList = []
        self.outputParameterUsagesIds = []
        self.inputParameterUsagesIds = []

    def add_input_parameter_usage(self, parameter_usage):
        trouve = False
        if parameter_usage is not None:
            for param in self.inputParameterUsagesList:
                if param.id == parameter_usage.id:
                    trouve = True
            if not trouve:
                self.inputParameterUsagesList.append(parameter_usage)
                self.inputParameterUsagesIds.append(parameter_usage.id)

    def add_output_parameter_usage(self, parameter_usage):
        trouve = False
        if parameter_usage is not None:
            for param in self.outputParameterUsagesList:
                if param.id == parameter_usage.id:
                    trouve = True
            if not trouve:
                self.outputParameterUsagesList.append(parameter_usage)
                self.outputParameterUsagesIds.append(parameter_usage.id)
