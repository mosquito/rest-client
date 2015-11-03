#!/usr/bin/env python
# encoding: utf-8
from tornado.testing import AsyncHTTPTestCase
from rest_client.async import RESTClient


class AsyncRESTTestCase(AsyncHTTPTestCase):
    @property
    def api_url(self):
        return "http://localhost:%s{}" % self.get_http_port()

    def get_http_client(self):
        return RESTClient(io_loop=self.io_loop)
