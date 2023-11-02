# coding: utf-8

from setuptools import setup, find_packages
from datetime import date


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

# Read the requirements.in file and extract the required dependencies
with open('requirements.in', 'r') as requirements_file:
    reqs_list = [line.strip() for line in requirements_file if line.strip()]

# Manage module version using date
today = date.today()

# formating the date as yy.mm.dd
version = today.strftime('%y.%m.%d')

setup(
    name='ontology',
    version=version,
    description='Package containing the Ontology data and functions used in SoSTrades project',
    long_description=readme,
    author='Airbus SAS, Capgemini',
    url='https://github.com/os-climate/sostrades-ontology',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    include_package_data=True,
    python_requires='>=3.9',
    install_requires=reqs_list,
)
