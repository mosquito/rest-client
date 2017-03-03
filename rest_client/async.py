#!/usr/bin/env python
# encoding: utf-8
from copy import copy

from tornado.web import Cookie
from tornado.gen import coroutine, Return
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError, HTTPResponse
from tornado.httputil import HTTPHeaders
from tornado.ioloop import IOLoop
from .common import RESTClientBase, _freeze_response
from .compat import b


try:
    import pycares
    from tornado.netutil import Resolver
    from tornado.platform.caresresolver import CaresResolver

    Resolver.configure(CaresResolver)
except ImportError:
    pass


class RESTClient(RESTClientBase):
    __slots__ = ('_cookies', 'io_loop')

    def _get_client(self, client=None, loop=None):
        return client if client else AsyncHTTPClient(io_loop=loop)

    def _get_loop(self, loop=None):
        return loop if loop else IOLoop.current()

    def prepare(self):
        self.io_loop = self.loop
        self._cookies = Cookie.SimpleCookie()

    def __init__(self, io_loop=None, client=None, headers=None, **kwargs):
        RESTClientBase.__init__(self, loop=io_loop, client=client, headers=headers, **kwargs)

    @property
    def close(self):
        return self._client.close

    @coroutine
    def fetch(self, url, method='GET', body=None, headers=None, fail=True, freeze=False,
              follow_redirects=True, max_redirects=5, **kwargs):

        headers = self.get_headers(headers)

        if body is not None and 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'

        if method in self.METHODS_WITH_BODY and 'body_producer' not in kwargs:
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

            request.headers['Cookie'] = '; '.join(
                '{0.key}={0.value}'.format(cookie) for cookie in self._cookies.values()
            )

            need_redirect = False

            try:
                response = yield self._client.fetch(request)
                response.fail = False
            except HTTPError as e:
                last_exc = e
                response = e.response

                if e.code == 599:
                    response = HTTPResponse(
                        request=request,
                        code=e.code,
                        headers=HTTPHeaders(),
                        effective_url=request.url
                    )

                    response.fail = True

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

        content_type = response.headers.get('Content-Type', '')
        response._body = self._decode_body(content_type, response.body)

        if response.body and 'json' in response.headers.get('Content-Type', ''):
            new_body = self._parse_json(response.body)
            response._body = _freeze_response(new_body)

        if not freeze:
            for cookie in response.headers.get_list('Set-Cookie'):
                self._cookies.load(cookie)

        raise Return(response)

    @property
    def close(self):
        return self._client.close

    def __copy__(self):
        client = RESTClient(
            io_loop=self.io_loop,
            headers=self._headers,
            **self._default_args
        )

        client._cookies = copy(self._cookies)
        return client
