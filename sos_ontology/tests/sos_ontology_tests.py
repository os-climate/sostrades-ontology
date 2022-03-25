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

from sos_ontology.core.ontology import Ontology
from sos_ontology.core.sos_ontology import SoSOntology
from os.path import dirname, join
import json

# load SoSOntology
# path = join(
#     dirname(sos_ontology.__file__),
#     'data',
#     'sos_ontology',
#     'SoSTrades_Ontology_ABox_Decentralized.owl',
# )

repositories_name_path = join(
    dirname(__file__), 'data', 'repositories_name.json')
with open(repositories_name_path, 'r') as outfile:
    repositories_name = json.loads(outfile.read())

processes_name_path = join(dirname(__file__), 'data', 'processes_name.json')
with open(processes_name_path, 'r') as outfile:
    processes_name = json.loads(outfile.read())

linked_process_dict_path = join(
    dirname(__file__), 'data', 'linked_process_dict.json')
with open(linked_process_dict_path, 'r') as outfile:
    linked_process_dict = json.loads(outfile.read())

data_request_path = join(dirname(__file__), 'data', 'data_request.json')
with open(data_request_path, 'r') as outfile:
    data_request = json.loads(outfile.read())

# onto.load(path, "xml")
onto = SoSOntology.instance()
print(f'Ontology loaded with {len(onto.graph)} triples')

result = {}
print('Test get_metadata')
result['get_metadata'] = onto.get_metadata(data_request)

# ontology.get_models_nodes_and_links_filtered(linked_process_dict)
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

print('Test get_models_nodes_and_links_filtered')
result['link_filtered'] = onto.get_models_nodes_and_links_filtered(
    linked_process_dict)

print('Test get_metadata')
result['get_metadata'] = onto.get_metadata(data_request)

print('Test done')
