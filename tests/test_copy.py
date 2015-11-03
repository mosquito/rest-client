#!/usr/bin/env python
# encoding: utf-8
from copy import copy
from tornado.testing import gen_test
from tornado.web import Application
from . import RESTTestHandler
from .server import AsyncRESTTestCase


class Handler(RESTTestHandler):
    COOKIES = [
        (('foo', 'baz'), dict(expires_days=20)),
        (('bar', '*'), dict(expires_days=20)),
        (('spam', 'egg'), dict()),
    ]

    def get(self, *args, **kwargs):
        for args, kwargs in self.COOKIES:
            self.set_cookie(*args, **kwargs)

        self.response({})

    def post(self, *args, **kwargs):
        assert self.get_cookie('foo') == 'baz'
        assert self.get_cookie('bar') == '*'
        assert self.get_cookie('spam') == 'egg'

        self.response({})


class TestCopy(AsyncRESTTestCase):
    def get_app(self):
        return Application(handlers=[
            ('/', Handler),
        ])

    @gen_test
    def test_copy(self):
        client = self.get_http_client()

        yield client.get(self.api_url.format("/"))

        clone = copy(client)
        assert client is not clone

        yield clone.post(self.api_url.format("/"), body={})


