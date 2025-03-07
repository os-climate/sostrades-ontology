'''
Copyright 2022 Airbus SAS
Modifications on 2023/03/13-2024/05/16 Copyright 2023 Capgemini

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

from rdflib import Literal
from rdflib.namespace import OWL, RDF

from sos_ontology.core.ontology import Ontology
from sos_ontology.core.sos_terminology import SoSTerminology

# function to transform any sos_ontology to sos_terminology


def ontology_to_terminology(
    loaded_ontology=None,
    ontology_file_path=None,
    loaded_terminology=None,
    terminology_file_path=None,
):
    """Makes the terminology from the ontology"""
    onto = None
    xl = None

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
        classes_dict, classesAttributes = retrieve_classes_dict_and_attributes(
            onto, xl, OWL.Class,
        )

        headers = list(classesAttributes.keys())
        sheetsToCreate = write_to_sheet(
            xl, classes_dict, headers, 'OWL Classes', is_classes=True,
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
                xl, individualsDict, headers, sheetClass['label'], is_classes=False,
            )

        #  Save excel file
        xl.workbook.save(xl.filePath)


def retrieve_classes_dict_and_attributes(onto, xl, typeURI):
    """Retrieves the classes dict and attributes"""
    class_dict = {}
    attributesDict = {'uri': {}, 'label': {}}
    activateInstances = False
    for classURI in onto.graph.subjects(RDF.type, typeURI):
        instances = onto.graph.subjects(RDF.type, classURI)
        instances_list = list(instances)
        attributes = getSubjectAttributes(onto, classURI)
        attributesDict.update(attributes)
        class_dict[classURI] = {'uri': classURI, 'label': onto.label(classURI)}
        for attribute, attrValue in attributes.items():
            if attribute not in ['uri', 'label']:
                object_labels = [o['label'] for o in attrValue['object']]
                attribute_value = xl.array_to_string(object_labels)

                class_dict[classURI][f'{attribute}'] = attribute_value
        if len(instances_list) > 0:
            activateInstances = True
            class_dict[classURI]['instances_quantity'] = len(instances_list)
            class_dict[classURI]['instances_list'] = xl.array_to_string(instances_list)
    if activateInstances:
        attributesDict['instances_quantity'] = {}
        attributesDict['instances_list'] = {}
    return class_dict, attributesDict


def getSubjectAttributes(onto, subject):
    """Gets the subject attributes"""
    attributes = {}
    for (predicateURI, object_uri) in onto.graph.predicate_objects(subject):
        predicate_label = onto.label(predicateURI)
        predicate_type = onto.value(predicateURI, RDF.type, None, 'label')
        object_type = onto.value(object_uri, RDF.type, None, 'label')
        if isinstance(object_uri, Literal):
            object_label = object_uri.value
        else:
            object_label = onto.label(object_uri)
        if predicate_label in attributes:
            attributes[predicate_label]['object'].append(
                {'label': object_label, 'type': object_type, 'uri': object_uri},
            )
        else:
            attributes[predicate_label] = {
                'predicate': {
                    'label': predicate_label,
                    'type': predicate_type,
                    'uri': predicateURI,
                },
                'object': [
                    {'label': object_label, 'type': object_type, 'uri': object_uri},
                ],
            }
    return attributes


def write_to_sheet(xl, elements_dict, headers, sheet_name, is_classes=False):
    """Writes elements_dict to excel file"""
    # create the  sheet
    sheet = xl.create_sheet(f'{sheet_name}', len(xl.workbook.sheetnames))
    xl.write_headers(sheet, headers)
    row_count = 2
    sheets_to_create = []
    for rowDict in elements_dict.values():
        for column_id, column_value in rowDict.items():
            col = headers.index(column_id) + 1
            try:
                sheet.cell(column=col, row=row_count, value=column_value)
            except:
                print(f'Impossible to write value {column_value}, it will be ignored')
        row_count += 1
        if is_classes and rowDict.get('instances_quantity', 0) > 0:
            sheets_to_create.append(
                {'uri': rowDict['uri'], 'label': rowDict['label']},
            )

    # Add an Excel Table to the terminology sheet
    xl.add_xl_table(f'{sheet_name}', sheet)

    # Set columns width
    xl.set_columns_width(sheet)
    return sheets_to_create
