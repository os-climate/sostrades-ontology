'''
Copyright 2022 Airbus SAS
Modifications on 2022/11/29-2024/07/10 Copyright 2023 Capgemini

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
import ast
import base64
import copy
import logging
import re
from datetime import datetime, timezone
from importlib import import_module
from logging import Logger
from os import environ, listdir, pathsep, scandir, sep
from os.path import abspath, basename, dirname, isdir, isfile, join, splitext
from pathlib import Path

import git
import pandas as pd
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.sos_processes.processes_factory import SoSProcessFactory

from sos_ontology.core.sos_entities.code_repository import CodeRepository
from sos_ontology.core.sos_entities.parameter import Parameter
from sos_ontology.core.sos_entities.parameter_usage import ParameterUsage
from sos_ontology.core.sos_entities.sos_coupling import SoSCoupling
from sos_ontology.core.sos_entities.sos_discipline import SoSDiscipline
from sos_ontology.core.sos_entities.sos_entity import SoSEntityDict
from sos_ontology.core.sos_entities.sos_process import SoSProcess
from sos_ontology.core.sos_entities.sos_process_repository import SoSProcessRepository
from sos_ontology.core.sos_entities.sos_usecase import SoSUsecase
from sos_ontology.core.sos_toolbox import SoSToolbox


class SoSCodeDataExtractor:
    """
    Class to read and parse Python code to look for entities and links for the ontology
    """

    def __init__(
            self,
            basepath: str = ".",
            logs_dict: dict = {},
            previous_code_repositories_traceability: dict = {},
    ):
        """
        Constructor
        """
        self.toolbox = SoSToolbox()
        self.basepath = basepath
        self.exclusions_list = [
            "__pycache__",
            "__init__.py",
            "chart_post_processing.py",
            ".settings",
            ".git",
            "sostrades_webgui",
            "test",
            "tests",
            ".metadata",
            ".vscode",
            ".idea",
            "node_modules",
            "script_perso",
            ".bin",
            "sos_sandbox",
            "sostrades_webapi",
            "sos_trades_gui",
            "mdotools",
            "gems",
            "infrastructure",
            ".metadata",
            ".gitlab",
            "gemseo",
            ".gitignore",
            "LICENSES",
        ]
        self.path_exclusion_list = [
            join("AppData", "Local", "Continuum", "anaconda3"),
            'sostrades-webgui',
            'sostrades-webapi',
            'sostrades-ontology',
            'sostrades-authapi',
            'gemseo',
        ]
        self.logs_dict = logs_dict

        self.code_repositories = SoSEntityDict()
        self.sos_process_repositories = SoSEntityDict()
        self.sos_processes = SoSEntityDict()
        self.sos_disciplines = SoSEntityDict()
        self.parameters = SoSEntityDict()
        self.parameters_usages = SoSEntityDict()
        self.usecases = SoSEntityDict()
        self.couplings = SoSEntityDict()
        self.current_code_repo = None
        self.current_sos_discipline = None
        self.current_process_repository = None
        self.logger = logging.getLogger("Ontology")

        self.ontology_data_keys = {
            'sos_discipline': [
                'label',
                'type',
                'source',
                'validated',
                'validated_by',
                'last_modification_date',
                'category',
                'definition',
                'icon',
                'version',
            ],
            'process': ['label', 'description', 'category', 'version'],
        }

        # retrieve traceability info concerning code repositories
        self.code_repositories_dict = self.retrieve_code_repositories(
            logger=self.logger,
            previous_code_repo_dict=previous_code_repositories_traceability,
        )

        # self.code_repositories_dict = {
        #     'sostrades-core': self.code_repositories_dict['sostrades-core']
        # }
        print(
            f'Ready to extract info from {len(self.code_repositories_dict.keys())} code repositories'
        )
        print(list(self.code_repositories_dict.keys()))

    def add_to_log(self, category, sub_category=None, message=None, exception=None):
        if self.logs_dict is not None:
            if category not in self.logs_dict:
                if sub_category is None:
                    self.logs_dict[category] = []
                else:
                    self.logs_dict[category] = {}
            if sub_category is not None:
                if sub_category not in self.logs_dict[category]:
                    self.logs_dict[category][sub_category] = []

            if category == "date":
                self.logs_dict[category] = datetime.now(
                ).strftime("%d/%m/%Y %H:%M:%S")
            elif category == "errors":
                error_info = {
                    "message": message,
                }
                if exception is not None:
                    error_info["error"] = f"{type(exception)} - {exception}"
                self.logs_dict[category][sub_category].append(error_info)
            elif category == "details":
                if sub_category == "scannedDirectories":
                    self.logs_dict[category][sub_category].append(message)
            elif category == "ontologyInfo":
                self.logs_dict[category][sub_category].append(
                    {"id": message, "error": exception}
                )
            elif (
                    category == "multiple_parameters_info"
                    or category == "no_parameter_info"
                    or category == "parameter_does_not_exist"
                    or category == "synthesis"
                    or category == "inconsistencies"
                    or category == "duplicateParametersGlossary"
            ):
                self.logs_dict[category][sub_category] = message

    def get_classes_from_parsing_code(self, file):
        # return the list of classes instantiated by the first declaration of
        # function in a Python file
        try:
            with open(file=file, mode="r", encoding="utf-8", errors="ignore") as myfile:
                data = myfile.read()
                p = ast.parse(data)
                classes = [
                     {
                        "name": node.name,
                        "type": [
                            n.id if hasattr(n, "id") else n.attr
                            for n in node.bases
                        ],
                    }
                    for node in ast.walk(p)
                    if isinstance(node, ast.ClassDef)
                ]
                return classes

        except Exception as ex:
            self.add_to_log(
                category="errors",
                sub_category="parsingClassList",
                message=f'Impossible to parse classes from {abspath(file).replace(self.basepath, "")}',
                exception=ex,
            )
            return []

    def get_disc_attributes_from_parsing_code(self, file):
        # return the METADATA dict of the discipline
        metadata = {}
        maturity = ""
        desc_in = {}
        desc_out = {}

        try:
            with open(file=file, mode="r", encoding="utf-8", errors="ignore") as myfile:
                data = myfile.read()
                p = ast.parse(data)
                for node in ast.walk(p):
                    if isinstance(node, ast.ClassDef):
                        for assign in node.body:
                            if isinstance(assign, ast.Assign):
                                if isinstance(assign.targets[0], ast.Name):
                                    if isinstance(assign.value, ast.Dict):
                                        if assign.targets[0].id == "_ontology_data":
                                            try:
                                                metadata = ast.literal_eval(
                                                    assign.value
                                                )
                                            except Exception as ex:
                                                self.add_to_log(
                                                    category="errors",
                                                    sub_category="parsingDiscipline",
                                                    message=f'Impossible to parse _ontology_data from {abspath(file).replace(self.basepath, "")}',
                                                    exception=ex,
                                                )
                                        if assign.targets[0].id == "DESC_IN":
                                            # this check is to avoid error on
                                            # statements where DESC_IN is updated via a
                                            # function
                                            try:
                                                desc_in = ast.literal_eval(
                                                    assign.value)
                                            except Exception as ex:
                                                self.add_to_log(
                                                    category="errors",
                                                    sub_category="parsingDiscipline",
                                                    message=f'Impossible to parse DESC_IN from {abspath(file).replace(self.basepath, "")}',
                                                    exception=ex,
                                                )
                                        if assign.targets[0].id == "DESC_OUT":
                                            # this check is to avoid error on
                                            # statements where DESC_IN is updated via a
                                            # function
                                            try:
                                                desc_out = ast.literal_eval(
                                                    assign.value
                                                )
                                            except Exception as ex:
                                                self.add_to_log(
                                                    category="errors",
                                                    sub_category="parsingDiscipline",
                                                    message=f'Impossible to parse DESC_OUT from {abspath(file).replace(self.basepath, "")}',
                                                    exception=ex,
                                                )
                                    if assign.targets[0].id == "_maturity":
                                        maturity = ast.literal_eval(
                                            assign.value)

        except Exception as ex:
            self.add_to_log(
                category="errors",
                sub_category="parsingDiscipline",
                message=f'Impossible to parse sos discipline {abspath(file).replace(self.basepath, "")}',
                exception=ex,
            )

        return metadata, maturity, desc_in, desc_out

    def get_imports_from_parsing_code(self, file):
        imports = {}
        try:
            with open(file=file, mode="r", encoding="utf-8", errors="ignore") as myfile:
                data = myfile.read()
                p = ast.parse(data)
                for node in ast.walk(p):
                    module = None
                    if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                        if isinstance(node, ast.ImportFrom):
                            module = node.module
                        for n in node.names:
                            imports[n.name] = {
                                "module": module, "name": n.name}
                return imports

        except Exception as ex:
            self.add_to_log(
                category="errors",
                sub_category="parsingImportList",
                message=f'Impossible to parse import list from {abspath(file).replace(self.basepath, "")}',
                exception=ex,
            )
            return {}

    def get_sos_discipline_internal_variables(self, entry, path, model_id):
        attributes = {
            "DESC_IN": {},
            "DESC_OUT": {},
            "maturity": "",
            "_ontology_data": {},
        }

        # retrieve attribute from discipline instanciation
        ee_name = "ExecEngineOntology"
        try:
            mod = import_module(".".join(path.split(".")[:-1:]))
            loaded_discipline = getattr(mod, path.split(".")[-1])

            if (
                    hasattr(loaded_discipline, "DESC_IN")
                    and loaded_discipline.DESC_IN is not None
            ):
                attributes["DESC_IN"] = copy.deepcopy(
                    loaded_discipline.DESC_IN)
            if (
                    hasattr(loaded_discipline, "_data_in")
                    and loaded_discipline.get_data_in() is not None
            ):
                attributes["DESC_IN"].update(
                    copy.deepcopy(loaded_discipline.get_data_in()))
            if (
                    hasattr(loaded_discipline, "DESC_OUT")
                    and loaded_discipline.DESC_OUT is not None
            ):
                attributes["DESC_OUT"] = copy.deepcopy(
                    loaded_discipline.DESC_OUT)
            if (
                    hasattr(loaded_discipline, "_data_out")
                    and loaded_discipline._data_out is not None
            ):
                attributes["DESC_OUT"].update(
                    copy.deepcopy(loaded_discipline._data_out)
                )
            if (
                    hasattr(loaded_discipline, "_maturity")
                    and loaded_discipline._maturity is not None
            ):
                attributes["maturity"] = copy.deepcopy(
                    loaded_discipline._maturity)
            if (
                    hasattr(loaded_discipline, "_ontology_data")
                    and loaded_discipline._ontology_data is not None
            ):
                attributes["_ontology_data"] = copy.deepcopy(
                    loaded_discipline._ontology_data
                )

            else:
                self.add_to_log(
                    category="ontologyInfo",
                    sub_category="discipline",
                    message=f"{model_id}",
                    exception="_ontology_data does not exist",
                )
            try:
                # try to complete information (io_type, ...) by configuring discipline
                # generate ns_list
                ns_list = list(
                    set(
                        [
                            *[
                                disc.get("namespace", None)
                                for disc in attributes["DESC_IN"].values()
                            ],
                            *[
                                disc.get("namespace", None)
                                for disc in attributes["DESC_OUT"].values()
                            ],
                        ]
                    )
                )
                ee = ExecutionEngine(ee_name)
                ee.ns_manager.add_ns_def({ns: ee_name for ns in ns_list})
                builder = ee.factory.get_builder_from_module(entry.name, path)
                ee.factory.set_builders_to_coupling_builder(builder)
                ee.configure()
                loaded_discipline = ee.factory.sos_disciplines[0]
                if loaded_discipline.get_data_in() is not None:
                    attributes["DESC_IN"].update(
                        copy.deepcopy(loaded_discipline.get_data_in())
                    )
                if loaded_discipline.get_data_out() is not None:
                    attributes["DESC_OUT"].update(
                        copy.deepcopy(loaded_discipline.get_data_out())
                    )
            except Exception as ex:
                self.add_to_log(
                    category="errors",
                    sub_category="loadingDiscipline",
                    message=f'Impossible to configure sos discipline {abspath(entry).replace(self.basepath, "")}',
                    exception=ex,
                )
        except Exception as ex:
            self.add_to_log(
                category="errors",
                sub_category="loadingDiscipline",
                message=f'Impossible to import sos discipline {abspath(entry).replace(self.basepath, "")}',
                exception=ex,
            )

        # retrieve info from code parsing
        (
            parsed_ontology_data,
            parsed_maturity,
            parsed_DESC_IN,
            parsed_DESC_OUT,
        ) = self.get_disc_attributes_from_parsing_code(entry)
        if parsed_DESC_IN is not None and parsed_DESC_IN != {}:
            if len(parsed_DESC_IN.keys()) > len(attributes.get("DESC_IN", {}).keys()):
                self.add_to_log(
                    category="errors",
                    sub_category="loadingDiscipline",
                    message=f'Parsed DESC_IN used because it contains more info than loaded DESC_IN for  {abspath(entry).replace(self.basepath, "")}',
                )
                attributes["DESC_IN"] = copy.deepcopy(parsed_DESC_IN)

        if parsed_DESC_OUT is not None and parsed_DESC_OUT != {}:
            if len(parsed_DESC_OUT.keys()) > len(attributes.get("DESC_OUT", {}).keys()):
                self.add_to_log(
                    category="errors",
                    sub_category="loadingDiscipline",
                    message=f'Parsed DESC_OUT used because it contains more info than loaded DESC_OUT for  {abspath(entry).replace(self.basepath, "")}',
                )
                attributes["DESC_OUT"] = copy.deepcopy(parsed_DESC_OUT)

        if attributes["_ontology_data"] == {} and parsed_ontology_data != {}:
            attributes["_ontology_data"] = parsed_ontology_data
        if attributes["maturity"] == "" and parsed_maturity != "":
            attributes["maturity"] = parsed_maturity

        return attributes

    def is_sos_discipline(self, entry):
        imports = self.get_imports_from_parsing_code(entry)
        classes = self.get_classes_from_parsing_code(entry)
        info = {}
        sos_disc = False
        for c in classes:
            class_name = c.get("name", "")
            class_type = c.get("type", [])
            for t in class_type:
                # we verify if this class is imported in the module
                if t in imports:
                    # we load the imported class
                    try:
                        classInstance = getattr(
                            import_module(
                                imports[t]["module"]), imports[t]["name"]
                        )
                        # we retrieve the inheritance_tree
                        inheritance_tree = type.mro(classInstance)
                        # we check if the SoSDiscipline or SoSWrapp (for Execution Engine v4) is present in the
                        # inheritance
                        if any(
                                [
                                    disc_class in [
                                        i.__name__ for i in inheritance_tree]
                                    for disc_class in ['ProxyDiscipline', 'SoSWrapp']
                                ]
                        ):
                            # it is a model !! (an SoSDIscipline)
                            # print(f'{entry.name} is a model !')
                            info = {
                                "name": class_name,
                                "inheritance_tree": [
                                    i.__name__ for i in inheritance_tree
                                ],
                            }
                            sos_disc = True

                    except Exception as ex:
                        self.add_to_log(
                            category="errors",
                            sub_category="isSoSDiscipline",
                            message=f'Error during checking if SoS Discipline for Class {t} of {abspath(entry).replace(self.basepath, "")}',
                            exception=ex,
                        )
        return sos_disc, info

    def add_sos_discipline_and_associated_parameters(self, entry, rootpath, class_info):
        # Fullpath
        fullpath = abspath(entry).replace(abspath(rootpath) + sep, "")

        loadingPath = (
                fullpath.replace(".py", "").replace(
                    sep, ".") + "." + class_info["name"]
        )

        model_id = fullpath.replace(".py", "").replace(sep, ".")
        short_id = entry.name.replace(".py", "") + "." + class_info["name"]
        modelAttributes = self.get_sos_discipline_internal_variables(
            entry, loadingPath, model_id
        )
        disc_label = modelAttributes['_ontology_data'].get('label', short_id)
        if disc_label == model_id:
            disc_label = short_id

        new_sos_discipline = SoSDiscipline(
            id=model_id,
            label=disc_label,
            repository=self.current_code_repo,
            pythonModulePath=fullpath,
            definition=modelAttributes['_ontology_data'].get('definition', ''),
            validated=modelAttributes['_ontology_data'].get('validated', ''),
            type=modelAttributes['_ontology_data'].get('type', ''),
            icon=modelAttributes['_ontology_data'].get('icon', ''),
            documentation=self.get_markdown_documentation(abspath(entry)),
            last_modification_date=modelAttributes['_ontology_data'].get(
                'last_modification_date', ''
            ),
            validated_by=modelAttributes['_ontology_data'].get(
                'validated_by', ''),
            pythonClassInheritance=class_info["inheritance_tree"],
            pythonClass=class_info["name"],
            source=modelAttributes['_ontology_data'].get('source', ''),
            category=modelAttributes['_ontology_data'].get('category', ''),
            version=modelAttributes['_ontology_data'].get('version', ''),
        )
        # add discipline to list
        self.sos_disciplines.add(new_sos_discipline)
        self.current_sos_discipline = new_sos_discipline

        # check ontology keys
        self.check_ontology_keys(
            modelAttributes['_ontology_data'], 'sos_discipline', model_id
        )

        # add input parameters
        self.generate_parameters(
            param_dict=modelAttributes["DESC_IN"],
            io="input",
            discipline_entity=self.current_sos_discipline,
        )

        # add output parameters
        self.generate_parameters(
            param_dict=modelAttributes["DESC_OUT"],
            io="output",
            discipline_entity=self.current_sos_discipline,
        )

    def generate_parameters(self, param_dict, io, discipline_entity):
        # add input parameters
        for param, attributes in param_dict.items():
            # sometimes the parameter name is containing part of a namespace,
            # we need to extract only the final name
            param_id = param
            if not isinstance(param, str):
                if isinstance(param, tuple):
                    param_id = f'{param[0]}.{param[1]}'
                else:
                    print(
                        f'Parameter {param} from discipline {discipline_entity.id} is not a string: {isinstance(param, str)}'
                    )
            else:
                param_name = param_id.split('.')[-1]
                parameter_entity = self.parameters.get(param_name)
                if parameter_entity is None:
                    parameter_entity = Parameter(
                        id=param_name, label=param_name, attributesDict=attributes
                    )
                    self.parameters.add(parameter_entity)

                param_usage_id = f"{discipline_entity.id}_{io}_{param_id}"
                parameter_usage_entity = self.parameters_usages.get(
                    param_usage_id)
                if parameter_usage_entity is None:
                    new_param_usage = ParameterUsage(
                        id=param_usage_id,
                        label=param_usage_id,
                        attributesDict=attributes,
                        parameter=parameter_entity,
                        sos_discipline=discipline_entity,
                    )
                    self.parameters_usages.add(new_param_usage)
                    parameter_entity.add_usage(new_param_usage)
                    parameter_usage_entity = new_param_usage
                else:
                    parameter_usage_entity.updateAttributes(
                        attributesDict=attributes)
                if io == "input":
                    discipline_entity.add_input_parameter_usage(
                        parameter_usage_entity)
                elif io == "output":
                    discipline_entity.add_output_parameter_usage(
                        parameter_usage_entity)

    def generate_sos_disciplines_and_parameters(self, basepath, level, rootpath):
        """This function looks for sos_discipline and associated parameters in all files in directory"""

        with scandir(basepath) as entries:
            for entry in entries:
                if entry.name not in self.exclusions_list:
                    if entry.is_file():
                        if splitext(entry)[1] == ".py":
                            is_sos_disc, class_info = self.is_sos_discipline(
                                entry)
                            if is_sos_disc:
                                self.add_sos_discipline_and_associated_parameters(
                                    entry=entry,
                                    rootpath=rootpath,
                                    class_info=class_info,
                                )

                    if entry.is_dir():
                        if level == 1:
                            self.add_to_log(
                                category="details",
                                sub_category="scannedDirectories",
                                message=abspath(entry).replace(
                                    self.basepath, ""),
                            )
                        self.generate_sos_disciplines_and_parameters(
                            abspath(entry), level + 1, rootpath
                        )

    def generate_process_repository(self, repo, code_repo):
        # retrive corresponding code repository
        label = repo
        description = ""
        try:
            repository_module = import_module(repo)

            if hasattr(repository_module, "label"):
                if (
                        repository_module.label is not None
                        and repository_module.label != ""
                ):
                    label = repository_module.label
            else:
                self.add_to_log(
                    category="ontologyInfo",
                    sub_category="processRepository",
                    message=f"{repo}",
                    exception="label not present in __init__.py",
                )
            if hasattr(repository_module, "description"):
                if (
                        repository_module.description is not None
                        and repository_module.description != ""
                ):
                    description = repository_module.description
            else:
                self.add_to_log(
                    category="ontologyInfo",
                    sub_category="processRepository",
                    message=f"{repo}",
                    exception="description not present in __init__.py",
                )

        except Exception as ex:
            self.add_to_log(
                category="errors",
                sub_category="__init__.py",
                message=f"Impossible to load __init__.py for process repository {repo}",
                exception=ex,
            )

        new_process_repo = SoSProcessRepository(
            id=repo, label=label, description=description, code_repository=code_repo
        )
        self.sos_process_repositories.add(new_process_repo)
        self.current_process_repository = new_process_repo
        code_repo.add_process_repository(new_process_repo)

    def generate_process(self, process):
        repo = self.current_process_repository.id
        ee = ExecutionEngine(f"EE.{repo}.{process}")
        process_path = ""
        documentation = ""
        disciplinesDict = {}
        _ontology_data = {}
        process_module_path = f"{repo}.{process}.process"
        try:
            process_module = import_module(process_module_path)
            process_path = process_module.__file__

            # instantiate process
            try:
                builder = ee.factory.get_builder_from_process(repo, process)
                ee.factory.set_builders_to_coupling_builder(builder)
                ee.configure()

                disciplinesDict = ee.dm.convert_disciplines_dict_with_full_name()

            except Exception as ex:
                self.add_to_log(
                    category="errors",
                    sub_category="loadProcess",
                    message=f"{repo}.{process}",
                    exception=ex,
                )
            # retrieve process ontology info
            try:
                # retrieve process Builder
                processBuilderClass = getattr(process_module, 'ProcessBuilder')
                if hasattr(processBuilderClass, "_ontology_data"):
                    _ontology_data = processBuilderClass._ontology_data

                else:
                    self.add_to_log(
                        category="ontologyInfo",
                        sub_category="process",
                        message=f"{process}",
                        exception="_ontology_data does not exist",
                    )

            except Exception as ex:
                self.add_to_log(
                    category="errors",
                    sub_category="loadProcessBuilder",
                    message=f"Impossible to retrieve process builder for {process}",
                    exception=ex,
                )
        except Exception as ex:
            self.add_to_log(
                category="errors",
                sub_category="loadProcess",
                message=f"{repo}.{process}",
                exception=ex,
            )

        if process_path != "":
            documentation = self.get_markdown_documentation(process_path)
        new_process = SoSProcess(
            id=f"{repo}.{process}",
            label=_ontology_data.get('label', process),
            description=_ontology_data.get('description', ''),
            repository=self.current_process_repository,
            documentation=documentation,
            process_module_path=process_module_path,
            category=_ontology_data.get('category', ''),
            version=_ontology_data.get('version', ''),
        )
        self.current_process_repository.add_process(new_process)
        self.sos_processes.add(new_process)

        # check ontology keys
        self.check_ontology_keys(_ontology_data, 'process', process)

        # add disciplines
        if disciplinesDict != {}:
            for disciplines_list in disciplinesDict.values():
                for discipline in disciplines_list:
                    disc_entity = self.sos_disciplines.get(
                        discipline["model_name_full_path"]
                    )
                    if disc_entity is not None:
                        new_process.add_model(disc_entity)
                        # add parameters
                        # IN
                        self.generate_parameters(
                            param_dict=discipline["reference"].get_data_in(),
                            io="input",
                            discipline_entity=disc_entity,
                        )
                        # OUT
                        self.generate_parameters(
                            param_dict=discipline["reference"].get_data_out(),
                            io="output",
                            discipline_entity=disc_entity,
                        )

                    else:
                        self.add_to_log(
                            category="errors",
                            sub_category="missingSoSDiscipline",
                            message=f'Impossible to find discipline {discipline["model_name_full_path"]}',
                        )

        return new_process, process_path

    def generate_entities_from_code_repositories(self) -> dict:

        # retrieve recursively models and parameters into self.models_with_params_dict
        # iterate over all paths folders
        print(
            "#####################    LOOKING FOR SOS DISCIPLINES AND PARAMETERS    #########################"
        )

        # only code repositories listed in traceability dict will be explored.
        # All code repo must be Git repositories
        for repo_name, repo_dict in self.code_repositories_dict.items():
            path = repo_dict.get('path', None)
            if path is not None:
                # each path is a code repository
                print(f"Scan code repository {path}")
                new_code_repo = CodeRepository(repo_name, repo_name)
                new_code_repo.update_info(repo_dict)
                self.code_repositories.add(new_code_repo)
                self.current_code_repo = new_code_repo
                self.generate_sos_disciplines_and_parameters(path, 0, path)

        # retrieve list of process repository
        print(
            "#####################    LOOKING FOR PROCESSES, USECASES AND COUPLINGS    #########################"
        )
        process_factory = SoSProcessFactory(
            additional_repository_list=[], search_python_path=True
        )
        # Get processes dictionary
        processes_dict = process_factory.get_processes_dict()

        # retrieve list of processes, reference and couplings
        for process_repo_id, processIdList in processes_dict.items():
            code_repo_entity = self.get_code_repository_entity(
                from_process_repo_id=process_repo_id
            )

            if code_repo_entity is not None:
                print('Process Repository', process_repo_id)
                # create process repository
                self.generate_process_repository(
                    process_repo_id, code_repo_entity)

                for process in processIdList:
                    # retrieve disciplines list via processes_treeviews generated by the run of usecases
                    # only usecases that can be configured will be available
                    # print(f"Process {process_repo_id}.{process}")
                    new_process_entity, new_process_path = self.generate_process(
                        process
                    )

                    # generate usecases
                    if new_process_path != "":
                        # construct usecases folder path
                        folder_path = dirname(new_process_path)
                        # match pattern to retrieve usecase files
                        pattern = re.compile(r"^usecase.*\.py")
                        for f in listdir(folder_path):
                            if (
                                    f != "__init__.py"
                                    and f != "process.py"
                                    and f != "__pycache__"
                            ):
                                if pattern.match(f):
                                    usecase_id = f"{process_repo_id}.{process}.{f}"
                                    (
                                        new_usecase_entity,
                                        couplings_list,
                                    ) = self.generate_usecase(
                                        usecase_id, process_entity=new_process_entity
                                    )

                                    # generate couplings
                                    self.generate_couplings(
                                        couplings_list, usecase=new_usecase_entity
                                    )

        print(
            "#####################    LOOKING FOR PARAMETERS GLOSSARY    #########################"
        )
        for repo_dict in self.code_repositories_dict.values():
            path = repo_dict.get('path', None)
            self.retrieve_parameter_glossary_for_code_repository(
                repository_path=path)

        # write log of multiple info for a parameter, no info for parameter and
        # inconsistencies for multiple info
        self.generate_full_extraction_logs()

        return self.logs_dict

    def add_ontology_data_to_parameters(
            self, parameters_glossary_dict, code_repository
    ):
        not_existing_parameters = []
        for parameter_id, ontology_data in parameters_glossary_dict.items():
            # get parameter
            parameter = self.parameters.get(parameter_id)
            if parameter is not None:
                parameter.updateOntologyAttributes(ontology_data)
                parameter.add_code_repository(code_repository)
                parameter.add_code_repository_attributes(
                    code_repository=code_repository, attributesDict=ontology_data
                )
            else:
                # parameter does not exist
                not_existing_parameters.append(parameter_id)
        if len(not_existing_parameters) > 0:
            self.add_to_log(
                category="parameter_does_not_exist",
                sub_category=code_repository.id,
                message=not_existing_parameters,
            )

    def get_markdown_documentation(self, filepath):
        # Manage markdown documentation

        doc_folder_path = join(dirname(filepath), "documentation")
        filename = basename(filepath).split(".")[0]
        markdown_data = ""
        if isdir(doc_folder_path):
            # look for markdown file with extension .markdown or .md
            markdown_list = [
                join(doc_folder_path, md_file)
                for md_file in listdir(doc_folder_path)
                if (
                        (md_file.endswith(r".markdown") or md_file.endswith(r".md"))
                        and md_file.startswith(filename)
                )
            ]

            if len(markdown_list) > 0:
                # build file path
                markdown_filepath = markdown_list[0]

                if isfile(markdown_filepath):
                    markdown_data = ""

                    try:
                        with open(markdown_filepath, "r+t", encoding="utf-8") as f:
                            markdown_data = f.read()

                        # Find file reference in markdown file
                        place_holder = "!\\[(.*)\\]\\((.*)\\)"
                        matches = re.finditer(place_holder, markdown_data)

                        images_base_64 = {}
                        base64_image_tags = []

                        for matche in matches:
                            # Format:
                            # (0) => full matche line
                            # (1) => first group (place holder name)
                            # (2) => second group (image path/name)

                            image_name = matche.group(2)

                            # Convert markdown image link to link to base64
                            # image
                            image_filepath = join(doc_folder_path, image_name)

                            if isfile(image_filepath):
                                image_data = open(image_filepath, "r+b").read()
                                encoded = base64.b64encode(
                                    image_data).decode("utf-8")

                                images_base_64.update({image_name: encoded})

                                # first replace the matches
                                matche_value = matche.group(1)
                                matches_replace = f"![{matche_value}]({image_name})"
                                matches_replace_by = f"![{matche_value}][{image_name}]"

                                base64_image_tag = f"[{image_name}]:data:image/png;base64,{images_base_64[image_name]}"
                                base64_image_tags.append(base64_image_tag)

                                markdown_data = markdown_data.replace(
                                    matches_replace, matches_replace_by
                                )

                        for image_tag in base64_image_tags:
                            markdown_data = f"{markdown_data}\n\n{image_tag}"

                    except Exception as ex:
                        self.add_to_log(
                            category="errors",
                            sub_category="documentation",
                            message=f'Impossible to retrive documentation for {abspath(markdown_filepath).replace(self.basepath, "")}',
                            exception=ex,
                        )
        return markdown_data

    def generate_usecase(self, reference_path, process_entity):
        couplings_list = []
        new_usecase = None
        usecase_id = f"{reference_path}"
        try:
            ref_module = import_module(reference_path.replace(".py", ""))
            loaded_ref = getattr(ref_module, "Study")()
            # configure usecase
            loaded_ref.load_data()
            loaded_ref.execution_engine.configure()
            usecase_name = loaded_ref.study_name
            usecase_id = f"{process_entity.process_module_path}.{usecase_name}"

            #  add run_usecase ?
            new_usecase = SoSUsecase(
                id=usecase_id,
                label=usecase_name,
                description="",
                process=process_entity,
                run_usecase=loaded_ref.run_usecase,
            )
            self.usecases.add(new_usecase)
            process_entity.add_usecase(new_usecase)

            disciplinesDict = loaded_ref.ee.dm.convert_disciplines_dict_with_full_name()
            # couplings_dict = loaded_ref.ee.root_process.export_couplings().to_dict(orient='index')
            couplings_list = (
                loaded_ref.ee.root_process.coupling_structure.graph.get_disciplines_couplings()
            )

            # add disciplines
            if disciplinesDict != {}:
                for discipline_local_name, disciplines_list in disciplinesDict.items():
                    disc_list = []
                    for discipline in disciplines_list:
                        disc_entity = self.sos_disciplines.get(
                            discipline["model_name_full_path"]
                        )
                        if disc_entity is not None:
                            process_entity.add_model(disc_entity)
                            # add parameters
                            # IN
                            self.generate_parameters(
                                param_dict=discipline["reference"].get_data_in(
                                ),
                                io="input",
                                discipline_entity=disc_entity,
                            )
                            # OUT
                            self.generate_parameters(
                                param_dict=discipline["reference"].get_data_out(
                                ),
                                io="output",
                                discipline_entity=disc_entity,
                            )
                            disc_list.append(disc_entity)
                        else:
                            self.add_to_log(
                                category="errors",
                                sub_category="missingSoSDiscipline",
                                message=f'Impossible to find discipline {discipline["model_name_full_path"]}',
                            )
                    new_usecase.add_disciplines(
                        local_discipline_name=discipline_local_name,
                        discipline_entities=disc_list,
                    )

        except Exception as ex:
            self.add_to_log(
                category="errors",
                sub_category="loadUsecase",
                message=f'{usecase_id}',
                exception=ex,
            )
        return new_usecase, couplings_list

    def generate_couplings(self, couplings_list: dict, usecase):

        for coupling in couplings_list:
            disc_from = self.sos_disciplines.get(coupling[0].__module__)
            disc_to = self.sos_disciplines.get(coupling[1].__module__)
            if disc_from is not None and disc_to is not None:
                for coupling_param in coupling[2]:
                    param_name = coupling_param.split(".")[-1]
                    coupling_id = (
                        f"from_{disc_from.id}_to_{disc_to.id}_param_{param_name}"
                    )
                    param_usage_out_id = f"{disc_from.id}_output_{param_name}"
                    param_usage_out = self.parameters_usages.get(
                        param_usage_out_id)
                    param_usage_in_id = f"{disc_to.id}_input_{param_name}"
                    param_usage_in = self.parameters_usages.get(
                        param_usage_in_id)

                    new_coupling = SoSCoupling(
                        id=coupling_id,
                        label=coupling_param,
                        disciplineFrom=disc_from,
                        disciplineTo=disc_to,
                        parameterUsageOut=param_usage_out,
                        parameterUsageIn=param_usage_in,
                        usecase=usecase,
                    )

                    self.couplings.add(new_coupling)

    def check_ontology_keys(self, ontology_data_dict, entity, id):
        for k in ontology_data_dict.keys():
            if k not in self.ontology_data_keys[entity]:
                self.add_to_log(
                    category="errors",
                    sub_category="ontologyKeys",
                    message=f"{entity} - {id}: {k} is not a valid ontology key",
                )

    def retrieve_code_repositories(
            self, logger: Logger, previous_code_repo_dict: dict
    ) -> dict:
        """
        Extract all git code repository with name, path and latest commit SHA
        It excludes repository that are in the list self.path_exclusion_list
        It also excludes repository which have not been modified since last update (SHA is the same)
        :param logger: logger for messages
        :type logger: Logger
        :param previous_code_repo_dict: code_repo_dict from previous extraction
        :type previous_code_repo_dict: dict
        """

        # Regular expression to remove connection info from url when token is
        # used
        INFO_REGEXP = ':\/\/.*@'
        INFO_REPLACE = '://'

        # Regular expression when it is a remote repostory with ssh
        SSH_REGEX =  r'^[a-zA-Z]+@[a-zA-Z0-9.-]+:'
        SSH_REGEX_TO_REPLACE = r'^.*@'
        SSH_REGEX_REPLACE = 'https://'

        BRANCH = 'branch'
        COMMIT = 'commit'
        URL = 'url'
        COMMITTED_DATE = 'committed_date'
        REPO_PATH = 'path'

        code_repo_dict = {}

        # check for PYTHONPATH environment variable
        python_path_libraries = environ.get('PYTHONPATH')

        if python_path_libraries is not None and len(python_path_libraries) > 0:

            # Set to list each library of the PYTHONPATH
            libraries = python_path_libraries.split(pathsep)

            for library_path in libraries:
                if isdir(library_path):
                    if all(
                            [
                                exclude not in library_path
                                for exclude in self.path_exclusion_list
                            ]
                    ):
                        try:
                            repo = git.Repo(
                                path=library_path, search_parent_directories=True
                            )

                            # there is an url
                            if len(repo.remotes) > 0:
                                # Retrieve url and remove connection info from it
                                raw_url = repo.remotes.origin.url
                                url = re.sub(INFO_REGEXP, INFO_REPLACE, raw_url)
                                try:
                                    repo_name = url.split('.git')[0].split('/')[-1]
                                except:
                                    print(
                                        f'Impossible to retrieve repo name from url {url}'
                                    )
                                    repo_name = url
                            else:
                                url = ""
                                repo_name = basename(library_path)
                            if repo.head.is_detached:
                                branch_name = 'detached'
                                commit = repo.head.commit
                                # get tag version (format v0.0.0)
                                tags = [tag.name for tag in repo.tags if tag.name.startswith('v') and tag.commit == commit]
                                if len(tags)>0:
                                    def convert_version(version:str)->list[int]:
                                        return [int(part) for part in version.strip('v').split('.')]

                                    # sort versions
                                    sorted_tags = sorted(tags, key=convert_version)
                                    
                                    branch_name = sorted_tags[-1]
                            else:
                                branch_name = repo.active_branch.name
                                commit = repo.active_branch.commit
                            commited_date = datetime.fromtimestamp(
                                commit.committed_date, timezone.utc
                            )

                            if previous_code_repo_dict.get(repo_name, {}) != {}:
                                previous_commit_hexsha = previous_code_repo_dict[
                                    repo_name
                                ].get(COMMIT, '')
                                if previous_commit_hexsha == commit.hexsha:
                                    print(
                                        f'Code Repository {repo_name} has not been updated since last Ontology update.'
                                    )

                            # Remove trailing .git
                            if url.endswith(".git"):
                                url = url[:-4]
                            # Verify if we are dealing with ssh remote repository and replace by https://
                            if bool(re.match(SSH_REGEX, url)):
                                url = url.replace(":", "/")
                                url = re.sub(SSH_REGEX_TO_REPLACE, SSH_REGEX_REPLACE, url)
                            code_repo_dict[repo_name] = {
                                URL: url,
                                BRANCH: branch_name,
                                COMMIT: commit.hexsha,
                                COMMITTED_DATE: commited_date.strftime(
                                    "%d/%m/%Y %H:%M:%S"
                                ),
                                REPO_PATH: str(Path(library_path)), # Allow to mixed / and \ on windows path of PYTHONPATH. Nothing Change for linux 
                            }

                        except git.exc.InvalidGitRepositoryError:  # type: ignore
                            logger.error(
                                f'{library_path} folder is not a git folder')
                        except Exception as error:
                            logger.error(
                                f'{library_path} folder generates the following error while accessing with git:\n {str(error)}'
                            )

        return code_repo_dict

    def get_code_repository_entity(self, from_process_repo_id: str) -> CodeRepository:
        code_repo_entity = None
        try:
            process_repo_path = dirname(
                import_module(from_process_repo_id).__file__)
            code_repo_path = None
            for repo_dict in self.code_repositories_dict.values():
                path = repo_dict.get('path', None)
                if path in process_repo_path:
                    code_repo_path = path
                    break
            repo_name = code_repo_path.split(sep)[-1]
            code_repo_entity = self.code_repositories.get(repo_name)
        except:
            print(
                f"Impossible to retrieve process repository {from_process_repo_id}")
            self.add_to_log(
                category="errors",
                sub_category="processRepository",
                message=f"Impossible to retrieve process repository {from_process_repo_id}",
            )
        return code_repo_entity

    def retrieve_parameter_glossary_for_code_repository(self, repository_path: str):
        repo_id = repository_path.split(sep)[-1]
        try:
            parameter_glossary_path = join(
                repository_path, "parameters_glossary.csv")
            if isfile(parameter_glossary_path):
                parameters_glossary_df = pd.read_csv(
                    parameter_glossary_path,
                    na_filter=False,
                    encoding="utf-8",
                    encoding_errors="ignore",
                    keep_default_na=False,
                )
                duplicated = parameters_glossary_df.duplicated(
                    subset=['id'], keep='first'
                )
                if any(duplicated.values.tolist()):
                    duplicated_list = parameters_glossary_df.loc[
                        duplicated, 'id'
                    ].values.tolist()
                    print(
                        f'There are {len(duplicated_list)} duplicated parameters in the glossary: {", ".join(duplicated_list)}, they will be ignored'
                    )
                    self.add_to_log(
                        category="errors",
                        sub_category="duplicateParametersGlossary",
                        message={repo_id: duplicated_list},
                    )
                    parameters_glossary_df = parameters_glossary_df.drop_duplicates(
                        subset=['id'], keep='first'
                    )

                parameters_glossary_df = parameters_glossary_df.set_index('id')
                parameters_glossary_dict = parameters_glossary_df.to_dict(
                    "index")

                code_repo_entity = self.code_repositories.get(repo_id)
                self.add_ontology_data_to_parameters(
                    parameters_glossary_dict, code_repo_entity
                )
            else:
                print(f"Parameters glossary does not exist for repo {repo_id}")
                self.add_to_log(
                    category="errors",
                    sub_category="parameterGlossary",
                    message=f"Parameters glossary does not exist for repo {repo_id}",
                    exception=None,
                )
        except Exception as ex:
            print(
                f"Impossible to retrieve parameter glossary for repo {repo_id}")
            self.add_to_log(
                category="errors",
                sub_category="parameterGlossary",
                message=f"Impossible to retrieve parameter glossary for repo {repo_id}",
                exception=ex,
            )

    def generate_full_extraction_logs(self):
        no_parameter_info = {}
        for parameter in self.parameters.sos_entity_dict.values():
            if len(parameter.code_repositories) > 1:
                self.add_to_log(
                    category="multiple_parameters_info",
                    sub_category=parameter.id,
                    message=[repo.id for repo in parameter.code_repositories],
                )

            elif len(parameter.code_repositories) == 0:
                parameter_code_repositories = [
                    instance.sos_discipline.repository.label
                    for instance in parameter.instances_list
                ]
                parameter_code_repositories = list(
                    set(parameter_code_repositories))
                no_parameter_info[parameter.id] = parameter_code_repositories

            datatypeDict = {}
            unitDict = {}
            for parameter_usage in parameter.instances_list:
                unitDict.setdefault(parameter_usage.unit, [])
                unitDict[parameter_usage.unit].append(
                    ('discipline', parameter_usage.sos_discipline.id)
                )

                datatypeDict.setdefault(parameter_usage.datatype, [])
                datatypeDict[parameter_usage.datatype].append(
                    ('discipline', parameter_usage.sos_discipline.id)
                )

            if len(parameter.code_repositories) > 1:
                for repo, attributes in parameter.code_repositories_attributes.items():
                    unitDict.setdefault(attributes['unit'], [])
                    unitDict[attributes['unit']].append(('glossary', repo))

                    datatypeDict.setdefault(attributes['datatype'], [])
                    datatypeDict[attributes['datatype']].append(
                        ('glossary', repo))

            message = {}
            if len(unitDict.keys()) > 1:
                message['unit'] = unitDict
            if len(datatypeDict.keys()) > 1:
                message['datatype'] = datatypeDict

            if message != {}:
                self.add_to_log(
                    category="inconsistencies",
                    sub_category=parameter.id,
                    message=message,
                )

        if no_parameter_info != {}:
            # transform dictionnary from
            # {parameter:[code_repository_list]} to
            # {code_repository:[parameter_list]}

            code_repo_list = list(
                set(
                    [
                        repo_name
                        for repo_list in no_parameter_info.values()
                        for repo_name in repo_list
                    ]
                )
            )
            param_by_code_repo_dict = {
                code_repo: [
                    p
                    for p, repo_list in no_parameter_info.items()
                    if code_repo in repo_list
                ]
                for code_repo in code_repo_list
            }
            if len(param_by_code_repo_dict.keys()) > 0:
                for code_repo, param_list in param_by_code_repo_dict.items():
                    self.add_to_log(
                        category="no_parameter_info",
                        sub_category=code_repo,
                        message=param_list,
                    )

        self.add_to_log(
            category="synthesis",
            sub_category="code_repositories",
            message=self.code_repositories.len(),
        )
        self.add_to_log(
            category="synthesis",
            sub_category="sos_disciplines",
            message=self.sos_disciplines.len(),
        )
        self.add_to_log(
            category="synthesis",
            sub_category="process_repositories",
            message=self.sos_process_repositories.len(),
        )
        self.add_to_log(
            category="synthesis",
            sub_category="sos_processes",
            message=self.sos_processes.len(),
        )
        self.add_to_log(
            category="synthesis",
            sub_category="usecases",
            message=self.usecases.len(),
        )
        self.add_to_log(
            category="synthesis",
            sub_category="couplings",
            message=self.couplings.len(),
        )
        self.add_to_log(
            category="synthesis",
            sub_category="parameters",
            message=self.parameters.len(),
        )

        # add code_repository traceability to log
        self.logs_dict['code_repositories_traceability'] = self.code_repositories_dict
