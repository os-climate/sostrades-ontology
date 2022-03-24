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

from rdflib.namespace import SKOS, XSD, OWL, RDF, RDFS, split_uri
from rdflib import Namespace, Literal
from os.path import dirname, join
from sos_ontology.core.ontology import Ontology
import pandas as pd
import sos_ontology
import logging
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

        # Load the SoS ontology
        if source == 'file':
            if self.ontologyVersion == 1.1:
                self.SOS = Namespace('https://sostrades.eu.airbus.corp/ontology#')
                self.load(
                    join(
                        dirname(sos_ontology.__file__),
                        'data',
                        'sos_ontology',
                        'SoSTrades_Ontology_ABox_Decentralized.owl',
                    ),
                    'xml',
                )

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

    def get_all_classes_id_dict(self, classURI):
        # methods which returns all classes id as a dict
        classIDDict = {}
        for classURI in self.graph.subjects(predicate=RDF.type, object=classURI):
            classID = self.value(classURI, self.SOS.id, None, 'value')
            if classID is not None:
                classIDDict[classID] = None

        return classIDDict

    def get_discipline_metadata(self, disciplineString):
        metadata = {}
        metadata = dict({'id': disciplineString, 'label': disciplineString})

        modelURI = self.value(
            None, self.SOS.id, Literal(disciplineString, datatype=XSD.string), 'uri'
        )

        if modelURI is not None:
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
                'outputParameterQuantity',
                'inputParameterQuantity',
                'modelType',
                'implemented',
                'validator',
                'delivered',
                'originSource',
                'icon',
            ]

            for attr in attributesList:
                if modelAttribute.get(attr, None) is not None:
                    metadata[attr] = modelAttribute.get(attr, None)

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

    def if_exists(self, value, valueType):
        # methods that tests if a specific parameter exists in the graph
        if valueType == 'parameter':
            if (None, self.SOS.id, Literal(value, datatype=XSD.string)) in self.graph:
                # Parameter is found
                return True
            else:
                # It means the value has not been found
                self.logger.debug(
                    f'The {valueType}: {value} HAS NOT BEEN FOUND in the Ontology'
                )
                return False

    def get_unique_namespace_list(self, nonUniqueList, separator):
        fullList = []
        for element in nonUniqueList:
            splitElements = element.split(separator)
            j = len(splitElements)
            while j > 0:
                joinElement = separator.join([splitElements[i] for i in range(0, j)])
                fullList.append(joinElement)
                j -= 1

        uniqueList = list(dict.fromkeys(fullList))
        return uniqueList

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
            if parameter not in parameterDict and parameterData['coupling'] == True:
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
            if parameterData['coupling'] == False:
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
            'Delivered': 4,
            'Implemented': 5,
            'Last publication date': 6,
            'Validator': 7,
            'Validated': 8,
            'Discipline': 9,
            'Processes Using Model': 10,
            'Processes Using Model List': 11,
            'id': 12,
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

            modelRow['Type'] = modelAttributes.get('modelType', '')
            modelRow['Source'] = modelAttributes.get('originSource', '')
            modelRow['Delivered'] = modelAttributes.get('delivered', '')
            modelRow['Implemented'] = modelAttributes.get('implemented', '')
            modelRow['Last publication date'] = modelAttributes.get(
                'publicationDate', ''
            )
            modelRow['Validator'] = modelAttributes.get('validator', '')
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

            # get discipline label
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

            if model_authorised or modelAttributes.get('delivered', '') == 'NO':
                # Add model to list
                new_model = ModelStatus()
                new_model.name = self.label(modelURI)
                new_model.id = modelAttributes.get('id', '')
                new_model.description = modelAttributes.get('description', 'Unknown')
                new_model.model_type = modelAttributes.get('modelType', 'Unknown')
                new_model.source = modelAttributes.get('originSource', 'Unknown')
                new_model.delivered = modelAttributes.get('delivered', 'YES')
                new_model.implemented = modelAttributes.get('implemented', 'YES')
                new_model.last_publication_date = modelAttributes.get(
                    'publicationDate', ''
                )
                new_model.validator = modelAttributes.get('validator', 'Unknown')
                new_model.validated = modelAttributes.get('validated', 'NO')
                new_model.discipline = codeRepositoryLabel
                new_model.processes_using_model = processesNumber
                new_model.processes_using_model_list = processesDict
                new_model.inputs_parameters_quantity = modelAttributes.get(
                    'inputParametersQuantity', ''
                )
                new_model.outputs_parameters_quantity = modelAttributes.get(
                    'outputParametersQuantity', ''
                )

                model_list.append(new_model)

        model_list_json = [md.serialize() for md in model_list]

        return model_list_json

    def get_models_status(self, linkedProcessList=None):
        # Get models status as a dataframe to display as a table in the GUI

        tableHeaders = {
            'Name': 1,
            'Type': 2,
            'Source': 3,
            'Delivered': 4,
            'Implemented': 5,
            'Last publication date': 6,
            'Validator': 7,
            'Validated': 8,
            'Discipline': 9,
            'Processes Using Model': 10,
            'Processes Using Model List': 11,
            'id': 12,
        }

        cleanedModels = []
        cleanedModels = self.get_models_list(onlyTable=True)

        #  Sort the results to display Official models first
        modelsStatusSorted = sorted(
            cleanedModels, key=lambda x: (x['Type'], x['Delivered'])
        )

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

    def get_models_nodes_and_links(self):
        # Get models nodes and links to display in GUI the models and their
        # interrelations
        modelsStatusNodesAndLinks = None

        nodes = self.get_models_list()

        # get links list
        modelIO = {}
        for paramURI in self.graph.subjects(
            predicate=RDF.type, object=self.SOS.Parameter
        ):
            paramId = self.value(paramURI, self.SOS.id, None, 'value')
            for paramUsageURI in self.graph.subjects(
                predicate=self.SOS.instanceOf, object=paramURI
            ):
                # for each parameter usage, retrieve its model inputs
                for modelURI in self.graph.subjects(
                    predicate=self.SOS.hasInput, object=paramUsageURI
                ):
                    modelID = self.value(modelURI, self.SOS.id, None, 'value')
                    # CHECK IF MODEL ID IS IN NODES LIST (AUTHORISED MODELS)
                    if paramId in modelIO:
                        if 'input' in modelIO[paramId]:
                            modelIO[paramId]['input'].append(modelID)
                        else:
                            modelIO[paramId]['input'] = [modelID]
                    else:
                        modelIO[paramId] = {'input': [modelID]}

                # for each parameter usage, retrieve its model outputs
                for modelURI in self.graph.subjects(
                    predicate=self.SOS.hasOutput, object=paramUsageURI
                ):
                    modelID = self.value(modelURI, self.SOS.id, None, 'value')
                    # CHECK IF MODEL ID IS IN NODES LIST (AUTHORISED MODELS)
                    if paramId in modelIO:
                        if 'output' in modelIO[paramId]:
                            modelIO[paramId]['output'].append(modelID)
                        else:
                            modelIO[paramId]['output'] = [modelID]
                    else:
                        modelIO[paramId] = {'output': [modelID]}

        linksDict = {}
        for paramId, pDict in modelIO.items():
            pName = paramId
            paramMetadata = self.get_parameter_metadata(paramId)
            if 'label' in paramMetadata:
                pName = paramMetadata['label']
            if 'output' in pDict and 'input' in pDict:
                for modelOut in pDict['output']:
                    for modelIn in pDict['input']:
                        linkId = modelOut + '_TO_' + modelIn
                        if linkId in linksDict:
                            linksDict[linkId]['metadata']['parameterList'].append(pName)
                            linksDict[linkId]['metadata']['size'] += 1
                        else:
                            linksDict[linkId] = dict(
                                {
                                    'id': linkId,
                                    'source': modelOut,
                                    'target': modelIn,
                                    'type': 'groupLink',
                                    'metadata': {'size': 1, 'parameterList': [pName]},
                                }
                            )
        links = [lDict for lDict in linksDict.values()]

        # get process list
        processList = {}
        for repoURI in self.graph.subjects(
            predicate=RDF.type, object=self.SOS.SoSProcessRepository
        ):
            repoId = self.value(repoURI, self.SOS.id, None, 'value')
            repoProcess = []
            for processURI in self.graph.subjects(
                predicate=self.SOS.belongsTo, object=repoURI
            ):
                processId = self.value(processURI, self.SOS.id, None, 'value')
                repoProcess.append(processId)
            processList[repoId] = repoProcess

        modelsStatusNodesAndLinks = dict(
            {'nodes': nodes, 'links': links, 'processList': processList}
        )

        return modelsStatusNodesAndLinks

    def get_models_nodes_and_links_filtered(self, linked_process_dict=None):
        # Get models nodes and links to display in GUI the models and their
        # interrelations
        modelsStatusNodesAndLinks = None

        nodes = self.get_models_list_filtered(linked_process_dict)
        id_authorised = [md['id'] for md in nodes]

        # get links list
        modelIO = {}
        for paramURI in self.graph.subjects(
            predicate=RDF.type, object=self.SOS.Parameter
        ):
            paramId = self.value(paramURI, self.SOS.id, None, 'value')
            for paramUsageURI in self.graph.subjects(
                predicate=self.SOS.instanceOf, object=paramURI
            ):
                # for each parameter usage, retrieve its model inputs
                for modelURI in self.graph.subjects(
                    predicate=self.SOS.hasInput, object=paramUsageURI
                ):
                    modelID = self.value(modelURI, self.SOS.id, None, 'value')

                    # CHECK IF MODEL ID IS IN NODES LIST (AUTHORISED MODELS)
                    if modelID in id_authorised:
                        if paramId in modelIO:
                            if 'input' in modelIO[paramId]:
                                modelIO[paramId]['input'].append(modelID)
                            else:
                                modelIO[paramId]['input'] = [modelID]
                        else:
                            modelIO[paramId] = {'input': [modelID]}

                # for each parameter usage, retrieve its model outputs
                for modelURI in self.graph.subjects(
                    predicate=self.SOS.hasOutput, object=paramUsageURI
                ):
                    modelID = self.value(modelURI, self.SOS.id, None, 'value')

                    # CHECK IF MODEL ID IS IN NODES LIST (AUTHORISED MODELS)
                    if modelID in id_authorised:
                        if paramId in modelIO:
                            if 'output' in modelIO[paramId]:
                                modelIO[paramId]['output'].append(modelID)
                            else:
                                modelIO[paramId]['output'] = [modelID]
                        else:
                            modelIO[paramId] = {'output': [modelID]}

        linksDict = {}
        for paramId, pDict in modelIO.items():
            pName = paramId
            paramMetadata = self.get_parameter_metadata(paramId)
            if 'label' in paramMetadata:
                pName = paramMetadata['label']
            if 'output' in pDict and 'input' in pDict:
                for modelOut in pDict['output']:
                    for modelIn in pDict['input']:
                        linkId = modelOut + '_TO_' + modelIn
                        if linkId in linksDict:
                            linksDict[linkId]['metadata']['parameterList'].append(pName)
                            linksDict[linkId]['metadata']['size'] += 1
                        else:
                            linksDict[linkId] = dict(
                                {
                                    'id': linkId,
                                    'source': modelOut,
                                    'target': modelIn,
                                    'type': 'groupLink',
                                    'metadata': {'size': 1, 'parameterList': [pName]},
                                }
                            )
        links = [lDict for lDict in linksDict.values()]

        # get process list
        processList = {}
        if linked_process_dict is None:
            for repoURI in self.graph.subjects(
                predicate=RDF.type, object=self.SOS.SoSProcessRepository
            ):
                repoId = self.value(repoURI, self.SOS.id, None, 'value')
                repoProcess = []
                for processURI in self.graph.subjects(
                    predicate=self.SOS.belongsTo, object=repoURI
                ):
                    processId = self.value(processURI, self.SOS.id, None, 'value')
                    repoProcess.append(processId)
                processList[repoId] = repoProcess
        else:
            for auth_repo, auth_processes in linked_process_dict.items():
                repo_metadata = self.get_repo_metadata(auth_repo)
                repo_name = repo_metadata.get('label', 'id')
                processList[repo_name] = []
                for auth_process in auth_processes:
                    process_metadata = self.get_process_metadata(
                        f'{auth_repo}.{auth_process}'
                    )
                    process_name = process_metadata.get('label', 'id')
                    processList[repo_name].append(process_name)

        modelsStatusNodesAndLinks = dict(
            {'nodes': nodes, 'links': links, 'processList': processList}
        )

        return modelsStatusNodesAndLinks

    def createDisciplineTriples(self, disciplinesDict):
        for discipline in disciplinesDict:

            # Create the discipline URI
            disciplineURI = self.create_new_URI(
                'https://sostrades.eu.airbus.corp/ontology#discipline_', discipline
            )

            disciplineTriples = [
                # add a new OWL individual for the Scheme
                (disciplineURI, RDF.type, OWL.NamedIndividual, self.graph),
                # add discipline type
                (disciplineURI, RDF.type, self.SOS.Discipline, self.graph),
                # add discipline name
                (
                    disciplineURI,
                    self.SOS.name,
                    Literal(discipline, datatype=XSD.string),
                    self.graph,
                ),
                (
                    disciplineURI,
                    self.SOS.id,
                    Literal(discipline, datatype=XSD.string),
                    self.graph,
                ),
                # initialise discipline definition
                (
                    disciplineURI,
                    self.SOS.description,
                    Literal(' ', datatype=XSD.string),
                    self.graph,
                ),
                # add model list
                (
                    disciplineURI,
                    self.SOS.modelList,
                    self.getLiteral(disciplinesDict, discipline),
                    self.graph,
                ),
            ]

            self.add_triples_list(disciplineTriples)

    def createCodeRepositoriesTriples(self, code_repositories):
        for code_repository in code_repositories.sos_entity_list:

            # Create the discipline URI
            codeRepoURI = self.create_new_URI(
                'https://sostrades.eu.airbus.corp/ontology#code_repository_',
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
                # add process_repositories list
                (
                    codeRepoURI,
                    self.SOS.processRepositoriesList,
                    self.toLiteral(code_repository.process_repositories_ids),
                    self.graph,
                ),
            ]

            self.add_triples_list(codeRepositoriesTriples)

    def createSoSProcessRepositoriesTriples(self, sos_process_repositories):
        for sos_process_repository in sos_process_repositories.sos_entity_list:

            # Create the discipline URI
            processRepoURI = self.create_new_URI(
                'https://sostrades.eu.airbus.corp/ontology#sos_process_repository_',
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

    def createModelsTriples(self, modelsDataDict):
        for modelId, modelDict in modelsDataDict.items():

            # Create the model URI
            modelURI = self.create_new_URI(
                'https://sostrades.eu.airbus.corp/ontology#model_', modelId
            )

            modelTriples = [
                # add a new OWL individual for the Scheme
                (modelURI, RDF.type, OWL.NamedIndividual, self.graph),
                # add model type
                (modelURI, RDF.type, self.SOS.SoSDiscipline, self.graph),
                # add model code name
                (
                    modelURI,
                    self.SOS.name,
                    self.getLiteral(modelDict, 'model name'),
                    self.graph,
                ),
                # (modelURI, SKOS.prefLabel,
                #  self.getLiteral(modelDict, 'model name'), self.graph),
                # (modelURI, RDFS.label,
                #  self.getLiteral(modelDict, 'model name'), self.graph),
                (
                    modelURI,
                    self.SOS.id,
                    Literal(modelId, datatype=XSD.string),
                    self.graph,
                ),
                # initialise model definition
                (
                    modelURI,
                    self.SOS.description,
                    Literal(' ', datatype=XSD.string),
                    self.graph,
                ),
                # add model class name
                (
                    modelURI,
                    self.SOS.pythonClass,
                    self.getLiteral(modelDict, 'class name'),
                    self.graph,
                ),
                # add model discipline
                (
                    modelURI,
                    self.SOS.disciplineName,
                    self.getLiteral(modelDict, 'discipline'),
                    self.graph,
                ),
                # add model class inheritance
                (
                    modelURI,
                    self.SOS.classInheritance,
                    self.getLiteral(modelDict, 'class inheritance'),
                    self.graph,
                ),
                # add model fullpath
                (
                    modelURI,
                    self.SOS.pythonModulePath,
                    self.getLiteral(modelDict, 'fullpath'),
                    self.graph,
                ),
                # add model input parameters quantity
                (
                    modelURI,
                    self.SOS.inputParametersQuantity,
                    self.getLiteral(modelDict, 'input parameters quantity'),
                    self.graph,
                ),
                # add model output parameters quantity
                (
                    modelURI,
                    self.SOS.outputParametersQuantity,
                    self.getLiteral(modelDict, 'output parameters quantity'),
                    self.graph,
                ),
                # add model input parameters
                (
                    modelURI,
                    self.SOS.inputParameters,
                    self.getLiteral(modelDict, 'input parameters'),
                    self.graph,
                ),
                # add model output parameters
                (
                    modelURI,
                    self.SOS.inputParameters,
                    self.getLiteral(modelDict, 'output parameters'),
                    self.graph,
                ),
                # add model markdown documentation
                (
                    modelURI,
                    self.SOS.documentation,
                    self.getLiteral(modelDict, 'documentation'),
                    self.graph,
                ),
                # add model icon
                (
                    modelURI,
                    self.SOS.icon,
                    self.getLiteral(modelDict, 'icon'),
                    self.graph,
                ),
            ]

            # we search for the discipline URI
            disciplineURI = self.value(
                None, self.SOS.id, self.getLiteral(modelDict, 'discipline'), 'uri'
            )

            if disciplineURI is not None:
                modelTriples.append(
                    (modelURI, self.SOS.belongsTo, disciplineURI, self.graph)
                )

            self.add_triples_list(modelTriples)

    def createSoSDisciplinesTriples(self, sos_disciplines):
        for sos_discipline in sos_disciplines.sos_entity_list:

            # Create the sosDiscipline URI
            sosDisciplineURI = self.create_new_URI(
                'https://sostrades.eu.airbus.corp/ontology#sosDiscipline_',
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
                    self.SOS.validator,
                    self.toLiteral(sos_discipline.validated_by),
                    self.graph,
                ),
                # add sosDiscipline maturity
                (
                    sosDisciplineURI,
                    self.SOS.maturity,
                    self.toLiteral(sos_discipline.maturity),
                    self.graph,
                ),
                # add sosDiscipline publication Date
                (
                    sosDisciplineURI,
                    self.SOS.publicationDate,
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
        for usecase in usecases.sos_entity_list:

            # Create the usecase URI
            usecaseURI = self.create_new_URI(
                'https://sostrades.eu.airbus.corp/ontology#usecase_', usecase.id
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
        for usecase in couplings.sos_entity_list:

            # Create the usecase URI
            couplingURI = self.create_new_URI(
                'https://sostrades.eu.airbus.corp/ontology#usecase_', usecase.id
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

    def createParametersTriples(self, parametersDict):
        ioList = ['input', 'output']

        for parameterId, parameterDict in parametersDict.items():

            # Create the parameter URI
            parameterURI = self.create_new_URI(
                'https://sostrades.eu.airbus.corp/ontology#parameter_', parameterId
            )

            parameterTriples = [
                # add a new OWL individual for the parameter
                (parameterURI, RDF.type, OWL.NamedIndividual, self.graph),
                # add Parameter type
                (parameterURI, RDF.type, self.SOS.Parameter, self.graph),
                # add parameter ID
                (
                    parameterURI,
                    self.SOS.id,
                    Literal(parameterId, datatype=XSD.string),
                    self.graph,
                ),
                # add parameter code name
                (
                    parameterURI,
                    self.SOS.name,
                    Literal(parameterId, datatype=XSD.string),
                    self.graph,
                ),
                (
                    parameterURI,
                    SKOS.prefLabel,
                    Literal(parameterId, datatype=XSD.string),
                    self.graph,
                ),
                (
                    parameterURI,
                    RDFS.label,
                    Literal(parameterId, datatype=XSD.string),
                    self.graph,
                ),
                (
                    parameterURI,
                    self.SOS.id,
                    Literal(parameterId, datatype=XSD.string),
                    self.graph,
                ),
                # DATATYPE AND UNIT LINKED TO PARAMETER AND NOT PARAMETER USAGE
                # add parameter type
                (
                    parameterURI,
                    self.SOS.datatype,
                    self.get_parameter_usage_attribute(parameterDict, 'type', ioList),
                    self.graph,
                ),
                # add parameter unit
                (
                    parameterURI,
                    self.SOS.unit,
                    self.get_parameter_usage_attribute(parameterDict, 'unit', ioList),
                    self.graph,
                ),
                # add namespace
                (
                    parameterURI,
                    self.SOS.namespace,
                    self.get_parameter_usage_attribute(
                        parameterDict, 'namespace', ioList
                    ),
                    self.graph,
                ),
                # initialise parameter definition
                (
                    parameterURI,
                    self.SOS.definition,
                    Literal(' ', datatype=XSD.string),
                    self.graph,
                ),
                # initialise parameter definition source
                (
                    parameterURI,
                    self.SOS.definitionSource,
                    Literal(' ', datatype=XSD.string),
                    self.graph,
                ),
                # initialise parameter Airbus Common Language TAG
                (
                    parameterURI,
                    self.SOS.ACLTag,
                    Literal(' ', datatype=XSD.string),
                    self.graph,
                ),
            ]

            self.add_triples_list(parameterTriples)

            # we will add triples for the parameter usage
            parameterUsageTriples = []
            for io in ioList:
                if 'models ' + io in parameterDict:
                    for modelId, parameterUsageDict in parameterDict[
                        'models ' + io
                    ].items():
                        parameterUsageId = modelId + '.' + io + '.' + parameterId
                        # Create the parameter usage URI
                        parameterUsageURI = self.create_new_URI(
                            'https://sostrades.eu.airbus.corp/ontology#parameter_usage_',
                            parameterUsageId,
                        )

                        parameterUsageTriples = parameterUsageTriples + [
                            # add a new OWL individual for the parameter
                            (
                                parameterUsageURI,
                                RDF.type,
                                OWL.NamedIndividual,
                                self.graph,
                            ),
                            # add Parameter type
                            (
                                parameterUsageURI,
                                RDF.type,
                                self.SOS.Parameter_Usage,
                                self.graph,
                            ),
                            # add parameter code name
                            # (parameterUsageURI, self.SOS.name,
                            #  Literal(parameterUsageId, datatype=XSD.string), self.graph),
                            # (parameterUsageURI, SKOS.prefLabel,
                            #  Literal(parameterUsageId, datatype=XSD.string), self.graph),
                            # (parameterUsageURI, RDFS.label,
                            #  Literal(parameterUsageId, datatype=XSD.string), self.graph),
                            (
                                parameterUsageURI,
                                self.SOS.id,
                                Literal(parameterUsageId, datatype=XSD.string),
                                self.graph,
                            ),
                            # add parameter default value
                            (
                                parameterUsageURI,
                                self.SOS.defaultValue,
                                self.getLiteral(parameterUsageDict, 'default'),
                                self.graph,
                            ),
                            # # add parameter type
                            # (parameterUsageURI, self.SOS.datatype,
                            #  self.getLiteral(parameterUsageDict, 'type'), self.graph),
                            # # add parameter unit
                            # (parameterUsageURI, self.SOS.unit,
                            #  self.getLiteral(parameterUsageDict, 'unit'), self.graph),
                            # add parameter possible_values
                            (
                                parameterUsageURI,
                                self.SOS.possibleValues,
                                self.getLiteral(parameterUsageDict, 'possible_values'),
                                self.graph,
                            ),
                            # add parameter range
                            (
                                parameterUsageURI,
                                self.SOS.range,
                                self.getLiteral(parameterUsageDict, 'range'),
                                self.graph,
                            ),
                            # add parameter user_level
                            (
                                parameterUsageURI,
                                self.SOS.userLevel,
                                self.getLiteral(parameterUsageDict, 'user_level'),
                                self.graph,
                            ),
                            # add parameter visibility
                            (
                                parameterUsageURI,
                                self.SOS.visibility,
                                self.getLiteral(parameterUsageDict, 'visibility'),
                                self.graph,
                            ),
                            # add parameter dataframe_descriptor
                            (
                                parameterUsageURI,
                                self.SOS.dataframeDescriptor,
                                self.getLiteral(
                                    parameterUsageDict, 'dataframe_descriptor'
                                ),
                                self.graph,
                            ),
                            # add parameter dataframe_edition_locked
                            (
                                parameterUsageURI,
                                self.SOS.dataframeEditionLocked,
                                self.getLiteral(
                                    parameterUsageDict, 'dataframe_edition_locked'
                                ),
                                self.graph,
                            ),
                            # add parameter usage instance link
                            (
                                parameterUsageURI,
                                self.SOS.instanceOf,
                                parameterURI,
                                self.graph,
                            ),
                        ]

                        # we search for the model IRI using id
                        modelURI = self.value(
                            None,
                            self.SOS.id,
                            Literal(modelId, datatype=XSD.string),
                            'uri',
                        )

                        # add parameter usage model link
                        if io == 'input' and modelURI is not None:
                            parameterUsageTriples.append(
                                (
                                    modelURI,
                                    self.SOS.hasInput,
                                    parameterUsageURI,
                                    self.graph,
                                )
                            )
                        elif io == 'output' and modelURI is not None:
                            parameterUsageTriples.append(
                                (
                                    modelURI,
                                    self.SOS.hasOutput,
                                    parameterUsageURI,
                                    self.graph,
                                )
                            )

            self.add_triples_list(parameterUsageTriples)

    def createRepoTriples(self, repoDataDict):

        for repo in repoDataDict:
            # Create the repo URI
            repoURI = self.create_new_URI(
                'https://sostrades.eu.airbus.corp/ontology#repository_', repo
            )

            repoTriples = [
                # add a new OWL individual for the Scheme
                (repoURI, RDF.type, OWL.NamedIndividual, self.graph),
                # add repo type
                (repoURI, RDF.type, self.SOS.SoSProcessRepository, self.graph),
                # add repo name
                (
                    repoURI,
                    self.SOS.name,
                    Literal(repo, datatype=XSD.string),
                    self.graph,
                ),
                # (repoURI, SKOS.prefLabel, Literal(
                #     repo, datatype=XSD.string), self.graph),
                # (repoURI, RDFS.label, Literal(
                #     repo, datatype=XSD.string), self.graph),
                (repoURI, self.SOS.id, Literal(repo, datatype=XSD.string), self.graph),
                # initialise repo definition
                (
                    repoURI,
                    self.SOS.description,
                    Literal(' ', datatype=XSD.string),
                    self.graph,
                ),
                # add process list
                (
                    repoURI,
                    self.SOS.processList,
                    self.getLiteral(repoDataDict, repo),
                    self.graph,
                ),
            ]

            self.add_triples_list(repoTriples)

    def createProcessesTriples(self, processDataDict):

        for processid, processDict in processDataDict.items():
            # Create the repo URI
            processURI = self.create_new_URI(
                'https://sostrades.eu.airbus.corp/ontology#process_', processid
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
                    Literal(processDict['name'], datatype=XSD.string),
                    self.graph,
                ),
                # (processURI, SKOS.prefLabel, Literal(
                #     processDict['name'], datatype=XSD.string), self.graph),
                # (processURI, RDFS.label, Literal(
                #     processDict['name'], datatype=XSD.string), self.graph),
                (
                    processURI,
                    self.SOS.id,
                    Literal(processid, datatype=XSD.string),
                    self.graph,
                ),
                # add repo name
                (
                    processURI,
                    self.SOS.repository,
                    self.getLiteral(processDict, 'repository'),
                    self.graph,
                ),
                # initialise process definition
                (
                    processURI,
                    self.SOS.description,
                    Literal(' ', datatype=XSD.string),
                    self.graph,
                ),
                # add process path
                (
                    processURI,
                    self.SOS.pythonModulePath,
                    self.getLiteral(processDict, 'process path'),
                    self.graph,
                ),
                # add discipline list
                (
                    processURI,
                    self.SOS.disciplineList,
                    self.getLiteral(processDict, 'disciplines_list'),
                    self.graph,
                ),
                # add process markdown documentation
                (
                    processURI,
                    self.SOS.documentation,
                    self.getLiteral(processDict, 'documentation'),
                    self.graph,
                ),
            ]

            # we search for the model IRI using id
            repoURI = self.value(
                None, self.SOS.id, self.getLiteral(processDict, 'repository'), 'uri'
            )

            # add parameter usage model link
            if repoURI is not None:
                # link process to repository
                processTriples.append(
                    (processURI, self.SOS.belongsTo, repoURI, self.graph)
                )

            # we search for each model and add links
            for disc in processDict.get('disciplines_list', []):
                modelURI = self.value(
                    None, self.SOS.id, Literal(disc, datatype=XSD.string), 'uri'
                )

                # add model link to process
                if modelURI is not None:
                    # link process to repository
                    processTriples.append(
                        (modelURI, self.SOS.usedIn, processURI, self.graph)
                    )

            self.add_triples_list(processTriples)

    def createSoSProcessTriples(self, sos_processes):

        for sos_process in sos_processes.sos_entity_list:
            # Create the process URI
            processURI = self.create_new_URI(
                'https://sostrades.eu.airbus.corp/ontology#sos_process_', sos_process.id
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

        for sos_process in sos_processes.sos_entity_list:
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

        for parameter in parameters.sos_entity_list:
            # Create the parameter URI
            parameterURI = self.create_new_URI(
                'https://sostrades.eu.airbus.corp/ontology#parameter_', parameter.id
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
            ]

            self.add_triples_list(parameterTriples)

            # we add parameter usages
            for parameterUsage in parameter.instances_list:
                # Create the param usage URI
                parameterUsageURI = self.create_new_URI(
                    'https://sostrades.eu.airbus.corp/ontology#parameterUsage_',
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
                    # add parameterUsage defaultValue
                    (
                        parameterUsageURI,
                        self.SOS.defaultValue,
                        self.toLiteral(parameterUsage.defaultValue),
                        self.graph,
                    ),
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
                    # add parameter usage instance link
                    (parameterUsageURI, self.SOS.instanceOf, parameterURI, self.graph),
                ]

                # # we search for the process URI
                # sos_disciplineURI = self.value(
                #     None, self.SOS.id, self.toLiteral(parameterUsage.sos_discipline.id), 'uri')

                # if sos_disciplineURI is not None:
                #     if parameterUsage.io_type == 'in':
                #         parameterUsageTriples.append(
                #             (sos_disciplineURI, self.SOS.hasInput, parameterUsageURI, self.graph))
                #     elif parameterUsage.io_type == 'out':
                #         parameterUsageTriples.append(
                #             (sos_disciplineURI, self.SOS.hasOutput, parameterUsageURI, self.graph))

                self.add_triples_list(parameterUsageTriples)

    def createReferenceStudyTriples(self, processDataDict):
        def createTreeNodeTriples(treeNodeDict, parentURI, parentId):
            treenodeId = self.toolbox.getID(
                parentId + '.treeNode.',
                treeNodeDict.get('proc_name', None),
                treeNodeDict.get('node_type', None),
            )
            # Create the treeNode URI
            treenodeURI = self.create_new_URI(
                'https://sostrades.eu.airbus.corp/ontology#', treenodeId
            )

            treenodeTriples = [
                # add a new OWL individual for the Scheme
                (treenodeURI, RDF.type, OWL.NamedIndividual, self.graph),
                # add treenode type
                (treenodeURI, RDF.type, self.SOS.SoSTreenode, self.graph),
                # add treenode name
                (
                    treenodeURI,
                    self.SOS.name,
                    Literal(treenodeId, datatype=XSD.string),
                    self.graph,
                ),
                (
                    treenodeURI,
                    SKOS.prefLabel,
                    self.getLiteral(treeNodeDict, 'proc_name'),
                    self.graph,
                ),
                (
                    treenodeURI,
                    RDFS.label,
                    self.getLiteral(treeNodeDict, 'proc_name'),
                    self.graph,
                ),
                (
                    treenodeURI,
                    self.SOS.id,
                    Literal(treenodeId, datatype=XSD.string),
                    self.graph,
                ),
                # initialise definition
                (
                    treenodeURI,
                    self.SOS.description,
                    Literal(' ', datatype=XSD.string),
                    self.graph,
                ),
                # initialise fullpath
                (
                    treenodeURI,
                    self.SOS.pythonModulePath,
                    Literal(
                        self.getLiteral(treeNodeDict, 'model_name_full_path'),
                        datatype=XSD.string,
                    ),
                    self.graph,
                ),
                # add level
                (
                    treenodeURI,
                    self.SOS.level,
                    self.getLiteral(treeNodeDict, 'level'),
                    self.graph,
                ),
                # add type
                (
                    treenodeURI,
                    self.SOS.treenodeType,
                    self.getLiteral(treeNodeDict, 'node_type'),
                    self.graph,
                ),
                # link node to parent
                (parentURI, self.SOS.composedOf, treenodeURI, self.graph),
            ]

            if (
                treeNodeDict.get('node_type', None) is not None
                and treeNodeDict.get('node_type', None) != 'root'
            ):
                # find model from which the treenode is an instance
                modelURI = self.value(
                    None,
                    self.SOS.id,
                    self.getLiteral(treeNodeDict, 'model_name_full_path'),
                    'uri',
                )

                if modelURI is not None:
                    # link node to model
                    treenodeTriples.append(
                        (treenodeURI, self.SOS.instanceOf, modelURI, self.graph)
                    )

            self.add_triples_list(treenodeTriples)

            if len(treeNodeDict['children']) > 0:
                for child in treeNodeDict['children']:
                    createTreeNodeTriples(child, treenodeURI, treenodeId)

        for repoName, repoDict in processDataDict.items():
            # Create the repo URI
            repoURI = self.create_new_URI(
                'https://sostrades.eu.airbus.corp/ontology#', repoName
            )

            repoTriples = [
                # add a new OWL individual for the Scheme
                (repoURI, RDF.type, OWL.NamedIndividual, self.graph),
                # add repo type
                (repoURI, RDF.type, self.SOS.SoSProcessRepository, self.graph),
                # add repo name
                # (repoURI, self.SOS.name, Literal(repoName, datatype=XSD.string), self.graph),
                # (repoURI, SKOS.prefLabel, Literal(repoName, datatype=XSD.string), self.graph),
                # (repoURI, RDFS.label, Literal(repoName, datatype=XSD.string), self.graph),
                (
                    repoURI,
                    self.SOS.id,
                    Literal(repoName, datatype=XSD.string),
                    self.graph,
                ),
                # # initialise definition
                # (repoURI, self.SOS.description,
                #  Literal(' ', datatype=XSD.string), self.graph),
            ]

            self.add_triples_list(repoTriples)

            for processName, processDict in repoDict.items():
                processid = repoName + '.' + processName
                # Create the repo URI
                processURI = self.create_new_URI(
                    'https://sostrades.eu.airbus.corp/ontology#', processid
                )

                processTriples = [
                    # add a new OWL individual for the Scheme
                    (processURI, RDF.type, OWL.NamedIndividual, self.graph),
                    # add repo type
                    (processURI, RDF.type, self.SOS.SoSProcess, self.graph),
                    # add repo name
                    (
                        processURI,
                        self.SOS.name,
                        Literal(processid, datatype=XSD.string),
                        self.graph,
                    ),
                    # (processURI, SKOS.prefLabel, Literal(
                    #     processName, datatype=XSD.string), self.graph),
                    # (processURI, RDFS.label, Literal(
                    #     processName, datatype=XSD.string), self.graph),
                    (
                        processURI,
                        self.SOS.id,
                        Literal(processid, datatype=XSD.string),
                        self.graph,
                    ),
                    # initialise definition
                    (
                        processURI,
                        self.SOS.description,
                        Literal(' ', datatype=XSD.string),
                        self.graph,
                    ),
                    # link process to repository
                    (processURI, self.SOS.belongsTo, repoURI, self.graph),
                ]

                self.add_triples_list(processTriples)

                createTreeNodeTriples(processDict, processURI, processid)

    def createParametersManualTriples(self, parametersDict):

        for parameterId, parameterDict in parametersDict.items():
            parameterNewTriples = []
            parameterUpdateTriples = []

            # we search for the parameter IRI using id
            parameterURI = self.value(
                None,
                self.SOS.id,
                self.getLiteral(parameterDict, 'Discipline Naming'),
                'uri',
            )

            if parameterURI is not None:
                if (
                    parameterDict['Conventional Name'] is not None
                    and parameterDict['Conventional Name'] != ''
                ):
                    # we update the parameter label
                    parameterUpdateTriples.append(
                        (
                            parameterURI,
                            self.SOS.name,
                            Literal(parameterId, datatype=XSD.string),
                            self.getLiteral(parameterDict, 'Conventional Name'),
                        )
                    )
                    parameterUpdateTriples.append(
                        (
                            parameterURI,
                            SKOS.prefLabel,
                            Literal(parameterId, datatype=XSD.string),
                            self.getLiteral(parameterDict, 'Conventional Name'),
                        )
                    )
                    parameterUpdateTriples.append(
                        (
                            parameterURI,
                            RDFS.label,
                            Literal(parameterId, datatype=XSD.string),
                            self.getLiteral(parameterDict, 'Conventional Name'),
                        )
                    )

                if parameterDict['Unit'] is not None and parameterDict['Unit'] != '':
                    # we update the parameter Unit
                    parameterUpdateTriples.append(
                        (
                            parameterURI,
                            self.SOS.unit,
                            Literal(' ', datatype=XSD.string),
                            self.getLiteral(parameterDict, 'Unit'),
                        )
                    )

                if (
                    parameterDict['Definition'] is not None
                    and parameterDict['Definition'] != ''
                ):
                    # we update the parameter definition
                    parameterUpdateTriples.append(
                        (
                            parameterURI,
                            self.SOS.definition,
                            Literal(' ', datatype=XSD.string),
                            self.getLiteral(parameterDict, 'Definition'),
                        )
                    )

                if (
                    parameterDict['Definition Source'] is not None
                    and parameterDict['Definition Source'] != ''
                ):
                    # we update the parameter Definition Source
                    parameterUpdateTriples.append(
                        (
                            parameterURI,
                            self.SOS.definitionSource,
                            Literal(' ', datatype=XSD.string),
                            self.getLiteral(parameterDict, 'Definition Source'),
                        )
                    )

                if (
                    parameterDict['Synonyms'] is not None
                    and parameterDict['Synonyms'] != ''
                ):
                    # we add synonyms
                    for synonym in parameterDict['Synonyms'].split(','):
                        synonym = synonym.strip()
                        parameterNewTriples.append(
                            (
                                parameterURI,
                                SKOS.altLabel,
                                Literal(synonym, datatype=XSD.string),
                                self.graph,
                            )
                        )

                if (
                    parameterDict['ACL TAG'] is not None
                    and parameterDict['ACL TAG'] != ''
                ):
                    # we update the parameter ACL TAG
                    parameterUpdateTriples.append(
                        (
                            parameterURI,
                            self.SOS.ACLTag,
                            Literal(' ', datatype=XSD.string),
                            self.getLiteral(parameterDict, 'ACL TAG'),
                        )
                    )

                self.add_triples_list(parameterNewTriples)
                self.update_triples_object_list(parameterUpdateTriples)

    def createDisciplineManualTriples(self, disciplinesDict):

        for disciplineId, disciplineDict in disciplinesDict.items():
            disciplineNewTriples = []

            # we search for the discipline IRI using id
            disciplineURI = self.value(
                None, self.SOS.id, self.getLiteral(disciplineDict, 'Discipline'), 'uri'
            )

            if disciplineURI is not None:
                if disciplineDict['Name'] is not None and disciplineDict['Name'] != '':
                    # we update the discipline label
                    disciplineNewTriples.append(
                        (
                            disciplineURI,
                            SKOS.prefLabel,
                            self.getLiteral(disciplineDict, 'Name'),
                            self.graph,
                        )
                    )
                    disciplineNewTriples.append(
                        (
                            disciplineURI,
                            RDFS.label,
                            self.getLiteral(disciplineDict, 'Name'),
                            self.graph,
                        )
                    )

                if (
                    disciplineDict['Definition'] is not None
                    and disciplineDict['Definition'] != ''
                ):
                    # we update the parameter definition
                    disciplineNewTriples.append(
                        (
                            disciplineURI,
                            self.SOS.description,
                            self.getLiteral(disciplineDict, 'Definition'),
                            self.graph,
                        )
                    )

                self.add_triples_list(disciplineNewTriples)

    def createProcessRepoManualTriples(self, processRepoDict):

        for processRepoId, processRepoDict in processRepoDict.items():
            processRepoNewTriples = []

            # we search for the processRepo IRI using id
            processRepoURI = self.value(
                None, self.SOS.id, self.getLiteral(processRepoDict, 'Repo ID'), 'uri'
            )

            if processRepoURI is not None:
                if (
                    processRepoDict['Repo Name'] is not None
                    and processRepoDict['Repo Name'] != ''
                ):
                    # we update the processRepo label
                    # processRepoNewTriples.append((processRepoURI, self.SOS.name, self.getLiteral(
                    #     processRepoDict, 'Repo Name'), self.graph))
                    processRepoNewTriples.append(
                        (
                            processRepoURI,
                            SKOS.prefLabel,
                            self.getLiteral(processRepoDict, 'Repo Name'),
                            self.graph,
                        )
                    )
                    processRepoNewTriples.append(
                        (
                            processRepoURI,
                            RDFS.label,
                            self.getLiteral(processRepoDict, 'Repo Name'),
                            self.graph,
                        )
                    )

                if (
                    processRepoDict['Repo Description'] is not None
                    and processRepoDict['Repo Description'] != ''
                ):
                    # we update the parameter Description
                    processRepoNewTriples.append(
                        (
                            processRepoURI,
                            self.SOS.description,
                            self.getLiteral(processRepoDict, 'Repo Description'),
                            self.graph,
                        )
                    )

                self.add_triples_list(processRepoNewTriples)

    def createProcessManualTriples(self, processesDict):

        for processDict in processesDict.values():
            processNewTriples = []

            # we search for the process IRI using id
            processURI = self.value(
                None, self.SOS.id, self.getLiteral(processDict, 'Process ID'), 'uri'
            )

            if processURI is not None:
                if (
                    processDict['Process Name'] is not None
                    and processDict['Process Name'] != ''
                ):
                    # we update the process label
                    # processNewTriples.append((processURI, self.SOS.name, self.getLiteral(
                    #     processDict, 'Process Name'), self.graph))
                    processNewTriples.append(
                        (
                            processURI,
                            SKOS.prefLabel,
                            self.getLiteral(processDict, 'Process Name'),
                            self.graph,
                        )
                    )
                    processNewTriples.append(
                        (
                            processURI,
                            RDFS.label,
                            self.getLiteral(processDict, 'Process Name'),
                            self.graph,
                        )
                    )

                if (
                    processDict['Process Description'] is not None
                    and processDict['Process Description'] != ''
                ):
                    # we update the parameter Description
                    processNewTriples.append(
                        (
                            processURI,
                            self.SOS.description,
                            self.getLiteral(processDict, 'Process Description'),
                            self.graph,
                        )
                    )

                self.add_triples_list(processNewTriples)

    def createModelsManualTriples(self, modelsDict):

        for modelRow in modelsDict.values():
            modelNewTriples = []

            if (
                modelRow['Model name in code'] is None
                or modelRow['Model name in code'] == ''
            ):
                # it is a model not yet implemented in the code so it is not yet existing in the ontology.
                # Create the model URI
                if (
                    modelRow['Display name'] is not None
                    and modelRow['Display name'] != ''
                ):
                    modelURI = self.create_new_URI(
                        'https://sostrades.eu.airbus.corp/ontology#expectedModel_',
                        modelRow['Display name'],
                    )
                else:
                    modelURI = self.create_new_URI(
                        'https://sostrades.eu.airbus.corp/ontology#expectedModel_', 1
                    )

                # add a new OWL individual for the model
                modelNewTriples.append(
                    (modelURI, RDF.type, OWL.NamedIndividual, self.graph)
                )
                # add model type
                modelNewTriples.append(
                    (modelURI, RDF.type, self.SOS.SoSDiscipline, self.graph)
                )

                modelNewTriples.append(
                    (
                        modelURI,
                        self.SOS.id,
                        Literal(modelURI, datatype=XSD.string),
                        self.graph,
                    )
                )

            else:
                # we search for the model IRI using id
                modelURI = self.value(
                    None,
                    self.SOS.id,
                    self.getLiteral(modelRow, 'Model name in code'),
                    'uri',
                )

            if modelURI is not None:
                if (
                    modelRow['Display name'] is not None
                    and modelRow['Display name'] != ''
                ):
                    # we update the model label
                    modelNewTriples.append(
                        (
                            modelURI,
                            self.SOS.name,
                            self.getLiteral(modelRow, 'Display name'),
                            self.graph,
                        )
                    )
                    modelNewTriples.append(
                        (
                            modelURI,
                            SKOS.prefLabel,
                            self.getLiteral(modelRow, 'Display name'),
                            self.graph,
                        )
                    )
                    modelNewTriples.append(
                        (
                            modelURI,
                            RDFS.label,
                            self.getLiteral(modelRow, 'Display name'),
                            self.graph,
                        )
                    )

                if modelRow['Type'] is not None and modelRow['Type'] != '':
                    # we update the model Type
                    modelNewTriples.append(
                        (
                            modelURI,
                            self.SOS.modelType,
                            self.getLiteral(modelRow, 'Type'),
                            self.graph,
                        )
                    )

                if (
                    modelRow['Origin/ source'] is not None
                    and modelRow['Origin/ source'] != ''
                ):
                    # we update the model Origin/ source
                    modelNewTriples.append(
                        (
                            modelURI,
                            self.SOS.originSource,
                            self.getLiteral(modelRow, 'Origin/ source'),
                            self.graph,
                        )
                    )

                if (
                    modelRow['Validated by'] is not None
                    and modelRow['Validated by'] != ''
                ):
                    # we update the model Validated by
                    modelNewTriples.append(
                        (
                            modelURI,
                            self.SOS.validator,
                            self.getLiteral(modelRow, 'Validated by'),
                            self.graph,
                        )
                    )

                if (
                    modelRow['Model delivered to SoSTrades?'] is not None
                    and modelRow['Model delivered to SoSTrades?'] != ''
                ):
                    # we update the model Model delivered to SoSTrades?
                    modelNewTriples.append(
                        (
                            modelURI,
                            self.SOS.delivered,
                            self.getLiteral(modelRow, 'Model delivered to SoSTrades?'),
                            self.graph,
                        )
                    )

                if (
                    modelRow['Model implemented in SoSTrades?'] is not None
                    and modelRow['Model implemented in SoSTrades?'] != ''
                ):
                    # we update the model Model implemented in SoSTrades?
                    modelNewTriples.append(
                        (
                            modelURI,
                            self.SOS.implemented,
                            self.getLiteral(
                                modelRow, 'Model implemented in SoSTrades?'
                            ),
                            self.graph,
                        )
                    )

                if (
                    modelRow['Last publication date (month-year)'] is not None
                    and modelRow['Last publication date (month-year)'] != ''
                ):
                    # we update the model Last publication date (month-year)
                    modelNewTriples.append(
                        (
                            modelURI,
                            self.SOS.publicationDate,
                            self.getLiteral(
                                modelRow, 'Last publication date (month-year)'
                            ),
                            self.graph,
                        )
                    )

                if modelRow['Validated'] is not None and modelRow['Validated'] != '':
                    # we update the model Validated
                    modelNewTriples.append(
                        (
                            modelURI,
                            self.SOS.validated,
                            self.getLiteral(modelRow, 'Validated'),
                            self.graph,
                        )
                    )

                if (
                    modelRow['Description'] is not None
                    and modelRow['Description'] != ''
                ):
                    # we update the model Description
                    modelNewTriples.append(
                        (
                            modelURI,
                            self.SOS.description,
                            self.getLiteral(modelRow, 'Description'),
                            self.graph,
                        )
                    )

                self.add_triples_list(modelNewTriples)

    def createSoSOntologyABox(
        self,
        parametersDict=None,
        modelsDataDict=None,
        processDataDict=None,
        disciplineDataDict=None,
        repoDataDict=None,
        referenceDataDict=None,
        incoherencesFilePath=None,
        logs_dict=None,
    ):

        if disciplineDataDict is not None:
            # we will add all triples for the disciplines
            self.createDisciplineTriples(disciplineDataDict)

        if modelsDataDict is not None:
            # we will add all triples for the models
            self.createModelsTriples(modelsDataDict)

        if parametersDict is not None:
            # we will add all triples for the parameters
            self.createParametersTriples(parametersDict)

        if repoDataDict is not None:
            # we will add all triples for the processes repository
            self.createRepoTriples(repoDataDict)

        if processDataDict is not None:
            # we will add all triples for the processes
            self.createProcessesTriples(processDataDict)

        if referenceDataDict is not None:
            # we will add all triples for the references
            # self.createReferencesTriples(referenceDataDict)
            pass

        # wrtie incoherences to log
        if logs_dict is not None and len(self.incoherences.keys()) > 0:
            logs_dict['incoherences'] = self.incoherences

        # write incoherences to file
        if incoherencesFilePath is not None:
            if len(self.incoherences.keys()) > 0:
                self.toolbox.write_json(
                    json_file_path=incoherencesFilePath,
                    dict_to_write=self.incoherences,
                    entity='incoherences',
                )
            else:
                print('No incoherences found in code parameter attributes')

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

    def complementOntologyWithGlossary(self, excelGlossaryTerminology=None):
        if excelGlossaryTerminology is not None:
            # we add the manual inputs for the parameters stored in the Glossary excel file
            headers = excelGlossaryTerminology.get_sheet_headers(
                'Parameters Terminology'
            )
            parametersDict = excelGlossaryTerminology.get_sheet_dict(
                'Parameters Terminology', headers, 'Discipline Naming'
            )
            print(f'Glossary file loaded with {len(parametersDict)} parameters')
            self.createParametersManualTriples(parametersDict)

            # we add the manual inputs for the disciplines stored in the Glossary excel file
            headers = excelGlossaryTerminology.get_sheet_headers(
                'Disciplines Terminology'
            )
            disciplinesDict = excelGlossaryTerminology.get_sheet_dict(
                'Disciplines Terminology', headers, 'Discipline'
            )
            print(f'Glossary file loaded with {len(disciplinesDict)} disciplines')
            self.createDisciplineManualTriples(disciplinesDict)

            # we add the manual inputs for the Process Repositiory stored in the Glossary excel file
            headers = excelGlossaryTerminology.get_sheet_headers(
                'Process Repository Terminology'
            )
            processRepoDict = excelGlossaryTerminology.get_sheet_dict(
                'Process Repository Terminology', headers, 'Repo ID'
            )
            print(
                f'Glossary file loaded with {len(processRepoDict)} Process Repository'
            )
            self.createProcessRepoManualTriples(processRepoDict)

            # we add the manual inputs for the Process  stored in the Glossary excel file
            headers = excelGlossaryTerminology.get_sheet_headers('Process Terminology')
            processDict = excelGlossaryTerminology.get_sheet_dict(
                'Process Terminology', headers, 'Process ID'
            )
            print(f'Glossary file loaded with {len(processDict)} Processes')
            self.createProcessManualTriples(processDict)

            # we add the manual inputs for the Models  stored in the Glossary excel file
            headers = excelGlossaryTerminology.get_sheet_headers('Models Terminology')
            modelsDict = excelGlossaryTerminology.get_sheet_dict(
                'Models Terminology', headers, ''
            )
            print(f'Glossary file loaded with {len(modelsDict)} Models')
            self.createModelsManualTriples(modelsDict)

    def exportOntology(self, aboxPath=None):
        if aboxPath is not None:
            # we export the graph with all the added triples
            self.graph.serialize(destination=aboxPath)

            print(f'SoS Ontology saved with {len(self.graph)} triples !')

    def get_parameter_usage_attribute(self, parameterDict, attribute, ioList):
        attr_values = []
        attr_values_dict = {}
        for io in ioList:
            if 'models ' + io in parameterDict:
                for modelId, parameterUsageDict in parameterDict[
                    'models ' + io
                ].items():
                    value = self.getLiteral(parameterUsageDict, attribute)
                    if value not in attr_values:
                        attr_values.append(value)
                        attr_values_dict[value] = [modelId]
                    else:
                        attr_values_dict[value].append(modelId)
        if len(attr_values) > 1:
            # print(
            #     f'WARNING: parameter {parameterDict["id"]} has several {attribute}s defined in the code: {", ".join(attr_values)}')
            if parameterDict["id"] not in self.incoherences:
                self.incoherences[parameterDict["id"]] = {}
            self.incoherences[parameterDict["id"]].update({attribute: attr_values_dict})
            # print(' || '.join(
            #     [f'{v} in:[ {", ".join(attr_values_dict[v])}]' for v in attr_values_dict.keys()]))
        if len(attr_values) > 0:
            return attr_values[0]
        else:
            return self.getLiteral({}, attribute)

    def get_markdow_documentation(self, identifier):
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
