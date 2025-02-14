'''
Copyright 2025 Capgemini
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
from __future__ import annotations

import cProfile
import io
import pstats
from time import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import logging


def copy_file(src_path, dst_path):
    """Copies file from src_path to dst_path without using shutil."""
    with open(src_path, "rb") as src_file, open(dst_path, "wb") as dst_file:
        dst_file.write(src_file.read())

def time_function(logger: logging.Logger | None = None):
    """
    This decorator times another function and logs time spend in logger given as argument (if any)
    """

    def inner(func):
        def wrapper_function(*args, **kwargs):
            """Fonction wrapper"""
            t_start = time()
            return_args = func(*args, **kwargs)
            t_end = time()
            execution_time = t_end - t_start
            if logger is not None:
                logger.info(f"Execution time {func.__name__}: {execution_time:.4f}s")
            else:
                print(f"Execution time {func.__name__}: {execution_time:.4f}s")
            return return_args

        return wrapper_function

    return inner

def cprofile_function(logger: logging.Logger | None = None):
    """
    This decorator cprofiles another function and logs result in logger given as argument (if any)
    """

    def inner(func):
        def wrapper_function(*args, **kwargs):
            """Fonction wrapper"""
            profiler = cProfile.Profile()
            profiler.enable()
            return_args = func(*args, **kwargs)
            profiler.disable()
            profiling_output = io.StringIO()
            stats = pstats.Stats(profiler, stream=profiling_output)
            stats.sort_stats(pstats.SortKey.CUMULATIVE)
            stats.print_stats()

            if logger is not None:
                logger.info(f"Execution time {func.__name__}:\n{profiling_output.getvalue()}")
            else:
                print(f"Execution time {func.__name__}:\n{profiling_output.getvalue()}")
            return return_args

        return wrapper_function

    return inner
