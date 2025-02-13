'''
Copyright 2022 Airbus SAS
Modifications on 2024/06/24 Copyright 2024 Capgemini

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
from datetime import datetime
from os import environ
from os.path import dirname, exists, isfile, join

from rdflib import Literal, Namespace, URIRef
from rdflib.namespace import DC, OWL, RDF, RDFS, SKOS, XSD, split_uri

import sos_ontology
from sos_ontology.core.ontology import Ontology
from sos_ontology.rest_api.models.model_status import ModelStatus

'''
Creating an SoS_Ontology class that uses the Ontology class and implement it for the SoS Ontology
It adds specific methods to interact with the SosTrades Ontology
'''

'''
End of documentation
'''


class SoSOntology(Ontology):
    """
    Class to use an SoS ontology
    """

    __instance = None
    BASE_URI = 'https://www.sostrades.org/ontology#'

    @staticmethod
    def instance(version=1.1):

        if SoSOntology.__instance is None:
            SoSOntology.__instance = SoSOntology(version)

        return SoSOntology.__instance

    def __init__(self, version=1.1, source='file'):
        """
        Constructor
        """

        # Retrieve logging system
        self.logger = logging.getLogger('SoS.Ontology')

        self.QUDT = Namespace('http://qudt.org/schema/qudt/')

        self.ontologyVersion = version

        Ontology.__init__(self)

        self.ontology_owl_file_path, self.ontology_excel_file_path, self.ontology_log_file_path = SoSOntology.get_files_paths()

        # Load the SoS ontology
        if source == 'file':
            if self.ontologyVersion == 1.1:
                self.SOS = Namespace(SoSOntology.BASE_URI)

                load_path = self.ontology_owl_file_path
                self.logger.info(f"Loading ontology from path {load_path}")

                if isfile(load_path):
                    self.load(path=load_path, onto_format='xml')
                    print(f'SoSOntology loaded from path {load_path}')
                else:
                    raise Exception('Impossible to load Ontology, path does not exists')

                # get a list of all dataproperties that will become attributes
                self.datapropertyDict = self.getOntologyPredicatesDict(
                    OWL.DatatypeProperty
                )

                # get a list of all objectproperties that will become links
                self.objectpropertyDict = self.getOntologyPredicatesDict(
                    OWL.ObjectProperty
                )

                # get a list of all AnnotationProperty that will become links
                self.annotationPropertyDict = self.getOntologyPredicatesDict(
                    OWL.AnnotationProperty
                )

        self.incoherences = {}

    @staticmethod
    def get_files_paths():
        """
        Gets the ontology files paths 
        
        Returns tuple:
            ontology_owl_file_path, ontology_excel_file_path, ontology_log_file_path
        """
        environ_dict = dict(environ)
        ONTOLOGY_FOLDER = environ_dict.get('ONTOLOGY_FOLDER', None)
        if ONTOLOGY_FOLDER is not None and ONTOLOGY_FOLDER != '':
            return join(
                ONTOLOGY_FOLDER, 'SoSTrades_Ontology_ABox_Decentralized.owl'
            ), join(
                ONTOLOGY_FOLDER, 'SoS_Trades_Terminology_ABox.xlsx'
            ), join(
                ONTOLOGY_FOLDER, 'ontologyCreationLogs.json'
            )
        else:
            return join(
                dirname(sos_ontology.__file__),
                'data',
                'sos_ontology',
                'SoSTrades_Ontology_ABox_Decentralized.owl',
            ), join(
                dirname(sos_ontology.__file__),
                'data',
                'terminology',
                'SoS_Trades_Terminology_ABox.xlsx',
            ), join(
                dirname(sos_ontology.__file__),
                'data',
                'logs',
                'ontologyCreationLogs.json',
            )

    def get_parameter_metadata(self, parameterString):
        # methods which returns all metadata for a given parameter name through
        # matching via rdflib (no SPARQL)
        metadata = dict({'id': parameterString, 'label': parameterString})

        parameterURI = self.value(
            None, self.SOS.id, Literal(parameterString, datatype=XSD.string), 'uri'
        )

        if parameterURI is not None:
            # get label
            metadata['label'] = self.label(parameterURI)

            # get attributes
            parameterAttributes = self.getSubjectAttributes(
                parameterURI, {**self.datapropertyDict, **self.annotationPropertyDict}
            )

            attributesList = [
                'uri',
                'datatype',
                'unit',
                'definition',
                'definitionSource',
                'ACLTag',
            ]

            for attr in attributesList:
                if parameterAttributes.get(attr, None) is not None:
                    metadata[attr] = parameterAttributes.get(attr, None)

            # get attributes for parameter usage (retrieve the first one)
            parameterUsagesURIList = list(
                self.graph.subjects(predicate=self.SOS.instanceOf, object=parameterURI)
            )

            attributesUsageList = ['id']

            if len(parameterUsagesURIList) > 0:
                parameterUsagesIDs = []
                for parameterUsageURI in parameterUsagesURIList:

                    # get attributes
                    parameterUsageAttributes = self.getSubjectAttributes(
                        parameterUsageURI,
                        {**self.datapropertyDict, **self.annotationPropertyDict},
                    )

                    if parameterUsageAttributes.get('id', None) is not None:
                        parameterUsagesIDs.append(
                            parameterUsageAttributes.get('id', None)
                        )

                    # for attr in attributesUsageList:
                    #     if parameterUsageAttributes.get(attr, None) is not None:
                    #         metadata[attr] = parameterUsageAttributes.get(
                    #             attr, None)
                metadata['parameterUsagesIDs'] = parameterUsagesIDs

        else:
            # It means the value has not been found
            self.logger.debug(
                f'The parameter: {parameterString} HAS NOT BEEN FOUND in the Ontology'
            )
        return metadata

    def get_discipline_metadata(self, disciplineString):
        metadata = {}
        metadata = dict({'id': disciplineString, 'label': disciplineString})

        modelURI = self.value(
            None, self.SOS.id, Literal(disciplineString, datatype=XSD.string), 'uri'
        )

        if modelURI is not None:
            entityTypes = list(self.graph.objects(modelURI, RDF.type))
            if self.SOS.SoSDiscipline in entityTypes:
                # get label
                metadata['label'] = self.label(modelURI)
                if split_uri(modelURI)[-1] == metadata['label']:
                    metadata['label'] = disciplineString
                # get attributes
                modelAttribute = self.getSubjectAttributes(
                    modelURI, {**self.datapropertyDict, **self.annotationPropertyDict}
                )

                attributesList = [
                    'uri',
                    'description',
                    'pythonClass',
                    'outputParameterUsagesQuantity',
                    'inputParameterUsagesQuantity',
                    'modelType',
                    'type',
                    'validated',
                    'validated_by',
                    'last_modification_date',
                    'publicationDate',
                    'codeRepository',
                    'pythonModulePath',
                    'category',
                    'definition',
                    'version',
                    'source',
                    'icon',
                ]

                for attr in attributesList:
                    if modelAttribute.get(attr, None) is not None:
                        metadata[attr] = modelAttribute.get(attr, None)

            else:
                # It means the value has been found but is not a discipline
                self.logger.debug(
                    f'The entity: {disciplineString} HAS BEEN FOUND in the Ontology but is not of type Discipline. It is a {", ".join(entityTypes)}'
                )
        else:
            # It means the value has not been found
            self.logger.debug(
                f'The model: {disciplineString} HAS NOT BEEN FOUND in the Ontology'
            )

        return metadata

    def get_process_metadata(self, process_identifier):
        metadata = dict({'id': process_identifier, 'label': process_identifier})

        processURI = self.value(
            None, self.SOS.id, Literal(process_identifier, datatype=XSD.string), 'uri'
        )

        if processURI is not None:
            if (processURI, RDF.type, self.SOS.SoSProcess) in self.graph:
                # get label
                metadata['label'] = self.label(processURI)
                if split_uri(processURI)[-1] == metadata['label']:
                    metadata['label'] = process_identifier

                # get attributes
                modelAttribute = self.getSubjectAttributes(
                    processURI, {**self.datapropertyDict, **self.annotationPropertyDict}
                )

                attributesList = [
                    'uri',
                    'description',
                    'disciplineList',
                    'pythonModulePath',
                    'repository',
                    'id',
                ]

                for attr in attributesList:
                    if modelAttribute.get(attr, None) is not None:
                        metadata[attr] = modelAttribute.get(attr, None)
            else:
                # It means the value has not been found
                self.logger.debug(
                    f'A concept has been found with id: {process_identifier} but is not a process'
                )

        else:
            # It means the value has not been found
            self.logger.debug(
                f'The process: {process_identifier} HAS NOT BEEN FOUND in the Ontology'
            )

        return metadata

    def get_repo_metadata(self, repository_identifier):
        metadata = dict({'id': repository_identifier, 'label': repository_identifier})

        repoURI = self.value(
            None,
            self.SOS.id,
            Literal(repository_identifier, datatype=XSD.string),
            'uri',
        )

        if repoURI is not None:
            if (repoURI, RDF.type, self.SOS.SoSProcessRepository) in self.graph:
                # get label
                metadata['label'] = self.label(repoURI)
                if split_uri(repoURI)[-1] == metadata['label']:
                    metadata['label'] = repository_identifier

                # get attributes
                modelAttribute = self.getSubjectAttributes(
                    repoURI, {**self.datapropertyDict, **self.annotationPropertyDict}
                )

                attributesList = ['uri', 'description', 'processList']

                for attr in attributesList:
                    if modelAttribute.get(attr, None) is not None:
                        metadata[attr] = modelAttribute.get(attr, None)
            else:
                # It means the value has not been found
                self.logger.debug(
                    f'A concept has been found with id: {repository_identifier} but is not a process repository'
                )

        else:
            # It means the value has not been found
            self.logger.debug(
                f'The process repository: {repository_identifier} HAS NOT BEEN FOUND in the Ontology'
            )

        return metadata

    def get_metadata(self, request):
        # methods that retrieves metadata for a given input list of parameters
        # and/or disciplines and/or processes and/or repository
        result = {}

        if 'disciplines' in request:
            result['disciplines'] = {}
            for requestDiscipline in request['disciplines']:
                result['disciplines'][requestDiscipline] = self.get_discipline_metadata(
                    requestDiscipline
                )
        if 'parameters' in request:
            result['parameters'] = {}
            for requestParameter in request['parameters']:
                result['parameters'][requestParameter] = self.get_parameter_metadata(
                    requestParameter
                )
        if 'process' in request:
            result['process'] = {}
            for requestProcess in request['process']:
                result['process'][requestProcess] = self.get_process_metadata(
                    requestProcess
                )
        if 'repository' in request:
            result['repository'] = {}
            for requestRepository in request['repository']:
                result['repository'][requestRepository] = self.get_repo_metadata(
                    requestRepository
                )

        return result

    def get_study_ontology_data(self, study_ontology_request: dict):
        """methods that retrieves ontology data for a given input list of disciplines and parameter usages

        Args:
            study_ontology_request (dict): _description_

        Returns:
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
        result = {}

        if 'disciplines' in study_ontology_request:
            result['disciplines'] = {}
            for requestDiscipline in study_ontology_request['disciplines']:
                result['disciplines'][requestDiscipline] = self.get_discipline_metadata(
                    requestDiscipline
                )
        if 'parameter_usages' in study_ontology_request:
            result['parameter_usages'] = {}
            for requestParameterUsage in study_ontology_request['parameter_usages']:
                result['parameter_usages'][
                    requestParameterUsage
                ] = self.get_parameter_usage_metadata(requestParameterUsage)

        return result

    def get_parameter_usage_metadata(self, parameterUsageString: str):
        """Retrieve parameter usage ontology data from an identifier

        Args:
            parameterUsageString (str): parameter usage identifier constructed as
            <discipline_id>_<input OR output>_<parameter_id>

        Returns:
            dict: <parameter_identifier> : {
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
        """
        metadata = dict({'id': parameterUsageString})

        parameterUsageURI = self.value(
            None, self.SOS.id, Literal(parameterUsageString, datatype=XSD.string), 'uri'
        )

        if parameterUsageURI is not None:
            entityTypes = list(self.graph.objects(parameterUsageURI, RDF.type))
            if self.SOS.Parameter_Usage in entityTypes:
                # get parameter usage attributes
                parameter_usage_info = {
                    'unit': self.SOS.unit,
                    'datatype': self.SOS.datatype,
                    'numerical': self.SOS.numerical,
                    'optional': self.SOS.optional,
                    'range': self.SOS.range,
                    'structuring': self.SOS.structuring,
                    'editable': self.SOS.editable,
                    'possible_values': self.SOS.possibleValues,
                    'dataframe_descriptor': self.SOS.dataframeDescriptor,
                    'dataframe_edition_locked': self.SOS.dataframeEditionLocked,
                    'namespace': self.SOS.namespace,
                    'user_level': self.SOS.userLevel,
                    'visibility': self.SOS.visibility,
                }

                parameter_usage_info = self.get_object_values_dict(
                    subjectURI=parameterUsageURI, values_dict=parameter_usage_info
                )

                # retrieve associated parameter
                parameterURI = list(
                    self.graph.objects(
                        subject=parameterUsageURI, predicate=self.SOS.instanceOf
                    )
                )[0]

                if parameterURI is not None:
                    parameter_info = {
                        'id': self.SOS.id,
                        'uri': None,
                        'label': None,
                        'definition': self.SOS.definition,
                        'definition_source': self.SOS.definitionSource,
                        'ACLTag': self.SOS.ACLTag,
                    }
                    # get parameter attributes
                    parameter_info = self.get_object_values_dict(
                        subjectURI=parameterURI, values_dict=parameter_info
                    )
                    parameter_info['uri'] = parameterURI
                    parameter_info['label'] = self.label(parameterURI)

                    metadata.update(parameter_info)

                metadata.update(parameter_usage_info)
            else:
                # It means the value has been found but is not a parameter usage
                self.logger.debug(
                    f'The entity: {parameterUsageString} HAS BEEN FOUND in the Ontology but is not of type Parameter_Usage. It is a {", ".join(entityTypes)}'
                )
        else:
            # It means the value has not been found
            self.logger.debug(
                f'The parameter usage: {parameterUsageString} HAS NOT BEEN FOUND in the Ontology'
            )
        return metadata

    def get_treeview_nodes_and_links(
        self,
        treeviewDict,
        treeNodes,
        parentNamespace,
        parameterNodes,
        hierarchyLinks,
        level,
        scatterParameter=None,
    ):
        multiscenario_types = ['SoSVerySimpleMultiScenario', 'SoSMultiScenario']
        # we ignore the data nodes, they will not be represented in the n2 diagram
        if treeviewDict['node_type'] != 'data':
            # Retrieve info concerning number of parameters and add couplings
            # parameters nodes
            if (
                treeviewDict['node_type'] == 'SoSDisciplineScatter'
                or treeviewDict['node_type'] == 'SoSMultiScatterBuilder'
                or treeviewDict['node_type'] == 'SoSDisciplineGather'
            ):
                scatterParameter = True

            totalParameters = len(treeviewDict['disc_data'])
            totalPrivateParameters = self.get_treeview_coupling_parameters(
                treeviewDict['disc_data'],
                parameterNodes,
                treeviewDict['full_namespace'],
                scatterParameter,
            )
            modelAdditionalData = self.get_discipline_metadata(
                treeviewDict['model_name_full_path']
            )
            modelMetadata = dict(
                {
                    'id': treeviewDict['full_namespace'],
                    'Parent Node': parentNamespace,
                    'Name': treeviewDict['name'],
                    'Type': 'DisciplineNode',
                    'Sub Type': treeviewDict['node_type'],
                    'Level': level,
                    'Total Parameters': totalParameters,
                    'Total Private Parameters': totalPrivateParameters,
                    'expandable': 0,
                }
            )

            # add children list to the attributes
            modelMetadata['childrenIDs'] = self.getChildrenList(
                treeviewDict, treeviewDict['full_namespace']
            )

            for attr, value in modelAdditionalData.items():
                if attr == 'label':
                    modelMetadata['label'] = value
                elif attr == 'definition':
                    modelMetadata['Definition'] = value

            if 'children' in treeviewDict:
                if len(treeviewDict['children']) > 0:
                    modelMetadata['expandable'] = 1

            treeNodes.append(modelMetadata)
            parentNamespace = treeviewDict['full_namespace']
            level += 1
        if 'children' in treeviewDict:
            multiscenario = False
            if treeviewDict['node_type'] in multiscenario_types:
                # it is a multiscenario node
                # only one of the children will be generated because there will all be the same and will complexify the N2 without any aded interest
                multiscenario = True
            for node in treeviewDict['children']:
                if node['node_type'] != 'data':
                    # Create hierarchy link between children and parent
                    link = dict(
                        {
                            'source': node['full_namespace'],
                            'target': parentNamespace,
                            'Type': 'PART_OF',
                            'Size': 2,
                        }
                    )
                    link['id'] = (
                        link['source']
                        + '_TO_'
                        + link['target']
                        + '_TYPE_'
                        + link['Type']
                    )
                    hierarchyLinks.append(link)

                self.get_treeview_nodes_and_links(
                    node,
                    treeNodes,
                    parentNamespace,
                    parameterNodes,
                    hierarchyLinks,
                    level,
                    scatterParameter,
                )
                if multiscenario and node['node_type'] != 'data':
                    # it means we have already generated everytong needed for 1 scenario, we will stop
                    break

    def getChildrenList(self, treeviewNode, namespace):
        #   Returns a list of all nodes under the root.
        nodesIDList = []

        def recurse(treeviewNode):
            if treeviewNode.get('children', None) is not None:
                for child in treeviewNode['children']:
                    if child['node_type'] != 'data':
                        nodesIDList.append(child['full_namespace'])
                    recurse(child)

        recurse(treeviewNode)
        return nodesIDList

    def get_treeview_coupling_parameters(
        self, parameterItems, parameterNodes, namespace, scatterParameter=None
    ):
        # Create a dict to verify if parameter already exist
        if len(parameterNodes) > 0:
            parameterDict = {p['id']: 1 for p in parameterNodes}
        else:
            parameterDict = {}
        totalPrivateParameters = 0

        # Go trough all parameters
        for parameter, parameterData in parameterItems.items():
            if parameter not in parameterDict and parameterData['coupling']:
                paramName = parameter.split('.')[-1]
                instanceLabel = None
                if scatterParameter is not None:
                    try:
                        instanceLabel = parameter.split('.')[-2]

                    except:
                        instanceLabel = None

                # retrieve parameter metadata in ontology
                additionalData = self.get_parameter_metadata(paramName)
                parameterMetadata = dict(
                    {'id': parameter, 'Type': 'CouplingParameter', 'Level': 0}
                )
                for attr, value in additionalData.items():
                    if attr != 'id':
                        if attr == 'label' and instanceLabel is not None:
                            parameterMetadata[attr] = value + ' ' + instanceLabel
                        else:
                            parameterMetadata[attr] = value
                parameterNodes.append(parameterMetadata)
            if not parameterData['coupling']:
                totalPrivateParameters += 1
        return totalPrivateParameters

    def get_n2_matrix(self, treeview):
        treeNodes = []
        parameterNodes = []
        hierarchyLinks = []

        # Create tree nodes and links from treeview
        self.get_treeview_nodes_and_links(
            treeview, treeNodes, '', parameterNodes, hierarchyLinks, 0
        )

        return treeNodes, parameterNodes, hierarchyLinks

    def get_models_list(self, onlyTable=False, linked_process_dict=None):

        tableHeaders = {
            'Name': 1,
            'Type': 2,
            'Source': 3,
            'Last modification date': 4,
            'Validated by': 5,
            'Validated': 6,
            'Discipline': 7,
            'Processes Using Model': 8,
            'Processes Using Model List': 9,
            'id': 10,
        }

        modelList = []
        # retrive all models
        for modelURI in self.graph.subjects(
            predicate=RDF.type, object=self.SOS.SoSDiscipline
        ):
            modelRow = dict.fromkeys(list(tableHeaders.keys()), '')
            modelRow['Name'] = self.label(modelURI)

            # get attributes
            modelAttributes = self.getSubjectAttributes(
                modelURI, {**self.datapropertyDict, **self.annotationPropertyDict}
            )

            # get discipline label
            disciplineLabel = ''
            for discURI in self.graph.objects(
                subject=modelURI, predicate=self.SOS.belongsTo
            ):
                if (discURI, RDF.type, self.SOS.Discipline) in self.graph:
                    disciplineLabel = self.label(discURI)
                    break

            # get processes number and details
            processesDict = {}
            processesNumber = 0
            for processURI in self.graph.objects(
                subject=modelURI, predicate=self.SOS.usedIn
            ):
                if (processURI, RDF.type, self.SOS.SoSProcess) in self.graph:
                    processAttributes = self.getSubjectAttributes(
                        processURI,
                        {**self.datapropertyDict, **self.annotationPropertyDict},
                    )
                    if 'repository' in processAttributes:
                        if processAttributes['repository'] in processesDict:
                            processesDict[processAttributes['repository']].append(
                                processAttributes.get('name', 'id')
                            )
                        else:
                            processesDict[processAttributes['repository']] = [
                                processAttributes.get('name', 'id')
                            ]
                        processesNumber += 1

            modelRow['Type'] = modelAttributes.get('type', '')
            modelRow['Source'] = modelAttributes.get('source', '')
            modelRow['Last modification date'] = modelAttributes.get(
                'last_modification_date', ''
            )
            modelRow['Validated by'] = modelAttributes.get('validated_by', '')
            modelRow['Validated'] = modelAttributes.get('validated', '')
            modelRow['Discipline'] = disciplineLabel
            modelRow['Processes Using Model'] = processesNumber
            modelRow['Processes Using Model List'] = processesDict
            modelRow['id'] = modelAttributes.get('id', '')
            if not onlyTable:
                modelRow['input parameters quantity'] = modelAttributes.get(
                    'outputParametersQuantity'
                )
                modelRow['output parameters quantity'] = modelAttributes.get(
                    'inputParametersQuantity'
                )
                modelRow['description'] = modelAttributes.get('description')

            modelList.append(modelRow)

        return modelList

    def get_models_list_filtered(self, linked_process_dict=None):

        model_list = []

        for modelURI in self.graph.subjects(
            predicate=RDF.type, object=self.SOS.SoSDiscipline
        ):
            # Model not authorised by default
            model_authorised = False

            # get attributes
            modelAttributes = self.getSubjectAttributes(
                modelURI, {**self.datapropertyDict, **self.annotationPropertyDict}
            )

            # get code repository label
            codeRepositoryLabel = ''
            for codeRepoURI in self.graph.objects(
                subject=modelURI, predicate=self.SOS.belongsTo
            ):
                if (codeRepoURI, RDF.type, self.SOS.CodeRepository) in self.graph:
                    codeRepositoryLabel = self.label(codeRepoURI)
                    break

            # get processes number and details
            processesDict = {}
            processesNumber = 0
            for processURI in self.graph.objects(
                subject=modelURI, predicate=self.SOS.usedIn
            ):
                if (processURI, RDF.type, self.SOS.SoSProcess) in self.graph:
                    processAttributes = self.getSubjectAttributes(
                        processURI,
                        {**self.datapropertyDict, **self.annotationPropertyDict},
                    )
                    if 'repository' in processAttributes:
                        # Check if repository and process authorised for user
                        if processAttributes['repository'] in linked_process_dict:
                            for process_name in linked_process_dict[
                                processAttributes['repository']
                            ]:
                                if (
                                    processAttributes.get('id', '')
                                    == f'{processAttributes["repository"]}.{process_name}'
                                ):
                                    model_authorised = True
                                    process_metadata = self.get_process_metadata(
                                        processAttributes.get('id', '')
                                    )
                                    repo_metadata = self.get_repo_metadata(
                                        processAttributes.get('repository', '')
                                    )
                                    process_name = process_metadata.get('label', 'id')
                                    repo_name = repo_metadata.get('label', 'id')

                                    if repo_name in processesDict:
                                        processesDict[repo_name].append(process_name)
                                    else:
                                        processesDict[repo_name] = [process_name]
                                    processesNumber += 1

            if model_authorised:
                # Add model to list
                new_model = ModelStatus()
                new_model.name = self.label(modelURI)
                new_model.id = modelAttributes.get('id', '')
                new_model.definition = modelAttributes.get('definition', '')
                new_model.type = modelAttributes.get('type', '')
                new_model.source = modelAttributes.get('source', '')
                new_model.last_modification_date = modelAttributes.get(
                    'last_modification_date', ''
                )
                new_model.validated_by = modelAttributes.get('validated_by', '')
                new_model.validated = modelAttributes.get('validated', 'NO')
                new_model.code_repository = codeRepositoryLabel
                new_model.processes_using_model = processesNumber
                new_model.processes_using_model_list = processesDict
                new_model.inputs_parameters_quantity = modelAttributes.get(
                    'inputParameterUsagesQuantity', ''
                )
                new_model.outputs_parameters_quantity = modelAttributes.get(
                    'outputParameterUsagesQuantity', ''
                )
                new_model.icon = modelAttributes.get('icon', '')
                new_model.version = modelAttributes.get('version', '')
                new_model.category = modelAttributes.get('category', '')

                model_list.append(new_model)

        model_list_json = [md.serialize() for md in model_list]

        return model_list_json

    def get_models_status(self, linkedProcessList=None):
        # Get models status as a dataframe to display as a table in the GUI

        tableHeaders = {
            'Name': 1,
            'Type': 2,
            'Source': 3,
            'Last modification date': 4,
            'Validated by': 5,
            'Validated': 6,
            'Discipline': 7,
            'Processes Using Model': 8,
            'Processes Using Model List': 9,
            'id': 10,
        }

        cleanedModels = []
        cleanedModels = self.get_models_list(onlyTable=True)

        #  Sort the results to display Official models first
        modelsStatusSorted = sorted(cleanedModels, key=lambda x: (x['Type']))

        #  Convert the result to ease the display as a table in the GUI
        modelsStatusTable = []
        for modelDict in modelsStatusSorted:
            modelStatusRow = []
            processList = modelDict.get('Processes Using Model List', None)
            if processList == {}:
                processList = None
            for key, value in modelDict.items():
                if key == 'Processes Using Model':
                    modelStatusRow.append(
                        {'header': key, 'value': value, 'details': processList}
                    )
                elif key == 'Name':
                    modelStatusRow.append(
                        {
                            'header': key,
                            'value': value,
                            'details': modelDict.get('id', None),
                        }
                    )
                elif key != 'Processes Using Model List' and key != 'id':
                    modelStatusRow.append(
                        {'header': key, 'value': value, 'details': None}
                    )

            modelsStatusTable.append(modelStatusRow)

        return modelsStatusTable

    def addOntologyCreationDate(self):
        # get ontology URI
        ontoURI = self.value(None, RDF.type, OWL.Ontology, 'uri')

        # update time
        update_date = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

        creationDateTriple = [
            (
                ontoURI,
                DC.modified,
                Literal(update_date, datatype=XSD.string),
                self.graph,
            ),
        ]

        self.add_triples_list(creationDateTriple)

    def createCodeRepositoriesTriples(self, code_repositories):
        for code_repository in code_repositories.sos_entity_dict.values():

            # Create the discipline URI
            codeRepoURI = self.create_new_URI(
                f'{SoSOntology.BASE_URI}code_repository_',
                code_repository.id,
            )

            codeRepositoriesTriples = [
                # add a new OWL individual for the Scheme
                (codeRepoURI, RDF.type, OWL.NamedIndividual, self.graph),
                # add discipline type
                (codeRepoURI, RDF.type, self.SOS.CodeRepository, self.graph),
                # add discipline name
                (
                    codeRepoURI,
                    self.SOS.name,
                    Literal(code_repository.id, datatype=XSD.string),
                    self.graph,
                ),
                (
                    codeRepoURI,
                    SKOS.prefLabel,
                    Literal(code_repository.id, datatype=XSD.string),
                    self.graph,
                ),
                (
                    codeRepoURI,
                    RDFS.label,
                    Literal(code_repository.id, datatype=XSD.string),
                    self.graph,
                ),
                (
                    codeRepoURI,
                    self.SOS.id,
                    Literal(code_repository.id, datatype=XSD.string),
                    self.graph,
                ),
                # add code repo url
                (
                    codeRepoURI,
                    self.SOS.url,
                    self.toLiteral(code_repository.url),
                    self.graph,
                ),
                # add code repo commit
                (
                    codeRepoURI,
                    self.SOS.commit,
                    self.toLiteral(code_repository.commit),
                    self.graph,
                ),
                # add code repo committed_date
                (
                    codeRepoURI,
                    self.SOS.committedDate,
                    self.toLiteral(code_repository.committed_date),
                    self.graph,
                ),
                # add code repo branch
                (
                    codeRepoURI,
                    self.SOS.branch,
                    self.toLiteral(code_repository.branch),
                    self.graph,
                ),
                # add code repo process_repositories list
                (
                    codeRepoURI,
                    self.SOS.processRepositoriesList,
                    self.toLiteral(code_repository.process_repositories_ids),
                    self.graph,
                ),
            ]

            self.add_triples_list(codeRepositoriesTriples)

    def createSoSProcessRepositoriesTriples(self, sos_process_repositories):
        for sos_process_repository in sos_process_repositories.sos_entity_dict.values():

            # Create the discipline URI
            processRepoURI = self.create_new_URI(
                f'{SoSOntology.BASE_URI}sos_process_repository_',
                sos_process_repository.id,
            )

            codeRepositoriesTriples = [
                # add a new OWL individual for the Scheme
                (processRepoURI, RDF.type, OWL.NamedIndividual, self.graph),
                # add discipline type
                (processRepoURI, RDF.type, self.SOS.SoSProcessRepository, self.graph),
                # add discipline name
                (
                    processRepoURI,
                    self.SOS.name,
                    self.toLiteral(sos_process_repository.label),
                    self.graph,
                ),
                (
                    processRepoURI,
                    SKOS.prefLabel,
                    self.toLiteral(sos_process_repository.label),
                    self.graph,
                ),
                (
                    processRepoURI,
                    RDFS.label,
                    self.toLiteral(sos_process_repository.label),
                    self.graph,
                ),
                (
                    processRepoURI,
                    self.SOS.id,
                    self.toLiteral(sos_process_repository.id),
                    self.graph,
                ),
                # add process description
                (
                    processRepoURI,
                    self.SOS.description,
                    self.toLiteral(sos_process_repository.description),
                    self.graph,
                ),
                # add process list
                (
                    processRepoURI,
                    self.SOS.processList,
                    self.toLiteral(sos_process_repository.processes_list_ids),
                    self.graph,
                ),
            ]

            # we add link to code_repository
            # we search for the code_repository URI
            codeRepoURI = self.value(
                None,
                self.SOS.id,
                self.toLiteral(sos_process_repository.code_repository.id),
                'uri',
            )

            if codeRepoURI is not None:
                codeRepositoriesTriples.append(
                    (processRepoURI, self.SOS.belongsTo, codeRepoURI, self.graph)
                )

            self.add_triples_list(codeRepositoriesTriples)

    def createSoSDisciplinesTriples(self, sos_disciplines):
        for sos_discipline in sos_disciplines.sos_entity_dict.values():

            # Create the sosDiscipline URI
            sosDisciplineURI = self.create_new_URI(
                f'{SoSOntology.BASE_URI}sosDiscipline_',
                sos_discipline.id,
            )

            sosDisciplineTriples = [
                # add a new OWL individual for the Scheme
                (sosDisciplineURI, RDF.type, OWL.NamedIndividual, self.graph),
                # add sosDiscipline type
                (sosDisciplineURI, RDF.type, self.SOS.SoSDiscipline, self.graph),
                # add sosDiscipline code name
                (
                    sosDisciplineURI,
                    self.SOS.name,
                    self.toLiteral(sos_discipline.label),
                    self.graph,
                ),
                (
                    sosDisciplineURI,
                    SKOS.prefLabel,
                    self.toLiteral(sos_discipline.label),
                    self.graph,
                ),
                (
                    sosDisciplineURI,
                    RDFS.label,
                    self.toLiteral(sos_discipline.label),
                    self.graph,
                ),
                (
                    sosDisciplineURI,
                    self.SOS.id,
                    self.toLiteral(sos_discipline.id),
                    self.graph,
                ),
                # initialise sosDiscipline definition
                (
                    sosDisciplineURI,
                    self.SOS.definition,
                    self.toLiteral(sos_discipline.definition),
                    self.graph,
                ),
                # add sosDiscipline class name
                (
                    sosDisciplineURI,
                    self.SOS.pythonClass,
                    self.toLiteral(sos_discipline.pythonClass),
                    self.graph,
                ),
                # add sosDiscipline class inheritance
                (
                    sosDisciplineURI,
                    self.SOS.classInheritance,
                    self.toLiteral(sos_discipline.pythonClassInheritance),
                    self.graph,
                ),
                # add sosDiscipline fullpath
                (
                    sosDisciplineURI,
                    self.SOS.pythonModulePath,
                    self.toLiteral(sos_discipline.pythonModulePath),
                    self.graph,
                ),
                # add sosDiscipline input parameters quantity
                (
                    sosDisciplineURI,
                    self.SOS.inputParameterUsagesQuantity,
                    self.toLiteral(len(sos_discipline.inputParameterUsagesIds)),
                    self.graph,
                ),
                # add sosDiscipline output parameters quantity
                (
                    sosDisciplineURI,
                    self.SOS.outputParameterUsagesQuantity,
                    self.toLiteral(len(sos_discipline.outputParameterUsagesIds)),
                    self.graph,
                ),
                # add sosDiscipline input parameters
                (
                    sosDisciplineURI,
                    self.SOS.inputParameterUsages,
                    self.toLiteral(sos_discipline.inputParameterUsagesIds),
                    self.graph,
                ),
                # add sosDiscipline output parameters
                (
                    sosDisciplineURI,
                    self.SOS.outputParameterUsages,
                    self.toLiteral(sos_discipline.outputParameterUsagesIds),
                    self.graph,
                ),
                # add sosDiscipline markdown documentation
                (
                    sosDisciplineURI,
                    self.SOS.documentation,
                    self.toLiteral(sos_discipline.documentation),
                    self.graph,
                ),
                # add sosDiscipline icon
                (
                    sosDisciplineURI,
                    self.SOS.icon,
                    self.toLiteral(sos_discipline.icon),
                    self.graph,
                ),
                # add sosDiscipline category
                (
                    sosDisciplineURI,
                    self.SOS.category,
                    self.toLiteral(sos_discipline.category),
                    self.graph,
                ),
                # add sosDiscipline validated
                (
                    sosDisciplineURI,
                    self.SOS.validated,
                    self.toLiteral(sos_discipline.validated),
                    self.graph,
                ),
                # add sosDiscipline validated_by
                (
                    sosDisciplineURI,
                    self.SOS.validated_by,
                    self.toLiteral(sos_discipline.validated_by),
                    self.graph,
                ),
                # add sosDiscipline maturity
                (
                    sosDisciplineURI,
                    self.SOS.type,
                    self.toLiteral(sos_discipline.type),
                    self.graph,
                ),
                # add sosDiscipline publication Date
                (
                    sosDisciplineURI,
                    self.SOS.last_modification_date,
                    self.toLiteral(sos_discipline.last_modification_date),
                    self.graph,
                ),
                # add sosDiscipline source
                (
                    sosDisciplineURI,
                    self.SOS.source,
                    self.toLiteral(sos_discipline.source),
                    self.graph,
                ),
                # add sosDiscipline code repository
                (
                    sosDisciplineURI,
                    self.SOS.codeRepository,
                    self.toLiteral(sos_discipline.repository.id),
                    self.graph,
                ),
                # add sosDiscipline version
                (
                    sosDisciplineURI,
                    self.SOS.version,
                    self.toLiteral(sos_discipline.version),
                    self.graph,
                ),
            ]

            # we search for the code repository URI
            codeRepositoryURI = self.value(
                None, self.SOS.id, self.toLiteral(sos_discipline.repository.id), 'uri'
            )

            if codeRepositoryURI is not None:

                sosDisciplineTriples.append(
                    (
                        sosDisciplineURI,
                        self.SOS.belongsTo,
                        codeRepositoryURI,
                        self.graph,
                    )
                )

            # we search for the code repository URI
            codeRepositoryURI = self.value(
                None, self.SOS.id, self.toLiteral(sos_discipline.repository.id), 'uri'
            )

            if codeRepositoryURI is not None:

                sosDisciplineTriples.append(
                    (
                        sosDisciplineURI,
                        self.SOS.belongsTo,
                        codeRepositoryURI,
                        self.graph,
                    )
                )

            if len(sos_discipline.inputParameterUsagesIds) > 0:
                for parameter_usage in sos_discipline.inputParameterUsagesList:
                    # we search for the URI
                    parameterUsageIRI = self.value(
                        None, self.SOS.id, self.toLiteral(parameter_usage.id), 'uri'
                    )

                    if parameterUsageIRI is not None:
                        sosDisciplineTriples.append(
                            (
                                sosDisciplineURI,
                                self.SOS.hasInput,
                                parameterUsageIRI,
                                self.graph,
                            )
                        )

            if len(sos_discipline.outputParameterUsagesIds) > 0:
                for parameter_usage in sos_discipline.outputParameterUsagesList:
                    # we search for the URI
                    parameterUsageIRI = self.value(
                        None, self.SOS.id, self.toLiteral(parameter_usage.id), 'uri'
                    )

                    if parameterUsageIRI is not None:
                        sosDisciplineTriples.append(
                            (
                                sosDisciplineURI,
                                self.SOS.hasOutput,
                                parameterUsageIRI,
                                self.graph,
                            )
                        )

            self.add_triples_list(sosDisciplineTriples)

    def createUsecasesTriples(self, usecases):
        for usecase in usecases.sos_entity_dict.values():

            # Create the usecase URI
            usecaseURI = self.create_new_URI(
                f'{SoSOntology.BASE_URI}usecase_', usecase.id
            )

            usecaseTriples = [
                # add a new OWL individual for the Scheme
                (usecaseURI, RDF.type, OWL.NamedIndividual, self.graph),
                # add usecase type
                (usecaseURI, RDF.type, self.SOS.Usecase, self.graph),
                # add usecase code name
                (usecaseURI, self.SOS.name, self.toLiteral(usecase.label), self.graph),
                (usecaseURI, SKOS.prefLabel, self.toLiteral(usecase.label), self.graph),
                (usecaseURI, RDFS.label, self.toLiteral(usecase.label), self.graph),
                (usecaseURI, self.SOS.id, self.toLiteral(usecase.id), self.graph),
                # initialise usecase definition
                (
                    usecaseURI,
                    self.SOS.runUsecase,
                    self.toLiteral(usecase.run_usecase),
                    self.graph,
                ),
            ]

            # we search for the process URI
            processURI = self.value(
                None, self.SOS.id, self.toLiteral(usecase.process.id), 'uri'
            )

            if processURI is not None:
                usecaseTriples.append(
                    (usecaseURI, self.SOS.implements, processURI, self.graph)
                )

            self.add_triples_list(usecaseTriples)

    def createCouplingsTriples(self, couplings):
        for usecase in couplings.sos_entity_dict.values():

            # Create the usecase URI
            couplingURI = self.create_new_URI(
                f'{SoSOntology.BASE_URI}usecase_', usecase.id
            )

            usecaseTriples = [
                # add a new OWL individual for the Scheme
                (couplingURI, RDF.type, OWL.NamedIndividual, self.graph),
                # add usecase type
                (couplingURI, RDF.type, self.SOS.Coupling, self.graph),
                # add usecase code name
                (couplingURI, self.SOS.name, self.toLiteral(usecase.label), self.graph),
                (
                    couplingURI,
                    SKOS.prefLabel,
                    self.toLiteral(usecase.label),
                    self.graph,
                ),
                (couplingURI, RDFS.label, self.toLiteral(usecase.label), self.graph),
                (couplingURI, self.SOS.id, self.toLiteral(usecase.id), self.graph),
            ]

            # we search for the disciplineFrom URI
            disciplineFromURI = self.value(
                None, self.SOS.id, self.toLiteral(usecase.disciplineFrom.id), 'uri'
            )
            # we search for the disciplineTo URI
            disciplineToURI = self.value(
                None, self.SOS.id, self.toLiteral(usecase.disciplineTo.id), 'uri'
            )

            if disciplineFromURI is not None and disciplineToURI is not None:
                usecaseTriples.append(
                    (couplingURI, self.SOS.couplingOut, disciplineFromURI, self.graph)
                )
                usecaseTriples.append(
                    (couplingURI, self.SOS.couplingIn, disciplineToURI, self.graph)
                )

            # we search for the parameterUsageIn URI
            parameterUsageIn = None
            if usecase.parameterUsageIn is not None:
                parameterUsageIn = self.value(
                    None,
                    self.SOS.id,
                    self.toLiteral(usecase.parameterUsageIn.id),
                    'uri',
                )
                if parameterUsageIn is not None:
                    usecaseTriples.append(
                        (couplingURI, self.SOS.represents, parameterUsageIn, self.graph)
                    )
            # we search for the parameterUsageOut URI
            parameterUsageOut = None
            if usecase.parameterUsageOut is not None:
                parameterUsageOut = self.value(
                    None,
                    self.SOS.id,
                    self.toLiteral(usecase.parameterUsageOut.id),
                    'uri',
                )
                if parameterUsageOut is not None:
                    usecaseTriples.append(
                        (
                            couplingURI,
                            self.SOS.represents,
                            parameterUsageOut,
                            self.graph,
                        )
                    )

            self.add_triples_list(usecaseTriples)

    def createSoSProcessTriples(self, sos_processes):

        for sos_process in sos_processes.sos_entity_dict.values():
            # Create the process URI
            processURI = self.create_new_URI(
                f'{SoSOntology.BASE_URI}sos_process_', sos_process.id
            )

            processTriples = [
                # add a new OWL individual for the Scheme
                (processURI, RDF.type, OWL.NamedIndividual, self.graph),
                # add process type
                (processURI, RDF.type, self.SOS.SoSProcess, self.graph),
                # add process name
                (
                    processURI,
                    self.SOS.name,
                    self.toLiteral(sos_process.label),
                    self.graph,
                ),
                (
                    processURI,
                    SKOS.prefLabel,
                    self.toLiteral(sos_process.label),
                    self.graph,
                ),
                (processURI, RDFS.label, self.toLiteral(sos_process.label), self.graph),
                (processURI, self.SOS.id, self.toLiteral(sos_process.id), self.graph),
                # add process description
                (
                    processURI,
                    self.SOS.description,
                    self.toLiteral(sos_process.description),
                    self.graph,
                ),
                # add process path
                (
                    processURI,
                    self.SOS.pythonModulePath,
                    self.toLiteral(sos_process.process_module_path),
                    self.graph,
                ),
                # add sos_disciplines list
                (
                    processURI,
                    self.SOS.disciplineList,
                    self.toLiteral(sos_process.models_list_ids),
                    self.graph,
                ),
                # add usecases list
                (
                    processURI,
                    self.SOS.usecaseList,
                    self.toLiteral(sos_process.usecases_list_ids),
                    self.graph,
                ),
                # add process markdown documentation
                (
                    processURI,
                    self.SOS.documentation,
                    self.toLiteral(sos_process.documentation),
                    self.graph,
                ),
                # add process category
                (
                    processURI,
                    self.SOS.category,
                    self.toLiteral(sos_process.category),
                    self.graph,
                ),
                # add process version
                (
                    processURI,
                    self.SOS.version,
                    self.toLiteral(sos_process.version),
                    self.graph,
                ),
                # add process repository
                (
                    processURI,
                    self.SOS.repository,
                    self.toLiteral(sos_process.repository.id),
                    self.graph,
                ),
            ]

            # we search for the process URI
            processRepoURI = self.value(
                None, self.SOS.id, self.toLiteral(sos_process.repository.id), 'uri'
            )

            if processRepoURI is not None:
                processTriples.append(
                    (processURI, self.SOS.belongsTo, processRepoURI, self.graph)
                )

            self.add_triples_list(processTriples)

    def createLinksBetweenSoSProcessAndSoSDisciplineTriples(self, sos_processes):

        for sos_process in sos_processes.sos_entity_dict.values():
            processDisciplineLinkTriples = []

            # retrieve the process URI
            processURI = self.value(
                None, self.SOS.id, self.toLiteral(sos_process.id), 'uri'
            )

            if processURI is not None:
                for modelId in sos_process.models_list_ids:
                    # we search for the sos_discipline URI
                    sosDisciplineURI = self.value(
                        None, self.SOS.id, self.toLiteral(modelId), 'uri'
                    )

                    if sosDisciplineURI is not None:
                        processDisciplineLinkTriples.append(
                            (sosDisciplineURI, self.SOS.usedIn, processURI, self.graph)
                        )

            if len(processDisciplineLinkTriples) > 0:
                self.add_triples_list(processDisciplineLinkTriples)

    def createParametersAndUsagesTriples(self, parameters):

        for parameter in parameters.sos_entity_dict.values():
            # Create the parameter URI
            parameterURI = self.create_new_URI(
                f'{SoSOntology.BASE_URI}parameter_', parameter.id
            )

            parameterTriples = [
                # add a new OWL individual for the Scheme
                (parameterURI, RDF.type, OWL.NamedIndividual, self.graph),
                # add parameter type
                (parameterURI, RDF.type, self.SOS.Parameter, self.graph),
                # add parameter name
                (
                    parameterURI,
                    self.SOS.name,
                    self.toLiteral(parameter.label),
                    self.graph,
                ),
                (
                    parameterURI,
                    SKOS.prefLabel,
                    self.toLiteral(parameter.label),
                    self.graph,
                ),
                (parameterURI, RDFS.label, self.toLiteral(parameter.label), self.graph),
                (parameterURI, self.SOS.id, self.toLiteral(parameter.id), self.graph),
                # add parameter definition
                (
                    parameterURI,
                    self.SOS.definition,
                    self.toLiteral(parameter.definition),
                    self.graph,
                ),
                # add parameter definition source
                (
                    parameterURI,
                    self.SOS.definitionSource,
                    self.toLiteral(parameter.definitionSource),
                    self.graph,
                ),
                # add parameter datatype
                (
                    parameterURI,
                    self.SOS.datatype,
                    self.toLiteral(parameter.datatype),
                    self.graph,
                ),
                # add parameter ACL tag
                (
                    parameterURI,
                    self.SOS.ACLTag,
                    self.toLiteral(parameter.ACLTag),
                    self.graph,
                ),
                # add parameter unit
                (
                    parameterURI,
                    self.SOS.unit,
                    self.toLiteral(parameter.unit),
                    self.graph,
                ),
                # add parameter code repositories
                (
                    parameterURI,
                    self.SOS.codeRepositoryList,
                    self.toLiteral([repo.id for repo in parameter.code_repositories]),
                    self.graph,
                ),
                # add disciplines using parameter list
                (
                    parameterURI,
                    self.SOS.disciplineUsingParameterList,
                    self.toLiteral(parameter.disciplinesUsingParameterIDs),
                    self.graph,
                ),
                # add parameter datatype list
                (
                    parameterURI,
                    self.SOS.datatypeList,
                    self.toLiteral(parameter.datatype_list),
                    self.graph,
                ),
                # add parameter unit list
                (
                    parameterURI,
                    self.SOS.unitList,
                    self.toLiteral(parameter.unit_list),
                    self.graph,
                ),
            ]

            self.add_triples_list(parameterTriples)

            # we add parameter usages
            for parameterUsage in parameter.instances_list:
                # Create the param usage URI
                parameterUsageURI = self.create_new_URI(
                    f'{SoSOntology.BASE_URI}parameterUsage_',
                    parameterUsage.id,
                )

                parameterUsageTriples = [
                    # add a new OWL individual for the Scheme
                    (parameterUsageURI, RDF.type, OWL.NamedIndividual, self.graph),
                    # add parameterUsage type
                    (parameterUsageURI, RDF.type, self.SOS.Parameter_Usage, self.graph),
                    # add parameterUsage name
                    (
                        parameterUsageURI,
                        self.SOS.name,
                        self.toLiteral(parameterUsage.label),
                        self.graph,
                    ),
                    (
                        parameterUsageURI,
                        SKOS.prefLabel,
                        self.toLiteral(parameterUsage.label),
                        self.graph,
                    ),
                    (
                        parameterUsageURI,
                        RDFS.label,
                        self.toLiteral(parameterUsage.label),
                        self.graph,
                    ),
                    (
                        parameterUsageURI,
                        self.SOS.id,
                        self.toLiteral(parameterUsage.id),
                        self.graph,
                    ),
                    # add parameterUsage visibility
                    (
                        parameterUsageURI,
                        self.SOS.visibility,
                        self.toLiteral(parameterUsage.visibility),
                        self.graph,
                    ),
                    # # add parameterUsage defaultValue
                    # (
                    #     parameterUsageURI,
                    #     self.SOS.defaultValue,
                    #     self.toLiteral(parameterUsage.defaultValue),
                    #     self.graph,
                    # ),
                    # add parameterUsage dataframeEditionLocked
                    (
                        parameterUsageURI,
                        self.SOS.dataframeEditionLocked,
                        self.toLiteral(parameterUsage.dataframeEditionLocked),
                        self.graph,
                    ),
                    # add parameterUsage userLevel
                    (
                        parameterUsageURI,
                        self.SOS.userLevel,
                        self.toLiteral(parameterUsage.userLevel),
                        self.graph,
                    ),
                    # add parameterUsage possibleValues
                    (
                        parameterUsageURI,
                        self.SOS.possibleValues,
                        self.toLiteral(parameterUsage.possibleValues),
                        self.graph,
                    ),
                    # add parameterUsage range
                    (
                        parameterUsageURI,
                        self.SOS.range,
                        self.toLiteral(parameterUsage.range),
                        self.graph,
                    ),
                    # add parameterUsage dataframeDescriptor
                    (
                        parameterUsageURI,
                        self.SOS.dataframeDescriptor,
                        self.toLiteral(parameterUsage.dataframeDescriptor),
                        self.graph,
                    ),
                    # add parameterUsage structuring
                    (
                        parameterUsageURI,
                        self.SOS.structuring,
                        self.toLiteral(parameterUsage.structuring),
                        self.graph,
                    ),
                    # add parameterUsage optional
                    (
                        parameterUsageURI,
                        self.SOS.optional,
                        self.toLiteral(parameterUsage.optional),
                        self.graph,
                    ),
                    # add parameterUsage namespace
                    (
                        parameterUsageURI,
                        self.SOS.namespace,
                        self.toLiteral(parameterUsage.namespace),
                        self.graph,
                    ),
                    # add parameterUsage numerical
                    (
                        parameterUsageURI,
                        self.SOS.numerical,
                        self.toLiteral(parameterUsage.numerical),
                        self.graph,
                    ),
                    # add parameterUsage coupling
                    (
                        parameterUsageURI,
                        self.SOS.coupling,
                        self.toLiteral(parameterUsage.coupling),
                        self.graph,
                    ),
                    # add parameterUsage io_type
                    (
                        parameterUsageURI,
                        self.SOS.ioType,
                        self.toLiteral(parameterUsage.io_type),
                        self.graph,
                    ),
                    # add parameterUsage editable
                    (
                        parameterUsageURI,
                        self.SOS.editable,
                        self.toLiteral(parameterUsage.editable),
                        self.graph,
                    ),
                    # add parameterUsage datatype
                    (
                        parameterUsageURI,
                        self.SOS.datatype,
                        self.toLiteral(parameterUsage.datatype),
                        self.graph,
                    ),
                    # add parameterUsage unit
                    (
                        parameterUsageURI,
                        self.SOS.unit,
                        self.toLiteral(parameterUsage.unit),
                        self.graph,
                    ),
                    # add parameter usage instance link
                    (parameterUsageURI, self.SOS.instanceOf, parameterURI, self.graph),
                ]

                self.add_triples_list(parameterUsageTriples)

    def createDecentralizedSoSOntologyABox(
        self,
        parameters,
        parameters_usages,
        sos_disciplines,
        sos_processes,
        code_repositories,
        sos_process_repositories,
        usecases,
        couplings,
        logs_dict=None,
    ):
        # add update time
        self.addOntologyCreationDate()

        if code_repositories is not None:
            # we will add all triples for the code_repositories
            print(f'Add {code_repositories.len()} Code Repositories triples')
            self.createCodeRepositoriesTriples(code_repositories)

        if sos_process_repositories is not None:
            # we will add all triples for the sos_process_repositories
            print(
                f'Add {sos_process_repositories.len()} SoS Process Repositories triples'
            )
            self.createSoSProcessRepositoriesTriples(sos_process_repositories)

        if sos_processes is not None:
            # we will add all triples for the sos_processes
            print(f'Add {sos_processes.len()} SoS Processes triples')
            self.createSoSProcessTriples(sos_processes)

        if parameters_usages is not None and parameters is not None:
            # we will add all triples for the sos_processes
            print(
                f'Add {parameters_usages.len()} Parameter Usage and {parameters.len()} Parameters triples'
            )
            self.createParametersAndUsagesTriples(parameters)

        if sos_disciplines is not None:
            # we will add all triples for the sos_disciplines
            print(f'Add {sos_disciplines.len()} SoS Disciplines triples')
            self.createSoSDisciplinesTriples(sos_disciplines)

        if sos_processes is not None:
            # we will add all triples links between sos_process and the sos_disciplines
            self.createLinksBetweenSoSProcessAndSoSDisciplineTriples(sos_processes)

        if usecases is not None:
            # we will add all triples for the usecases
            print(f'Add {usecases.len()} Usecases triples')
            self.createUsecasesTriples(usecases)

        if couplings is not None:
            # we will add all triples for the couplings
            print(f'Add {couplings.len()} Couplings triples')
            self.createCouplingsTriples(couplings)

    def exportOntology(self, aboxPath=None):
        if aboxPath is not None:
            if not exists(aboxPath):
                # we create the file
                try:
                    open(aboxPath, 'w+').close()
                except OSError:
                    print(f'Failed creating {aboxPath}')

            # we export the graph with all the added triples
            self.graph.serialize(destination=aboxPath)

            print(f'SoS Ontology saved with {len(self.graph)} triples !')

    def get_markdown_documentation(self, identifier):
        """
        Method to retrive Markdown documentation as a string associated to a model or a process represented by the identifier
        """
        markdown_documentation = ''

        # we first need to find the entity associated to the identifier
        entityURI = self.value(
            None, self.SOS.id, Literal(identifier, datatype=XSD.string), 'uri'
        )

        if entityURI is not None:
            # get documentation
            entity_documentation = self.value(
                entityURI, self.SOS.documentation, None, 'value'
            )
            if entity_documentation is not None and entity_documentation != '':
                markdown_documentation = entity_documentation

        else:
            # It means the value has not been found
            self.logger.debug(
                f'The entity: {identifier} HAS NOT BEEN FOUND in the Ontology'
            )

        return markdown_documentation

    def retrieve_documentations(self, identifier_list: list) -> dict:
        """Methods that retrieve documentation from a list of identifier

        Args:
            identifier_list (list): list of Process or Discipline identifier

        Returns:
            dict: identifier: Markdown documentation as string
        """
        documentation_dict = {}

        for identifier in identifier_list:
            documentation_dict[identifier] = self.get_markdown_documentation(identifier)
        return documentation_dict

    def get_full_parameter_list(self):
        """Method that return a list of all ontology parameters and their related information
        with this specific structure:
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
                disciplines_using_parameter:string list,
                nb_disciplines_using_parameter:int,
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

        parameterList = []
        # retrieve all parameter URI
        for parameterURI in self.graph.subjects(
            predicate=RDF.type, object=self.SOS.Parameter
        ):
            parameter_info = {
                'id': self.SOS.id,
                'uri': None,
                'label': None,
                'definition': self.SOS.definition,
                'definition_source': self.SOS.definitionSource,
                'ACLTag': self.SOS.ACLTag,
                'code_repositories': self.SOS.codeRepositoryList,
                'possible_datatypes': self.SOS.datatypeList,
                'possible_units': self.SOS.unitList,
                'disciplines_using_parameter': self.SOS.disciplineUsingParameterList,
                'nb_disciplines_using_parameter': 0,
                'parameter_usage_details': [],
            }
            # get parameter attributes
            parameter_info = self.get_object_values_dict(
                subjectURI=parameterURI, values_dict=parameter_info
            )
            parameter_info['uri'] = parameterURI
            parameter_info['label'] = self.label(parameterURI)
            if parameter_info['code_repositories'] is not None:
                parameter_info['code_repositories'] = parameter_info[
                    'code_repositories'
                ].split(',\n')
            if parameter_info['possible_datatypes'] is not None:
                parameter_info['possible_datatypes'] = parameter_info[
                    'possible_datatypes'
                ].split(',\n')
            if parameter_info['possible_units'] is not None:
                parameter_info['possible_units'] = parameter_info[
                    'possible_units'
                ].split(',\n')
            if parameter_info['disciplines_using_parameter'] is not None:
                parameter_info['disciplines_using_parameter'] = parameter_info[
                    'disciplines_using_parameter'
                ].split(',\n')
                parameter_info['nb_disciplines_using_parameter'] = len(
                    parameter_info['disciplines_using_parameter']
                )

            # get all parameter usage
            models_using_parameter = set()
            parameter_usage_details = []
            for parameterUsageURI in self.graph.subjects(
                predicate=self.SOS.instanceOf, object=parameterURI
            ):
                parameter_usage_info = {
                    'model_id': None,
                    'model_label': None,
                    'io_type': self.SOS.ioType,
                    'unit': self.SOS.unit,
                    'datatype': self.SOS.datatype,
                    'numerical': self.SOS.numerical,
                    'optional': self.SOS.optional,
                    'range': self.SOS.range,
                    'structuring': self.SOS.structuring,
                    'editable': self.SOS.editable,
                    'possible_values': self.SOS.possibleValues,
                    'dataframe_descriptor': self.SOS.dataframeDescriptor,
                    'dataframe_edition_locked': self.SOS.dataframeEditionLocked,
                    'namespace': self.SOS.namespace,
                    'user_level': self.SOS.userLevel,
                    'visibility': self.SOS.visibility,
                }

                parameter_usage_info = self.get_object_values_dict(
                    subjectURI=parameterUsageURI, values_dict=parameter_usage_info
                )

                modelURI = None
                if parameter_usage_info['io_type'] == 'in':
                    modelURI = self.value(
                        s=None,
                        p=self.SOS.hasInput,
                        o=parameterUsageURI,
                        returnType='uri',
                    )
                elif parameter_usage_info['io_type'] == 'out':
                    modelURI = self.value(
                        s=None,
                        p=self.SOS.hasOutput,
                        o=parameterUsageURI,
                        returnType='uri',
                    )

                if modelURI is not None:
                    parameter_usage_info['model_id'] = self.value(
                        s=modelURI, p=self.SOS.id, o=None, returnType='value'
                    )
                    parameter_usage_info['model_label'] = self.label(modelURI)
                    models_using_parameter.add(parameter_usage_info['model_id'])

                parameter_usage_details.append(parameter_usage_info)

            parameter_info['parameter_usage_details'] = parameter_usage_details

            parameterList.append(parameter_info)

        return parameterList

    def get_full_parameter_label_list(self):
        """Method that return a list of all ontology parameters and their related information
        with this specific structure:
        [
            parameter_id:{
                uri:string,
                id:string,
                label: string,
            }
        ]
        """

        parameterList = []
        # retrieve all parameter URI
        for parameterURI in self.graph.subjects(
            predicate=RDF.type, object=self.SOS.Parameter
        ):
            parameter_info = {
                'id': None,
                'uri': None,
                'label': None,
            }
            parameter_info['id'] = self.value(
                s=parameterURI, p=self.SOS.id, o=None, returnType='value'
            )
            parameter_info['uri'] = parameterURI
            parameter_info['label'] = self.label(parameterURI)

            parameterList.append(parameter_info)

        return parameterList

    def get_full_process_list(self):
        """Method that return a list of all ontology processes and their related information
        with this specific structure:
        [
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
                discipline_list: [{id: string, label: string,icon: string}]
                associated_usecases: [{id: string, name: string, process: string,repository: string,run_usecase: boolean}]
            }
        ]
        """

        processList = []
        # retrieve all process URI
        for processURI in self.graph.subjects(
            predicate=RDF.type, object=self.SOS.SoSProcess
        ):
            process_info = {
                'id': self.SOS.id,
                'uri': None,
                'label': None,
                'description': self.SOS.description,
                'category': self.SOS.category,
                'version': self.SOS.version,
                'process_repository': self.SOS.repository,
                'process_repository_label': None,
                'quantity_disciplines_used': 0,
                'discipline_list': None,
                'associated_usecases': None,
            }
            # get parameter attributes
            process_info = self.get_object_values_dict(
                subjectURI=processURI, values_dict=process_info
            )
            process_info['uri'] = processURI
            process_info['label'] = self.label(processURI)

            processRepositoryURI = self.value(
                s=processURI, p=self.SOS.belongsTo, o=None, returnType='uri'
            )
            if processRepositoryURI is not None:
                process_info['process_repository_label'] = self.label(
                    processRepositoryURI
                )

            # get all disciplines used in the process
            disciplines_used_in_process = []
            for discURI in self.graph.subjects(
                predicate=self.SOS.usedIn, object=processURI
            ):
                disc_info = {
                    'id': self.SOS.id,
                    'label': None,
                    'icon': self.SOS.icon,
                }

                disc_info = self.get_object_values_dict(
                    subjectURI=discURI, values_dict=disc_info
                )
                disc_info['label'] = self.label(discURI)
                disciplines_used_in_process.append(disc_info)
                process_info['quantity_disciplines_used'] += 1
            process_info['discipline_list'] = sorted(
                disciplines_used_in_process, key=lambda x: x['label'].lower()
            )

            # get all usecases associated to the process
            associated_usecases = []
            for usecaseURI in self.graph.subjects(
                predicate=self.SOS.implements, object=processURI
            ):
                usecase_info = {
                    'id': self.SOS.id,
                    'name': self.SOS.name,
                    'process': None,
                    'repository': None,
                    'run_usecase': self.SOS.runUsecase,
                }

                usecase_info = self.get_object_values_dict(
                    subjectURI=usecaseURI, values_dict=usecase_info
                )
                usecase_info['process'] = process_info['label']
                usecase_info['repository'] = process_info['process_repository_label']
                associated_usecases.append(usecase_info)
            process_info['associated_usecases'] = sorted(
                associated_usecases, key=lambda x: x['name'].lower()
            )

            processList.append(process_info)

        return processList

    def get_full_discipline_list(self):
        """Method that return a list of all ontology disciplines and their related information
        with this specific structure:
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

        disciplineList = []
        # retrieve all discipline URI
        for disciplineURI in self.graph.subjects(
            predicate=RDF.type, object=self.SOS.SoSDiscipline
        ):
            discipline_info = {
                'id': self.SOS.id,
                'uri': None,
                'label': None,
                'definition': self.SOS.definition,
                'category': self.SOS.category,
                'version': self.SOS.version,
                'last_modification_date': self.SOS.last_modification_date,
                'source': self.SOS.source,
                'validated_by': self.SOS.validated_by,
                'python_class': self.SOS.pythonClass,
                'validated': self.SOS.validated,
                'icon': self.SOS.icon,
                'output_parameters_quantity': self.SOS.outputParameterUsagesQuantity,
                'input_parameters_quantity': self.SOS.inputParameterUsagesQuantity,
                'class_inheritance': self.SOS.classInheritance,
                'code_repository': self.SOS.codeRepository,
                'type': self.SOS.type,
                'python_module_path': self.SOS.pythonModulePath,
                # 'output_parameters': self.SOS.outputParameterUsages,
                # 'input_parameters': self.SOS.inputParameterUsages,
                'output_parameters': None,
                'input_parameters': None,
                'process_using_discipline': None,
            }
            # get discipline attributes
            discipline_info = self.get_object_values_dict(
                subjectURI=disciplineURI, values_dict=discipline_info
            )
            discipline_info['uri'] = disciplineURI
            discipline_info['label'] = self.label(disciplineURI)

            if discipline_info['class_inheritance'] is not None:
                discipline_info['class_inheritance'] = discipline_info[
                    'class_inheritance'
                ].split(',\n')

            # get all processes using the discipline
            process_using_discipline = []
            for processURI in self.graph.objects(
                predicate=self.SOS.usedIn, subject=disciplineURI
            ):
                # {process_id: string, process_label: string, repository_id: string, repository_label: string}
                process_info = {
                    'process_id': self.SOS.id,
                    'process_label': None,
                    'repository_id': self.SOS.repository,
                    'repository_label': None,
                }

                process_info = self.get_object_values_dict(
                    subjectURI=processURI, values_dict=process_info
                )
                process_info['process_label'] = self.label(processURI)

                processRepositoryURI = self.value(
                    s=processURI, p=self.SOS.belongsTo, o=None, returnType='uri'
                )
                if processRepositoryURI is not None:
                    process_info['repository_label'] = self.label(processRepositoryURI)

                process_using_discipline.append(process_info)
            discipline_info['process_using_discipline'] = process_using_discipline

            # get all output parameters od the discipline
            output_parameters = []
            for parameterUsageURI in self.graph.objects(
                predicate=self.SOS.hasOutput, subject=disciplineURI
            ):
                # {parameter_usage_id: string, parameter_id: string, parameter_label: string}
                parameter_info = {
                    'parameter_usage_id': self.SOS.id,
                    'parameter_id': None,
                    'parameter_label': None,
                }

                parameter_info = self.get_object_values_dict(
                    subjectURI=parameterUsageURI, values_dict=parameter_info
                )

                parameterURI = self.value(
                    s=parameterUsageURI, p=self.SOS.instanceOf, o=None, returnType='uri'
                )
                if parameterURI is not None:
                    parameter_info['parameter_id'] = self.value(
                        s=parameterURI, p=self.SOS.id, o=None, returnType='value'
                    )
                    parameter_info['parameter_label'] = self.label(parameterURI)

                output_parameters.append(parameter_info)
            discipline_info['output_parameters'] = output_parameters

            # get all input parameters od the discipline
            input_parameters = []
            for parameterUsageURI in self.graph.objects(
                predicate=self.SOS.hasInput, subject=disciplineURI
            ):
                # {parameter_usage_id: string, parameter_id: string, parameter_label: string}
                parameter_info = {
                    'parameter_usage_id': self.SOS.id,
                    'parameter_id': None,
                    'parameter_label': None,
                }

                parameter_info = self.get_object_values_dict(
                    subjectURI=parameterUsageURI, values_dict=parameter_info
                )

                parameterURI = self.value(
                    s=parameterUsageURI, p=self.SOS.instanceOf, o=None, returnType='uri'
                )
                if parameterURI is not None:
                    parameter_info['parameter_id'] = self.value(
                        s=parameterURI, p=self.SOS.id, o=None, returnType='value'
                    )
                    parameter_info['parameter_label'] = self.label(parameterURI)

                input_parameters.append(parameter_info)
            discipline_info['input_parameters'] = input_parameters
            print(discipline_info)
            disciplineList.append(discipline_info)

        discipline_list_sorted = sorted(
            disciplineList, key=lambda x: x['label'].lower().strip()
        )
        return discipline_list_sorted

    def get_general_information(self) -> dict:
        """
        Methods returning generic information concerning the current ontology

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
        general_information = {
            'description': '',
            'version': '',
            'iri': '',
            'last_updated': '',
            'entity_count': {},
            'source_code_traceability': {},
        }
        ontoURI = self.value(None, RDF.type, OWL.Ontology, 'uri')
        description = str(self.value(ontoURI, DC.description, None, 'uri'))
        versionIRI = str(
            self.graph.value(ontoURI, OWL.versionIRI, None, default=None, any=True)
        )
        last_updated = str(
            self.graph.value(ontoURI, DC.modified, None, default=None, any=True)
        )
        general_information['description'] = description
        general_information['iri'] = str(ontoURI)
        general_information['version'] = versionIRI.split('/')[-1]
        general_information['last_updated'] = last_updated

        # calculate entitycount
        entities_dict = {
            'code_repositories': self.SOS.CodeRepository,
            'process_repositories': self.SOS.SoSProcessRepository,
            'processes': self.SOS.SoSProcess,
            'models': self.SOS.SoSDiscipline,
            'parameters': self.SOS.Parameter,
            'usecases': self.SOS.Usecase,
        }

        entity_count = {}
        for entityName, entityURI in entities_dict.items():
            entity_count[entityName] = self.get_entity_count(entityURI=entityURI)
        general_information['entity_count'] = entity_count

        source_code_traceability = []
        for codeRepoURI in self.graph.subjects(
            predicate=RDF.type, object=self.SOS.CodeRepository
        ):
            codeRepo_info = {
                'name': self.SOS.name,
                'url': self.SOS.url,
                'branch': self.SOS.branch,
                'commit': self.SOS.commit,
                'committed_date': self.SOS.committedDate,
            }
            # get discipline attributes
            codeRepo_info = self.get_object_values_dict(
                subjectURI=codeRepoURI, values_dict=codeRepo_info
            )
            source_code_traceability.append(codeRepo_info)
        general_information['source_code_traceability'] = sorted(
            source_code_traceability, key=lambda x: x['name'].lower()
        )

        return general_information

    def get_entity_count(self, entityURI: URIRef) -> int:
        entityList = list(self.graph.subjects(RDF.type, entityURI))

        return len(entityList)
