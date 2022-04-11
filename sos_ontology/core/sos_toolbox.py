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

from sos_ontology.core.sos_terminology import SoSTerminology
from shutil import copy, SameFileError
from os import path
from filecmp import cmp
import jsonpickle
from table_logger import TableLogger
import pandas as pd


class SoSToolbox:
    """
    Toolbox Class
    """

    def getID(self, base, name, nodeType):
        id = base
        if name is not None:
            id += name
        if nodeType is not None:
            id += nodeType
        return id

    def array_to_string(self, arrayToConvert):
        if arrayToConvert is not None:
            if isinstance(arrayToConvert, list):
                for v in arrayToConvert:
                    if v is None:
                        arrayToConvert.remove(v)
                    if v == 'null':
                        arrayToConvert.remove(v)
                if arrayToConvert is not None and len(arrayToConvert) > 0:
                    return ',\n'.join([str(i) for i in arrayToConvert])
                else:
                    return ''
            elif (
                isinstance(arrayToConvert, int)
                or isinstance(arrayToConvert, float)
                or isinstance(arrayToConvert, dict)
                or isinstance(arrayToConvert, str)
            ):
                return str(arrayToConvert)
            else:
                print(f'Unknown type for {arrayToConvert}')
                return arrayToConvert
        else:
            return ''

    def replaceFile(self, pathFrom, pathTo, message):
        if isinstance(pathFrom, list):
            existingPathFrom = ''
            for possiblePath in pathFrom:
                if path.exists(f'{possiblePath}'):
                    existingPathFrom = possiblePath
                    break
        elif isinstance(pathFrom, str):
            existingPathFrom = pathFrom

        if path.exists(f'{existingPathFrom}') and path.exists(f'{pathTo}'):
            if cmp(existingPathFrom, pathTo):
                print("Both files seems to be identical, nothing to update")
            else:
                print("Files seems different, update started")
                copy(existingPathFrom, pathTo)
                print(message)

    def saveFileWithBackup(self, sourcePath, destinationPath):
        if isinstance(destinationPath, list):
            existingdestinationPath = ''
            for possiblePath in destinationPath:
                if path.exists(f'{possiblePath}'):
                    existingdestinationPath = possiblePath
                    break
        elif isinstance(destinationPath, str):
            existingdestinationPath = destinationPath

        if path.exists(f'{sourcePath}') and path.exists(f'{existingdestinationPath}'):
            # backup destination file
            try:
                copy(
                    existingdestinationPath,
                    f'{existingdestinationPath.split(".")[0]}_backup.{existingdestinationPath.split(".")[1]}',
                )
            except SameFileError:
                pass

            # copy the file
            try:
                copy(sourcePath, existingdestinationPath)
            except SameFileError:
                pass

    def diffDictKeys(self, diffDict, codeKeys, manualKeys, objectType):
        index = len(diffDict.keys())
        for kc in codeKeys:
            if not (kc in manualKeys):
                index += 1
                diffDict[index] = {
                    'Type': objectType,
                    'Details': 'Exist in code but not in manual Excel file',
                    'ID': kc,
                }

        for km in manualKeys:
            if not (km in codeKeys):
                index += 1
                diffDict[index] = {
                    'Type': objectType,
                    'Details': 'Exist in manual Excel file but not in code file',
                    'ID': km,
                }

        return diffDict

    def write_json(self, json_file_path, dict_to_write, entity):
        if json_file_path is not None:
            with open(json_file_path, 'w+') as outfile:
                outfile.write(jsonpickle.encode(dict_to_write, unpicklable=False))
            print(
                f'Writing of {len(dict_to_write.keys())} {entity} to {json_file_path}'
            )

    def load_json(self, json_file_path, entity):
        loaded_json = None
        if json_file_path is not None:
            try:
                with open(json_file_path, 'r') as outfile:
                    loaded_json = jsonpickle.decode(outfile.read())
                print(f'{len(loaded_json.keys())} {entity} loaded')
            except Exception as ex:
                print(f'{type(ex)} - {ex}')
        return loaded_json

    def getDiffCodeManual(
        self,
        excelDiffFilePath,
        parametersDict,
        modelsDict,
        processDict,
        disciplineDict,
        repoDict,
        excelGlossary,
    ):
        diffDict = {}
        if excelGlossary is not None:

            if parametersDict is not None:
                # we will look for differences between automatic information and manual info for parameters
                headers = excelGlossary.get_sheet_headers('Parameters Terminology')
                parametersManualDict = excelGlossary.get_sheet_dict(
                    'Parameters Terminology', headers, 'Discipline Naming'
                )

                codeKeys = dict.fromkeys(
                    [k['id'] for k in parametersDict.values()], None
                )
                manualKeysList = [
                    k['Discipline Naming'] for k in parametersManualDict.values()
                ]
                for k in parametersManualDict.values():
                    if k['Synonyms'] != '':
                        manualKeysList.append(k['Synonyms'])
                manualKeys = dict.fromkeys(manualKeysList, None)

                diffDict = self.diffDictKeys(
                    diffDict, codeKeys, manualKeys, 'Parameter'
                )

            if disciplineDict is not None:

                headers = excelGlossary.get_sheet_headers('Disciplines Terminology')
                disciplinesManualDict = excelGlossary.get_sheet_dict(
                    'Disciplines Terminology', headers, 'Discipline'
                )

                codeKeys = dict.fromkeys(disciplineDict.keys(), None)
                manualKeys = dict.fromkeys(
                    [k['Discipline'] for k in disciplinesManualDict.values()], None
                )

                diffDict = self.diffDictKeys(
                    diffDict, codeKeys, manualKeys, 'Discipline'
                )

            if processDict is not None:

                headers = excelGlossary.get_sheet_headers('Process Terminology')
                processManualDict = excelGlossary.get_sheet_dict(
                    'Process Terminology', headers, 'Process ID'
                )

                codeKeys = dict.fromkeys([k['id'] for k in processDict.values()], None)
                manualKeys = dict.fromkeys(
                    [k['Process ID'] for k in processManualDict.values()], None
                )

                diffDict = self.diffDictKeys(diffDict, codeKeys, manualKeys, 'Process')

            if repoDict is not None:

                headers = excelGlossary.get_sheet_headers(
                    'Process Repository Terminology'
                )
                repoManualDict = excelGlossary.get_sheet_dict(
                    'Process Repository Terminology', headers, 'Repo ID'
                )

                codeKeys = dict.fromkeys(repoDict.keys(), None)
                manualKeys = dict.fromkeys(
                    [k['Repo ID'] for k in repoManualDict.values()], None
                )

                diffDict = self.diffDictKeys(
                    diffDict, codeKeys, manualKeys, 'Process Repo'
                )

            if modelsDict is not None:

                # we will look for differences between automatic information and manual info for parameters
                headers = excelGlossary.get_sheet_headers('Models Terminology')
                modelsManualDict = excelGlossary.get_sheet_dict(
                    'Models Terminology', headers, ''
                )

                codeKeys = dict.fromkeys(
                    [k['model_id'] for k in modelsDict.values()], None
                )
                manualKeys = dict.fromkeys(
                    [k['Model name in code'] for k in modelsManualDict.values()], None
                )

                diffDict = self.diffDictKeys(diffDict, codeKeys, manualKeys, 'Model')

        xlDiff = SoSTerminology(excelDiffFilePath)
        headers = ['Type', 'Details', 'ID']

        # Create a new sheet and taking care of creating a backup of previous sheet
        diffSheet = xlDiff.create_sheet('Diff', 1)

        # Write the worksheet headers
        xlDiff.write_headers(diffSheet, headers)

        # Fill the new sheet with the terminology data
        rowCount = 2
        for diff in diffDict.values():
            for columnId, columnValue in diff.items():
                col = headers.index(columnId) + 1
                cell = diffSheet.cell(column=col, row=rowCount, value=columnValue)
            rowCount += 1

        # Add an Excel Table to the terminology sheet
        xlDiff.add_xl_table('Diff_table', diffSheet)

        print(
            f'{len(diffDict)} differences between code and Excel Glossary found and written in file {excelDiffFilePath}'
        )

        if parametersDict:
            # add list of parameter id
            paramSheet = xlDiff.create_sheet('Parameter', 2)
            xlDiff.write_headers(paramSheet, ['id'])
            rowCount = 2
            for param in parametersDict.keys():
                cell = paramSheet.cell(column=1, row=rowCount, value=param)
                rowCount += 1
            xlDiff.add_xl_table('Parameter', paramSheet)

        if modelsDict:
            # add list of models id
            modelSheet = xlDiff.create_sheet('Models', 2)
            xlDiff.write_headers(modelSheet, ['id'])
            rowCount = 2
            for param in modelsDict.keys():
                cell = modelSheet.cell(column=1, row=rowCount, value=param)
                rowCount += 1
            xlDiff.add_xl_table('Models', modelSheet)

        xlDiff.workbook.save(excelDiffFilePath)

        return diffDict

    def getDiffRAWAboxManual(self, excelDiffFilePath, SoSRAWaBox, excelGlossary):
        diffDict = {}
        if excelGlossary is not None:

            # retrieve all parameters in Ontology
            parametersDict = SoSRAWaBox.get_all_classes_id_dict(
                SoSRAWaBox.SOS.Parameter
            )
            if parametersDict is not None:
                # we will look for differences between automatic information and manual info for parameters
                headers = excelGlossary.get_sheet_headers('Parameters Terminology')
                parametersManualDict = excelGlossary.get_sheet_dict(
                    'Parameters Terminology', headers, 'Discipline Naming'
                )

                manualKeysList = [
                    k['Discipline Naming'] for k in parametersManualDict.values()
                ]
                for k in parametersManualDict.values():
                    if k['Synonyms'] != '':
                        manualKeysList.append(k['Synonyms'])
                manualKeys = dict.fromkeys(manualKeysList, None)

                diffDict = self.diffDictKeys(
                    diffDict, parametersDict, manualKeys, 'Parameter'
                )

            # retrieve all disciplines in Ontology
            disciplineDict = SoSRAWaBox.get_all_classes_id_dict(
                SoSRAWaBox.SOS.SoSDiscipline
            )
            if disciplineDict is not None:

                headers = excelGlossary.get_sheet_headers('Disciplines Terminology')
                disciplinesManualDict = excelGlossary.get_sheet_dict(
                    'Disciplines Terminology', headers, 'Discipline'
                )

                manualKeys = dict.fromkeys(
                    [k['Discipline'] for k in disciplinesManualDict.values()], None
                )

                diffDict = self.diffDictKeys(
                    diffDict, disciplineDict, manualKeys, 'Discipline'
                )

            # retrieve all disciplines in Ontology
            processDict = SoSRAWaBox.get_all_classes_id_dict(SoSRAWaBox.SOS.SoSProcess)
            if processDict is not None:

                headers = excelGlossary.get_sheet_headers('Process Terminology')
                processManualDict = excelGlossary.get_sheet_dict(
                    'Process Terminology', headers, 'Process ID'
                )

                manualKeys = dict.fromkeys(
                    [k['Process ID'] for k in processManualDict.values()], None
                )

                diffDict = self.diffDictKeys(
                    diffDict, processDict, manualKeys, 'Process'
                )

            # retrieve all repository in Ontology
            repoDict = SoSRAWaBox.get_all_classes_id_dict(
                SoSRAWaBox.SOS.SoSProcessRepository
            )
            if repoDict is not None:

                headers = excelGlossary.get_sheet_headers(
                    'Process Repository Terminology'
                )
                repoManualDict = excelGlossary.get_sheet_dict(
                    'Process Repository Terminology', headers, 'Repo ID'
                )

                manualKeys = dict.fromkeys(
                    [k['Repo ID'] for k in repoManualDict.values()], None
                )

                diffDict = self.diffDictKeys(
                    diffDict, repoDict, manualKeys, 'Process Repo'
                )

            # retrieve all repository in Ontology
            modelsDict = SoSRAWaBox.get_all_classes_id_dict(
                SoSRAWaBox.SOS.SoSDiscipline
            )
            if modelsDict is not None:

                # we will look for differences between automatic information and manual info for parameters
                headers = excelGlossary.get_sheet_headers('Models Terminology')
                modelsManualDict = excelGlossary.get_sheet_dict(
                    'Models Terminology', headers, ''
                )

                manualKeys = dict.fromkeys(
                    [k['Model name in code'] for k in modelsManualDict.values()], None
                )

                diffDict = self.diffDictKeys(diffDict, modelsDict, manualKeys, 'Model')

        xlDiff = SoSTerminology(excelDiffFilePath)
        headers = ['Type', 'Details', 'ID']

        # Create a new sheet and taking care of creating a backup of previous sheet
        diffSheet = xlDiff.create_sheet('Diff', 1)

        # Write the worksheet headers
        xlDiff.write_headers(diffSheet, headers)

        # Fill the new sheet with the terminology data
        rowCount = 2
        for diff in diffDict.values():
            for columnId, columnValue in diff.items():
                col = headers.index(columnId) + 1
                cell = diffSheet.cell(column=col, row=rowCount, value=columnValue)
            rowCount += 1

        # Add an Excel Table to the terminology sheet
        xlDiff.add_xl_table('Diff_table', diffSheet)

        print(
            f'{len(diffDict)} differences between code and Excel Glossary found and written in file {excelDiffFilePath}'
        )

        if parametersDict:
            # add list of parameter id
            paramSheet = xlDiff.create_sheet('Parameter', 2)
            xlDiff.write_headers(paramSheet, ['id'])
            rowCount = 2
            for param in parametersDict.keys():
                cell = paramSheet.cell(column=1, row=rowCount, value=param)
                rowCount += 1
            xlDiff.add_xl_table('Parameter', paramSheet)

        if modelsDict:
            # add list of models id
            modelSheet = xlDiff.create_sheet('Models', 2)
            xlDiff.write_headers(modelSheet, ['id'])
            rowCount = 2
            for param in modelsDict.keys():
                cell = modelSheet.cell(column=1, row=rowCount, value=param)
                rowCount += 1
            xlDiff.add_xl_table('Models', modelSheet)

        xlDiff.workbook.save(excelDiffFilePath)

        return diffDict

    def diffDictElements(self, diffDict, oldDict, newDict):
        # convert dict to be simpler to compare
        oldDictComp = {}
        for key, entityDict in oldDict.items():
            oldDictComp[key] = {e['id'] for e in entityDict[0].values()}
        newDictComp = {}
        for key, entityDict in newDict.items():
            newDictComp[key] = {e['id'] for e in entityDict[0].values()}

        for key, entityDict in oldDictComp.items():
            diffDict[key] = {'new': 0, 'new_list': [], 'removed': 0, 'removed_list': []}
            for id in entityDict:
                if not (id in newDictComp[key]):
                    diffDict[key]['removed'] += 1
                    diffDict[key]['removed_list'].append(id)

        for key, entityDict in newDictComp.items():
            for id in entityDict:
                if not (id in oldDictComp[key]):
                    diffDict[key]['new'] += 1
                    diffDict[key]['new_list'].append(id)

        return diffDict

    def calculate_difference_before_after(
        self, oldOntology, newOntology, ontologyNamespace, logs_dict=None
    ):

        # construct oldOntology dict
        oldOntoDict = {}
        oldOntoDict[
            'Code Repository'
        ] = oldOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.CodeRepository
        )
        oldOntoDict[
            'SoSProcessRepository'
        ] = oldOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.SoSProcessRepository
        )
        oldOntoDict['SoSProcess'] = oldOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.SoSProcess
        )
        oldOntoDict['Parameter'] = oldOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.Parameter
        )
        oldOntoDict['SoSDiscipline'] = oldOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.SoSDiscipline
        )

        # construct newOntology dict
        newOntoDict = {}
        newOntoDict[
            'Code Repository'
        ] = newOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.CodeRepository
        )
        newOntoDict[
            'SoSProcessRepository'
        ] = newOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.SoSProcessRepository
        )
        newOntoDict['SoSProcess'] = newOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.SoSProcess
        )
        newOntoDict['Parameter'] = newOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.Parameter
        )
        newOntoDict['SoSDiscipline'] = newOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.SoSDiscipline
        )

        # calculate updated dict containing differences list
        updatedDict = {}
        self.diffDictElements(
            diffDict=updatedDict, oldDict=oldOntoDict, newDict=newOntoDict
        )

        if logs_dict is not None:
            logs_dict['updatesDetails'] = updatedDict

    def write_logs(
        self, logs_dict, log_file_name, short_log_file_name, full_log_json_path
    ):

        log_file = open(log_file_name, 'wb+')
        short_log_file = open(short_log_file_name, 'wb+')

        # write summary of modification entity by entity
        diffDict = logs_dict['updatesDetails']
        interesting_diff_log = False
        if (
            max(
                [
                    diffDict["new"] + diffDict["removed"]
                    for diffDict in diffDict.values()
                ]
            )
            > 0
        ):
            interesting_diff_log = True

        log_file.write(b'\n\nSummary of entities updated in Ontology\n\n')
        if interesting_diff_log:
            for key, diffDict in diffDict.items():
                if diffDict["new"] > 0 or diffDict["removed"] > 0:
                    message = f' - {key}: '
                    if diffDict["new"] > 0 and diffDict["removed"] > 0:
                        message += (
                            f'{diffDict["new"]} Added, {diffDict["removed"]} Removed\n'
                        )
                    elif diffDict["new"] > 0 and diffDict["removed"] == 0:
                        message += f'{diffDict["new"]} Added\n'
                    elif diffDict["new"] == 0 and diffDict["removed"] > 0:
                        message += f'{diffDict["removed"]} Removed\n'

                    short_log_file.write(bytes(f'{message}', encoding='utf-8'))

                    log_file.write(bytes(f'\n{key}:\n', encoding='utf-8'))
                    added_col_width = max([len(p) for p in diffDict["new_list"]] + [5])
                    removed_col_width = max(
                        [len(p) for p in diffDict["removed_list"]] + [7]
                    )
                    tbl_log = TableLogger(
                        columns=f'Added,Removed',
                        file=log_file,
                        colwidth={
                            "Added": added_col_width,
                            "Removed": removed_col_width,
                        },
                    )
                    max_item = max(diffDict["new"], diffDict["removed"])
                    new_dict = dict(enumerate(diffDict["new_list"]))
                    removed_dict = dict(enumerate(diffDict["removed_list"]))
                    for i in range(max_item):
                        tbl_log(new_dict.get(i, ''), removed_dict.get(i, ''))
                    tbl_log('-' * added_col_width, '-' * removed_col_width)

        else:
            short_log_file.write(b'No changes, nothing to update')
            log_file.write(b'No changes, nothing to update')

        short_log_file.write(b"\n\nWarnings:")
        if 'errors' in logs_dict:
            # write info about processes that are impossible to load
            if "loadProcess" in logs_dict["errors"]:
                if len(logs_dict["errors"]["loadProcess"]) > 0:
                    nb_process = len(logs_dict["errors"]["loadProcess"])
                    short_log_file.write(
                        b"\n - "
                        + bytes(str(nb_process), encoding='utf-8')
                        + b" processes fail to load"
                    )

                    log_file.write(
                        b"\n\n--------------Processes that fail to load:--------------\n\n"
                    )

                    tbl_log = TableLogger(
                        columns=f'Process,Error', file=log_file, default_colwidth=70
                    )
                    for process_error_dict in logs_dict["errors"]["loadProcess"]:
                        tbl_log(
                            process_error_dict['message'], process_error_dict['error']
                        )

            # write info about Usecases that are impossible to load
            if "loadUsecase" in logs_dict["errors"]:
                if len(logs_dict["errors"]["loadUsecase"]) > 0:
                    nb_usecase = len(logs_dict["errors"]["loadUsecase"])
                    short_log_file.write(
                        b"\n - "
                        + bytes(str(nb_usecase), encoding='utf-8')
                        + b" usecases fail to load"
                    )

                    log_file.write(
                        b"\n\n--------------Usecases that fail to load:--------------\n\n"
                    )

                    tbl_log = TableLogger(
                        columns=f'Usecase,Error', file=log_file, default_colwidth=70
                    )
                    for process_error_dict in logs_dict["errors"]["loadUsecase"]:
                        tbl_log(
                            process_error_dict['message'], process_error_dict['error']
                        )

        # write info about ontology info missing
        if "ontologyInfo" in logs_dict:
            log_file.write(
                b"\n\n--------------Missing Ontology info:--------------\n\n"
            )

            for entity, entity_list in logs_dict["ontologyInfo"].items():
                nb_entity = len(set([e['id'] for e in entity_list]))

                short_log_file.write(
                    bytes(
                        f'\n - {nb_entity} {entity} lack ontology info',
                        encoding='utf-8',
                    )
                )

                log_file.write(bytes(f'\n- {entity}:\n', encoding='utf-8'))
                entity_width = max(
                    [len(entity_dict['id']) for entity_dict in entity_list]
                    + [len('Entity')]
                )
                error_width = max(
                    [len(entity_dict['error']) for entity_dict in entity_list]
                    + [len('Error')]
                )
                tbl_log = TableLogger(
                    columns=f'Entity,Error',
                    file=log_file,
                    colwidth={'Entity': entity_width, 'Error': error_width},
                )
                for entity_dict in entity_list:
                    tbl_log(entity_dict['id'], entity_dict['error'])

        # write info when parameter is missing from glossary
        if "no_parameter_info" in logs_dict:
            if logs_dict["no_parameter_info"] != {}:
                nb_param = sum(
                    [
                        len(param_list)
                        for param_list in logs_dict["no_parameter_info"].values()
                    ]
                )
                short_log_file.write(
                    b"\n - "
                    + bytes(str(nb_param), encoding='utf-8')
                    + b" parameters missing in glossary files"
                )

                log_file.write(
                    b"\n\n--------------Parameters missing in Parameter Glossary:--------------\n\n"
                )
                self.log_as_two_columns_table(
                    list_dict=logs_dict["no_parameter_info"],
                    first_col_name='Code Repository',
                    second_col_name='Missing Parameters',
                    log_file=log_file,
                )

        # write info when parameter exists in multiple glossary
        if "multiple_parameters_info" in logs_dict:
            if logs_dict["multiple_parameters_info"] != {}:
                nb_param = len(list(logs_dict["multiple_parameters_info"].keys()))
                short_log_file.write(
                    b"\n - "
                    + bytes(str(nb_param), encoding='utf-8')
                    + b" parameters in multiple code repositories"
                )

                log_file.write(
                    b"\n\n--------------Parameters present in multiple Parameter Glossary:--------------\n\n"
                )
                self.log_as_two_columns_table(
                    list_dict=logs_dict["multiple_parameters_info"],
                    first_col_name='Parameter',
                    second_col_name='Code Repositories',
                    log_file=log_file,
                )

        if "parameter_does_not_exist" in logs_dict:
            if logs_dict["parameter_does_not_exist"] != {}:
                log_file.write(
                    b"\n\n--------------Parameters present in Parameter Glossary but do not exist in the code:--------------\n\n"
                )
                self.log_as_two_columns_table(
                    list_dict=logs_dict["parameter_does_not_exist"],
                    first_col_name='Code Repository',
                    second_col_name='parameter does not exist in code',
                    log_file=log_file,
                )

        if "inconsistencies" in logs_dict:
            if logs_dict["inconsistencies"] != {}:
                log_file.write(
                    b"\n\n--------------Parameter inconsistencies found in the code:--------------\n\n"
                )

                self.log_inconsistencies_as_table(
                    inconsistencies_dict=logs_dict["inconsistencies"], log_file=log_file
                )

        log_file.close()
        short_log_file.close()

        # write logs to JSON
        self.write_json(
            json_file_path=full_log_json_path,
            dict_to_write=logs_dict,
            entity="Logs",
        )

    def update_glossary_from_diff(
        self, diffDict, excelGlossary, parametersDict, modelsDict
    ):
        modified = False
        # Filter only missing info in glossary (glossary can contains more information, only manual operation can remove elements from glossary)
        filteredDiffDict = [
            {'ID': f['ID'], 'Type': f['Type']}
            for f in diffDict.values()
            if f['Details'] != 'Exist in manual Excel file but not in code file'
        ]
        if filteredDiffDict is not None:
            # check if we need to add parameters
            parametersToAdd = [
                p['ID'] for p in filteredDiffDict if p['Type'] == 'Parameter'
            ]
            if len(parametersToAdd):
                excelGlossary.add_list_to_sheet(
                    listToAdd=parametersToAdd,
                    sheetName='Parameters Terminology',
                    columnName='Discipline Naming',
                )
                modified = True
            # check if we need to add process
            processToAdd = [p['ID'] for p in filteredDiffDict if p['Type'] == 'Process']
            if len(processToAdd):
                excelGlossary.add_list_to_sheet(
                    listToAdd=processToAdd,
                    sheetName='Process Terminology',
                    columnName='Process ID',
                )
                modified = True
            # check if we need to add models
            modelsToAdd = [p['ID'] for p in filteredDiffDict if p['Type'] == 'Model']
            if len(modelsToAdd):
                excelGlossary.add_list_to_sheet(
                    listToAdd=modelsToAdd,
                    sheetName='Models Terminology',
                    columnName='Model name in code',
                )
                modified = True
            # check if we need to add process repository
            reposToAdd = [
                p['ID'] for p in filteredDiffDict if p['Type'] == 'Process Repo'
            ]
            if len(reposToAdd):
                excelGlossary.add_list_to_sheet(
                    listToAdd=reposToAdd,
                    sheetName='Process Repository Terminology',
                    columnName='Repo ID',
                )
                modified = True
            # check if we need to add disciplines
            disciplinesToAdd = [
                p['ID'] for p in filteredDiffDict if p['Type'] == 'Discipline'
            ]
            if len(disciplinesToAdd):
                excelGlossary.add_list_to_sheet(
                    listToAdd=disciplinesToAdd,
                    sheetName='Disciplines Terminology',
                    columnName='Discipline',
                )
                modified = True

            if modified:
                if parametersDict:
                    # update list of parameters
                    excelGlossary.update_list_in_sheet(
                        listToUpdate=list(parametersDict.keys()),
                        sheetName='CHECK',
                        columnName='Parameter Name in Code',
                    )

                if modelsDict:
                    # update list of models
                    excelGlossary.update_list_in_sheet(
                        listToUpdate=list(modelsDict.keys()),
                        sheetName='list_models',
                        columnName='Model ID',
                    )

                    # Save modifications
                excelGlossary.workbook.save(excelGlossary.filePath)

    def log_as_two_columns_table(
        self, list_dict, first_col_name, second_col_name, log_file
    ):
        if list_dict != {}:
            max_width_first_col = max([len(k) for k in list_dict.keys()])
            max_width_first_col = max([max_width_first_col, len(first_col_name)])
            max_width_second_col = max(
                [
                    len(param)
                    for param_list in list_dict.values()
                    for param in param_list
                ]
            )
            max_width_second_col = max([max_width_second_col, len(second_col_name)])
            tbl = TableLogger(
                columns=f'{first_col_name},{second_col_name}',
                colwidth={
                    first_col_name: max_width_first_col,
                    second_col_name: max_width_second_col,
                },
                file=log_file,
            )
            for code_repo, param_list in list_dict.items():
                for i, param in enumerate(param_list):
                    if i == 0:
                        tbl(code_repo, param)
                    else:
                        tbl('', param)
                tbl('-' * max_width_first_col, '-' * max_width_second_col)

    def log_as_three_columns_table(self, inconsistencies_dict, log_file):
        if inconsistencies_dict != {}:
            inconsistencies_df = pd.DataFrame(
                columns={'Disciplines', 'Type', 'Parameter'}
            )
            for parameter, specific_dict in inconsistencies_dict.items():
                first_row = True
                for inconsistency_type, values_dict in specific_dict.items():
                    for value, disciplines_list in values_dict.items():
                        for i, discipline in enumerate(disciplines_list):
                            parameter_name = ''
                            if first_row:
                                parameter_name = parameter
                                first_row = False
                            if i == 0:
                                inconsistencies_df.append(
                                    [
                                        {
                                            'Parameter': parameter_name,
                                            'Type': f'{inconsistency_type}: {value}',
                                            'Disciplines': discipline,
                                        }
                                    ]
                                )
                            else:
                                inconsistencies_df.append(
                                    [
                                        {
                                            'Parameter': parameter_name,
                                            'Type': '',
                                            'Disciplines': discipline,
                                        }
                                    ]
                                )

            max_width_first_col = max([len(k) for k in inconsistencies_df['Parameter']])
            max_width_first_col = max([max_width_first_col, len('Parameter')])
            max_width_second_col = max([len(k) for k in inconsistencies_df['Type']])
            max_width_second_col = max([max_width_second_col, len('Type')])
            max_width_third_col = max(
                [len(k) for k in inconsistencies_df['Disciplines']]
            )
            max_width_third_col = max([max_width_third_col, len('Disciplines')])
            tbl = TableLogger(
                columns='Parameter,Type,Disciplines',
                colwidth={
                    'Parameter': inconsistencies_df['Parameter'].values.to_list(),
                    'Type': inconsistencies_df['Type'].values.to_list(),
                    'Disciplines': inconsistencies_df['Disciplines'].values.to_list(),
                },
                file=log_file,
            )
            for index, row in inconsistencies_df.iterrows():
                if row['Parameter'] != '':
                    tbl(
                        '-' * max_width_first_col,
                        '-' * max_width_second_col,
                        '-' * max_width_third_col,
                    )
                tbl(row['Parameter'], row['Type'], row['Disciplines'])
            tbl(
                '-' * max_width_first_col,
                '-' * max_width_second_col,
                '-' * max_width_third_col,
            )
