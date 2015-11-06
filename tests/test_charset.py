#!/usr/bin/env python
# encoding: utf-8
from tornado.testing import gen_test
from tornado.web import Application, RequestHandler
from .server import AsyncRESTTestCase


class Handler(RequestHandler):
    S = u"test\u0440\u0430\u0437\u0440\u0430\u0437"

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