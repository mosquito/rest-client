#!/usr/bin/env python
# encoding: utf-8
from copy import copy
from tornado.web import Cookie
from tornado.gen import coroutine, Return
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from tornado.httputil import HTTPHeaders
from tornado.ioloop import IOLoop
from tornado.netutil import Resolver
from . import PY2

try:
    import pycares
    Resolver.configure('tornado.platform.caresresolver.CaresResolver')
except ImportError:
    pass


if PY2:
    b = unicode
    iteritems = lambda x: x.iteritems()
else:
    b = str
    iteritems = lambda x: x.items()


try:
    import ujson as json
except ImportError:
    import json


def _freeze_response(response):
    if isinstance(response, list):
        return tuple(_freeze_response(x) for x in response)
    elif isinstance(response, dict):
        data = dict((k, _freeze_response(v)) for k, v in iteritems(response))
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
    _DEFAULT = {}

    METHODS_WITH_BODY = set(['POST', 'PUT', 'PATCH'])

    __slots__ = ('_client', '_cookies', 'io_loop', '_headers', '_default_args')

    @classmethod
    def configure(cls, **kwargs):
        cls._DEFAULT.update(kwargs)

    def __init__(self, io_loop=None, client=None, headers=None, **kwargs):
        self.io_loop = IOLoop.current() if io_loop is None else io_loop

        self._headers = headers if headers else {}

        self._client = AsyncHTTPClient() if client is None else client
        self._cookies = Cookie.SimpleCookie()
        self._default_args = copy(self._DEFAULT)
        self._default_args.update(kwargs)

    @coroutine
    def fetch(self, url, method='GET', body=None, headers=None, fail=True, freeze=False, follow_redirects=True, max_redirects=5, **kwargs):
        if not headers:
            headers = {}

        default_headers = copy(self._headers)
        default_headers.update(headers)

        headers = default_headers

        if body is not None and "Content-Type" not in headers:
            headers['Content-Type'] = 'application/json'

        if method in self.METHODS_WITH_BODY:
            body = body or ''

            if headers.get('Content-Type', '') == 'application/json':
                body = self._make_json(body)

        params = copy(self._default_args)
        params.update(kwargs)

        last_exc = RuntimeError("Something wrong")

        for _ in range(max_redirects + 1):
            request = HTTPRequest(
                b(url),
                method=method,
                body=body,
                headers=HTTPHeaders(headers),
                follow_redirects=False,
                **params
            )

            request.headers['Cookie'] = "; ".join(
                "{0.key}={0.value}".format(cookie) for cookie in self._cookies.values()
            )

            need_redirect = False

            try:
                response = yield self._client.fetch(request)
                response.fail = False
            except HTTPError as e:
                last_exc = e
                response = e.response

                if e.code == 599:
                    response = e

                if e.code in (301, 302, 303, 307) and follow_redirects:
                    need_redirect = True
                else:
                    response.fail = True

                if fail and e.response:
                    content_type = e.response.headers.get('Content-Type', '')
                    e.response._body = self._decode_body(content_type, response.body)

                    if e.response.body and 'application/json' in content_type.lower():
                        e.response._body = self._parse_json(e.response.body)

            if not need_redirect:
                break

            if not freeze:
                for cookie in response.headers.get_list('Set-Cookie'):
                    self._cookies.load(cookie)
        else:
            response.fail = True

        if fail and response.fail:
            raise last_exc

        content_type = response.headers.get("Content-Type", '')
        response._body = self._decode_body(content_type, response.body)

        if response.body and 'json' in response.headers.get("Content-Type", ""):
            new_body = self._parse_json(response.body)
            response._body = _freeze_response(new_body)

        if not freeze:
            for cookie in response.headers.get_list('Set-Cookie'):
                self._cookies.load(cookie)

        raise Return(response)

    @classmethod
    def _decode_body(cls, content_type, body):
        if 'charset=' in content_type:
            _, charset = content_type.split("charset=")
            charset = charset.lower()
        else:
            charset = 'utf-8'

        try:
            return body.decode(charset)
        except:
            return body

    def _parse_json(self, data):
        return json.loads(data)

    def _make_json(self, data):
        return json.dumps(data)

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
            io_loop=self.io_loop,
            headers=self._headers,
            **self._default_args
        )

        client._cookies = copy(self._cookies)
        return client
