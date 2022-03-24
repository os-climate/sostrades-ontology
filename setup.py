# coding: utf-8

from setuptools import setup, find_packages
from datetime import date
import os


def __path(filename):
    ''''Build a full absolute path using the given filename

        :params filename : filename to ass to the path of this module
        :returns: full builded path
    '''
    return os.path.join(os.path.dirname(__file__), filename)


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()


# Manage module version using date
today = date.today()

# formating the date as yy.mm.dd
version = today.strftime('%y.%m.%d')

reqs_list = [
    'nose2==0.9.1',
    'rdflib==5.0.0',
    'openpyxl==3.0.9',
    'textdistance==4.2.0',
    'python-gitlab==2.5.0',
    'Flask==1.1.1',
    'jsonpickle==1.4.1',
    'requests==2.25.1',
    'PyYAML==5.1.2',
    'pandas==1.3.0',
    'numpy==1.20.3',
    'datetime==4.3',
    'werkzeug==2.0.1',
    'itsdangerous==2.0.1',
    'table-logger==0.3.6',
    'uvicorn==0.15.0',
    'fastapi==0.70.0',
             ]

setup(
    name='ontology',
    version=version,
    description='Package containing the Ontology data and functions used in SoSTrades project',
    long_description=readme,
    author='Airbus SAS',
    url='https://idlvsrv284.eu.airbus.corp/sostrade/ontology.git',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    include_package_data=True,
    python_requires='>=3.7',
    install_requires=reqs_list
)

