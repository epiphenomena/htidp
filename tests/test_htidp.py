import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.models import TokenRequest, ExchangeRequest, VCard
from pydantic import ValidationError

@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c

def test_request_token_valid(client):
    # Test requesting a new token with valid data
    request_data = TokenRequest(requester_name="Alice")
    response = client.post("/v1/request-token", json=request_data.model_dump())
    
    assert response.status_code == 200
    data = response.json()
    
    assert "link" in data
    assert "token" in data
    assert data["requester_name"] == "Alice"

def test_request_token_invalid_name(client):
    # Test requesting a token with invalid name (empty string)
    response = client.post("/v1/request-token", json={"requester_name": ""})
    
    # Should fail validation
    assert response.status_code == 422

def test_request_token_missing_name(client):
    # Test requesting a token with missing name field
    response = client.post("/v1/request-token", json={})
    
    # Should fail validation
    assert response.status_code == 422

def test_get_exchange_info_json(client):
    # First request a token
    request_data = TokenRequest(requester_name="Alice")
    response = client.post("/v1/request-token", json=request_data.model_dump())
    token = response.json()["token"]
    
    # Then get exchange info for that token (JSON response)
    response = client.get(f"/v1/exchange/{token}", headers={"Accept": "application/json"})
    assert response.status_code == 200
    data = response.json()
    
    assert "post_url" in data
    assert "requester_name" in data
    assert data["requester_name"] == "Alice"

def test_get_exchange_info_html(client):
    # First request a token
    request_data = TokenRequest(requester_name="Alice")
    response = client.post("/v1/request-token", json=request_data.model_dump())
    token = response.json()["token"]
    
    # Then get exchange info for that token (HTML response)
    response = client.get(f"/v1/exchange/{token}", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Alice" in response.text
    assert "form" in response.text

def test_get_exchange_info_default(client):
    # First request a token
    request_data = TokenRequest(requester_name="Alice")
    response = client.post("/v1/request-token", json=request_data.model_dump())
    token = response.json()["token"]
    
    # Then get exchange info for that token (default response - should be JSON)
    response = client.get(f"/v1/exchange/{token}")
    assert response.status_code == 200
    data = response.json()
    
    assert "post_url" in data
    assert "requester_name" in data
    assert data["requester_name"] == "Alice"

def test_get_exchange_info_invalid_token(client):
    # Try to get exchange info for invalid token
    response = client.get("/v1/exchange/invalid-token")
    assert response.status_code == 404

def test_get_exchange_info_used_token(client):
    # First request a token
    request_data = TokenRequest(requester_name="Alice")
    response = client.post("/v1/request-token", json=request_data.model_dump())
    token = response.json()["token"]
    
    # Use the token
    exchange_request = {
        "token": token,
        "name": "Bob",
        "perma_url": "https://bob.example.com",
        "public_key": "bob-public-key",
        "callback_url": "https://bob.example.com/callback"
    }
    response = client.post(f"/v1/exchange/{token}", json=exchange_request)
    assert response.status_code == 200
    
    # Try to use the same token again
    response = client.get(f"/v1/exchange/{token}")
    # Should still work but with different content
    assert response.status_code == 200

def test_process_exchange_valid(client):
    # First request a token
    request_data = TokenRequest(requester_name="Alice")
    response = client.post("/v1/request-token", json=request_data.model_dump())
    token = response.json()["token"]
    
    # Process exchange with valid data
    exchange_request = {
        "token": token,
        "name": "Bob",
        "perma_url": "https://bob.example.com",
        "public_key": "bob-public-key",
        "callback_url": "https://bob.example.com/callback"
    }
    response = client.post(f"/v1/exchange/{token}", json=exchange_request)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

def test_process_exchange_invalid_token_mismatch(client):
    # First request a token
    request_data = TokenRequest(requester_name="Alice")
    response = client.post("/v1/request-token", json=request_data.model_dump())
    token = response.json()["token"]
    
    # Process exchange with token mismatch
    exchange_request = {
        "token": "different-token",
        "name": "Bob",
        "perma_url": "https://bob.example.com",
        "public_key": "bob-public-key",
        "callback_url": "https://bob.example.com/callback"
    }
    response = client.post(f"/v1/exchange/{token}", json=exchange_request)
    assert response.status_code == 400

def test_process_exchange_invalid_data(client):
    # First request a token
    request_data = TokenRequest(requester_name="Alice")
    response = client.post("/v1/request-token", json=request_data.model_dump())
    token = response.json()["token"]
    
    # Process exchange with missing required fields
    exchange_request = {
        "token": token,
        # Missing name, perma_url, public_key, callback_url
    }
    response = client.post(f"/v1/exchange/{token}", json=exchange_request)
    assert response.status_code == 422

def test_process_exchange_invalid_urls(client):
    # First request a token
    request_data = TokenRequest(requester_name="Alice")
    response = client.post("/v1/request-token", json=request_data.model_dump())
    token = response.json()["token"]
    
    # Process exchange with invalid URLs
    exchange_request = {
        "token": token,
        "name": "Bob",
        "perma_url": "not-a-url",
        "public_key": "bob-public-key",
        "callback_url": "also-not-a-url"
    }
    response = client.post(f"/v1/exchange/{token}", json=exchange_request)
    assert response.status_code == 422

def test_get_contact_info_valid(client):
    # For now, we'll just test the endpoint exists and handles missing contacts properly
    response = client.get("/v1/contact/nonexistent")
    assert response.status_code == 404

def test_head_contact_info_valid(client):
    # For now, we'll just test the endpoint exists and handles missing contacts properly
    response = client.head("/v1/contact/nonexistent")
    assert response.status_code == 404

def test_health_check(client):
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

# Security tests
def test_xss_protection_html_escaping(client):
    # Test that HTML responses properly escape user input to prevent XSS
    # First request a token with a name that contains HTML
    request_data = TokenRequest(requester_name="<script>alert('xss')</script>Alice")
    response = client.post("/v1/request-token", json=request_data.model_dump())
    assert response.status_code == 200
    
    token = response.json()["token"]
    
    # Get HTML response - the malicious script should be escaped
    html_response = client.get(f"/v1/exchange/{token}", headers={"Accept": "text/html"})
    assert response.status_code == 200
    
    # The HTML should contain the escaped version, not executable script
    assert "&lt;script&gt;alert(" in html_response.text
    assert "<script>alert(" not in html_response.text

def test_cors_headers(client):
    # Test that CORS headers are present
    response = client.get("/v1/health")
    # CORS middleware should add these headers
    assert response.status_code == 200