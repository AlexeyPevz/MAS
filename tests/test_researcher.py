import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / 'root_mas' / 'root_mas'))

from tools import researcher


class FakeResp:
    def __init__(self, data):
        self._data = data
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def test_web_search_returns_result(monkeypatch):
    def fake_get(url, params=None, timeout=10):
        return FakeResp({
            "RelatedTopics": [{"Text": "Title", "FirstURL": "https://example.com", "Result": "Snippet"}]
        })

    monkeypatch.setattr(researcher.requests, "get", fake_get)
    results = researcher.web_search("test", max_results=1)
    assert len(results) == 1
    assert results[0]["url"] == "https://example.com"
