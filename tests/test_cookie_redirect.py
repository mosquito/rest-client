#!/usr/bin/env python
# encoding: utf-8
from tornado.httpclient import HTTPError as ClientHTTPError
from tornado.testing import gen_test
from tornado.web import Application, HTTPError
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
        with self.assertRaises(ClientHTTPError):
            yield self.http_client.get(self.api_url.format("/"))


class CookieRedirectFailHandler(RESTTestHandler):
    def get(self, *args, **kwargs):
        cookie = self.get_cookie("test")
        if not cookie:
            self.set_cookie("test", '1')
            return self.redirect(self.request.uri)

        raise HTTPError(500)


class TestCookieRedirectFail(AsyncRESTTestCase):
    def get_app(self):
        return Application(handlers=[
            ('/', CookieRedirectFailHandler),
        ])

    @gen_test
    def test_cycle_cookie(self):
        with self.assertRaises(ClientHTTPError) as e:
            yield self.http_client.get(self.api_url.format("/"))

        self.assertEqual(e.exception.response.code, 500)


class FailHandler(RESTTestHandler):
    def get(self, *args, **kwargs):
        raise HTTPError(500)


class TestFail(AsyncRESTTestCase):
    def get_app(self):
        return Application(handlers=[
            ('/', CookieRedirectFailHandler),
        ])

    @gen_test(timeout=600)
    def test_cycle_cookie(self):
        with self.assertRaises(ClientHTTPError) as e:
            yield self.http_client.get(self.api_url.format("/"))

        self.assertEqual(e.exception.response.code, 500)
