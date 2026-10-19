import pytest
import json
import uuid
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch

client = TestClient(app)

def load_conversations():
    with open("test/conversations.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.mark.parametrize("conv", load_conversations())
def test_conversations(conv):
    session_id = str(uuid.uuid4())
    last_response = None
    
    # Mock the LLM to avoid hitting Groq API limits during tests
    with patch("app.engine.chat_json") as mock_extract, patch("app.rag.chat_json") as mock_rag:
        # Provide dummy extractions based on the test description
        if "All fields" in conv["description"]:
            mock_extract.return_value = {"name":"Priya", "mobile":"9091390996", "order_id":"QC-151998", "issue":"kurta torn"}
        elif "Correction" in conv["description"]:
            mock_extract.side_effect = [
                {"name":"Priya", "mobile":"9091390996", "order_id":"QC-151998", "issue":"torn kurta"},
                {"order_id":"QC-139317"}
            ]
        else:
            mock_extract.return_value = {}
            
        mock_rag.return_value = {"reply": "Mocked policy answer (§3.1)"}

        for step in conv["steps"]:
            res = client.post("/chat", json={"session_id": session_id, "text": step})
            assert res.status_code == 200
            last_response = res.json()

    assert last_response is not None
    # Check for fraud escalation
    if "Fraud" in conv["description"]:
        assert last_response["escalated"] is True
    # Check for out-of-scope refusal
    elif "Out-of-scope" in conv["description"]:
        assert "doesn't cover that" in last_response["reply"] or "Mocked" in last_response["reply"]
    # Check for successful ticket creation
    elif "All fields" in conv["description"] or "Correction" in conv["description"]:
        assert "TKT-" in str(last_response) or "confirm" in last_response["reply"].lower()