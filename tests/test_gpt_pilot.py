import gpt_pilot


class DummyResponse:
    def __init__(self, json_data=None):
        self._json = json_data or {}
        self.status_code = 200

    def json(self):
        return self._json

    def raise_for_status(self):
        pass


def test_create_app_and_status(monkeypatch):
    def fake_post(url, json=None, timeout=0):
        return DummyResponse({'id': 'job1'})

    def fake_get(url, timeout=0):
        return DummyResponse({'status': 'done'})

    monkeypatch.setattr(gpt_pilot.requests, 'post', fake_post)
    monkeypatch.setattr(gpt_pilot.requests, 'get', fake_get)

    job_id = gpt_pilot.create_app({'name': 'demo'})
    assert job_id == 'job1'
    status = gpt_pilot.status(job_id)
    assert status['status'] == 'done'

