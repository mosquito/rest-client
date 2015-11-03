#!/usr/bin/env python
# encoding: utf-8
import sys
import ujson
from Cookie import SimpleCookie
from tornado.gen import coroutine, Return
from tornado.concurrent import futures
from multiprocessing import cpu_count
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from tornado.httputil import HTTPHeaders
from tornado.ioloop import IOLoop


if sys.version_info < (3,):
    b = unicode
else:
    b = str


def make_method(method_name):
    def method(self, url, **kwargs):
        return self.fetch(url, method=method_name, **kwargs)

    method.__name__ = method_name.lower()

    return method


class RESTResponse(dict):
    def __setitem__(self, key, value):
        raise TypeError("Response is immutable")

    def __getitem__(self, key):
        item = super(RESTResponse, self).__getitem__(key)

        processors = {
            list: tuple,
            dict: RESTResponse
        }

        processor = processors.get(type(item))
        return processor(item) if processor else item

    __getattr__ = __getitem__
    __setattr__ = __setitem__


class RESTClient(object):
    CLIENT_CLASS = AsyncHTTPClient
    COOKIE_CLASS = SimpleCookie

    METHODS_WITH_BODY = {'POST', 'PUT'}

    __slots__ = ('__client', '__cookies', 'io_loop', '__thread_pool')

    def __init__(self, io_loop=None, thread_pool=None):
        if io_loop is None:
            self.io_loop = IOLoop.current()

        if thread_pool is None:
            self.__thread_pool = futures.ThreadPoolExecutor(cpu_count())

        assert isinstance(self.__thread_pool, futures.ThreadPoolExecutor)

        self.__client = self.CLIENT_CLASS()
        self.__cookies = self.COOKIE_CLASS()

    @coroutine
    def fetch(self, url, method='GET', body=None, headers=None, fail=True, freeze=False, **kwargs):
        if not headers:
            headers = {}

        if "Content-Type" not in headers:
            headers['Content-Type'] = 'application/json'

        if method in self.METHODS_WITH_BODY and headers['Content-Type'] == 'application/json':
            body = yield self.__thread_pool.submit(ujson.dumps, body)

        request = HTTPRequest(b(url), method=method, body=body, headers=HTTPHeaders(headers), **kwargs)
        request.headers['Cookie'] = ";".join("{0.key}={0.value}".format(cookie) for cookie in self.__cookies.values())

        try:
            response = yield self.__client.fetch(request)
        except HTTPError:
            if fail:
                raise

        if response.body and 'json' in response.headers.get("Content-Type", ""):
            response._body = RESTResponse((yield self.__thread_pool.submit(ujson.loads, response.body)))

        if not freeze:
            for cookie in response.headers.get_list('Set-Cookie'):
                self.__cookies.load(cookie)

        raise Return(response)

    @property
    def close(self):
        return self.__client.close

    get = make_method('GET')
    post = make_method('POST')
    put = make_method('PUT')
    options = make_method('OPTIONS')
    delete = make_method('DELETE')
    head = make_method('HEAD')


