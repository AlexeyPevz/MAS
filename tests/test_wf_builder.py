import json
from tools import wf_builder


class DummyClient:
    def __init__(self):
        self.created = None
        self.activated = None

    def create_workflow(self, data):
        self.created = data
        return {"id": "1"}

    def activate_workflow(self, workflow_id):
        self.activated = workflow_id
        return True


def test_generate_n8n_json_from_json():
    spec = json.dumps({"name": "Demo", "nodes": [], "connections": {}})
    wf = wf_builder.generate_n8n_json(spec)
    assert wf["name"] == "Demo"
    assert wf["nodes"] == []


def test_create_workflow_uses_client(monkeypatch):
    import tools.n8n_client as n8n_client

    dummy = DummyClient()
    monkeypatch.setattr(n8n_client, "N8NClient", lambda url, key: dummy)
    spec = {"name": "Demo", "nodes": [], "connections": {}}
    result = wf_builder.create_workflow(spec, "url", "key")
    assert result == {"id": "1"}
    assert dummy.created == spec
    assert dummy.activated == "1"
