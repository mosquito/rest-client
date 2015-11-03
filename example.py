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
