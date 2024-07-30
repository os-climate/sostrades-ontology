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


class SoSEntity:
    def __init__(self, id: str, label: str) -> None:
        self.id = id
        self.label = label


class SoSEntityDict:
    def __init__(self) -> None:
        self.sos_entity_dict = {}

    def add(self, entity) -> None:
        if entity.id not in self.sos_entity_dict:
            self.sos_entity_dict[entity.id] = entity

    def get(self, id: str):
        return self.sos_entity_dict.get(id, None)

    def len(self):
        return len(self.sos_entity_dict)
