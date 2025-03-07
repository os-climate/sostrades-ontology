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

import json
from os.path import dirname, join

from sos_ontology.core.sos_ontology import SoSOntology

parameter_usages_path = join(dirname(__file__), 'data', 'parameter_usages.json')
with open(parameter_usages_path) as outfile:
    parameter_usages = json.loads(outfile.read())

repositories_name_path = join(dirname(__file__), 'data', 'repositories_name.json')
with open(repositories_name_path) as outfile:
    repositories_name = json.loads(outfile.read())

processes_name_path = join(dirname(__file__), 'data', 'processes_name.json')
with open(processes_name_path) as outfile:
    processes_name = json.loads(outfile.read())

linked_process_dict_path = join(dirname(__file__), 'data', 'linked_process_dict.json')
with open(linked_process_dict_path) as outfile:
    linked_process_dict = json.loads(outfile.read())

data_request_path = join(dirname(__file__), 'data', 'data_request.json')
with open(data_request_path) as outfile:
    data_request = json.loads(outfile.read())

onto = SoSOntology.instance()
print(f'Ontology loaded with {len(onto.graph)} triples')

result = {}
print('Test get parameter glossary')
result['parameter_glossary'] = onto.get_full_parameter_list()

print('Test study ontology data')
result['study_ontology_data'] = onto.get_study_ontology_data(parameter_usages)


print('Test get_metadata')
result['get_metadata'] = onto.get_metadata(data_request)

print('Test get_repo_metadata')
for repository_name in repositories_name:
    metadata = onto.get_repo_metadata(repository_name)
    result[repository_name] = metadata

print('Test get_process_metadata')
for process_name in processes_name:
    metadata = onto.get_process_metadata(process_name)
    result[process_name] = metadata

print('Test get_models_status')
result['status_info'] = onto.get_models_status()

print('Test get_models_list_filtered')
result['models_filtered'] = onto.get_models_list_filtered(linked_process_dict)
print(result['models_filtered'])

print('Test get_models_nodes_and_links_filtered')
result['link_filtered'] = onto.get_models_nodes_and_links_filtered(linked_process_dict)

print('Test get_metadata')
result['get_metadata'] = onto.get_metadata(data_request)

print('Test done')
