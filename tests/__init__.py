#!/usr/bin/env python
# encoding: utf-8
import ujson
from tornado.web import RequestHandler


class RESTTestHandler(RequestHandler):
    def prepare(self):
        self.set_header('Content-Type', 'application/json')

    def response(self, data):
        self.finish(ujson.dumps(data))
