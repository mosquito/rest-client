#!/usr/bin/env python
# encoding: utf-8
import sys

PY2 = (sys.version_info < (3,))

try:
    __import__('__pypy__')
    IS_PYPY = True
except ImportError:
    IS_PYPY = False

author_info = ("Dmitry Orlov", "me@mosquito.su")
version_info = (0, 3, 1)

__version__ = ".".join(map(str, version_info))
__author__ = "{0} <{1}>".format(*author_info)


