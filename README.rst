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

    from rest_client.async import RESTClient

    @coroutine
    def repo_list():
        client = RESTClient()
        response = yield client.get('https://api.github.com/users/octocat/orgs')



