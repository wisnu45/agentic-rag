import json
from pathlib import Path


def test_n8n_ollama_workflow_has_secure_webhook_and_expected_contract():
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / "n8n"
        / "workflows"
        / "agentic-rag-ollama.json"
    )
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))

    nodes = {node["name"]: node for node in workflow["nodes"]}
    assert set(nodes) == {
        "Webhook",
        "Generate Answer with Ollama",
        "Respond to Webhook",
    }
    assert nodes["Webhook"]["parameters"]["httpMethod"] == "POST"
    assert nodes["Webhook"]["parameters"]["authentication"] == "headerAuth"
    assert nodes["Webhook"]["parameters"]["path"] == "agentic-rag-chat"
    assert nodes["Generate Answer with Ollama"]["parameters"]["url"].endswith(
        "/api/chat"
    )
    body = nodes["Generate Answer with Ollama"]["parameters"]["body"]
    assert "qwen2.5:3b" in body
    assert "$json.body.question" in body
    assert "$json.body.contexts" in body
    assert nodes["Respond to Webhook"]["parameters"]["respondWith"] == "json"
    assert "answer" in nodes["Respond to Webhook"]["parameters"]["responseBody"]

    assert workflow["connections"]["Webhook"]["main"][0][0]["node"] == (
        "Generate Answer with Ollama"
    )
    assert workflow["connections"]["Generate Answer with Ollama"]["main"][0][0][
        "node"
    ] == "Respond to Webhook"
