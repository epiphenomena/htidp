import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.models import TokenRequest, ExchangeRequest, VCard

@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c

def test_request_token(client):
    # Test requesting a new token
    request_data = TokenRequest(requester_name="Alice")
    response = client.post("/v1/request-token", json=request_data.model_dump())
    
    assert response.status_code == 200
    data = response.json()
    
    assert "link" in data
    assert "token" in data
    assert data["requester_name"] == "Alice"

def test_get_exchange_info(client):
    # First request a token
    request_data = TokenRequest(requester_name="Alice")
    response = client.post("/v1/request-token", json=request_data.model_dump())
    token = response.json()["token"]
    
    # Then get exchange info for that token
    response = client.get(f"/v1/exchange/{token}")
    assert response.status_code == 200
    data = response.json()
    
    assert "post_url" in data
    assert "requester_name" in data
    assert data["requester_name"] == "Alice"

def test_health_check(client):
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}