import asyncio
from tornado.testing import AsyncHTTPTestCase as BaseTestCase
from rest_client.aiohttp import RESTClient
from tornado.ioloop import IOLoop
from .. import RESTTestHandler

IOLoop.configure('tornado.platform.asyncio.AsyncIOLoop')


class AsyncRESTTestCase(BaseTestCase):
    def setUp(self):
        super(AsyncRESTTestCase, self).setUp()
        asyncio.set_event_loop(self.io_loop.asyncio_loop)

    @property
    def api_url(self):
        return "http://localhost:%s{0}" % self.get_http_port()

    def get_http_client(self):
        return RESTClient(loop=self.io_loop.asyncio_loop)
