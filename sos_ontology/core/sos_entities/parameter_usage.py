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
from sos_ontology.core.sos_entities.parameter import Parameter


class ParameterUsage(SoSEntity):
    def __init__(
        self,
        id: str,
        label: str,
        attributesDict: dict,
        parameter: Parameter,
        sos_discipline,
    ) -> None:
        super().__init__(id, label)
        self.visibility = None
        self.defaultValue = None
        self.dataframeEditionLocked = None
        self.userLevel = None
        self.possibleValues = None
        self.range = None
        self.dataframeDescriptor = None
        self.structuring = None
        self.optional = None
        self.namespace = None
        self.numerical = None
        self.coupling = None
        self.io_type = None
        self.editable = None
        self.sos_discipline = sos_discipline
        self.instanceOf = parameter
        for key, value in attributesDict.items():
            if key == 'visibility':
                self.visibility = value
            if key == 'defaultValue':
                self.defaultValue = value
            if key == 'dataframeEditionLocked':
                self.dataframeEditionLocked = value
            if key == 'userLevel':
                self.userLevel = value
            if key == 'possibleValues':
                self.possibleValues = value
            if key == 'range':
                self.range = value
            if key == 'dataframeDescriptor':
                self.dataframeDescriptor = value
            if key == 'structuring':
                self.structuring = value
            if key == 'optional':
                self.optional = value
            if key == 'namespace':
                self.namespace = value
            if key == 'numerical':
                self.numerical = value
            if key == 'coupling':
                self.coupling = value
            if key == 'editable':
                self.editable = value
            if key == 'io_type':
                self.io_type = value
        parameter.add_usage(self)

    def updateAttributes(self, attributesDict):
        for key, value in attributesDict.items():
            if value is not None:
                if key == 'visibility' and self.visibility != value:
                    self.visibility = value
                if (
                    key == 'dataframeEditionLocked'
                    and self.dataframeEditionLocked != value
                ):
                    self.dataframeEditionLocked = value
                if key == 'user_level' and self.userLevel != value:
                    self.userLevel = value
                if key == 'possible_values' and self.possibleValues != value:
                    self.possibleValues = value
                if key == 'range' and self.range != value:
                    self.range = value
                if key == 'dataframeDescriptor' and self.dataframeDescriptor != value:
                    self.dataframeDescriptor = value
                if key == 'structuring' and self.structuring != value:
                    self.structuring = value
                if key == 'optional' and self.optional != value:
                    self.optional = value
                if key == 'namespace' and self.namespace != value:
                    self.namespace = value
                if key == 'numerical' and self.numerical != value:
                    self.numerical = value
                if key == 'coupling' and self.coupling != value:
                    self.coupling = value
                if key == 'editable' and self.editable != value:
                    self.editable = value
                if key == 'io_type' and self.io_type != value:
                    self.io_type = value
