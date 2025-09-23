'''
Copyright 2022 Airbus SAS
Modifications on 2024/06/07 Copyright 2024 Capgemini
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

import jsonpickle


class SimpleTableLogger:
    """Simple replacement for table-logger with basic formatting capabilities"""

    def __init__(self, columns, file=None, colwidth=None, default_colwidth=20):
        self.columns = columns.split(',') if isinstance(columns, str) else columns
        self.file = file
        self.colwidth = colwidth or {}
        self.default_colwidth = default_colwidth

        # Calculate column widths
        self.column_widths = {}
        for col in self.columns:
            if col in self.colwidth:
                self.column_widths[col] = self.colwidth[col]
            else:
                self.column_widths[col] = max(len(col), self.default_colwidth)

        # Write header
        self._write_header()

    def _write_header(self):
        """Write table header with column names and top border"""
        header_parts = []
        separator_parts = []
        top_border_parts = []

        for col in self.columns:
            width = self.column_widths[col]
            header_parts.append(col.ljust(width))
            separator_parts.append('-' * width)
            top_border_parts.append('-' * width)

        # Top border
        top_border_line = '+-' + '-+-'.join(top_border_parts) + '-+\n'
        # Header with side borders
        header_line = '| ' + ' | '.join(header_parts) + ' |\n'
        # Header separator with side borders
        separator_line = '+-' + '-+-'.join(separator_parts) + '-+\n'

        if self.file:
            self.file.write(top_border_line.encode('utf-8'))
            self.file.write(header_line.encode('utf-8'))
            self.file.write(separator_line.encode('utf-8'))
        else:
            print(top_border_line, end='')
            print(header_line, end='')
            print(separator_line, end='')

    def __call__(self, *args):
        """Log a row of data"""
        row_parts = []

        for i, (col, value) in enumerate(zip(self.columns, args)):
            if i < len(args):
                str_value = str(value) if value is not None else ''
                width = self.column_widths[col]

                # Handle multi-line values
                if '\n' in str_value:
                    lines = str_value.split('\n')
                    # For multi-line, just use the first line for the main row
                    formatted_value = lines[0][:width].ljust(width)
                else:
                    formatted_value = str_value[:width].ljust(width)

                row_parts.append(formatted_value)
            else:
                row_parts.append(' ' * self.column_widths[col])

        row_line = '| ' + ' | '.join(row_parts) + ' |\n'

        if self.file:
            self.file.write(row_line.encode('utf-8'))
        else:
            print(row_line, end='')

        # Handle multi-line values - write additional lines
        max_lines = 1
        for i, value in enumerate(args):
            if i < len(self.columns) and value is not None:
                str_value = str(value)
                if '\n' in str_value:
                    max_lines = max(max_lines, len(str_value.split('\n')))

        # Write additional lines for multi-line content
        for line_num in range(1, max_lines):
            row_parts = []
            for i, (col, value) in enumerate(zip(self.columns, args)):
                if i < len(args) and value is not None:
                    str_value = str(value)
                    if '\n' in str_value:
                        lines = str_value.split('\n')
                        if line_num < len(lines):
                            width = self.column_widths[col]
                            formatted_value = lines[line_num][:width].ljust(width)
                        else:
                            formatted_value = ' ' * self.column_widths[col]
                    else:
                        formatted_value = ' ' * self.column_widths[col]
                else:
                    formatted_value = ' ' * self.column_widths[col]
                row_parts.append(formatted_value)

            row_line = '| ' + ' | '.join(row_parts) + ' |\n'
            if self.file:
                self.file.write(row_line.encode('utf-8'))
            else:
                print(row_line, end='')

    def separator(self, columns=None):
        """
        Write a separator row for the specified columns or all columns
        
        Args:
            columns (list, optional): List of column names to add separators for.
                                    If None, separates all columns.

        """
        separator_parts = []
        junction_chars = []

        for i, col in enumerate(self.columns):
            width = self.column_widths[col]
            if columns is None or col in columns:
                # Add separator for this column
                separator_parts.append('-' * width)
                # Junction character depends on whether this column has separator
                junction_chars.append('-')
            else:
                # Add empty space for this column
                separator_parts.append(' ' * width)
                # Junction character is space for non-separator columns
                junction_chars.append(' ')

        # Build the row with appropriate junction characters
        row_line = '+'
        for i, (part, junction_char) in enumerate(zip(separator_parts, junction_chars)):
            row_line += junction_char + part + junction_char
            if i < len(separator_parts) - 1:
                row_line += '+'
        row_line += '+\n'

        if self.file:
            self.file.write(row_line.encode('utf-8'))
        else:
            print(row_line, end='')


class SoSToolbox:
    """Toolbox Class"""

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
            elif isinstance(arrayToConvert, (int | float | dict | str)):
                return str(arrayToConvert)
            else:
                print(f'Unknown type for {arrayToConvert}')
                return arrayToConvert
        else:
            return ''

    def write_json(self, json_file_path, dict_to_write, entity):
        if json_file_path is not None:
            with open(json_file_path, 'w+') as outfile:
                outfile.write(jsonpickle.encode(dict_to_write, unpicklable=False))
            print(
                f'Writing of {len(dict_to_write.keys())} {entity} to {json_file_path}',
            )

    def load_json(self, json_file_path, entity):
        loaded_json = None
        if json_file_path is not None:
            try:
                with open(json_file_path) as outfile:
                    loaded_json = jsonpickle.decode(outfile.read())
                print(f'{len(loaded_json.keys())} {entity} loaded')
            except Exception as ex:
                print(f'{type(ex)} - {ex}')
        return loaded_json

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
                if id not in newDictComp[key]:
                    diffDict[key]['removed'] += 1
                    diffDict[key]['removed_list'].append(id)

        for key, entityDict in newDictComp.items():
            for id in entityDict:
                if id not in oldDictComp[key]:
                    diffDict[key]['new'] += 1
                    diffDict[key]['new_list'].append(id)

        return diffDict

    def calculate_difference_before_after(
        self, oldOntology, newOntology, ontologyNamespace, logs_dict=None,
    ):

        # construct oldOntology dict
        oldOntoDict = {}
        oldOntoDict[
            'Code Repository'
        ] = oldOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.CodeRepository,
        )
        oldOntoDict[
            'SoSProcessRepository'
        ] = oldOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.SoSProcessRepository,
        )
        oldOntoDict['SoSProcess'] = oldOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.SoSProcess,
        )
        oldOntoDict['Parameter'] = oldOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.Parameter,
        )
        oldOntoDict['SoSDiscipline'] = oldOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.SoSDiscipline,
        )

        # construct newOntology dict
        newOntoDict = {}
        newOntoDict[
            'Code Repository'
        ] = newOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.CodeRepository,
        )
        newOntoDict[
            'SoSProcessRepository'
        ] = newOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.SoSProcessRepository,
        )
        newOntoDict['SoSProcess'] = newOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.SoSProcess,
        )
        newOntoDict['Parameter'] = newOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.Parameter,
        )
        newOntoDict['SoSDiscipline'] = newOntology.retrieve_classes_dict_and_attributes(
            ontologyNamespace.SoSDiscipline,
        )

        # calculate updated dict containing differences list
        updatedDict = {}
        self.diffDictElements(
            diffDict=updatedDict, oldDict=oldOntoDict, newDict=newOntoDict,
        )

        if logs_dict is not None:
            logs_dict['updatesDetails'] = updatedDict

    def write_logs(
        self, logs_dict, log_file_name, short_log_file_name, full_log_json_path,
    ):
        with open(log_file_name, 'wb+') as log_file, open(short_log_file_name, 'wb+') as short_log_file:

            # write summary of modification entity by entity
            diffDict = logs_dict['updatesDetails']
            interesting_diff_log = False
            if (
                max(
                    [
                        diffDict["new"] + diffDict["removed"]
                        for diffDict in diffDict.values()
                    ],
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
                            [len(p) for p in diffDict["removed_list"]] + [7],
                        )
                        tbl_log = SimpleTableLogger(
                            columns='Added,Removed',
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
                        tbl_log.separator()

            else:
                short_log_file.write(b'No changes, nothing to update')
                log_file.write(b'No changes, nothing to update')

            short_log_file.write(b"\n\nWarnings:")
            if 'errors' in logs_dict:
                # write info about processes that are impossible to load
                if "loadProcess" in logs_dict["errors"] and len(logs_dict["errors"]["loadProcess"]) > 0:
                    nb_process = len(logs_dict["errors"]["loadProcess"])
                    short_log_file.write(
                        b"\n - "
                        + bytes(str(nb_process), encoding='utf-8')
                        + b" processes fail to load",
                    )

                    log_file.write(
                        b"\n\n--------------Processes that fail to load:--------------\n\n",
                    )

                    tbl_log = SimpleTableLogger(
                        columns='Process,Error', file=log_file, default_colwidth=70,
                    )
                    for process_error_dict in logs_dict["errors"]["loadProcess"]:
                        tbl_log(
                            process_error_dict['message'], process_error_dict['error'],
                        )
                    tbl_log.separator()

                # write info about Usecases that are impossible to load
                if "loadUsecase" in logs_dict["errors"] and len(logs_dict["errors"]["loadUsecase"]) > 0:
                    nb_usecase = len(logs_dict["errors"]["loadUsecase"])
                    short_log_file.write(
                        b"\n - "
                        + bytes(str(nb_usecase), encoding='utf-8')
                        + b" usecases fail to load",
                    )

                    log_file.write(
                        b"\n\n--------------Usecases that fail to load:--------------\n\n",
                    )

                    tbl_log = SimpleTableLogger(
                        columns='Usecase,Error', file=log_file, default_colwidth=70,
                    )
                    for process_error_dict in logs_dict["errors"]["loadUsecase"]:
                        tbl_log(
                            process_error_dict['message'], process_error_dict['error'],
                        )
                    tbl_log.separator()

            # write info about ontology info missing
            if "ontologyInfo" in logs_dict:
                log_file.write(
                    b"\n\n--------------Missing Ontology info:--------------\n\n",
                )

                for entity, entity_list in logs_dict["ontologyInfo"].items():
                    nb_entity = len(set([e['id'] for e in entity_list]))

                    short_log_file.write(
                        bytes(
                            f'\n - {nb_entity} {entity} lack ontology info',
                            encoding='utf-8',
                        ),
                    )

                    log_file.write(bytes(f'\n- {entity}:\n', encoding='utf-8'))
                    entity_width = max(
                        [len(entity_dict['id']) for entity_dict in entity_list]
                        + [len('Entity')],
                    )
                    error_width = max(
                        [len(entity_dict['error']) for entity_dict in entity_list]
                        + [len('Error')],
                    )
                    tbl_log = SimpleTableLogger(
                        columns='Entity,Error',
                        file=log_file,
                        colwidth={'Entity': entity_width, 'Error': error_width},
                    )
                    for entity_dict in entity_list:
                        tbl_log(entity_dict['id'], entity_dict['error'])
                    tbl_log.separator()

            # write info when parameter is missing from glossary
            if "no_parameter_info" in logs_dict and logs_dict["no_parameter_info"] != {}:
                nb_param = sum(
                    [
                        len(param_list)
                        for param_list in logs_dict["no_parameter_info"].values()
                    ],
                )
                short_log_file.write(
                    b"\n - "
                    + bytes(str(nb_param), encoding='utf-8')
                    + b" parameters missing in glossary files",
                )

                log_file.write(
                    b"\n\n--------------Parameters missing in Parameter Glossary:--------------\n\n",
                )
                self.log_as_two_columns_table(
                    list_dict=logs_dict["no_parameter_info"],
                    first_col_name='Code Repository',
                    second_col_name='Missing Parameters',
                    log_file=log_file,
                )

            # write info when parameter exists in multiple glossary
            if "multiple_parameters_info" in logs_dict and logs_dict["multiple_parameters_info"] != {}:
                nb_param = len(list(logs_dict["multiple_parameters_info"].keys()))
                short_log_file.write(
                    b"\n - "
                    + bytes(str(nb_param), encoding='utf-8')
                    + b" parameters in multiple code repositories",
                )

                log_file.write(
                    b"\n\n--------------Parameters present in multiple Parameter Glossary:--------------\n\n",
                )
                self.log_as_two_columns_table(
                    list_dict=logs_dict["multiple_parameters_info"],
                    first_col_name='Parameter',
                    second_col_name='Code Repositories',
                    log_file=log_file,
                )

            if "parameter_does_not_exist" in logs_dict and logs_dict["parameter_does_not_exist"] != {}:
                log_file.write(
                    b"\n\n--------------Parameters present in Parameter Glossary but do not exist in the code:--------------\n\n",
                )
                self.log_as_two_columns_table(
                    list_dict=logs_dict["parameter_does_not_exist"],
                    first_col_name='Code Repository',
                    second_col_name='parameter does not exist in code',
                    log_file=log_file,
                )

            if "inconsistencies" in logs_dict and logs_dict["inconsistencies"] != {}:
                log_file.write(
                    b"\n\n--------------Parameter inconsistencies found in the code:--------------\n\n",
                )

                self.log_inconsistencies_as_table(
                    unsorted_inconsistencies_dict=logs_dict["inconsistencies"],
                    log_file=log_file,
                )

        # write logs to JSON
        self.write_json(
            json_file_path=full_log_json_path,
            dict_to_write=logs_dict,
            entity="Logs",
        )

    def log_as_two_columns_table(
        self, list_dict, first_col_name, second_col_name, log_file,
    ):
        if list_dict != {}:
            max_width_first_col = max([len(k) for k in list_dict])
            max_width_first_col = max([max_width_first_col, len(first_col_name)])
            max_width_second_col = max(
                [
                    len(param)
                    for param_list in list_dict.values()
                    for param in param_list
                ],
            )
            max_width_second_col = max([max_width_second_col, len(second_col_name)])
            tbl = SimpleTableLogger(
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
                tbl.separator()

    def log_inconsistencies_as_table(self, unsorted_inconsistencies_dict, log_file):
        if unsorted_inconsistencies_dict != {}:
            param_sorted = list(sorted(unsorted_inconsistencies_dict.keys()))
            inconsistencies_dict = {
                k: unsorted_inconsistencies_dict[k] for k in param_sorted
            }

            first_col_elements = ['Parameter']
            second_col_elements = ['Inconsistent Info']
            third_col_elements = ['Discipline / Glossary']
            for param, param_dict in inconsistencies_dict.items():
                first_col_elements.append(param)
                for inconsistency_type, values_dict in param_dict.items():
                    second_col_elements.append(inconsistency_type)
                    for value, disciplines_list in values_dict.items():
                        disc_count = len(
                            [t[1] for t in disciplines_list if t[0] == 'discipline'],
                        )
                        glossary_count = len(
                            [t[1] for t in disciplines_list if t[0] == 'glossary'],
                        )
                        element_message_list = []
                        if disc_count > 0:
                            element_message_list.append(
                                f'{value}: {disc_count} disciplines',
                            )
                        if glossary_count > 0:
                            element_message_list.append(
                                f'{value}: {glossary_count} glossaries',
                            )
                        if len(element_message_list) > 0:
                            third_col_elements.append('\n'.join(element_message_list))

            max_width_first_col = max([len(k) for k in first_col_elements])
            max_width_second_col = max([len(k) for k in second_col_elements])
            max_width_third_col = max([len(k) for k in third_col_elements])

            tbl = SimpleTableLogger(
                columns='Parameter,Type,Discipline / Glossary',
                colwidth={
                    'Parameter': max_width_first_col,
                    'Inconsistent Info': max_width_second_col,
                    'Discipline / Glossary': max_width_third_col,
                },
                file=log_file,
            )

            for parameter, param_dict in inconsistencies_dict.items():
                first_row_param = True
                for inconsistency_type_count, (inconsistency_type, values_dict) in enumerate(param_dict.items()):
                    first_row_type = True
                    for value, disciplines_list in values_dict.items():

                        disc_count = len(
                            [t[1] for t in disciplines_list if t[0] == 'discipline'],
                        )
                        glossary_count = len(
                            [t[1] for t in disciplines_list if t[0] == 'glossary'],
                        )
                        element_message_list = []
                        if disc_count > 0:
                            element_message_list.append(
                                f'{value}: {disc_count} disciplines',
                            )
                        if glossary_count > 0:
                            element_message_list.append(
                                f'{value}: {glossary_count} glossaries',
                            )

                        if first_row_param:
                            first_row_param = False
                            first_row_type = False
                            tbl(
                                parameter,
                                f'{inconsistency_type}',
                                '\n'.join(element_message_list),
                            )
                        elif first_row_type:
                            first_row_type = False
                            tbl(
                                '',
                                f'{inconsistency_type}',
                                '\n'.join(element_message_list),
                            )

                        else:
                            tbl(
                                '',
                                '',
                                f'{value}: {len(disciplines_list)} disciplines',
                            )
                    if inconsistency_type_count + 1 < len(param_dict.keys()):
                        tbl.separator(['Type', 'Discipline / Glossary'])
                tbl.separator()
