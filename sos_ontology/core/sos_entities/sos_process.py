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

from sos_ontology.core.sos_entities.sos_discipline import SoSDiscipline
from sos_ontology.core.sos_entities.sos_entity import SoSEntity


class SoSProcess(SoSEntity):
    def __init__(
        self,
        id: str,
        label: str,
        description: str,
        repository,
        documentation: str,
        process_module_path: str,
        category: str,
        version: str,
    ) -> None:
        super().__init__(id, label)
        self.description = description
        self.repository = repository
        self.documentation = documentation
        self.process_module_path = process_module_path
        self.category = category
        self.version = version
        self.models_list = []
        self.models_list_ids = []
        self.usecases_list = []
        self.usecases_list_ids = []

    def add_model(self, model: SoSDiscipline) -> None:
        if model not in self.models_list:
            self.models_list.append(model)
            self.models_list_ids.append(model.id)

    def add_usecase(self, usecase) -> None:
        if usecase not in self.usecases_list:
            self.usecases_list.append(usecase)
            self.usecases_list_ids.append(usecase.id)
