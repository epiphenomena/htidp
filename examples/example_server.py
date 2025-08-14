"""
Example HTIDP server that can be used with the client.html demo
"""
import uvicorn
import argparse
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os

# Create the example app
app = FastAPI(
    title="HTIDP Example Server",
    description="Example server for HTIDP client demo",
    version="1.0.0"
)

# Serve static files (including our client.html)
static_dir = os.path.join(os.path.dirname(__file__))
if os.path.exists(static_dir):
    app.mount("/examples", StaticFiles(directory=static_dir), name="examples")

# Simple in-memory storage for demo purposes
contacts = {}
exchanges = {}

@app.get("/")
async def root():
    return {
        "message": "HTIDP Example Server",
        "docs": "/docs",
        "client_demo": "/examples/client.html"
    }

@app.get("/contact/{contact_id}")
async def get_contact(contact_id: str):
    """Get contact information by ID"""
    if contact_id not in contacts:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return contacts[contact_id]

@app.post("/contact")
async def create_contact(contact: dict):
    """Create a new contact"""
    contact_id = len(contacts) + 1
    contact["id"] = contact_id
    contacts[contact_id] = contact
    return {"id": contact_id, "message": "Contact created successfully"}

@app.post("/exchange")
async def initiate_exchange(exchange: dict):
    """Initiate a contact exchange"""
    exchange_id = len(exchanges) + 1
    exchange["id"] = exchange_id
    exchanges[exchange_id] = exchange
    return {
        "id": exchange_id,
        "message": "Exchange initiated successfully",
        "token": f"exchange-token-{exchange_id}"
    }

@app.get("/exchange/{token}")
async def get_exchange(token: str):
    """Get exchange information by token"""
    # In a real implementation, this would parse the token and return exchange info
    return {
        "post_url": "/exchange/submit",
        "requester_name": "Demo User"
    }

@app.post("/exchange/{token}")
async def process_exchange(token: str, exchange_data: dict):
    """Process an exchange request"""
    return {"status": "success", "message": "Exchange processed successfully"}

@app.head("/contact/{contact_id}")
async def check_contact_update(contact_id: str, request: Request):
    """Check if contact information has been updated"""
    if contact_id not in contacts:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    response = JSONResponse(content={})
    response.headers["Last-Modified"] = "Wed, 21 Oct 2025 07:28:00 GMT"
    return response

def main():
    parser = argparse.ArgumentParser(description="HTIDP Example Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    uvicorn.run(
        "examples.example_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()