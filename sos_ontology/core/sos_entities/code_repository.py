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


class CodeRepository(SoSEntity):
    def __init__(self, id: str, label: str) -> None:
        super().__init__(id, label)
        self.process_repositories_list = []
        self.process_repositories_ids = []
        self.branch = None
        self.commit = None
        self.committed_date = None
        self.url = None

    def add_process_repository(self, process_repository) -> None:
        if process_repository not in self.process_repositories_list:
            self.process_repositories_list.append(process_repository)
            self.process_repositories_ids.append(process_repository.id)

    def update_info(self, traceability_dict):
        self.branch = traceability_dict.get('branch', None)
        self.commit = traceability_dict.get('commit', None)
        self.url = traceability_dict.get('url', None)
        self.committed_date = traceability_dict.get('committed_date', None)
