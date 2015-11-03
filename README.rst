rest-client
===========

.. image:: https://travis-ci.org/mosquito/rest-client.svg
    :target: https://travis-ci.org/mosquito/rest-client

.. image:: https://img.shields.io/pypi/v/rest-client.svg
    :target: https://pypi.python.org/pypi/rest-client/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/wheel/rest-client.svg
    :target: https://pypi.python.org/pypi/rest-client/

.. image:: https://img.shields.io/pypi/pyversions/rest-client.svg
    :target: https://pypi.python.org/pypi/rest-client/

.. image:: https://img.shields.io/pypi/l/rest-client.svg
    :target: https://pypi.python.org/pypi/rest-client/


RESTful Client for tornado with support cookies.

Example::

    # encoding: utf-8
    from tornado.ioloop import IOLoop
    from tornado.gen import coroutine, Return
    from rest_client.async import RESTClient

    io_loop = IOLoop.current()

    @coroutine
    def repo_list():
        client = RESTClient(headers={'User-Agent': 'curl/7.43.0'})
        # check api
        yield client.get('https://api.github.com/users/octocat/orgs')

        response = yield client.get('https://api.github.com/repos/vmg/redcarpet/issues?state=closed')
        data = sum(map(lambda x: x.comments, response.body))
        print('Total comments: {0}'.format(data))

    exit(io_loop.run_sync(repo_list))

