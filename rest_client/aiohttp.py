#!/usr/bin/env python
# encoding: utf-8
import aiohttp
import asyncio
from copy import copy
from .common import RESTClientBase, _freeze_response


class RESTClient(RESTClientBase):
    __slots__ = ('_cookies', 'io_loop')

    def _get_client(self, client=None, loop=None):
        return client if client else aiohttp.ClientSession(loop=self.loop)

    def _get_loop(self, loop=None):
        return loop if loop else asyncio.get_event_loop()

    def close(self):
        return self._client.close()

    @asyncio.coroutine
    def fetch(self, url, method='GET', body=None, headers=None, fail=True, freeze=False,
              follow_redirects=True, max_redirects=5, **kwargs):

        assert not freeze, "Freeze not supported yet. Sorry."

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

        url = str(url)

        for _ in range(max_redirects + 1):
            need_redirect = False

            try:
                response = yield from self._client.request(
                    method,
                    url,
                    data=body,
                    headers=headers,
                    **params
                )   # type: aiohttp.ClientResponse

                response.fail = False

                if fail:
                    response.raise_for_status()

            except (aiohttp.ClientError, aiohttp.ClientConnectionError, aiohttp.ClientDisconnectedError) as e:
                last_exc = e

                response = aiohttp.ClientResponse(
                    method,
                    url,
                    writer=lambda x: None
                )

                response.fail = True

            if not need_redirect:
                break
        else:
            response.fail = True

        if fail and response.fail:
            raise last_exc

        content_type = response.headers.get('Content-Type', '')

        response.body = self._decode_body(
            content_type,
            (yield from response.read())
        )

        if response.body and 'application/json' in content_type.lower():
            response.body = self._parse_json(response.body)

        content_type = response.headers.get('Content-Type', '')
        response._body = self._decode_body(content_type, response.body)

        if response.body and 'json' in response.headers.get('Content-Type', ''):
            new_body = self._parse_json(response.body)
            response._body = _freeze_response(new_body)

        if not freeze:
            for cookie in response.headers.get('Set-Cookie', []):
                self._cookies.load(cookie)

        return response

    def close(self):
        self._client.close()

    def __copy__(self):
        client = RESTClient(
            io_loop=self.io_loop,
            headers=self._headers,
            **self._default_args
        )

        client._cookies = copy(self._cookies)
        return client
