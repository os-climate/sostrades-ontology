'''
Copyright 2022 Airbus SAS
Modifications on 2024/06/07 Copyright 2024 Capgemini
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

from numpy import array_equal

from sos_ontology.core.sos_entities.parameter import Parameter
from sos_ontology.core.sos_entities.sos_entity import SoSEntity


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
        self.datatype = None
        self.unit = None
        self.editable = None
        self.subtypeDescriptor = None
        self.sos_discipline = sos_discipline
        self.instanceOf = parameter
        for key, value in attributesDict.items():
            if key == 'visibility':
                self.visibility = value
            if key == 'default':
                self.defaultValue = value
            if key == 'dataframe_edition_locked':
                self.dataframeEditionLocked = value
            if key == 'user_level':
                self.userLevel = value
            if key == 'possible_values':
                self.possibleValues = value
            if key == 'range':
                self.range = value
            if key == 'dataframe_descriptor':
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
            if key == 'type':
                self.datatype = value
            if key == 'unit':
                self.unit = value
            if key == 'subtype_descriptor':
                self.subtypeDescriptor = value
        parameter.add_usage(self)
        parameter.add_disciplineUsingParameter(sos_discipline.id)

    def updateAttributes(self, attributesDict):
        for key, value in attributesDict.items():
            if value is not None and (
                isinstance(value, str) and value != '' and value != ' '
            ):
                if key == 'visibility' and self.visibility != value:
                    self.visibility = value
                if (
                    key == 'dataframe_edition_locked'
                    and self.dataframeEditionLocked != value
                ):
                    self.dataframeEditionLocked = value
                if key == 'user_level' and self.userLevel != value:
                    self.userLevel = value
                if key == 'possible_values' and array_equal(
                    self.possibleValues, value, equal_nan=False,
                ):
                    self.possibleValues = value
                if key == 'range' and self.range != value:
                    self.range = value
                if key == 'dataframe_descriptor' and self.dataframeDescriptor != value:
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
                if key == 'subtype_descriptor' and self.io_type != value:
                    self.subtypeDescriptor = value
