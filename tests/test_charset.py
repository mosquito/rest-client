#!/usr/bin/env python
# encoding: utf-8
from rest_client import PY2
from tornado.testing import gen_test
from tornado.web import Application, RequestHandler
from .server import AsyncRESTTestCase


class Handler(RequestHandler):
    if PY2:
        S = '\xd0\x9f\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82 \xd0\xbc\xd0\xb8\xd1\x80'.decode('utf-8')
    else:
        S = 'Привет мир'

    def get(self):
        self.set_header('Content-Type', 'text/plain; charset=utf-8')
        self.write(self.S.encode('utf-8'))


class TestCopy(AsyncRESTTestCase):
    def get_app(self):
        return Application(handlers=[
            ('/', Handler),
        ])

    @gen_test
    def test_get(self):
        response = yield self.http_client.get(self.api_url.format("/"))
        assert response.body == Handler.S