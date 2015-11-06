#!/usr/bin/env python
# encoding: utf-8
import sys

PY2 = (sys.version_info < (3,))

author_info = ("Dmitry Orlov", "me@mosquito.su")
version_info = (0, 1, 9)

__version__ = ".".join(map(str, version_info))
__author__ = "{0} <{1}>".format(*author_info)


