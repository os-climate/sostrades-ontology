'''
Copyright 2022 Airbus SAS
Modifications on 2024/06/07-2024/07/11 Copyright 2024 Capgemini
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
from copy import deepcopy
from os.path import basename

import numpy as np
import pandas as pd
from rdflib import ConjunctiveGraph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, XSD, split_uri
from rdflib.term import bind

from sos_ontology.core.sos_toolbox import SoSToolbox


class Ontology:
    """
    Class to use an ontology
    """

    def __init__(self):
        """
        Constructor
        """

        # Retrieve logging system
        self.logger = logging.getLogger('SoS.Ontology')

        self.graph = ConjunctiveGraph()
        self.namespace_dict = {}
        self.countAddedTriples = dict({'individuals': 0, 'triples': 0})
        self.namespace_dict = {}
        self.toolbox = SoSToolbox()

        # bind custom datatypes to python objects to be able to extract them properly
        bind(datatype=URIRef('http://qudt.org/schema/qudt/UCUMcs'), pythontype=str)
        bind(datatype=URIRef('http://qudt.org/schema/qudt/LatexString'), pythontype=str)

    def __del__(self):
        """
        Destructor
        """
        self.graph.close()

    def add_namespace_dict(self, namespace_dict):
        for key, value in namespace_dict.items():
            self.namespace_dict[key] = Namespace(value)

    def load(self, path, onto_format):
        # Load ontology owl file
        self.graph.load(path, format=onto_format)
        self.logger.info(
            f'Ontology {basename(path)} loaded with {len(self.graph)} triples'
        )

    def getOntologyPredicatesDict(self, predicate):
        propertyDict = {}
        for propertyURI in self.graph.subjects(RDF.type, predicate):
            propertyDict[propertyURI] = {
                'uri': propertyURI,
                'label': self.label(propertyURI),
            }
        return propertyDict

    def getSubjectAttributes(self, subject, attributesDict):
        attributes = {'uri': str(subject), 'label': self.label(subject)}
        for (attribute, attributeValue) in self.graph.predicate_objects(subject):
            if attribute in attributesDict:
                if (
                    attributeValue.value is not None
                    and attributeValue.value != ''
                    and attributeValue.value != ' '
                ):
                    attributes[
                        attributesDict[attribute]['label']
                    ] = attributeValue.value
        return attributes

    def getSubjectFullAttributes(self, subject):
        attributes = {}
        for (predicateURI, objectURI) in self.graph.predicate_objects(subject):
            predicatelabel = self.label(predicateURI)
            predicateType = self.value(predicateURI, RDF.type, None, 'label')
            objectType = self.value(objectURI, RDF.type, None, 'label')
            if isinstance(objectURI, Literal):
                objectLabel = objectURI.value
            else:
                objectLabel = self.label(objectURI)
            if predicatelabel in attributes:
                attributes[predicatelabel]['object'].append(
                    {'label': objectLabel, 'type': objectType, 'uri': objectURI}
                )
            else:
                attributes[predicatelabel] = {
                    'predicate': {
                        'label': predicatelabel,
                        'type': predicateType,
                        'uri': predicateURI,
                    },
                    'object': [
                        {'label': objectLabel, 'type': objectType, 'uri': objectURI}
                    ],
                }
        return attributes

    def attributesToDictString(self, attributes):
        attributesDict = {}
        for attributeName, attrDict in attributes.items():
            attributeValue = [
                objectValue['label']
                for objectValue in attrDict['object']
            ]
            attributesDict[attributeName] = attributeValue
        return attributesDict

    def query(self, queryString, resultType):
        queryResults = self.graph.query(queryString, initNs=self.namespace_dict)
        self.logger.debug(
            f'SPARQL Query Executed, {len(list(queryResults))} result lines.'
        )
        # self.graph.query.ResultSerializer(queryResults)
        if resultType == 'dict':
            resultDict = []
            for row in queryResults:
                rowDict = {}
                for label in row.labels:
                    if row[label]:
                        rowDict[label] = row[label].value
                    else:
                        rowDict[label] = ''
                resultDict.append(rowDict)
            queryResults = resultDict

        return queryResults

    def label(self, objectValue):
        labelList = self.graph.preferredLabel(objectValue)
        if objectValue is not None:
            if len(labelList) > 0:
                return labelList[0][1].value
            else:
                splitURI = split_uri(objectValue)
                return splitURI[len(splitURI) - 1]
        else:
            return ''

    def value(self, s, p, o, returnType):
        valueUri = self.graph.value(s, p, o, default=None, any=True)
        if valueUri is None:
            return None
        elif returnType == 'label':
            return self.label(valueUri)
        elif returnType == 'uri':
            return valueUri
        elif returnType == 'value':
            return valueUri.value
        else:
            return valueUri

    def get_object_values_dict(self, subjectURI, values_dict):
        result_dict = {
            key: self.value(s=subjectURI, p=predicate, o=None, returnType='value')
            for key, predicate in values_dict.items()
            if predicate is not None and isinstance(predicate, URIRef)
        }
        return result_dict

    def create_new_URI(self, namespace, URIstring):
        # Create new URI by replacing spaces and putting it in lower and if the URI
        # exists, add a number at the end to make sure it is a new URI
        cpt = 0
        # first clean of the string
        URIstring = (
            URIstring.replace('-', ' ')
            .replace('(', ' ')
            .replace(')', ' ')
            .replace('|', ' ')
            .strip()
            .lower()
            .replace(' ', '_')
        )
        # we recreate the separated words
        URIstring = URIstring.replace('_', ' ')
        # we put in Title case
        URIstring = URIstring.title()
        # we remove the spaces
        URIstring = URIstring.replace(' ', '')

        URI = URIRef(namespace + URIstring)
        if (URI, None, None) in self.graph:
            cpt += 1
            while (
                URIRef(namespace + URIstring + '_' + str(cpt)),
                None,
                None,
            ) in self.graph:
                cpt += 1
            return URIRef(namespace + URIstring + '_' + str(cpt))
        else:
            return URI

    def copy_triples(self, s, p, o, graphToCopyFrom):
        # Copy triple from one external graph to the ontology graph
        if (s, p, o) in graphToCopyFrom:
            for s, p, o in graphToCopyFrom.triples((s, p, o)):
                if (s, p, o) not in self.graph:
                    self.add_triple(s, p, o)

    def add_triple(self, s, p, o):
        # Add triple to the graph
        if s is not None and p is not None and o is not None:
            if (type(o) is Literal and o.value != '' and o.value is not None) or (
                type(o) is not Literal
            ):
                if (s, p, o) not in self.graph:
                    self.graph.add((s, p, o))
                    self.countAddedTriples['triples'] += 1
                    if p == RDF.type and o == OWL.NamedIndividual:
                        self.countAddedTriples['individuals'] += 1

    def update_triple_object(self, s, p, o_origin, o_updated):
        # Update triple object
        if s is not None and p is not None and o_updated is not None:
            if (
                type(o_updated) is Literal
                and o_updated.value != ''
                and o_updated.value is not None
            ) or (type(o_updated) is not Literal):
                self.graph.set((s, p, o_updated))
                # if (s, p, o_origin) in self.graph:
                # self.graph.remove([s, p, o_origin])
                # self.add_triple(s, p, o_updated)

    def add_triples_list(self, triplesList):
        # make use of addN method
        self.graph.addN(triplesList)
        # for triple in triplesList:
        #     self.add_triple(triple[0], triple[1], triple[2])

    def update_triples_object_list(self, triplesList):
        for triple in triplesList:
            self.update_triple_object(triple[0], triple[1], triple[2], triple[3])

    def retrieve_classes_dict_and_attributes(self, typeURI):
        classDict = {}
        attributesDict = {'uri': {}, 'label': {}}
        activateInstances = False
        for classURI in self.graph.subjects(RDF.type, typeURI):
            instances = self.graph.subjects(RDF.type, classURI)
            instancesList = list(instances)
            attributes = self.getSubjectFullAttributes(classURI)
            attributesDict.update(attributes)
            classDict[classURI] = {'uri': classURI, 'label': self.label(classURI)}
            for attribute, attrValue in attributes.items():
                if attribute not in ['uri', 'label']:
                    objectLabels = [o['label'] for o in attrValue['object']]
                    # attributeValue = ',\n'.join(objectLabels)
                    attributeValue = self.toolbox.array_to_string(objectLabels)

                    classDict[classURI][f'{attribute}'] = attributeValue
            if len(instancesList) > 0:
                activateInstances = True
                classDict[classURI]['instances_quantity'] = len(instancesList)
                classDict[classURI]['instances_list'] = self.toolbox.array_to_string(
                    instancesList
                )
        if activateInstances:
            attributesDict['instances_quantity'] = {}
            attributesDict['instances_list'] = {}
        return classDict, attributesDict

    def getLiteral(self, parameterDict, key):
        valueLiteral = parameterDict.get(key, None)
        returnLiteral = ' '
        if isinstance(valueLiteral, pd.DataFrame):
            # convert dataframe to dict
            valueLiteral = valueLiteral.to_dict(orient='list')
        elif isinstance(valueLiteral, np.ndarray):
            # convert np.ndarray to list
            valueLiteral = valueLiteral.tolist()
        if valueLiteral is not None:
            if isinstance(valueLiteral, list):
                for v in valueLiteral:
                    if v is None or v == 'null':
                        valueLiteral.remove(v)
                if valueLiteral is not None and len(valueLiteral) > 0:
                    returnLiteral = ',\n'.join([str(i) for i in valueLiteral])
            elif (
                isinstance(valueLiteral, int)
                or isinstance(valueLiteral, float)
                or isinstance(valueLiteral, dict)
                or isinstance(valueLiteral, str)
            ):
                returnLiteral = str(valueLiteral)

        return Literal(returnLiteral, datatype=XSD.string)

    def toLiteral(self, valueLiteral):
        returnLiteral = ' '
        if isinstance(valueLiteral, pd.DataFrame):
            # convert dataframe to dict
            valueLiteral = valueLiteral.to_dict(orient='list')
        elif isinstance(valueLiteral, np.ndarray):
            # convert np.ndarray to list
            valueLiteral = valueLiteral.tolist()
        if valueLiteral is not None:
            if isinstance(valueLiteral, list):
                for v in valueLiteral:
                    if v is None or v == 'null':
                        valueLiteral.remove(v)
                if valueLiteral is not None and len(valueLiteral) > 0:
                    returnLiteral = ',\n'.join([str(i) for i in valueLiteral])
            elif (
                isinstance(valueLiteral, int)
                or isinstance(valueLiteral, float)
                or isinstance(valueLiteral, dict)
                or isinstance(valueLiteral, str)
            ):
                returnLiteral = str(valueLiteral)

        return Literal(returnLiteral, datatype=XSD.string)
