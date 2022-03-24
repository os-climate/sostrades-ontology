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

from sos_ontology.rest_api.api import load_ontology_markdown_documentation

# test process documentation
process_doc = load_ontology_markdown_documentation(
    'business_case.sos_processes.business_case.bc_level_0_by_subsystem')

# test model Documentation
model_doc = load_ontology_markdown_documentation(
    'business_case.sos_wrapping.infrastructure_discipline.infrastructure_vb_discipline')

# test model not exists Documentation
model_doc = load_ontology_markdown_documentation(
    'business_case.sos_wrapping.infrastructure_discipline.infrastructure_vb_discipline2')

# test model without Documentation
model_doc = load_ontology_markdown_documentation(
    'business_case.sos_wrapping.valueblock_disciplines.subcomponent_oss_vb_discipline')

if process_doc != '' and model_doc != '':
    print('DONE')
