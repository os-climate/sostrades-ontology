'''
Copyright 2022 Airbus SAS
Modifications on 2024/06/07-2024/07/16 Copyright 2024 Capgemini
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

import logging
import os
import tempfile
import time

from flask import Flask, jsonify, make_response, request, send_file, session
from werkzeug.exceptions import BadRequest

from sos_ontology.core.sos_ontology import SoSOntology
from sos_ontology.rest_api.utils import copy_file


def random_string_for_secret_key():
    '''
    Generate a random string tu use at secret key
    :return:
    '''
    import random
    import string

    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    num = string.digits
    letters = string.ascii_letters
    symbols = string.punctuation

    # Put them in the same list
    all_characters = lower + upper + num + symbols + letters

    return random.sample(all_characters, 32)


# When in API mode, create a copy of the file in a tempoary copy of the ontology
# So it can be loaded in parallel by several workers
# Because rdflib does not allow parallel loading of the same file
file_paths = SoSOntology.get_files_paths()

ontology_owl_file_path, ontology_excel_file_path, ontology_log_file_path = file_paths

# Create a temporary folder.
temp_folder = tempfile.mkdtemp(prefix="ontology_temp_")

# List of files to copy.
files_to_copy = [
    ontology_owl_file_path,
    ontology_excel_file_path,
    ontology_log_file_path,
]

# Copy each file into the temporary folder.
for file_path in files_to_copy:
    if not os.path.exists(file_path):
        raise Exception(f"File not found {file_path}")
    dest_path = os.path.join(temp_folder, os.path.basename(file_path))
    copy_file(file_path, dest_path)

# Update the ONTOLOGY_FOLDER environment variable.
os.environ['ONTOLOGY_FOLDER'] = temp_folder

SoSOntology.instance()

app = Flask(__name__)
flask_config_dict = {'SECRET_KEY': random_string_for_secret_key()}
app.config.update(flask_config_dict)
app.logger.propagate = False

for handler in app.logger.handlers:
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s : %(message)s"))

if app.config['DEBUG']:
    app.logger.setLevel(logging.DEBUG)
else:
    app.logger.setLevel(logging.INFO)

logging._srcfile = None
logging.logThreads = 0
logging.logProcesses = 0

START_TIME = 'start_time'


@app.route('/api/ontology/v1/general_information', methods=['GET'])
def get_general_information():
    """
    Methods returning generic information concerning the current ontology

    Request object has no parameters

    Returned response is with the following data structure
        {
            description:string,
            version:string,
            iri: string,
            last_updated:string
            entity_count:{
                'Code Repositories':integer,
                'Process Repositories':integer,
                'Processes':integer,
                'Models':integer,
                'Parameters':integer,
                'Usecases':integer,
            },
            source_code_traceability:[
                {
                    name:string
                    url: string
                    branch: string,
                    commit: string,
                    committed_date: string
                },
            ]
        }
    """

    ontology = SoSOntology.instance()

    resp = make_response(jsonify(ontology.get_general_information()), 200)

    return resp


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
                    uri:string,
                    id:string,
                    label: string,
                    definition: string,
                    definition_source: string,
                    ACLTag: string,
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
                process_repository_label: string,
                quantity_disciplines_used:int,
                discipline_list: [{id: string, label: string, icon: string}]
                associated_usecases: [{id: string, name: string, process: string,repository: string,run_usecase: boolean}]
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
                'output_parameters_quantity': int,
                'input_parameters_quantity': int,
                'class_inheritance': string list,
                'code_repository': string,
                'type': string,
                'python_module_path': string,
                'output_parameters': [{parameter_usage_id: string, parameter_id: string, parameter_label: string}],
                'input_parameters': [{parameter_usage_id: string, parameter_id: string, parameter_label: string}],
                'process_using_discipline': [{process_id: string, process_label: string, repository_id: string, repository_label: string}],
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


@app.route('/api/ontology/v1/documentation', methods=['POST'])
def retrieve_documentations():
    """
    Methods that retrieve documentation from a list of identifier

    Request object is intended with the following data structure
        {
            identifier_list: string[], // list of disciplines or processes string identifier
        }

    Returned response is with the following data structure
        {
            identifier : documentation Markdown as string,
        }

    """
    data_request = request.json.get('identifier_list', None)

    missing_parameter = []
    if data_request is None:
        missing_parameter.append('Missing mandatory parameter: identifier_list')

    if len(missing_parameter) > 0:
        raise BadRequest('\n'.join(missing_parameter))

    ontology = SoSOntology.instance()

    resp = make_response(jsonify(ontology.retrieve_documentations(data_request)), 200)

    return resp


@app.route('/api/ontology/v1/download', methods=['GET'])
def download_ontology_owl():
    """
    Methods that return the ontology owl to be downloaded
    """
    args = request.args
    if args is not None:
        filetype = args.get("filetype", None)
        if filetype is not None:
            ontology = SoSOntology.instance()
            if filetype == 'owl':
                path = ontology.ontology_owl_file_path
            elif filetype == 'xlsx':
                path = ontology.ontology_excel_file_path
            else:
                return str(
                    f'Filetype {filetype} does not exists. Possible options are filetype == owl or filetype == xlsx',
                )

            try:
                return send_file(path, as_attachment=True)
            except Exception as e:
                return str(e)
    return str(
        'No correct parameter were given. Possible options are filetype == owl or filetype == xlsx',
    )


@app.route('/api/ontology/v1/download_logs', methods=['GET'])
def download_ontology_logs():
    """
    Methods that return the ontology creation logs to be downloaded
    """
    ontology = SoSOntology.instance()
    path = ontology.ontology_log_file_path

    try:
        return send_file(path, as_attachment=True)
    except Exception as e:
        return str(e)


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


@app.route('/api/ontology/process/<string:process_identifier>', methods=['GET'])
def load_ontology_process_metadata(process_identifier):
    """Given a process identifier, return the associated metadata"""
    ontology = SoSOntology.instance()

    return make_response(
        jsonify(ontology.get_process_metadata(process_identifier)), 200,
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
            f'Parameter "processes_name" has the wrong type, intended "list" received "{type(processes_name)}"',
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
        jsonify(ontology.get_repo_metadata(repository_identifier)), 200,
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
            f'Parameter "repositories_name" has the wrong type, intended "list" received "{type(repositories_name)}"',
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
    '/api/ontology/markdown_documentation/<string:element_identifier>', methods=['GET'],
)
def load_ontology_markdown_documentation(element_identifier):
    ontology = SoSOntology.instance()

    return make_response(
        jsonify(ontology.get_markdown_documentation(element_identifier)), 200,
    )


@app.route('/api/ping', methods=['GET'])
def ping():
    return make_response(jsonify('pong'), 200)


@app.before_request
def before_request():
    session[START_TIME] = time.time()


@app.after_request
def after_request(response):

    duration = 0
    if START_TIME in session:
        duration = time.time() - session[START_TIME]

    app.logger.info(
        f'{request.remote_addr}, {request.method}, {request.scheme}, {request.full_path}, {response.status}, {duration} sec.',
    )
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555)
