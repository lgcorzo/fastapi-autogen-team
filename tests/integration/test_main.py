import pytest
import logging
from fastapi import status
from fastapi.testclient import TestClient

from fastapi_autogen_team.main import app


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.skip(reason="waiting to develop a full llm simulator for a interation test in CI pipeline")
def test_chat_nonstream_completion_success(client):
    test_input = {
        "model": "internal-gpt",
        "stream": False,
        "messages": [
            {"role": "user", "content": "¿Qué es el leadin en lantek expert?"},
            {
                "role": "assistant",
                "content": "Expert es uno de los programas de lantek",
            },
            {"role": "user", "content": "Translate to english"},
        ],
    }
    headers = {
        "x-ssl-dn": "CN=aBZ23Npql5ywVeMdqKPLHg== 92tkoPLVmB\\+/SbrqKzmtLf==.epc",
        "x-kai-user-id": "dev_integration_test",
    }
    response = client.post("/manuals-rag/api/v1beta1/chat/completions", headers=headers, json=test_input)

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert isinstance(response_json, dict)
    assert "choices" in response_json or "data" in response_json


@pytest.mark.skip(reason="waiting to develop a full llm simulator for a interation test in CI pipeline")
def test_chat_stream_completion_success(client):
    test_input = {
        "model": "internal-gpt",
        "stream": True,
        "messages": [
            {"role": "user", "content": "¿Qué es el leadin en lantek expert?"},
            {
                "role": "assistant",
                "content": "Expert es uno de los programas de lantek",
            },
            {"role": "user", "content": "Zer dauka berria Lantek V44 bertsioan"},
        ],
    }
    headers = {
        "x-ssl-dn": "CN=aBZ23Npql5ywVeMdqKPLHg== 92tkoPLVmB\\+/SbrqKzmtLf==.epc",
        "x-kai-user-id": "dev_integration_test",
    }

    response = client.post("/manuals-rag/api/v1beta1/chat/completions", headers=headers, json=test_input)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.skip(reason="waiting to develop a full llm simulator for a interation test in CI pipeline")
def test_chat_stream_completion_system_message(client):
    test_input = {
        "model": "internal-gpt",
        "stream": True,
        "messages": [
            {"role": "system", "content": "QUERY: Translate to english"},
            {"role": "user", "content": "¿Qué es el leadin en lantek expert?"},
            {
                "role": "assistant",
                "content": "Expert es uno de los programas de lantek",
            },
            {"role": "user", "content": "Translate to english"},
        ],
    }
    headers = {
        "x-ssl-dn": "CN=aBZ23Npql5ywVeMdqKPLHg== 92tkoPLVmB\\+/SbrqKzmtLf==.epc",
        "x-kai-user-id": "dev_integration_test",
    }
    response = client.post("/manuals-rag/api/v1beta1/chat/completions", headers=headers, json=test_input)
    assert response.status_code == status.HTTP_200_OK
