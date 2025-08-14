"""
Example usage of the HTIDP API
"""
import requests
import json

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000"

def demo_flow():
    print("HTIDP Demo Flow")
    print("==============")
    
    # Step 1: Alice requests a token with a message
    print("\n1. Alice requests a token with a message...")
    token_response = requests.post(
        f"{BASE_URL}/request-token",
        json={"msg": "Hi Bob, I'd like to connect with you!"}
    )
    
    if token_response.status_code != 200:
        print(f"Error requesting token: {token_response.status_code}")
        return
    
    token_data = token_response.json()
    print(f"Token: {token_data['token']}")
    print(f"Link: {token_data['link']}")
    
    # Step 2: Bob uses the token to get exchange info (JSON response)
    print("\n2. Bob gets exchange info (JSON)...")
    exchange_response = requests.get(
        f"{BASE_URL}/exchange/{token_data['token']}",
        headers={"Accept": "application/json"}
    )
    
    if exchange_response.status_code != 200:
        print(f"Error getting exchange info: {exchange_response.status_code}")
        return
    
    exchange_data = exchange_response.json()
    print(f"Post URL: {exchange_data['post_url']}")
    print(f"Message: {exchange_data['msg']}")
    
    # Step 3: Show HTML response for browser users
    print("\n3. HTML response for browser users...")
    html_response = requests.get(
        f"{BASE_URL}/exchange/{token_data['token']}",
        headers={"Accept": "text/html"}
    )
    
    if html_response.status_code != 200:
        print(f"Error getting HTML response: {html_response.status_code}")
        return
    
    print("HTML response received successfully")
    print(f"Content-Type: {html_response.headers['content-type']}")
    # Print first 200 characters of HTML
    print(f"HTML preview: {html_response.text[:200]}...")
    
    print("\nDemo completed successfully!")

def public_demo_flow():
    print("\nHTIDP Public Demo Flow")
    print("======================")
    
    # Step 1: Someone requests a token via the public endpoint
    print("\n1. Someone requests a token via the public endpoint...")
    token_response = requests.post(
        f"{BASE_URL}/public-request-token",
        json={"msg": "I found your website and would like to connect!"}
    )
    
    if token_response.status_code != 200:
        print(f"Error requesting token: {token_response.status_code}")
        return
    
    token_data = token_response.json()
    print(f"Token: {token_data['token']}")
    print(f"Link: {token_data['link']}")
    
    print("\nPublic demo completed successfully!")

if __name__ == "__main__":
    demo_flow()
    public_demo_flow()