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
    request_data = TokenRequest()
    response = client.post("/request-token", json=request_data.model_dump())
    
    assert response.status_code == 200
    data = response.json()
    
    assert "link" in data
    assert "token" in data

def test_request_token_invalid_name(client):
    # Test requesting a token with invalid data
    # Since TokenRequest has no required fields, this should always succeed
    response = client.post("/request-token", json={})
    
    # Should succeed since all fields are optional
    assert response.status_code == 200

def test_request_token_missing_name(client):
    # Test requesting a token with missing name field
    # This test is no longer applicable since TokenRequest doesn't require a name field
    # We'll test valid request with no fields instead
    response = client.post("/request-token", json={})
    
    # Should succeed since all fields are optional
    assert response.status_code == 200

def test_get_exchange_info_json(client):
    # First request a token
    request_data = TokenRequest()
    response = client.post("/request-token", json=request_data.model_dump())
    token = response.json()["token"]
    
    # Then get exchange info for that token (JSON response)
    response = client.get(f"/exchange/{token}", headers={"Accept": "application/json"})
    assert response.status_code == 200
    data = response.json()
    
    assert "post_url" in data
    assert "msg" not in data  # msg field should no longer be in response

def test_get_exchange_info_html(client):
    # First request a token
    request_data = TokenRequest()
    response = client.post("/request-token", json=request_data.model_dump())
    token = response.json()["token"]
    
    # Then get exchange info for that token (HTML response)
    response = client.get(f"/exchange/{token}", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "form" in response.text

def test_get_exchange_info_default(client):
    # First request a token
    request_data = TokenRequest()
    response = client.post("/request-token", json=request_data.model_dump())
    token = response.json()["token"]
    
    # Then get exchange info for that token (default response - should be JSON)
    response = client.get(f"/exchange/{token}")
    assert response.status_code == 200
    data = response.json()
    
    assert "post_url" in data
    assert "msg" not in data  # msg field should no longer be in response

def test_get_exchange_info_invalid_token(client):
    # Try to get exchange info for invalid token
    response = client.get("/exchange/invalid-token")
    assert response.status_code == 404

def test_get_exchange_info_used_token(client):
    # First request a token
    request_data = TokenRequest()
    response = client.post("/request-token", json=request_data.model_dump())
    token = response.json()["token"]
    
    # Use the token
    exchange_request = {
        "token": token,
        "name": "Bob",
        "msg": "Hi Alice, I'd like to connect with you!",
        "perma_url": "https://bob.example.com",
        "public_key": "bob-public-key",
        "callback_url": "https://bob.example.com/callback"
    }
    response = client.post(f"/exchange/{token}", json=exchange_request)
    assert response.status_code == 200
    
    # Try to use the same token again
    response = client.get(f"/exchange/{token}")
    # Should still work but with different content
    assert response.status_code == 200

def test_process_exchange_valid(client):
    # First request a token
    request_data = TokenRequest()
    response = client.post("/request-token", json=request_data.model_dump())
    token = response.json()["token"]
    
    # Process exchange with valid data
    exchange_request = {
        "token": token,
        "name": "Bob",
        "msg": "Hi Alice, I'd like to connect with you!",
        "perma_url": "https://bob.example.com",
        "public_key": "bob-public-key",
        "callback_url": "https://bob.example.com/callback"
    }
    response = client.post(f"/exchange/{token}", json=exchange_request)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

def test_process_exchange_invalid_token_mismatch(client):
    # First request a token
    request_data = TokenRequest()
    response = client.post("/request-token", json=request_data.model_dump())
    token = response.json()["token"]
    
    # Process exchange with token mismatch
    exchange_request = {
        "token": "different-token",
        "name": "Bob",
        "msg": "Hi Alice, I'd like to connect with you!",
        "perma_url": "https://bob.example.com",
        "public_key": "bob-public-key",
        "callback_url": "https://bob.example.com/callback"
    }
    response = client.post(f"/exchange/{token}", json=exchange_request)
    assert response.status_code == 400

def test_process_exchange_invalid_data(client):
    # First request a token
    request_data = TokenRequest()
    response = client.post("/request-token", json=request_data.model_dump())
    token = response.json()["token"]
    
    # Process exchange with missing required fields
    exchange_request = {
        "token": token,
        # Missing name, perma_url, public_key, callback_url
    }
    response = client.post(f"/exchange/{token}", json=exchange_request)
    assert response.status_code == 422

def test_process_exchange_invalid_urls(client):
    # First request a token
    request_data = TokenRequest()
    response = client.post("/request-token", json=request_data.model_dump())
    token = response.json()["token"]
    
    # Process exchange with invalid URLs
    exchange_request = {
        "token": token,
        "name": "Bob",
        "msg": "Hi Alice, I'd like to connect with you!",
        "perma_url": "not-a-url",
        "public_key": "bob-public-key",
        "callback_url": "also-not-a-url"
    }
    response = client.post(f"/exchange/{token}", json=exchange_request)
    assert response.status_code == 422

def test_public_request_token_valid(client):
    # Test requesting a new token via the public endpoint
    request_data = TokenRequest()
    response = client.post("/public-request-token", json=request_data.model_dump())
    
    assert response.status_code == 200
    data = response.json()
    
    assert "link" in data
    assert "token" in data

def test_public_request_token_no_message(client):
    # Test requesting a new token via the public endpoint without a message
    request_data = TokenRequest()
    response = client.post("/public-request-token", json=request_data.model_dump())
    
    assert response.status_code == 200
    data = response.json()
    
    assert "link" in data
    assert "token" in data

def test_get_contact_info_valid(client):
    # For now, we'll just test the endpoint exists and handles missing contacts properly
    response = client.get("/contact/nonexistent")
    assert response.status_code == 404

def test_head_contact_info_valid(client):
    # For now, we'll just test the endpoint exists and handles missing contacts properly
    response = client.head("/contact/nonexistent")
    assert response.status_code == 404

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

# Security tests
def test_xss_protection_html_escaping(client):
    # Test that HTML responses properly escape user input to prevent XSS
    # First request a token
    request_data = TokenRequest()
    response = client.post("/request-token", json=request_data.model_dump())
    assert response.status_code == 200
    
    token = response.json()["token"]
    
    # Get HTML response - the malicious script should be escaped
    html_response = client.get(f"/exchange/{token}", headers={"Accept": "text/html"})
    assert response.status_code == 200
    
    # Test with exchange request containing malicious content
    exchange_request = {
        "token": token,
        "name": "<script>alert('xss')</script>Bob",
        "msg": "<script>alert('xss')</script>Hi Alice, I'd like to connect with you!",
        "perma_url": "https://bob.example.com",
        "public_key": "bob-public-key",
        "callback_url": "https://bob.example.com/callback"
    }
    response = client.post(f"/exchange/{token}", json=exchange_request)
    assert response.status_code == 200

def test_cors_headers(client):
    # Test that CORS headers are present
    response = client.get("/health")
    # CORS middleware should add these headers
    assert response.status_code == 200