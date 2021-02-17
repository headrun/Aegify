import os
from urllib.request import Request, urlopen
from urllib.parse import urljoin
from urllib.error import HTTPError
from json import loads, dumps
from random import randint

class APIMixin(object):

    def setUp(self):
        self.create_view = self.view_module.ListCreateUpdateView
        self.detail_view = self.view_module.DetailView
        self.detail_list_view = self.view_module.DetailListView

        self.source_name = 'test'
        self.source = {'name': self.source_name}

        self.key = 'TC%06d' % randint(1, 1000000)

    def request(self, method, url_path, data=None):
        url = urljoin(os.environ.get('DEV_SERVER', 'http://localhost:8000'), url_path)
        print()

        kwargs = {'method': method}
        if data is not None:
            data['key'] = self.key
        print(method, url, data)
        if data is not None:
            kwargs['data'] = bytes(dumps(data), encoding='utf8')
            kwargs['headers'] = {'content-type': 'application/json'}

        req = Request(url, **kwargs)
        with urlopen(req) as resp:
            data = resp.read().decode('utf-8')

        data = loads(data) if data else data
        print(resp.status, resp.reason, data)
        return resp, data

    def verify_item(self, data, **kwargs):
        self.assertEqual(data['key'], self.key)
        self.assertEqual(data['active'], kwargs.get('active', True))
        return data

    def api_create(self, view, **kwargs):
        resp, data = self.request('POST', view.get_url(), data=kwargs)
        self.assertEqual(resp.status, 201)
        return self.verify_item(data, **kwargs)

    def api_update(self, view, **kwargs):
        resp, data = self.request('POST', view.get_url(), data=kwargs)
        self.assertEqual(resp.status, 200)
        return self.verify_item(data, **kwargs)

    def api_get(self, view, source_name, http_status=200):
        resp, data = self.request('GET', view.get_url(source_name, self.key))
        self.assertEqual(resp.status, http_status)

        if http_status == 200:
            self.assertEqual(data['key'], self.key)

        return data

    def api_list(self, view, *sources):
        resp, data = self.request('GET', view.get_url(self.key))
        self.assertEqual(resp.status, 200)

        self.assertEqual(isinstance(data, list), True)
        self.assertEqual(len(data), len(sources))
        for i, val in enumerate(data):
            self.assertEqual(val['key'], self.key)
            self.assertEqual(val['source']['name'], sources[i])

        return data

    def api_error(self, func, code, *args, **kwargs):
        try:
            data = func(*args, **kwargs)
            self.fail('Dead Code')
        except HTTPError as e:
            print(e)
            self.assertEqual(e.code, code)

    def _test_unknown_source(self):
        print('\n..................test_unknown_source..............')
        self.api_error(self.api_create, 400, self.create_view)

    def test_all(self):
        self._test_unknown_source()
        print('\n..................test_all..............')
        data = self.api_create(self.create_view, source=self.source)
        data = self.api_get(self.detail_view, self.source_name, 204)
        data = self.api_update(self.create_view, source=self.source, active=False)

        data = self.api_list(self.detail_list_view, self.source_name)

