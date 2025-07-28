"""Demo for generating and activating an n8n workflow."""
import os

from n8n_client import N8nClient


WORKFLOW_SPEC = {
    "name": "Echo Workflow",
    "nodes": [],
    "connections": {},
}


def main() -> None:
    base = os.getenv("N8N_URL", "http://localhost:5678")
    key = os.getenv("N8N_API_KEY", "changeme")
    client = N8nClient(base, key)
    result = client.create_workflow(WORKFLOW_SPEC)
    print("create_workflow:", result)
    if result and result.get("id"):
        client.activate_workflow(result["id"])
        print("workflow activated")


if __name__ == "__main__":
    main()

