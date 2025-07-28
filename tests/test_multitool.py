import types

import tools.multitool as mt


class DummyResp:
    def __init__(self, json_data=None, status=200):
        self._json = json_data or {}
        self.status_code = status

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("err")


def test_call_success(monkeypatch):
    def fake_post(url, json=None, headers=None, timeout=0):
        return DummyResp({"ok": True})

    monkeypatch.setattr(mt.requests, "post", fake_post)
    result = mt.call("demo", {"x": 1}, fallbacks={})
    assert result["ok"] is True


def test_call_with_fallback(monkeypatch):
    calls = []

    def fake_post(url, json=None, headers=None, timeout=0):
        calls.append(url)
        if url.endswith("/api/kimi_k2"):
            return DummyResp(status=404)
        return DummyResp({"alt": True})

    monkeypatch.setattr(mt.requests, "post", fake_post)
    result = mt.call("kimi_k2", {}, fallbacks={"kimi_k2": ["kimi_k1"]})
    assert result["alt"] is True
    assert len(calls) == 2
