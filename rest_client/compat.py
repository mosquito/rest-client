# encoding: utf-8
from . import PY2

if PY2:
    b = unicode
    iteritems = lambda x: x.iteritems()
else:
    b = str
    iteritems = lambda x: x.items()


try:
    import ujson as json
except ImportError:
    import json
