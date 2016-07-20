#!/usr/bin/env python
# encoding: utf-8
from setuptools import setup, find_packages
import rest_client
import sys


requires = [
    'tornado',
]


if sys.version_info < (3,):
    requires.append('futures')


setup(
    name='rest-client',
    version=rest_client.__version__,
    author=rest_client.__author__,
    url="https://github.com/mosquito/rest-client",
    author_email=rest_client.author_info[1],
    license="MIT",
    description="RESTful Client for tornado",
    platforms="all",
    classifiers=[
        'Environment :: Console',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests']),
    install_requires=requires,
)


