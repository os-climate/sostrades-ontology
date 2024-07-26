'''
Copyright 2022 Airbus SAS
Modifications on 2024/02/08 Copyright 2024 Capgemini

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

#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logging
import sys
from os import environ, pathsep, system, name
from os.path import dirname, join

from rdflib.namespace import Namespace

import sos_ontology
from sos_ontology.core.functions.ontology_to_terminology import ontology_to_terminology
from sos_ontology.core.functions.sendGChatNotifications import sendGChatNotification
from sos_ontology.core.ontology import Ontology
from sos_ontology.core.sos_decentralized_codedataextractor import SoSCodeDataExtractor
from sos_ontology.core.sos_ontology import SoSOntology
from sos_ontology.core.sos_terminology import SoSTerminology
from sos_ontology.core.sos_toolbox import SoSToolbox

webhookURL = None
platform = None
if len(sys.argv) > 1:
    webhookURL = str(sys.argv[1])
if len(sys.argv) >= 2:
    platform = str(sys.argv[2])

BUILD_URL = None
environ_dict = dict(environ)
# prepare necessary paths
dataPath = dirname(dirname(dirname(sos_ontology.__file__)))
dataOntologyPath = join(dirname(sos_ontology.__file__), 'data')

# retrieve PYTHONPATH
try:
    PYTHONPATH_list = environ_dict['PYTHONPATH'].split(pathsep)
except Exception:
    PYTHONPATH_list = []
    print('Impossible to retrieve Python Path. Stopping script')

# retrieve path to current SoSOntology
ONTOLOGY_FOLDER = environ_dict.get('ONTOLOGY_FOLDER', None)
if ONTOLOGY_FOLDER is not None and ONTOLOGY_FOLDER != '':
    SoSaBox_current_path = join(
        ONTOLOGY_FOLDER, 'SoSTrades_Ontology_ABox_Decentralized.owl'
    )
else:
    SoSaBox_current_path = join(
        dataOntologyPath,
        'sos_ontology',
        'SoSTrades_Ontology_ABox_Decentralized.owl',
    )

if len(PYTHONPATH_list) > 0:
    pathsDict = {
        'SoStBox': join(
            dataOntologyPath, 'sos_ontology', 'SoSTrades_Ontology_TBox.owl'
        ),
        'SoSaBox': join(
            dataOntologyPath,
            'sos_ontology',
            'SoSTrades_Ontology_ABox_Decentralized.owl',
        ),
        'SoSaBoxCurrent': SoSaBox_current_path,
        'ontologyCreationLogs': join(
            dataOntologyPath, 'logs', 'ontologyCreationLogs.json'
        ),
        'excelTerminology': join(
            dataOntologyPath, 'terminology', 'SoS_Trades_Terminology_ABox.xlsx'
        ),
    }

    logging.disable(logging.WARNING)
    # initialise elements
    oldOnto = Ontology()
    toolbox = SoSToolbox()
    logs_dict = {}

    # retrieve previous traceability
    previous_extraction_logs_path = pathsDict.get('ontologyCreationLogs', None)
    previous_extraction_logs = toolbox.load_json(
        json_file_path=previous_extraction_logs_path, entity='Previous Logs'
    )
    previous_code_repositories_traceability = {}
    if previous_extraction_logs is not None:
        previous_code_repositories_traceability = previous_extraction_logs.get(
            'code_repositories_traceability', {}
        )

    codeData = SoSCodeDataExtractor(
        basepath=dirname(sos_ontology.__file__),
        logs_dict=logs_dict,
        previous_code_repositories_traceability=previous_code_repositories_traceability,
    )

    # retrieve code data on all repositories
    logs_dict = codeData.generate_entities_from_code_repositories()

    print(
        "#####################    CREATE ONTOLOGY ABOX FROM CODE  #########################"
    )

    # Load SoS Tbox
    sosOnto = SoSOntology(version=0, source="empty")
    sosOnto.load(pathsDict["SoStBox"], "xml")
    sosOnto.SOS = Namespace(SoSOntology.BASE_URI)

    # Create instances of updated ontology from extracted code data
    sosOnto.createDecentralizedSoSOntologyABox(
        parameters=codeData.parameters,
        parameters_usages=codeData.parameters_usages,
        sos_disciplines=codeData.sos_disciplines,
        sos_processes=codeData.sos_processes,
        code_repositories=codeData.code_repositories,
        sos_process_repositories=codeData.sos_process_repositories,
        usecases=codeData.usecases,
        couplings=codeData.couplings,
        logs_dict=logs_dict,
    )

    print(
        "#####################    LOAD PREVIOUS ONTOLOGY    #########################"
    )
    oldOnto.load(pathsDict["SoSaBoxCurrent"], "xml")

    print(
        "#####################    EXPORT UPDATED ONTOLOGY TO OWL   #########################"
    )
    # save ontology to OWL
    sosOnto.exportOntology(aboxPath=pathsDict["SoSaBox"])

    print(
        '#####################    EXPORT ONTOLOGY TO EXCEL TERMINOLOGY   #########################'
    )
    excelTerminology = SoSTerminology(pathsDict['excelTerminology'])
    ontology_to_terminology(
        loaded_ontology=sosOnto,
        ontology_file_path=None,
        loaded_terminology=excelTerminology,
        terminology_file_path=None,
    )

    print(
        "#####################    CALCULATE DIFFERENCES BETWEEN BEFORE AND AFTER UPDATE #########################"
    )
    toolbox.calculate_difference_before_after(
        oldOntology=oldOnto,
        newOntology=sosOnto,
        ontologyNamespace=sosOnto.SOS,
        logs_dict=logs_dict,
    )

    print("#####################    WRITE LOGS #########################")
    toolbox.write_logs(
        logs_dict=logs_dict,
        log_file_name='output_log.txt',
        short_log_file_name='short_log.txt',
        full_log_json_path=pathsDict['ontologyCreationLogs'],
    )

    # Display output_log.txt file
    with open('output_log.txt', 'r') as file:
        content = file.read()
        print(content)

    logging.disable(logging.INFO)

    print(
        "###################################    CODE DATA EXTRACTION DONE    ##################################"
    )


print(
    '#####################    SEND GOOGLE CHAT NOTIFICATION    #########################'
)

if 'BUILD_URL' in environ_dict:
    BUILD_URL = environ_dict['BUILD_URL']

if webhookURL is not None and BUILD_URL is not None:
    with open('short_log.txt', 'r') as short_log_file:
        shortLog = short_log_file.read()

    if platform is None:
        platform = ''
    else:
        platform = ' on platform ' + platform

    cards = [
        {
            "header": {
                "title": "Decentralized Ontology Update" + platform,
                "subtitle": "Mister Jenkins",
                "imageUrl": "https://www.coolcatcollars.co.uk/user/products/large/Leopold.jpg",
                "imageStyle": "IMAGE",
            },
            "sections": [
                {
                    "header": "Update results",
                    "widgets": [{"textParagraph": {"text": f"{shortLog}"}}],
                },
                {
                    "widgets": [
                        {
                            "buttons": [
                                {
                                    "textButton": {
                                        "text": "FULL LOG",
                                        "onClick": {"openLink": {"url": BUILD_URL}},
                                    }
                                }
                            ]
                        }
                    ]
                },
            ],
        }
    ]

    sendGChatNotification(webhook_url=webhookURL, textMessage=None, cards=cards)
