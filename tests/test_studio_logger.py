import json
from types import SimpleNamespace

import tools.studio_logger as sl


def test_log_interaction(monkeypatch, tmp_path):
    path = tmp_path / "log.jsonl"
    monkeypatch.setattr(sl, "LOG_PATH", path)
    sl.log_interaction("a", ["b"], {"role": "user", "content": "hi"})
    data = path.read_text().strip()
    entry = json.loads(data)
    assert entry["sender"] == "a"
    assert entry["receivers"] == ["b"]
    assert entry["message"]["content"] == "hi"


def test_export_logs(monkeypatch, tmp_path):
    src = tmp_path / "src.jsonl"
    src.write_text("data")
    monkeypatch.setattr(sl, "LOG_PATH", src)
    dest = tmp_path / "dest.jsonl"
    sl.export_logs(dest)
    assert dest.read_text() == "data"


def test_send_to_studio(monkeypatch, tmp_path):
    src = tmp_path / "s.jsonl"
    src.write_text("data")
    monkeypatch.setattr(sl, "LOG_PATH", src)

    called = {}

    class FakeResp(SimpleNamespace):
        def raise_for_status(self):
            pass

    def fake_post(url, files=None, timeout=10):
        called["url"] = url
        return FakeResp(status_code=200)

    monkeypatch.setattr(sl, "requests", SimpleNamespace(post=fake_post))
    assert sl.send_to_studio("http://x") is True
    assert called["url"] == "http://x"
