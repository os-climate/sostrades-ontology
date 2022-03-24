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


class SoSEntityList:
    def __init__(self) -> None:
        self.sos_entity_list = []
        self.sos_entity_ids = set()

    def add(self, entity) -> None:
        if entity.id not in self.sos_entity_ids:
            self.sos_entity_list.append(entity)
            self.sos_entity_ids.add(entity.id)

    def get(self, id: str):
        if id in self.sos_entity_ids:
            for entity in self.sos_entity_list:
                if entity.id == id:
                    return entity
        return None

    def len(self):
        return len(self.sos_entity_list)
