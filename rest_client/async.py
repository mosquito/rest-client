#!/usr/bin/env python
# encoding: utf-8
import ujson
from copy import copy
from multiprocessing import cpu_count
from tornado.web import Cookie
from tornado.gen import coroutine, Return
from tornado.concurrent import futures
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from tornado.httputil import HTTPHeaders
from tornado.ioloop import IOLoop
from . import PY2


if PY2:
    b = unicode
    iteritems = lambda x: x.iteritems()
else:
    b = str
    iteritems = lambda x: x.items()


def _freeze_response(response):
    if isinstance(response, list):
        return tuple(_freeze_response(x) for x in response)
    elif isinstance(response, dict):
        data = {k: _freeze_response(v) for k, v in iteritems(response)}
        return FrozenDict(data)
    else:
        return response


def make_method(method_name):
    def method(self, url, **kwargs):
        return self.fetch(url, method=method_name, **kwargs)

    method.__name__ = method_name.lower()

    return method


class FrozenDict(dict):
    __slots__ = ('__hash',)
    __getattr__ = dict.__getitem__

    def __init__(self, data):
        super(FrozenDict, self).__init__(data)
        self.__hash = hash(tuple(i for i in sorted(iteritems(self))))

    def __setitem__(self, key, value):
        raise TypeError("Response is immutable")

    def __setattr__(self, key, value):
        if key.startswith("_{0.__class__.__name__}".format(self)):
            return super(FrozenDict, self).__setattr__(key, value)
        raise TypeError("Response is immutable")

    def __hash__(self):
        return self.__hash


class RESTClient(object):
    CLIENT_CLASS = AsyncHTTPClient
    COOKIE_CLASS = Cookie.SimpleCookie

    METHODS_WITH_BODY = {'POST', 'PUT'}

    __slots__ = ('__client', '__cookies', 'io_loop', '__thread_pool', '__headers')

    def __init__(self, io_loop=None, thread_pool=None, headers=None):
        if io_loop is None:
            self.io_loop = IOLoop.current()

        if thread_pool is None:
            self.__thread_pool = futures.ThreadPoolExecutor(cpu_count())

        assert isinstance(self.__thread_pool, futures.ThreadPoolExecutor)

        self.__headers = headers if headers else {}
        self.__client = self.CLIENT_CLASS()
        self.__cookies = self.COOKIE_CLASS()

    @coroutine
    def fetch(self, url, method='GET', body=None, headers=None, fail=True, freeze=False, **kwargs):
        if not headers:
            headers = {}

        defailt_headers = copy(self.__headers)
        defailt_headers.update(headers)

        headers = defailt_headers

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
            new_body = yield self.__thread_pool.submit(ujson.loads, response._body)
            response._body = _freeze_response(new_body)

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


