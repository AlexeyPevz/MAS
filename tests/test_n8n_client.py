from types import SimpleNamespace

import n8n_client


class DummyResponse:
    def __init__(self, json_data=None):
        self._json = json_data or {}
        self.status_code = 200

    def json(self):
        return self._json

    def raise_for_status(self):
        pass


def test_create_and_activate_workflow(monkeypatch):
    called = {}

    def fake_post(url, headers=None, json=None, timeout=0):
        called['url'] = url
        called['json'] = json
        return DummyResponse({'id': '42'})

    monkeypatch.setattr(n8n_client.requests, 'post', fake_post)

    client = n8n_client.N8nClient('http://host', 'key')
    result = client.create_workflow({'name': 'demo'})
    assert result == {'id': '42'}
    assert called['url'].endswith('/workflows')

    called.clear()
    client.activate_workflow('42')
    assert called['url'].endswith('/workflows/42/activate')

