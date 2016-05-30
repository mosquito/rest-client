#!/usr/bin/env python
# encoding: utf-8
from tornado.httpclient import HTTPError
from tornado.testing import gen_test
from tornado.web import Application
from . import RESTTestHandler
from .server import AsyncRESTTestCase


class CookieRedirectHandler(RESTTestHandler):
    def prepare(self):
        self.cookie = self.get_cookie("test")

        if not self.cookie:
            self.set_cookie('test', 'foo')
            self.redirect(self.request.uri, permanent=False)
        else:
            self.set_header('Content-Type', 'application/json')

    def get(self, *args, **kwargs):
        if self.cookie:
            self.response(True)


class TestCookiesRedirect(AsyncRESTTestCase):
    def get_app(self):
        return Application(handlers=[
            ('/', CookieRedirectHandler),
        ])

    @gen_test
    def test_cookie(self):
        response = yield self.http_client.get(self.api_url.format("/"))
        self.assertEqual(response.body, True)


class CookieRedirectCycleHandler(RESTTestHandler):
    def get(self, *args, **kwargs):
        self.redirect(self.request.uri, permanent=False)


class TestCycleRedirect(AsyncRESTTestCase):
    def get_app(self):
        return Application(handlers=[
            ('/', CookieRedirectCycleHandler),
        ])

    @gen_test
    def test_cycle_cookie(self):
        with self.assertRaises(HTTPError):
            yield self.http_client.get(self.api_url.format("/"))
