#!/usr/bin/env python
# encoding: utf-8
from tornado.testing import gen_test
from tornado.web import Application
from . import RESTTestHandler, AsyncRESTTestCase


class CookieHandler(RESTTestHandler):
    COOKIES = [
        (('foo', 'baz'), dict(expires_days=20)),
        (('bar', '*'), dict(expires_days=20)),
        (('spam', 'egg'), dict()),
    ]

    def get(self, *args, **kwargs):
        for args, kwargs in self.COOKIES:
            self.set_cookie(*args, **kwargs)

        self.response([])

    def post(self, *args, **kwargs):
        assert self.get_cookie('foo') == 'baz'
        assert self.get_cookie('bar') == '*'
        assert self.get_cookie('spam') == 'egg'

        self.response({})


class TestCookies(AsyncRESTTestCase):
    def get_app(self):
        return Application(handlers=[
            ('/', CookieHandler),
        ])

    @gen_test
    def test_cookie(self):
        yield self.http_client.get(self.api_url.format("/"))
        yield self.http_client.post(self.api_url.format("/"), body={})

    @gen_test
    def test_freeze(self):
        yield self.http_client.get(self.api_url.format("/"), freeze=True)
        assert not len(self.http_client._cookies)

    @gen_test
    def test_fail(self):
        response = yield self.http_client.put(self.api_url.format("/"), fail=False)
        assert response.fail
