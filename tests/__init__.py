#!/usr/bin/env python
# encoding: utf-8
from tornado.web import RequestHandler

try:
    import ujson as json
except ImportError:
    import json

try:
    b = unicode
except NameError:
    b = str


class RESTTestHandler(RequestHandler):
    def prepare(self):
        self.set_header('Content-Type', 'application/json')

    def response(self, data):
        self.finish(json.dumps(data))
