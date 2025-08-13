from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from ..models import (
    TokenRequest, TokenResponse, ExchangeRequest, 
    VCard, ContactInfoResponse
)
from ..service import htidp_service

router = APIRouter()

@router.post("/request-token", response_model=TokenResponse)
async def request_token(token_request: TokenRequest):
    """
    Request a new link+token for sharing contact information
    """
    return htidp_service.generate_token(token_request.requester_name)

@router.get("/exchange/{token}")
async def get_exchange_info(token: str):
    """
    Get exchange information for a token
    This endpoint would return either HTML or JSON with:
    - URL to POST the form or data to
    - Name or nickname selected by the requester
    """
    # First check if this is a valid, unused token
    token_info = htidp_service.validate_token(token)
    if not token_info:
        # Check if this token was already used and has connection info
        connection_info = htidp_service.get_connection_info(token)
        if connection_info:
            return connection_info
        raise HTTPException(status_code=404, detail="Token not found or expired")
    
    # Return exchange information
    return {
        "post_url": f"/v1/exchange/{token}",
        "requester_name": token_info["requester_name"]
    }

@router.post("/exchange/{token}")
async def process_exchange(token: str, exchange_request: ExchangeRequest):
    """
    Process the exchange of contact information between servers
    """
    # Verify the token in the request matches the path parameter
    if exchange_request.token != token:
        raise HTTPException(status_code=400, detail="Token mismatch")
        
    try:
        # Process the exchange
        result = htidp_service.process_exchange(token, exchange_request)
        
        if result:
            # In a real implementation, we would send our information
            # to the callback URL
            return {"status": "success", "message": "Exchange completed"}
        else:
            raise HTTPException(status_code=400, detail="Exchange failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/contact/{contact_id}", response_model=ContactInfoResponse)
async def get_contact_info(contact_id: str):
    """
    Get contact information with passkey challenge
    """
    contact_info = htidp_service.get_contact_info(contact_id)
    if not contact_info:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return contact_info

@router.head("/contact/{contact_id}")
async def check_contact_update(contact_id: str, request: Request):
    """
    Check if contact information has changed since a timestamp
    """
    # In a real implementation, we would:
    # 1. Extract timestamp from headers
    # 2. Decrypt it with the public key
    # 3. Compare with last updated time
    # 4. Return appropriate headers indicating changes
    
    contact_info = htidp_service.get_contact_info(contact_id)
    if not contact_info:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # For demonstration, we'll just return headers indicating
    # the resource exists
    response = JSONResponse(content={})
    response.headers["Last-Modified"] = contact_info.last_updated.isoformat()
    return response

# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}