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

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return hash(self) != hash(other)


class RESTClient(object):
    THREAD_POOL = None

    _DEFAULT = {}

    METHODS_WITH_BODY = {'POST', 'PUT'}

    __slots__ = ('_client', '_cookies', 'io_loop', '_thread_pool', '_headers', '_default_args')

    @classmethod
    def configure(cls, **kwargs):
        cls._DEFAULT.update(kwargs)

    def __init__(self, io_loop=None, client=None, thread_pool=None, headers=None, **kwargs):
        self.io_loop = IOLoop.current() if io_loop is None else io_loop

        if thread_pool is None:
            self._thread_pool = futures.ThreadPoolExecutor(cpu_count()) if not self.THREAD_POOL else self.THREAD_POOL
        else:
            self._thread_pool = thread_pool

        assert isinstance(self._thread_pool, futures.ThreadPoolExecutor)

        self._headers = headers if headers else {}

        self._client = AsyncHTTPClient() if client is None else client
        self._cookies = Cookie.SimpleCookie()
        self._default_args = copy(self._DEFAULT)
        self._default_args.update(kwargs)

    @coroutine
    def fetch(self, url, method='GET', body=None, headers=None, fail=True, freeze=False, **kwargs):
        if not headers:
            headers = {}

        default_headers = copy(self._headers)
        default_headers.update(headers)

        headers = default_headers

        if "Content-Type" not in headers:
            headers['Content-Type'] = 'application/json'

        if method in self.METHODS_WITH_BODY and headers['Content-Type'] == 'application/json':
            body = yield self._thread_pool.submit(ujson.dumps, body)

        params = copy(self._default_args)
        params.update(kwargs)

        request = HTTPRequest(b(url), method=method, body=body, headers=HTTPHeaders(headers), **params)
        request.headers['Cookie'] = "; ".join("{0.key}={0.value}".format(cookie) for cookie in self._cookies.values())

        try:
            response = yield self._client.fetch(request)
            response.fail = False
        except HTTPError as e:
            if fail:
                raise

            response = e.response
            response.fail = True

        if response.body and 'json' in response.headers.get("Content-Type", ""):
            new_body = yield self._thread_pool.submit(ujson.loads, response._body)
            response._body = _freeze_response(new_body)

        if not freeze:
            for cookie in response.headers.get_list('Set-Cookie'):
                self._cookies.load(cookie)

        raise Return(response)

    @property
    def close(self):
        return self._client.close

    get = make_method('GET')
    post = make_method('POST')
    put = make_method('PUT')
    options = make_method('OPTIONS')
    delete = make_method('DELETE')
    head = make_method('HEAD')

    def __copy__(self):
        client = RESTClient(
            thread_pool=self._thread_pool,
            io_loop=self.io_loop,
            headers=self._headers,
            **self._default_args
        )

        client._cookies = copy(self._cookies)
        return client