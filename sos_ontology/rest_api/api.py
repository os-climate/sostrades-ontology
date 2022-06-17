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

from flask import Flask
from flask import request, jsonify, make_response
from werkzeug.exceptions import BadRequest

from sos_ontology.core.sos_ontology import SoSOntology

SoSOntology.instance()
app = Flask(__name__)


@app.route('/api/ontology/v1/study', methods=['POST'])
def load_study_ontology_data():
    """
    Methods that retrieve disciplines and parameter usage ontology data

    Request object is intended with the following data structure
        {
            study_ontology_request: {
                disciplines: string[], // list of disciplines string identifier
                parameter_usages: string[] // list of parameter_usage string identifier composed of <discipline_id>_<input OR output>_<parameter_id>
            }
        }

    Returned response is with the following data structure
        {
            parameter_usages : {
                <parameter_usage_identifier> : {
                    parameter_uri: string
                    parameter_id: string
                    parameter_label: string
                    parameter_definition: string
                    parameter_definitionSource: string
                    parameter_ACLTag: string

                    visibility: string
                    dataframeEditionLocked: string
                    userLevel: string
                    range: string
                    dataframeDescriptor: string
                    structuring: string
                    optional: string
                    namespace: string
                    numerical: string
                    coupling: string
                    io_type: string
                    datatype: string
                    unit: string
                    editable: string
                }
            }
            disciplines {
                <discipline_identifier>: {
                    id: string
                    delivered: string
                    implemented: string
                    label: string
                    modelType: string
                    originSource: string
                    pythonClass: string
                    uri: string
                    validator: string
                    validated: string
                    icon:string
                }
            }
        }

    """

    data_request = request.json.get('study_ontology_request', None)

    missing_parameter = []
    if data_request is None:
        missing_parameter.append('Missing mandatory parameter: study_ontology_request')

    if len(missing_parameter) > 0:
        raise BadRequest('\n'.join(missing_parameter))

    ontology = SoSOntology.instance()

    resp = make_response(jsonify(ontology.get_study_ontology_data(data_request)), 200)

    return resp


@app.route('/api/ontology/v1/full_parameter_label_list', methods=['GET'])
def get_full_parameter_label_list():
    """
    Methods that retrieve all parameters label

    Request object has no parameters

    Returned response is with the following data structure
        [
            parameter_id:{
                uri:string,
                id:string,
                label: string,
            }
        ]
    """

    ontology = SoSOntology.instance()

    resp = make_response(jsonify(ontology.get_full_parameter_label_list()), 200)

    return resp


@app.route('/api/ontology/v1/full_process_list', methods=['GET'])
def get_full_process_list():
    """
    Methods that retrieve all processes and related information

    Request object has no parameters

    Returned response is with the following data structure
            process_id:{
                uri:string,
                id:string,
                label: string,
                description: string,
                category: string,
                version: string,
                process_repository: string,
                quantity_disciplines_used:int,
                discipline_list:string list,
                associated_usecases: string list,
            }
        ]
    """

    ontology = SoSOntology.instance()

    resp = make_response(jsonify(ontology.get_full_process_list()), 200)

    return resp


@app.route('/api/ontology/v1/full_discipline_list', methods=['GET'])
def get_full_discipline_list():
    """
    Methods that retrieve all disciplines and related information

    Request object has no parameters

    Returned response is with the following data structure
        [
            discipline_id:{
                'id': string,
                'uri': string,
                'label': string,
                'definition': string,
                'category': string,
                'version': string,
                'last_modification_date': string,
                'source': string,
                'validated_by': string,
                'python_class': string,
                'validated': string,
                'icon': string,
                'output_parameter_usages_quantity': int,
                'input_parameter_usages_quantity': int,
                'class_inheritance': string list,
                'code_repository': string,
                'type': string,
                'python_module_path': string,
                'output_parameter_usages': string list,
                'input_parameter_usages': string list,
                'process_using_discipline': [
                    {
                        'id': string,
                        'uri': string,
                        'label': string,
                    }
                ,]
            }
        ]
    """

    ontology = SoSOntology.instance()

    resp = make_response(jsonify(ontology.get_full_discipline_list()), 200)

    return resp


@app.route('/api/ontology/v1/full_parameter_list', methods=['GET'])
def get_full_parameter_list():
    """
    Methods that retrieve all parameters and associated information

    Request object has no parameters

    Returned response is with the following data structure
        [
            parameter_id:{
                uri:string,
                id:string,
                label: string,
                definition: string,
                definition_source: string,
                ACLTag: string,
                code_repositories: string list,
                possible_datatypes:string list,
                possible_units:string list,
                quantity_models_using_parameter:int,
                parameter_usage_details:[
                    parameter_usage_id:{
                        model_id: string,
                        model_label: string,
                        io_type: string,
                        unit: string,
                        datatype: string,
                        numerical: boolean,
                        optional: boolean,
                        range: string,
                        structuring: boolean,
                        editable: boolean,
                        possible_values: string,
                        dataframe_descriptor: string,
                        dataframe_edition_locked: boolean,
                        namespace: string,
                        user_level: string,
                        visibility: string,
                        structuring: boolean,
                    }
                ]
            }
        ]
    """

    ontology = SoSOntology.instance()

    resp = make_response(jsonify(ontology.get_full_parameter_list()), 200)

    return resp


@app.route('/api/ontology', methods=['POST'])
def load_ontology_request():
    """
    Methods that retrieve disciplines and parameters information

    Request object is intended with the following data structure
        {
            ontology_request: {
                disciplines: string[], // list of disciplines string identifier
                parameters: string[] // list of parameters string identifier
            }
        }

    Returned response is with the following data structure
        {
            parameters : {
                <parameter_identifier> : {
                    id: string
                    datatype: string
                    definition: string
                    label: string
                    quantityKind: string
                    unit: string
                    uri: string
                    definitionSource: string
                    ACLTag: string
                }
            }
            disciplines {
                <discipline_identifier>: {
                    id: string
                    delivered: string
                    implemented: string
                    label: string
                    modelType: string
                    originSource: string
                    pythonClass: string
                    uri: string
                    validator: string
                    validated: string
                    icon:string
                }
            }
        }

    """

    data_request = request.json.get('ontology_request', None)

    missing_parameter = []
    if data_request is None:
        missing_parameter.append('Missing mandatory parameter: ontology_request')

    if len(missing_parameter) > 0:
        raise BadRequest('\n'.join(missing_parameter))

    ontology = SoSOntology.instance()

    resp = make_response(jsonify(ontology.get_metadata(data_request)), 200)

    return resp


@app.route('/api/ontology/models/status', methods=['GET'])
def load_ontology_models_status():
    """
    Relay to ontology server to retrieve the whole sos_trades models status
    Object returned is a form of plotly table data structure

    Returned response is with the following data structure
        {
            headers : string[],
            values: array of {
                details: string,
                header: string,
                value: string
            }
        }
    """

    ontology = SoSOntology.instance()

    result = {}
    result['status_info'] = ontology.get_models_status()

    return make_response(jsonify(result), 200)


@app.route('/api/ontology/models/status-filtered', methods=['POST'])
def load_ontology_models_status_filtered():
    """
    Relay to ontology server to retrieve the whole sos_trades models status
    Object returned is a form of plotly table data structure

    Returned response is a list of class ModelStatus
    """

    linked_process_dict = request.json.get('linked_process_dict', None)

    ontology = SoSOntology.instance()
    result = ontology.get_models_list_filtered(linked_process_dict)

    return make_response(jsonify(result), 200)


@app.route('/api/ontology/models/links', methods=['GET'])
def load_ontology_models_links():
    """
    Method that retrieve the whole sos_trades models links diagram
    Object returned is a form of d3 js data structure

    Returned response is with the following data structure
        {
            nodes : array of {
                id: string,
                group: integer
            }
            links: array of {
                source: string,
                target: string,
                value: integer
            }

        }
    """

    ontology = SoSOntology.instance()

    return make_response(jsonify(ontology.get_models_nodes_and_links()), 200)


@app.route('/api/ontology/models/links-filtered', methods=['POST'])
def load_ontology_models_links_filtered():
    """
    Method that retrieve the whole sos_trades models links diagram
    Object returned is a form of d3 js data structure

    Returned response is with the following data structure
        {
            nodes : array of {
                id: string,
                group: integer
            }
            links: array of {
                source: string,
                target: string,
                value: integer
            }

        }
    """
    linked_process_dict = request.json.get('linked_process_dict', None)
    ontology = SoSOntology.instance()

    return make_response(
        jsonify(ontology.get_models_nodes_and_links_filtered(linked_process_dict)), 200
    )


@app.route('/api/ontology/process/<string:process_identifier>', methods=['GET'])
def load_ontology_process_metadata(process_identifier):
    """Given a process identifier, return the associated metadata"""
    ontology = SoSOntology.instance()

    return make_response(
        jsonify(ontology.get_process_metadata(process_identifier)), 200
    )


@app.route('/api/ontology/process/by/names', methods=['POST'])
def load_ontology_process_metadata_by_names():
    """given a list of process identifier, return a dictionary with each of their
    metadata
    """

    processes_name = request.json.get('processes_name', None)

    if processes_name is None:
        raise BadRequest('Missing mandatory parameter list "processes_name"')
    if not isinstance(processes_name, list):
        raise BadRequest(
            f'Parameter "processes_name" has the wrong type, intended "list" received "{type(processes_name)}"'
        )

    ontology = SoSOntology.instance()

    result = {}

    for process_name in processes_name:
        metadata = ontology.get_process_metadata(process_name)
        result[process_name] = metadata

    return make_response(jsonify(result), 200)


@app.route('/api/ontology/repository/<string:repository_identifier>', methods=['GET'])
def load_ontology_repository_metadata(repository_identifier):
    ontology = SoSOntology.instance()

    return make_response(
        jsonify(ontology.get_repo_metadata(repository_identifier)), 200
    )


@app.route('/api/ontology/repository/by/names', methods=['POST'])
def load_ontology_repository_metadata_by_names():
    """given a list of repository identifier, return a dictionary with each of their
    metadata
    """

    repositories_name = request.json.get('repositories_name', None)

    if repositories_name is None:
        raise BadRequest('Missing mandatory repository list "repositories_name"')
    if not isinstance(repositories_name, list):
        raise BadRequest(
            f'Parameter "repositories_name" has the wrong type, intended "list" received "{type(repositories_name)}"'
        )

    ontology = SoSOntology.instance()

    result = {}

    for repository_name in repositories_name:
        metadata = ontology.get_repo_metadata(repository_name)
        result[repository_name] = metadata

    return make_response(jsonify(result), 200)


@app.route('/api/ontology/n2', methods=['POST'])
def load_ontology_n2():

    treeView = request.json.get('treeview', None)

    missing_parameter = []
    if treeView is None:
        missing_parameter.append('Missing mandatory parameter: treeview')

    if len(missing_parameter) > 0:
        raise BadRequest('\n'.join(missing_parameter))

    ontology = SoSOntology.instance()

    tree_nodes, parameter_nodes, hierarchy_links = ontology.get_n2_matrix(treeView)

    result = {}
    result.update({'tree_nodes': tree_nodes})
    result.update({'parameter_nodes': parameter_nodes})
    result.update({'hierarchy_links': hierarchy_links})

    return make_response(jsonify(result), 200)


@app.route(
    '/api/ontology/markdown_documentation/<string:element_identifier>', methods=['GET']
)
def load_ontology_markdown_documentation(element_identifier):
    ontology = SoSOntology.instance()

    return make_response(
        jsonify(ontology.get_markdown_documentation(element_identifier)), 200
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555)
