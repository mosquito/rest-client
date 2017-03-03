import abc
from copy import copy
from functools import total_ordering
from .compat import iteritems, json


@total_ordering
class FrozenDict(dict):
    __slots__ = ('__hash',)
    __getattr__ = dict.__getitem__

    def __init__(self, data):
        super(FrozenDict, self).__init__(data)
        self.__hash = hash(tuple(i for i in sorted(iteritems(self))))

    def __setitem__(self, key, value):
        raise TypeError("Response is immutable")

    def __setattr__(self, key, value):
        if key.startswith('_{0.__class__.__name__}'.format(self)):
            return super(FrozenDict, self).__setattr__(key, value)
        raise TypeError("Response is immutable")

    def __hash__(self):
        return self.__hash

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return hash(self) != hash(other)


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


class RESTClientBase(object):
    _DEFAULT = {}

    METHODS_WITH_BODY = {'POST', 'PUT', 'PATCH'}

    __slots__ = ('_client', '_cookies', 'loop', '_headers', '_default_args')

    @classmethod
    def configure(cls, **kwargs):
        cls._DEFAULT.update(kwargs)

    @abc.abstractclassmethod
    def _get_loop(self, loop=None):
        pass

    @abc.abstractclassmethod
    def _get_client(self, client=None, loop=None):
        pass

    def prepare(self):
        pass

    def _prepare_args(self, kwargs):
        defaults = copy(self._DEFAULT)
        defaults.update(kwargs)
        return defaults

    def __init__(self, loop=None, client=None, headers=None, **kwargs):
        self.loop = self._get_loop(loop)
        self._headers = headers if headers else {}
        self._client = self._get_client(client, loop=self.loop)
        self._default_args = self._prepare_args(kwargs)

        self.prepare()

    @abc.abstractclassmethod
    def fetch(self, url, method='GET', body=None, headers=None, fail=True, freeze=False,
              follow_redirects=True, max_redirects=5, **kwargs):
        pass

    @classmethod
    def _decode_body(cls, content_type, body):
        if 'charset=' in content_type:
            _, charset = content_type.split('charset=')
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

    def get_headers(self, headers=None):
        if not headers:
            headers = {}

        default_headers = copy(self._headers)
        default_headers.update(headers)

        headers = default_headers

        return headers

    @abc.abstractclassmethod
    def close(self):
        pass

    def __copy__(self):
        return RESTClientBase(
            loop=self.loop,
            headers=self._headers,
            client=copy(self._client),
            **self._default_args
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close()

    get = make_method('GET')
    post = make_method('POST')
    put = make_method('PUT')
    options = make_method('OPTIONS')
    delete = make_method('DELETE')
    head = make_method('HEAD')
