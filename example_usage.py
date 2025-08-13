"""
Example usage of the HTIDP API
"""
import requests
import json

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000/v1"

def demo_flow():
    print("HTIDP Demo Flow")
    print("==============")
    
    # Step 1: Alice requests a token
    print("\n1. Alice requests a token...")
    token_response = requests.post(
        f"{BASE_URL}/request-token",
        json={"requester_name": "Alice"}
    )
    
    if token_response.status_code != 200:
        print(f"Error requesting token: {token_response.status_code}")
        return
    
    token_data = token_response.json()
    print(f"Token: {token_data['token']}")
    print(f"Link: {token_data['link']}")
    
    # Step 2: Bob uses the token to get exchange info
    print("\n2. Bob gets exchange info...")
    exchange_response = requests.get(
        f"{BASE_URL}/exchange/{token_data['token']}"
    )
    
    if exchange_response.status_code != 200:
        print(f"Error getting exchange info: {exchange_response.status_code}")
        return
    
    exchange_data = exchange_response.json()
    print(f"Post URL: {exchange_data['post_url']}")
    print(f"Requester name: {exchange_data['requester_name']}")
    
    print("\nDemo completed successfully!")

if __name__ == "__main__":
    demo_flow()