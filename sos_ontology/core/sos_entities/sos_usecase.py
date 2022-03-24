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


class SoSUsecase(SoSEntity):
    def __init__(
        self, id: str, label: str, description: str, process, run_usecase: bool
    ) -> None:
        super().__init__(id, label)
        self.description = description
        self.process = process
        self.disciplines_dict = {}
        self.run_usecase = run_usecase

    def add_disciplines(self, local_discipline_name, discipline_entities):
        self.disciplines_dict[local_discipline_name] = discipline_entities
