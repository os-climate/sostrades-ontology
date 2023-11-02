'''
Copyright 2022 Airbus SAS
Modifications on 2023/03/13-2023/11/02 Copyright 2023 Capgemini

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
from sos_ontology.core.sos_terminology import SoSTerminology
from rdflib import Literal
from rdflib.namespace import OWL, RDF

# function to transform any sos_ontology to sos_terminology


def ontology_to_terminology(
    loaded_ontology=None,
    ontology_file_path=None,
    loaded_terminology=None,
    terminology_file_path=None,
):
    onto = None
    if loaded_ontology is None and ontology_file_path is not None:
        # Load the ontology
        onto = Ontology()
        onto.load(ontology_file_path, 'xml')
    elif loaded_ontology is not None:
        onto = loaded_ontology

    if loaded_terminology is None and terminology_file_path is not None:
        # Load Excel file
        xl = SoSTerminology(terminology_file_path)
    elif loaded_terminology is not None:
        xl = loaded_terminology

    if onto is not None and xl is not None:
        # get a list of all dataproperties that will become attributes
        datapropertyDict = onto.getOntologyPredicatesDict(OWL.DatatypeProperty)

        # get a list of all objectproperties that will become links
        objectpropertyDict = onto.getOntologyPredicatesDict(OWL.ObjectProperty)

        # get a list of all AnnotationProperty that will become links
        annotationPropertyDict = onto.getOntologyPredicatesDict(OWL.AnnotationProperty)

        # each OWL class will have dedicated sheet in the excel file
        # get the list of class in the ontology
        classesDict, classesAttributes = retrieve_classes_dict_and_attributes(
            onto, xl, OWL.Class
        )

        headers = list(classesAttributes.keys())
        sheetsToCreate = write_to_sheet(
            xl, classesDict, headers, 'OWL Classes', isClasses=True
        )

        # loop through the sheets to create and fill them
        for sheetClass in sheetsToCreate:
            # get the list of class individuals in the ontology
            (
                individualsDict,
                individualsAttributes,
            ) = retrieve_classes_dict_and_attributes(onto, xl, sheetClass['uri'])
            # write sheet
            headers = list(individualsAttributes.keys())
            write_to_sheet(
                xl, individualsDict, headers, sheetClass['label'], isClasses=False
            )

        #  Save excel file
        xl.workbook.save(xl.filePath)


def retrieve_classes_dict_and_attributes(onto, xl, typeURI):
    classDict = {}
    attributesDict = {'uri': {}, 'label': {}}
    activateInstances = False
    for classURI in onto.graph.subjects(RDF.type, typeURI):
        instances = onto.graph.subjects(RDF.type, classURI)
        instancesList = list(instances)
        attributes = getSubjectAttributes(onto, classURI)
        attributesDict.update(attributes)
        classDict[classURI] = {'uri': classURI, 'label': onto.label(classURI)}
        for attribute, attrValue in attributes.items():
            if attribute not in ['uri', 'label']:
                objectLabels = [o['label'] for o in attrValue['object']]
                # attributeValue = ',\n'.join(objectLabels)
                attributeValue = xl.array_to_string(objectLabels)

                classDict[classURI][f'{attribute}'] = attributeValue
        if len(instancesList) > 0:
            activateInstances = True
            classDict[classURI]['instances_quantity'] = len(instancesList)
            classDict[classURI]['instances_list'] = xl.array_to_string(instancesList)
    if activateInstances:
        attributesDict['instances_quantity'] = {}
        attributesDict['instances_list'] = {}
    return classDict, attributesDict


def getSubjectAttributes(onto, subject):
    attributes = {}
    for (predicateURI, objectURI) in onto.graph.predicate_objects(subject):
        predicatelabel = onto.label(predicateURI)
        predicateType = onto.value(predicateURI, RDF.type, None, 'label')
        objectType = onto.value(objectURI, RDF.type, None, 'label')
        if isinstance(objectURI, Literal):
            objectLabel = objectURI.value
        else:
            objectLabel = onto.label(objectURI)
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


def write_to_sheet(xl, elementsDict, headers, sheetName, isClasses=False):
    # create the  sheet
    sheet = xl.create_sheet(f'{sheetName}', len(xl.workbook.sheetnames))
    xl.write_headers(sheet, headers)
    rowCount = 2
    sheetsToCreate = []
    for rowDict in elementsDict.values():
        for columnId, columnValue in rowDict.items():
            col = headers.index(columnId) + 1
            try:
                cell = sheet.cell(column=col, row=rowCount, value=columnValue)
            except:
                print(f'Impossible to write value {columnValue}, it will be ignored')
        rowCount += 1
        if isClasses:
            if rowDict.get('instances_quantity', 0) > 0:
                sheetsToCreate.append(
                    {'uri': rowDict['uri'], 'label': rowDict['label']}
                )

    # Add an Excel Table to the terminology sheet
    xl.add_xl_table(f'{sheetName}', sheet)

    # Set columns width
    xl.set_columns_width(sheet)
    return sheetsToCreate