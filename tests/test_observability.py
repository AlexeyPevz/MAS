import types

import tools.observability as obs


def test_start_metrics_server(monkeypatch):
    called = {}

    def fake_start(port):
        called['port'] = port

    monkeypatch.setattr(obs, 'start_http_server', fake_start)
    obs.start_metrics_server(1234)
    assert called['port'] == 1234


def test_metric_functions():
    obs.record_request('a')
    obs.record_tokens('a', 2)
    obs.record_error('a')
    obs.observe_duration('a', 0.1)
    obs.observe_response_time('a', 0.2)
