#!/usr/bin/env python
# encoding: utf-8
from copy import copy
from tornado.testing import gen_test
from tornado.web import Application
from . import RESTTestHandler
from .server import AsyncRESTTestCase


class Handler(RESTTestHandler):
    def default(self):
        self.response({'status': True})

    get = default
    head = default
    post = default
    delete = default
    put = default
    options = default


class TestCopy(AsyncRESTTestCase):
    def get_app(self):
        return Application(handlers=[
            ('/', Handler),
        ])

    @gen_test
    def test_get(self):
        yield self.http_client.get(self.api_url.format("/"))

    @gen_test
    def test_post(self):
        yield self.http_client.post(self.api_url.format("/"), body=True)

    @gen_test
    def test_put(self):
        yield self.http_client.put(self.api_url.format("/"), body=True)

    @gen_test
    def test_delete(self):
        yield self.http_client.delete(self.api_url.format("/"))

    @gen_test
    def test_options(self):
        yield self.http_client.options(self.api_url.format("/"))

    @gen_test
    def test_head(self):
        yield self.http_client.head(self.api_url.format("/"))
