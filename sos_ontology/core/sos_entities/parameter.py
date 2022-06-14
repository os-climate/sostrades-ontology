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


class Parameter(SoSEntity):
    def __init__(self, id: str, label: str, attributesDict: dict) -> None:
        super().__init__(id, label)
        self.unit = None
        self.unit_list = []
        self.datatype_list = []
        self.definition = None
        self.definitionSource = None
        self.datatype = None
        self.ACLTag = None
        self.instances_list = []
        self.code_repositories = []
        self.code_repositories_attributes = {}
        self.disciplinesUsingParameterIDs = []

        for key, value in attributesDict.items():
            if key == 'unit':
                self.unit = value
            if key == 'definition':
                self.definition = value
            if key == 'definitionSource':
                self.definitionSource = value
            if key == 'type':
                self.datatype = value
            if key == 'ACLTag':
                self.ACLTag = value

    def add_usage(self, usage) -> None:
        if usage not in self.instances_list:
            self.instances_list.append(usage)

    def add_unit(self, usage) -> None:
        if usage.unit is not None:
            if usage.unit not in self.unit_list:
                self.unit_list.append(usage.unit)

    def add_datatype(self, usage) -> None:
        if usage.datatype is not None:
            if usage.datatype not in self.datatype_list:
                self.datatype_list.append(usage.datatype)

    def add_disciplineUsingParameter(self, disciplineID) -> None:
        if disciplineID not in self.instances_list:
            self.disciplinesUsingParameterIDs.append(disciplineID)

    def add_code_repository(self, code_repository) -> None:
        if code_repository not in self.code_repositories:
            self.code_repositories.append(code_repository)

    def add_code_repository_attributes(self, code_repository, attributesDict) -> None:
        if code_repository not in self.code_repositories:
            self.code_repositories_attributes[code_repository.id] = attributesDict

    def updateOntologyAttributes(self, attributesDict):
        for key, value in attributesDict.items():
            if value is not None:
                if key == 'unit' and self.unit != value:
                    self.unit = value
                if key == 'definition' and self.definition != value:
                    self.definition = value
                if key == 'definitionSource' and self.definitionSource != value:
                    self.definitionSource = value
                if key == 'ACLTag' and self.ACLTag != value:
                    self.ACLTag = value
                if key == 'label' and self.label != value:
                    self.label = value
