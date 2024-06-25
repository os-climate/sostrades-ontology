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

from sos_ontology.core.sos_entities.code_repository import CodeRepository
from sos_ontology.core.sos_entities.sos_entity import SoSEntity


class SoSProcessRepository(SoSEntity):
    def __init__(
        self, id: str, label: str, description: str, code_repository: CodeRepository
    ) -> None:
        super().__init__(id, label)
        self.description = description
        self.processes_list = []
        self.processes_list_ids = []
        self.code_repository = code_repository

    def add_process(self, process) -> None:
        if process not in self.processes_list:
            self.processes_list.append(process)
            self.processes_list_ids.append(process.id)
